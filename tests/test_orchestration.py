"""Offline real subprocess/Git pipeline; this fixture never invokes an LLM."""
import json

from support import ProjectCase
from agentic_codage.store import FrameworkError, canonical, atomic_write, validate_record
from agentic_codage.orchestration import engine, profiles, protocol, adapters
from agentic_codage.costs import report
from agentic_codage.checks import check

BRIDGE = '''import json, sys, pathlib, time
request = json.load(sys.stdin)
role, payload = request['role'], request['payload']
mode = sys.argv[1] if len(sys.argv) > 1 else 'ok'
if mode == 'timeout':
    pathlib.Path(__file__).parent.joinpath('.git','fixture-started').touch()
    time.sleep(10)
if role == 'orchestrator':
    result = dict(summary='Fixture plan', items=[dict(id='write', title='Write value', scope=['src/app.py'], criteria=['value 2'], depends_on=[])])
elif role == 'worker':
    pathlib.Path('src/app.py').write_text('value = 2\\n')
    if mode == 'escape': pathlib.Path('outside.txt').write_text('bad')
    result = dict(summary='Fixture implemented')
elif role == 'reviewer':
    if mode == 'edit': pathlib.Path('src/app.py').write_text('value = 3\\n')
    result = dict(summary='Fixture review', verdict='request_changes' if mode == 'reject' else 'approve', criteria=payload['task']['criteria'])
else: result = dict(summary='Retry the requested implementation')
print(json.dumps(dict(result=result, model='wrong' if mode == 'mismatch' else request['model'], usage=dict(currency='EUR', cost_minor=3, cost_source='estimate', input_tokens=1, output_tokens=1))))
'''


