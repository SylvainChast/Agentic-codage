"""Immutable document registrations with pinned inputs and independent readiness reviews."""
import hashlib

from .. import leases
from ..store import FrameworkError, covers, digest, now, safe_relative, uid


def editable(task):
    if task['status'] in ('accepted', 'cancelled'):
        raise FrameworkError('Start a new task to change an accepted/cancelled method contract')


def baseline(task):
    data = dict(contract={k: v for k, v in task.items() if k not in ('status', 'acceptance', 'method')},
                story=task.get('method', {}).get('story'))
    if 'architecture' in task.get('method', {}):
        data['architecture'] = task['method']['architecture']
    return digest(data)


def document(store, record):
    safe_relative(record['path'])
    path = store._contained(store.root / record['path'])
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != record['sha256']:
        raise FrameworkError(f"Stale or missing document: {record['id']} ({record['path']})")
    return path


def current(store, record, seen=None):
    seen = set() if seen is None else seen
    if record['id'] in seen:
        raise FrameworkError('Artifact dependency cycle')
    seen = seen | {record['id']}
    document(store, record)
    for ref in record['inputs']:
        parent = store.get('artifacts', ref['artifact'])
        if digest(parent) != ref['digest']:
            raise FrameworkError(f"Changed input registration: {parent['id']}")
        current(store, parent, seen)
    return record


def selected(store, task):
    result = {}
    for ident in task.get('method', {}).get('artifacts', []):
        record = store.get('artifacts', ident)
        if record['kind'] in result:
            raise FrameworkError('Only one selected revision per document kind')
        result[record['kind']] = record
    return result


def initialize(store, task, track, ui):
    editable(task)
    if 'method' in task:
        raise FrameworkError('Method already configured; revise its task contract explicitly')
    task['method'] = dict(track=track, ui=ui, artifacts=[])
    store.put('tasks', task)
    return task


def use(store, task, record):
    editable(task)
    if 'method' not in task:
        raise FrameworkError('Configure method init first')
    current(store, record)
    chosen = selected(store, task)
    chosen[record['kind']] = record
    task['method']['artifacts'] = [r['id'] for r in chosen.values()]
    store.put('tasks', task)
    return record


def register(store, task, kind, path, author, inputs):
    editable(task)
    if 'method' not in task:
        raise FrameworkError('Configure method init first')
    leases.require_lease(store, task)
    if task['status'] != 'active':
        raise FrameworkError('Start the task before registering framing work')
    safe_relative(path)
    if not path.endswith('.md') or not any(covers(scope, path) for scope in task['scope']):
        raise FrameworkError('Artifact must be a Markdown file inside the task scope')
    target = store._contained(store.root / path)
    content = target.read_bytes()
    if not content.decode('utf-8').strip():
        raise FrameworkError('Artifact is empty')
    if kind in ('prd', 'stories'):
        from .templates import validate_selection
        validate_selection(task, kind, content.decode('utf-8'))
    refs = [current(store, store.get('artifacts', ident)) for ident in inputs]
    record = dict(id=uid('artifacts'), created_at=now(), task=task['id'], kind=kind, path=path,
                  sha256=hashlib.sha256(content).hexdigest(), author=author,
                  inputs=[dict(artifact=r['id'], digest=digest(r)) for r in refs])
    if kind == 'architecture' and 'architecture' in task['method']:
        from .starters import validate_choice
        validate_choice(task['method']['architecture'], ready=True)
        record['architecture_basis'] = digest(task['method']['architecture'])
    store.put('artifacts', record, new=True)
    return use(store, task, record)


def closure(store, record):
    current(store, record)
    result = {record['id']: record}
    for ref in record['inputs']:
        result.update(closure(store, store.get('artifacts', ref['artifact'])))
    return result


def review(store, task, ident, reviewer, verdict, summary, findings):
    record = store.get('artifacts', ident)
    if ident not in task.get('method', {}).get('artifacts', []):
        raise FrameworkError('Review a selected task artifact')
    dependencies = closure(store, record)
    if reviewer == task['owner'] or reviewer in {r['author'] for r in dependencies.values()}:
        raise FrameworkError('Readiness reviewer must differ from task owner and document authors')
    if verdict == 'approve' and findings:
        raise FrameworkError('Resolve blocking findings before approving; do not invent findings')
    result = dict(id=uid('artifact_reviews'), created_at=now(), task=task['id'], artifact=ident,
        artifact_digest=digest(record), task_baseline=baseline(task), reviewer=reviewer,
        verdict=verdict, summary=summary, findings=findings)
    store.put('artifact_reviews', result, new=True)
    return result


def approval(store, task, record):
    dependencies = closure(store, record)
    reviews = [r for r in store.all('artifact_reviews') if r['task'] == task['id']
               and r['artifact'] == record['id'] and r['artifact_digest'] == digest(record)
               and r['task_baseline'] == baseline(task)]
    # A rejection of this revision remains blocking: resolve with a new revision/review.
    if not reviews or any(r['verdict'] != 'approve' for r in reviews):
        return False
    authors = {task['owner']} | {r['author'] for r in dependencies.values()}
    return all(r['reviewer'] not in authors and not r['findings'] for r in reviews)


def set_story(store, task, ident, complexity, notes):
    editable(task)
    if 'method' not in task:
        raise FrameworkError('Configure method init first')
    task['method']['story'] = dict(id=ident, complexity=complexity, agent_notes=notes)
    store.put('tasks', task)
    return task
