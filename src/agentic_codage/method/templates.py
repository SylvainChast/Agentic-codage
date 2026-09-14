"""Versioned PRD/story Markdown templates validated through explicit JSON Schemas."""
import re

from .. import leases
from ..store import ASSETS, FrameworkError, atomic_write, covers, read_json, safe_relative, validate

KINDS = ('prd', 'stories')


def schema(kind):
    if kind not in KINDS:
        raise FrameworkError('No strict document template for this kind')
    return read_json(ASSETS / 'schemas' / f'document-{kind}.json')


def render(kind, values=None):
    spec = schema(kind)
    text = f'# {"PRD" if kind == "prd" else "User story"}\n\nDocument: {kind}@1\n'
    for key, field in spec['properties'].items():
        if key in ('kind', 'schema_version'):
            continue
        value = values[key] if values is not None else '{{ ' + field['description'] + ' }}'
        text += f"\n## {field['title']}\n\n{value}\n"
    return text


def parse(kind, text):
    spec = schema(kind)
    if text.count(f'Document: {kind}@1') != 1:
        raise FrameworkError(f'Expected version marker Document: {kind}@1')
    if '{{' in text or '}}' in text:
        raise FrameworkError('Template fields still need completing')
    parts = re.split(r'^## (.+)\s*$', text, flags=re.M)
    headings = parts[1::2]
    if len(headings) != len(set(headings)):
        raise FrameworkError('Duplicate document section')
    sections = dict(zip(headings, parts[2::2]))
    result = dict(schema_version=1, kind=kind)
    for key, field in spec['properties'].items():
        if key in ('kind', 'schema_version'):
            continue
        heading = field['title']
        if heading not in sections:
            raise FrameworkError(f'Missing required document section: {heading}')
        result[key] = sections[heading].strip()
    if set(sections) != {f['title'] for f in spec['properties'].values() if 'title' in f}:
        raise FrameworkError('Unknown level-two section; use level-three headings inside the schema')
    validate(result, spec)
    if kind == 'prd' and not re.search(r'\bREQ-[A-Za-z0-9_-]+', result['requirements']):
        raise FrameworkError('PRD needs stable REQ identifiers')
    acceptance = result['acceptance'] if kind == 'prd' else result['criteria']
    if not re.search(r'\bAC-[A-Za-z0-9_-]+', acceptance):
        raise FrameworkError('Document needs stable AC identifiers')
    return result


def validate_selection(task, kind, text):
    data = parse(kind, text)
    selected = task.get('method', {}).get('story')
    if kind == 'stories' and selected:
        if selected['id'] not in data['story']:
            raise FrameworkError('Story document differs from the selected story')
        if f"Complexité: {selected['complexity']}/5" not in data['complexity']:
            raise FrameworkError('Story complexity differs from its document')
        if any(note not in data['agent_notes'] for note in selected['agent_notes']):
            raise FrameworkError('Agent notes differ from the story document')
    return data


def scaffold(store, task, kind, path):
    from .artifacts import editable
    editable(task)
    leases.require_lease(store, task)
    safe_relative(path)
    if not path.endswith('.md') or not any(covers(s, path) for s in task['scope']):
        raise FrameworkError('Template output must be Markdown inside the task scope')
    target = store._contained(store.root / path)
    atomic_write(target, render(kind), exclusive=True)
    return dict(ok=True, path=path, registered=False,
                next='Complete every section, then method record. Placeholder content cannot be registered.')
