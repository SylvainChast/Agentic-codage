"""Deterministic readiness and focused context; no paid model calls."""
from ..store import FrameworkError, digest
from . import artifacts, catalog


def status(store, task):
    if 'method' not in task:
        return dict(enabled=False, ready=True, missing=[], problems=[], documents=[])
    method = task['method']
    chosen = artifacts.selected(store, task)
    missing = [kind for kind in catalog.required(method) if kind not in chosen]
    problems, documents = [], []
    if 'architecture' in method:
        from .starters import validate_choice
        try:
            validate_choice(method['architecture'], ready=True)
        except FrameworkError as exc:
            problems.append(str(exc))
    story = method.get('story')
    if method['track'] != 'express' and not story:
        missing.append('Selected story, complexity and agent notes')
    if story and story['complexity'] == 5:
        problems.append('Story complexity 5: split or resolve uncertainty before planning/execution')
    for kind, record in chosen.items():
        try:
            if kind in ('prd', 'stories'):
                from .templates import validate_selection
                validate_selection(task, kind, artifacts.document(store, record).read_text(encoding='utf-8'))
            if kind == 'architecture' and 'architecture' in method:
                if record.get('architecture_basis') != digest(method['architecture']):
                    raise FrameworkError('Architecture document was registered for a different choice; revise and register it again')
            dependencies = artifacts.closure(store, record)
            for dependency in dependencies.values():
                pinned = chosen.get(dependency['kind'])
                if pinned and pinned['id'] != dependency['id']:
                    raise FrameworkError(f"{kind} references an unselected revision of {dependency['kind']}")
            for needed in catalog.parents(kind, method):
                if needed not in chosen or chosen[needed]['id'] not in dependencies:
                    raise FrameworkError(f'{kind} must reference selected {needed}')
            if kind == 'stories' and method['track'] != 'express' and not artifacts.approval(store, task, record):
                raise FrameworkError('Stories need an independent approving readiness review')
            current = True
        except FrameworkError as exc:
            problems.append(str(exc))
            current = False
        documents.append(dict(id=record['id'], kind=kind, path=record['path'], current=current))
    return dict(enabled=True, track=method['track'], ui=method['ui'], ready=not missing and not problems,
                missing=missing, problems=problems, documents=documents)


def require_ready(store, task):
    result = status(store, task)
    if not result['ready']:
        raise FrameworkError('Method not ready: ' + '; '.join(result['missing'] + result['problems']))
    return result


def step_inputs(step, method):
    if step in ('execute', 'review', 'ship'):
        return ['plan', 'design', 'stories', 'architecture', 'design-system', 'prd']
    if step == 'story-review':
        return ['stories', 'prd', 'architecture', 'design-system']
    return catalog.parents(step, method) + {
        'research': [], 'prd': ['research'], 'architecture': ['research'],
        'design-system': ['prd'], 'stories': ['research'],
        'design': ['architecture'], 'plan': [],
    }.get(step, [])


def packet(store, task, step, max_chars=12000):
    if max_chars < 0 or max_chars > 100000:
        raise FrameworkError('Context excerpt allowance must be between 0 and 100000 characters')
    method = task.get('method', dict(track='express', ui=False, artifacts=[]))
    chosen = artifacts.selected(store, task)
    needed = list(dict.fromkeys(step_inputs(step, method)))
    documents, remaining = [], max_chars
    for kind in needed:
        if kind not in chosen:
            continue
        record = chosen[kind]
        artifacts.current(store, record)
        body = artifacts.document(store, record).read_text(encoding='utf-8')
        excerpt = body[:remaining]
        remaining -= len(excerpt)
        documents.append(dict(id=record['id'], kind=kind, path=record['path'], sha256=record['sha256'],
                              excerpt=excerpt, truncated=len(excerpt) < len(body)))
    from ..interfaces import for_task
    result = dict(step=step, task={k: task[k] for k in ('id', 'title', 'scope', 'criteria', 'deliverables')},
        track=method['track'], story=method.get('story'),
        readiness=status(store, task), documents=documents,
        interfaces=for_task(store, task),
        decisions=[store.get('decisions', ident) for ident in task['decisions']],
        excerpt_characters=max_chars-remaining,
        note='Excerpts are bounded characters, not token counts. Read referenced files for omitted detail; never infer missing requirements.')
    if 'architecture' in method:
        result['architecture'] = method['architecture']
    return result


def prompt(store, task, step, max_chars):
    if step == 'plan' and task.get('method', {}).get('story', {}).get('complexity') == 5:
        raise FrameworkError('Story complexity 5: split before planning')
    if step in ('execute', 'review', 'ship'):
        require_ready(store, task)
    return dict(procedure=catalog.procedure(step), context=packet(store, task, step, max_chars))


def validate_records(store):
    """Validate links without treating intentionally retained historical documents as current."""
    records = {r['id']: r for r in store.all('artifacts')}
    for record in records.values():
        task = store.get('tasks', record['task'])
        from ..store import safe_relative
        safe_relative(record['path'])
        visiting = set()
        def visit(ident):
            if ident in visiting:
                raise FrameworkError('Artifact dependency cycle')
            if ident not in records:
                raise FrameworkError('Unknown artifact input')
            visiting.add(ident)
            for ref in records[ident]['inputs']:
                if ref['artifact'] not in records or digest(records[ref['artifact']]) != ref['digest']:
                    raise FrameworkError('Missing or changed artifact input registration')
                visit(ref['artifact'])
            visiting.remove(ident)
        visit(record['id'])
    for review in store.all('artifact_reviews'):
        store.get('tasks', review['task'])
        if review['artifact'] not in records or digest(records[review['artifact']]) != review['artifact_digest']:
            raise FrameworkError('Missing or changed reviewed artifact registration')
    for task in store.all('tasks'):
        if 'architecture' in task.get('method', {}):
            from .starters import validate_choice
            validate_choice(task['method']['architecture'])
        artifacts.selected(store, task)
