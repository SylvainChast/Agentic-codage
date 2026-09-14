"""One billable invocation, one durable run, including transport failures."""
import threading

from .. import leases
from ..costs import run_cost
from ..lifecycle import record_run
from ..store import FrameworkError
from . import adapters, transport, workspaces


class Calls:
    def __init__(self, store, session):
        self.store, self.session = store, session
        self.lock = threading.Lock()
        self.pending = 0

    def cancelled(self):
        return (workspaces.local(self.store) / self.session['id'] / 'cancel').exists()

    def invoke(self, role, payload, target, item=None, finish=None):
        session, store = self.session, self.store
        profile = session['profile']
        config = profile['roles'][role]
        with self.lock:
            from .coordination import assert_current
            assert_current(store, session)
            task = store.get('tasks', session['task'])
            runs = [r for r in store.all('runs') if r['task'] == task['id']]
            if self.cancelled():
                raise FrameworkError('Execution cancelled')
            if len(runs) + self.pending >= task['max_runs'] or sum(run_cost(r) for r in runs) >= task['budget_minor']:
                raise FrameworkError('Recorded budget/run limit exhausted; no further invocation')
            leases.acquire(store, task, task['owner'], 86400)
            self.pending += 1
            from uuid import uuid4
            scratch = workspaces.local(store) / session['id'] / 'calls' / uuid4().hex
            scratch.mkdir(parents=True)
        decoded = dict(observed_models=[], llm_cost_minor=None, cost_source='unknown',
                       input_tokens=None, output_tokens=None)
        identity, error, outcome, summary = 'unverified', None, 'failed', 'Transport did not complete'
        try:
            argv, text = adapters.request(profile, role, payload, target.root, scratch)
            output = transport.execute(argv, text, target.root, scratch, profile['timeout_seconds'], self.cancelled)
            decoded = adapters.decode(config['adapter'], role, output, scratch, store.policy()['currency'])
            identity, error = adapters.validate_response(profile, role, decoded, payload.get("phase"))
            if error:
                raise FrameworkError(error)
            if finish:
                finish(decoded['result'])
            summary = decoded['result']['summary']
            outcome = 'succeeded'
        except (Exception, KeyboardInterrupt) as exc:
            error = str(exc) or 'Interrupted'
            outcome = 'cancelled' if self.cancelled() or isinstance(exc, KeyboardInterrupt) else 'failed'
            summary = error
        finally:
            with self.lock:
                self.pending -= 1
                record = record_run(store, task=task['id'], actor=f"{session['id']}:{role}:{item or 'main'}",
                    model=config['model'], purpose={'worker': 'implementation', 'reviewer': 'review'}.get(role, 'coordination'),
                    outcome=outcome, currency=store.policy()['currency'], llm_cost_minor=decoded['llm_cost_minor'],
                    infra_cost_minor=0, human_seconds=0, human_rate_minor=0, cost_source=decoded['cost_source'],
                    cost_note=f"{config['adapter']} report; unknown includes unavailable billing or currency conversion. Local logs: {scratch}",
                    summary=summary, next_step='Continue controller or inspect blocked session',
                    input_tokens=decoded['input_tokens'], output_tokens=decoded['output_tokens'],
                    stage={'worker': 'execute', 'reviewer': 'review', 'arbiter': 'execute'}.get(
                        role, 'execute' if payload.get('phase') == 'checkpoint' else 'plan'),
                    orchestration=session['id'], role=role, work_item=item, requested_model=config['model'],
                    observed_models=decoded['observed_models'], identity_status=identity,
                    identity_source=f"{config['adapter']}-reported")
                session['steps'].append(dict(run=record['id'], role=role, item=item, requested_model=config['model'],
                    observed_models=decoded['observed_models'], identity=identity, source=f"{config['adapter']}-reported",
                    outcome=outcome, summary=summary))
                store.put('orchestrations', session)
        if error:
            raise FrameworkError(error)
        return decoded['result']
