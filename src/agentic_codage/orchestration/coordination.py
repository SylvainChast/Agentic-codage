"""Frozen coordination snapshots and mandatory gates between worker batches."""
from ..interfaces import for_task, references, validate_handoff, validate_interfaces
from ..store import FrameworkError, digest, task_contract
from . import workspaces as ws


def initialize(store, task, session):
    validate_interfaces(store)
    from ..method.workflow import packet
    if "method" in task:
        session["method_context"] = packet(store, task, "execute")
    session.update(coordination_version=1, interfaces=for_task(store, task),
                   checkpoints=[], handoffs=[], plans=[])


def snapshot(session):
    return dict(method_context=session.get('method_context'), plan=session['plan'], interfaces=session['interfaces'],
                interface_references=references(session['interfaces']),
                handoffs=list(session['handoffs']), completed_items=list(session['completed_items']),
                checkpoints=list(session['checkpoints']))


def assert_current(store, session):
    task = store.get('tasks', session['task'])
    if task_contract(task) != session['contract']:
        raise FrameworkError('Task contract changed during orchestration; revise and restart')
    if for_task(store, task) != session['interfaces']:
        raise FrameworkError('Pinned interfaces changed during orchestration; revise and restart')
    from ..method.workflow import packet, require_ready
    require_ready(store, task)
    if 'method_context' in session and packet(store, task, 'execute') != session['method_context']:
        raise FrameworkError('Preparation context changed during orchestration; revise and restart')


def handoff(session, item, result, commit):
    validate_handoff(result, session['interfaces'])
    return dict(round=session['round'], item=item['id'], commit=commit, **result)


def checkpoint(store, task, session, candidate, calls, items, base, readonly):
    assert_current(store, session)
    payload = dict(phase='checkpoint', task=task, coordination=snapshot(session),
                   interface_references=references(session['interfaces']),
                   batch=[i['id'] for i in items], base_commit=base,
                   candidate_commit=candidate.head(),
                   diff=ws.patch(candidate, base, candidate.head()).decode(errors='replace'))
    def validate(result):
        if sorted(result['acknowledged_interfaces']) != references(session['interfaces']):
            raise FrameworkError('Checkpoint did not acknowledge the exact pinned interfaces')
    result = readonly(calls, 'orchestrator', payload, candidate, finish=validate)
    session['checkpoints'].append(dict(round=session['round'], items=payload['batch'],
        candidate_commit=candidate.head(), interface_digest=digest(session['interfaces']),
        verdict=result['verdict'], summary=result['summary'], run=session['steps'][-1]['run']))
    store.put('orchestrations', session)
    if result['verdict'] != 'continue':
        raise FrameworkError('Coordination checkpoint blocked: ' + result['summary'])


def validate_session(session):
    """A ready candidate must have a continuing gate for every item of its final plan."""
    required = ('interfaces', 'handoffs', 'plans', 'checkpoints')
    if any(key not in session for key in required):
        raise FrameworkError('Incomplete coordination records')
    if session['status'] not in ('ready', 'integrated'):
        return
    gates = [g for g in session['checkpoints'] if g['round'] == session['round']]
    completed = [item for gate in gates for item in gate['items']]
    expected = {i['id'] for i in session['plan']['items']}
    if set(completed) != expected or len(completed) != len(expected):
        raise FrameworkError('Missing or duplicate mandatory checkpoint')
    steps = {s['run']: s for s in session['steps']}
    for gate in gates:
        step = steps.get(gate['run'])
        if not (gate['verdict'] == 'continue' and gate['interface_digest'] == digest(session['interfaces'])
                and step and step['role'] == 'orchestrator' and step['outcome'] == 'succeeded'):
            raise FrameworkError('Invalid coordination gate')
    if not gates or gates[-1]['candidate_commit'] != session['candidate_commit']:
        raise FrameworkError('Candidate differs from last coordination gate')
    handoffs = [h for h in session['handoffs'] if h['round'] == session['round']]
    if {h['item'] for h in handoffs} != expected or len(handoffs) != len(expected):
        raise FrameworkError('Missing worker handoff')
    for result in handoffs:
        validate_handoff(result, session['interfaces'])
        if result['change_requests'] or not result['commit']:
            raise FrameworkError('Unresolved interface change')
