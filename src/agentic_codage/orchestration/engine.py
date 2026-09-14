"""Foreground orchestration; isolated candidates, bounded rounds, explicit integration."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import json

from .. import leases
from ..evidence import accept, current_evidence, review, verify
from ..lifecycle import transition
from ..store import FrameworkError, Store, now, task_contract, uid
from . import profiles, protocol, workspaces as ws
from .calls import Calls
from . import coordination


@contextmanager
def lock(store, task):
    path = ws.local(store) / f'{task}.lock'
    try:
        path.mkdir()
    except FileExistsError as exc:
        raise FrameworkError(f'Controller lock exists: {path}; inspect active processes before removing a stale lock') from exc
    try:
        yield
    finally:
        path.rmdir()


def readonly(calls, role, payload, target, finish=None):
    before = ws.seal(target)
    def validate(result):
        if before != ws.seal(target):
            raise FrameworkError(f'{role} modified its read-only candidate')
        if finish:
            finish(result)
    return calls.invoke(role, payload, target, finish=validate)


def feedback(store, ident, message=None, cancel=False):
    session = store.get('orchestrations', ident)
    if session['status'] != 'running':
        raise FrameworkError('Only a running session accepts feedback/cancellation')
    directory = ws.local(store) / ident
    directory.mkdir(parents=True, exist_ok=True)
    if cancel:
        (directory / 'cancel').touch()
    else:
        from uuid import uuid4
        (directory / f'feedback-{uuid4().hex}.txt').write_text(message, encoding='utf-8')
    return dict(ok=True, session=ident)


def run(store, task_id):
    task = store.get('tasks', task_id)
    from ..method.workflow import require_ready
    require_ready(store, task)
    profile = profiles.load(store)
    if not profiles.doctor(store)["ok"]:
        raise FrameworkError("Adapter executable unavailable; run orchestration doctor")
    if task['status'] not in ('planned', 'active', 'submitted'):
        raise FrameworkError('Task must be executable')
    # Tracked lifecycle records may be dirty; source/config must match committed base.
    base = store.head()
    if base == 'unborn':
        raise FrameworkError('Commit the project and task before orchestration')
    committed = json.loads(store.git('show', f'{base}:.framework/tasks/{task_id}.json'))
    if task_contract(committed) != task_contract(task):
        raise FrameworkError('Commit the current task contract before orchestration')
    session = dict(id=uid('orchestrations'), created_at=now(), task=task_id, profile=profile,
        contract=task_contract(task), base_commit=base, base_fingerprint=store.fingerprint(), status='running',
        round=0, steps=[], plan=None, candidate_commit=None, candidate_fingerprint=None,
        evidence=None, review=None, message='Starting', completed_items=[])
    coordination.initialize(store, task, session)
    with lock(store, task_id):
        candidate = ws.workspace(store, session['id'], 'candidate', base)
        ws.prepare_candidate(store, candidate, base)
        if candidate.fingerprint() != session['base_fingerprint']:
            raise FrameworkError('Commit source/config changes before orchestration; lifecycle records may remain dirty')
        leases.acquire(store, task, task['owner'], 86400)
        task = transition(store, task, 'start', task['owner'])
        store.put('orchestrations', session, new=True)
        calls = Calls(store, session)
        try:
            execute_rounds(store, task, session, candidate, calls)
        except (Exception, KeyboardInterrupt) as exc:
            session['status'] = 'cancelled' if calls.cancelled() or isinstance(exc, KeyboardInterrupt) else 'blocked'
            session['message'] = str(exc) or 'Interrupted'
        finally:
            store.put('orchestrations', session)
            leases.release(store, task_id, task['owner'])
    return dict(ok=session['status'] == 'ready', **session)


def execute_rounds(store, task, session, candidate, calls):
    guidance = ''
    for number in range(1, session['profile']['max_rounds'] + 1):
        session['round'] = number
        messages = [p.read_text(encoding='utf-8') for p in sorted((ws.local(store) / session['id']).glob('feedback-*.txt'))]
        planner = ws.workspace(store, session['id'], f'plan-{number}', candidate.head())
        coordination.assert_current(store, session)
        payload = dict(task=task, guidance=guidance, user_feedback=messages,
                       coordination=coordination.snapshot(session))
        plan = readonly(calls, 'orchestrator', payload, planner)
        protocol.validate_plan(plan, task, session['profile']['max_items'])
        session['plan'], session['completed_items'] = plan, []
        session['plans'].append(dict(round=number, plan=plan))
        store.put('orchestrations', session)
        done = set()
        while len(done) < len(plan['items']):
            items = protocol.batch(plan['items'], done, session['profile']['max_parallel'])
            coordination.assert_current(store, session)
            base = candidate.head()
            shared = coordination.snapshot(session)
            targets = [(item, ws.workspace(store, session['id'], f"r{number}-{item['id']}", base)) for item in items]
            def worker(pair):
                item, target = pair
                def finish(result):
                    from ..interfaces import validate_handoff
                    validate_handoff(result, session['interfaces'])
                    if not result['change_requests']:
                        ws.commit_worker(target, base, item['scope'])
                result = calls.invoke('worker', dict(task=task, item=item, coordination=shared,
                    interface_references=shared['interface_references']), target, item['id'], finish=finish)
                return coordination.handoff(session, item, result,
                    None if result['change_requests'] else target.head())
            # Wait for all dispatched calls even when one fails; retain every cost.
            with ThreadPoolExecutor(max_workers=len(targets)) as pool:
                futures = [pool.submit(worker, pair) for pair in targets]
                heads = []
                errors = []
                for future in futures:
                    try:
                        heads.append(future.result())
                    except Exception as exc:
                        heads.append(None)
                        errors.append(str(exc))
                session['handoffs'].extend(h for h in heads if h is not None)
                store.put('orchestrations', session)
                if errors:
                    raise FrameworkError('; '.join(errors))
                if any(h['change_requests'] for h in heads):
                    raise FrameworkError('Interface change requested; revise the pinned contract before restarting')
            for (item, target), head in zip(targets, heads):
                ws.apply(candidate, ws.patch(target, base, head['commit']))
                ws.commit_worker(candidate, candidate.head(), item['scope'], managed=True)
                done.add(item['id'])
            session['completed_items'] = sorted(done)
            store.put('orchestrations', session)
            coordination.checkpoint(store, task, session, candidate, calls, items, base, readonly)
        ws.sync_records(store, candidate)
        proof = verify(candidate, task['id'])
        ws.copy_evidence(candidate, store, proof)
        session['evidence'] = proof['id']
        if not proof['passed']:
            guidance = 'Required verification failed: ' + json.dumps(proof)
        else:
            task = transition(store, store.get('tasks', task['id']), 'submit', task['owner'])
            candidate.put('tasks', task)
            payload = dict(task=task, evidence=proof, coordination=coordination.snapshot(session), base_commit=session['base_commit'],
                           diff=ws.patch(candidate, session['base_commit'], candidate.head()).decode(errors='replace'))
            verdict = readonly(calls, 'reviewer', payload, candidate)
            record = review(candidate, task, f"{session['id']}:reviewer:main", verdict['verdict'],
                            verdict['summary'], verdict['criteria'], proof['id'])
            store.put('reviews', record, new=True)
            session['review'] = record['id']
            if calls.cancelled():
                raise FrameworkError('Execution cancelled')
            if verdict['verdict'] == 'approve':
                session.update(status='ready', candidate_commit=candidate.head(),
                               candidate_fingerprint=candidate.fingerprint(), message='Verified and reviewed; explicit integration required')
                return
            guidance = verdict['summary']
        if number < session['profile']['max_rounds']:
            guidance = readonly(calls, 'arbiter', dict(task=task, problem=guidance), candidate)['summary']
            task = transition(store, store.get('tasks', task['id']), 'start', task['owner'])
    raise FrameworkError('Round limit reached without approved delivery: ' + guidance)


def integrate(store, ident, actor):
    session = store.get('orchestrations', ident)
    with lock(store, session['task']):
        task = store.get('tasks', session['task'])
        if session['status'] != 'ready' or task_contract(task) != session['contract']:
            raise FrameworkError('Session is not ready or task contract changed')
        coordination.assert_current(store, session)
        if store.head() != session['base_commit'] or store.fingerprint() != session['base_fingerprint']:
            raise FrameworkError('Source changed since launch; create a fresh session')
        candidate = Store(ws.local(store) / ident / 'candidate')
        if candidate.head() != session['candidate_commit'] or candidate.fingerprint() != session['candidate_fingerprint']:
            raise FrameworkError('Candidate changed after review')
        current_evidence(candidate, task, session['evidence'])
        approval = store.get('reviews', session['review'])
        if approval['verdict'] != 'approve' or approval['task'] != task['id']:
            raise FrameworkError('Approving review missing')
        from ..checks import check
        validation = check(store)
        if not validation['ok']:
            raise FrameworkError('Invalid records before integration: ' + '; '.join(validation['errors']))
        if task['status'] != 'submitted' or approval != candidate.get('reviews', session['review']):
            raise FrameworkError('Task/review changed after approval')
        if store.get('evidence', session['evidence']) != candidate.get('evidence', session['evidence']):
            raise FrameworkError('Evidence changed after verification')
        leases.acquire(store, task, task['owner'], 86400)
        try:
            ws.apply(store, ws.patch(candidate, session['base_commit'], session['candidate_commit']))
            result = accept(store, task, session['review'], actor)
            session.update(status='integrated', message='Approved candidate applied to working tree; no branch merge or push')
            store.put('orchestrations', session)
            return dict(ok=True, task=result, session=ident)
        finally:
            leases.release(store, task['id'], task['owner'])
