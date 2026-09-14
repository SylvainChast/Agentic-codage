"""Interface mismatch and semantic gates stop dependent work with every call cost retained."""
from copy import deepcopy
import test_orchestration
from support import ProjectCase
from agentic_codage.interfaces import import_interface, references
from agentic_codage.orchestration import engine
from agentic_codage.store import FrameworkError, now
from agentic_codage.context import context
from agentic_codage.checks import check


def contract(**kw):
    result = dict(id='I-prices-v1', name='prices', version=1, created_at=now(), paths=['src/app.py'],
                  specification='value is an integer count, never a decimal or monetary amount',
                  checks=['test'], supersedes=None)
    result.update(kw)
    return result


class InterfaceTests(ProjectCase):
    def test_import_pinning_context_and_invalid_revisions(self):
        one = import_interface(self.store, contract())
        original = self.store.fingerprint()
        two = import_interface(self.store, contract(id='I-prices-v2', version=2, supersedes=one['id']))
        self.assertNotEqual(original, self.store.fingerprint())
        task = self.task(interfaces=[two['id']])
        self.assertIn('interface:prices', task['resources'])
        self.assertEqual(len(context(self.store, 'src')['interfaces']), 2)
        with self.assertRaisesRegex(FrameworkError, 'multiple versions'):
            self.task(interfaces=[one['id'], two['id']])
        for bad in (contract(id='I-duplicate'), contract(id='I-skipped', version=4, supersedes=two['id']),
                    contract(id='I-check', name='bad', checks=['missing'])):
            with self.assertRaises(FrameworkError): import_interface(self.store, bad)
            self.assertFalse(self.store.path('interfaces', bad['id']).exists())
        self.assertTrue(check(self.store)['ok'], check(self.store))


class CoordinationTests(ProjectCase):
    setup_profile = test_orchestration.OrchestrationTests.setup_profile

    def scenario(self, mode):
        interface = import_interface(self.store, contract())
        task = self.setup_profile(interfaces=[interface['id']])
        bridge = self.root / 'bridge.py'
        script = bridge.read_text()
        if mode == 'stale':
            script = script.replace("acknowledged_interfaces=payload['interface_references'], change_requests=[]",
                                    "acknowledged_interfaces=['I-old@1:wrong'], change_requests=[]")
        if mode == 'change':
            script = script.replace('change_requests=[]', "change_requests=['Need decimal units instead of count']")
        if mode == 'blocked':
            script = script.replace("verdict='continue'", "verdict='block'")
        bridge.write_text(script)
        if mode != "ok":
            self.commit()
        return task, engine.run(self.store, task['id'])

    def test_exact_contract_and_delivery_gates_are_retained(self):
        task, session = self.scenario('ok')
        self.assertTrue(session['ok'], session['message'])
        self.assertEqual(session['handoffs'][0]['acknowledged_interfaces'], references(session['interfaces']))
        self.assertEqual(session['checkpoints'][0]['verdict'], 'continue')
        changed = deepcopy(self.store.get('orchestrations', session['id']))
        changed['checkpoints'] = []
        self.store.put('orchestrations', changed)
        with self.assertRaisesRegex(FrameworkError, 'mandatory checkpoint'):
            engine.integrate(self.store, session['id'], 'human')
        self.assertEqual((self.root / 'src/app.py').read_text(), 'value = 1\n')
        self.store.put('orchestrations', {k: v for k, v in session.items() if k != 'ok'})
        engine.integrate(self.store, session['id'], 'human')
        self.assertEqual(self.store.get('tasks', task['id'])['status'], 'accepted')

    def test_worker_must_acknowledge_exact_version_and_hash(self):
        _, session = self.scenario('stale')
        self.assertFalse(session['ok'])
        self.assertIn('exact pinned', session['message'])
        self.assertEqual(session['steps'][-1]['outcome'], 'failed')
        self.assertEqual(len(self.store.all('runs')), 2)

    def test_interface_change_retained_without_integration_or_review(self):
        _, session = self.scenario('change')
        self.assertFalse(session['ok'])
        self.assertTrue(session['handoffs'][0]['change_requests'])
        self.assertIsNone(session['handoffs'][0]['commit'])
        self.assertFalse(self.store.all('reviews'))
        self.assertEqual((self.root / 'src/app.py').read_text(), 'value = 1\n')

    def test_orchestrator_block_prevents_acceptance_and_retains_cost(self):
        _, session = self.scenario('blocked')
        self.assertFalse(session['ok'])
        self.assertEqual(session['checkpoints'][0]['verdict'], 'block')
        self.assertEqual(len(self.store.all('runs')), 3)
        self.assertFalse(self.store.all('reviews'))

    def test_downstream_receives_completed_handoff_and_cannot_skip_gate(self):
        task = self.setup_profile()
        bridge = self.root / 'bridge.py'
        script = bridge.read_text().replace("items=[dict(id='write', title='Write value', scope=['src/app.py'], criteria=['value 2'], depends_on=[])]",
            "items=[dict(id=n, title=n, scope=['src/'+n+'.py'], criteria=['ok'], depends_on=['a'] if n=='app' else []) for n in ['a','app']]")
        script = script.replace("pathlib.Path('src/app.py').write_text('value = 2\\n')",
            "item=payload['item']['id']\n    if item=='app':\n        assert payload['coordination']['completed_items']==['a']\n        assert payload['coordination']['handoffs'][0]['item']=='a'\n        assert payload['coordination']['checkpoints'][0]['verdict']=='continue'\n    pathlib.Path('src/'+item+'.py').write_text('value = 2\\n')")
        bridge.write_text(script)
        self.commit()
        session = engine.run(self.store, task['id'])
        self.assertTrue(session['ok'], session['message'])
        self.assertEqual(len(session['checkpoints']), 2)
        # Repeat from root with a rejecting gate: downstream is never invoked.
        bridge.write_text(script.replace("verdict='continue'", "verdict='block'"))
        self.commit()
        session = engine.run(self.store, task['id'])
        self.assertFalse(session['ok'])
        self.assertEqual([h['item'] for h in session['handoffs']], ['a'])