class OrchestrationTests(ProjectCase):
    def setup_profile(self, mode='ok', **task_options):
        bridge = self.root / 'bridge.py'
        bridge.write_text(BRIDGE, encoding='utf-8')
        profiles.initialize(self.store, 'user-chosen-sol-or-opus', 'command', ['{python}', str(bridge), mode])
        self.set_checks(['{python}', '-c', 'from src.app import value; assert value == 2'])
        task = self.task(max_runs=20, **task_options)
        self.commit()
        return task

    def test_full_delivery_and_explicit_integration(self):
        task = self.setup_profile()
        result = engine.run(self.store, task['id'])
        self.assertTrue(result['ok'], result['message'])
        self.assertEqual((self.root / 'src/app.py').read_text(), 'value = 1\n')
        self.assertEqual(len(result['steps']), 3)
        self.assertTrue(check(self.store)['ok'], check(self.store))
        engine.integrate(self.store, result['id'], 'human')
        self.assertEqual((self.root / 'src/app.py').read_text(), 'value = 2\n')
        self.assertTrue(check(self.store)['ok'], check(self.store))
        costs = report(self.store)
        self.assertEqual(costs['accepted_deliverables'], 1)
        self.assertEqual(costs['total_known_cost_minor'], 9)
        self.assertEqual(len(costs['by_role']), 3)

    def test_scope_escape_never_integrates(self):
        task = self.setup_profile('escape')
        result = engine.run(self.store, task['id'])
        self.assertFalse(result['ok'])
        self.assertIn('exceeded scope', result['message'])
        self.assertFalse((self.root / 'outside.txt').exists())
        self.assertEqual(len(self.store.all('runs')), 2)

    def test_readonly_reviewer_cannot_approve_modified_candidate(self):
        task = self.setup_profile('edit')
        result = engine.run(self.store, task['id'])
        self.assertFalse(result['ok'])
        self.assertIn('read-only', result['message'])
        self.assertFalse(self.store.all('reviews'))

    def test_model_mismatch_is_recorded_and_stops_without_fallback(self):
        task = self.setup_profile('mismatch')
        result = engine.run(self.store, task['id'])
        self.assertFalse(result['ok'])
        runs = self.store.all('runs')
        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0]['identity_status'], 'mismatch')
        self.assertEqual(runs[0]['llm_cost_minor'], 3)

    def test_failed_review_arbitration_and_bounded_retry(self):
        task = self.setup_profile('reject')
        result = engine.run(self.store, task['id'])
        self.assertFalse(result['ok'])
        self.assertEqual(result['round'], 2)
        self.assertIn('Round limit', result['message'])
        self.assertEqual([s['role'] for s in result['steps']], ['orchestrator', 'worker', 'reviewer', 'arbiter', 'orchestrator', 'worker', 'reviewer'])
        self.assertEqual(len(self.store.all('reviews')), 2)

    def test_stale_source_blocks_integration(self):
        task = self.setup_profile()
        result = engine.run(self.store, task['id'])
        (self.root / 'src/app.py').write_text('value = 9\n')
        with self.assertRaisesRegex(FrameworkError, 'Source changed'):
            engine.integrate(self.store, result['id'], 'human')
        self.assertEqual((self.root / 'src/app.py').read_text(), 'value = 9\n')

    def test_run_budget_stops_before_next_call(self):
        task = self.setup_profile()
        task['max_runs'] = 1
        self.store.put('tasks', task)
        self.commit()
        result = engine.run(self.store, task['id'])
        self.assertFalse(result['ok'])
        self.assertEqual(len(self.store.all('runs')), 1)

    def test_timeout_records_unknown_cost(self):
        task = self.setup_profile('timeout')
        profile = profiles.load(self.store)
        profile['timeout_seconds'] = 1
        atomic_write(profiles.path(self.store), canonical(profile))
        self.commit()
        result = engine.run(self.store, task['id'])
        self.assertIn('timeout', result['message'])
        self.assertEqual(self.store.all('runs')[0]['cost_source'], 'unknown')

    def test_model_selection_is_user_owned_and_atomic(self):
        self.setup_profile()
        for name in ('sol', 'opus', 'astra', 'fable', 'my-private-model-2028'):
            value = profiles.set_role(self.store, 'orchestrator', name, 'codex', ['{python}'], [])
            self.assertEqual(value['roles']['orchestrator']['model'], name)
        before = profiles.path(self.store).read_bytes()
        with self.assertRaises(FrameworkError):
            profiles.set_role(self.store, 'orchestrator', 'opus', 'codex', ['codex', '--fallback'], [])
        self.assertEqual(before, profiles.path(self.store).read_bytes())

    def test_native_argv_preserves_exact_model(self):
        self.setup_profile()
        scratch = self.root / 'scratch'
        scratch.mkdir()
        for adapter in ('codex', 'claude'):
            config = profiles.set_role(self.store, 'orchestrator', 'custom model', adapter, ['{python}'], [])
            argv, text = adapters.request(config, 'orchestrator', {}, self.root, scratch)
            self.assertEqual(argv[argv.index('--model') + 1], 'custom model')
            self.assertNotIn('--fallback-model', argv)
            self.assertNotIn('--dangerously-skip-permissions', argv)
        config['require_model_report'] = True
        identity, error = adapters.validate_response(config, 'worker', dict(observed_models=[], result={'summary': 'ok'}))
        self.assertEqual(identity, 'unverified')
        self.assertIsNotNone(error)

    def test_dag_rejects_cycles_and_parent_escape(self):
        task = self.task()
        item = dict(id='one', title='one', scope=['src'], criteria=['ok'], depends_on=[])
        plan = dict(summary='plan', items=[item])
        protocol.validate_plan(plan, task, 2)
        item['depends_on'] = ['one']
        with self.assertRaises(FrameworkError): protocol.validate_plan(plan, task, 2)
        item['depends_on'], item['scope'] = [], ['docs']
        with self.assertRaises(FrameworkError): protocol.validate_plan(plan, task, 2)

    def test_repeated_argv_is_valid(self):
        policy = self.store.policy()
        policy['checks'][0]['argv'] = ['python', '-c', 'print(1)', 'same', 'same']
        validate_record('policy', policy)

    def test_parallel_disjoint_workers_and_dependency_observe_merged_code(self):
        task = self.setup_profile()
        bridge = self.root / 'bridge.py'
        script = BRIDGE.replace("mode = sys.argv[1] if len(sys.argv) > 1 else 'ok'", "mode = 'ok'")
        script = script.replace("result = dict(summary='Fixture plan', items=[dict(id='write', title='Write value', scope=['src/app.py'], criteria=['value 2'], depends_on=[])])", "result = dict(summary='DAG', items=[dict(id=n, title=n, scope=['src/'+n+'.py'], criteria=['ok'], depends_on=['a','b'] if n=='app' else []) for n in ['a','b','app']])")
        script = script.replace("pathlib.Path('src/app.py').write_text('value = 2\\n')", "item=payload['item']['id']\n    if item=='app':\n        assert pathlib.Path('src/a.py').read_text()=='1'\n        assert pathlib.Path('src/b.py').read_text()=='1'\n    time.sleep(.2)\n    pathlib.Path('src/'+item+'.py').write_text('value = 2\\n' if item=='app' else '1')")
        bridge.write_text(script, encoding='utf-8')
        self.commit()
        result = engine.run(self.store, task['id'])
        self.assertTrue(result['ok'], result['message'])
        self.assertEqual(set(result['completed_items']), {'a','b','app'})
        engine.integrate(self.store, result['id'], 'human')
        self.assertEqual(report(self.store)['run_count'], 5)

    def test_cancellation_stops_process_and_records_attempt(self):
        import threading
        import time
        task = self.setup_profile('timeout')
        results = []
        thread = threading.Thread(target=lambda: results.append(engine.run(self.store, task['id'])))
        thread.start()
        try:
            deadline = time.monotonic() + 15
            session = None
            while time.monotonic() < deadline:
                sessions = self.store.all('orchestrations')
                if sessions and (self.root / '.git/fixture-started').exists():
                    session = sessions[0]
                    break
                time.sleep(.02)
            self.assertIsNotNone(session)
            engine.feedback(self.store, session['id'], cancel=True)
        finally:
            thread.join(8)
        self.assertFalse(thread.is_alive())
        self.assertEqual(results[0]['status'], 'cancelled')
        self.assertEqual(self.store.all('runs')[0]['outcome'], 'cancelled')

    def test_parallel_budget_reserves_inflight_slots(self):
        task = self.setup_profile()
        task['max_runs'] = 2
        self.store.put('tasks', task)
        bridge = self.root / 'bridge.py'
        script = BRIDGE.replace("items=[dict(id='write', title='Write value', scope=['src/app.py'], criteria=['value 2'], depends_on=[])]", "items=[dict(id=n, title=n, scope=['src/'+n+'.py'], criteria=['ok'], depends_on=[]) for n in ['app','other']]")
        bridge.write_text(script, encoding='utf-8')
        self.commit()
        result = engine.run(self.store, task['id'])
        self.assertFalse(result['ok'])
        self.assertEqual(len(self.store.all('runs')), 2)

    def test_invalid_root_proof_prevents_patch_application(self):
        task = self.setup_profile()
        result = engine.run(self.store, task['id'])
        proof = self.store.get('evidence', result['evidence'])
        (self.root / proof['checks'][0]['log']).write_text('altered')
        with self.assertRaises(FrameworkError):
            engine.integrate(self.store, result['id'], 'human')
        self.assertEqual((self.root / 'src/app.py').read_text(), 'value = 1\n')

    def test_native_response_normalization_does_not_invent_billing(self):
        scratch = self.root / 'native'
        scratch.mkdir()
        (scratch / 'result.json').write_text('{"summary":"ok"}')
        result = adapters.decode('codex', 'worker', '{"type":"turn.completed","usage":{"input_tokens":12,"output_tokens":3}}\n', scratch, 'EUR')
        self.assertEqual(result['observed_models'], [])
        self.assertIsNone(result['llm_cost_minor'])
        data = json.dumps(dict(structured_output={'summary':'ok'}, modelUsage={'exact-model':{}}, total_cost_usd=.125, usage={'input_tokens':10}))
        self.assertEqual(adapters.decode('claude', 'worker', data, scratch, 'USD')['llm_cost_minor'], 13)
        self.assertIsNone(adapters.decode('claude', 'worker', data, scratch, 'EUR')['llm_cost_minor'])

    def test_clean_autocrlf_checkout_keeps_exact_candidate_bytes(self):
        self.git('config', 'core.autocrlf', 'true')
        task = self.setup_profile()
        (self.root / 'src/app.py').write_bytes(b'value = 1\r\n')
        result = engine.run(self.store, task['id'])
        self.assertTrue(result['ok'], result['message'])
        engine.integrate(self.store, result['id'], 'human')
        self.assertTrue(check(self.store)['ok'])
