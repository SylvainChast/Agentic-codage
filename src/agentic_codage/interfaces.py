"""Versioned interface agreements, pinned to tasks and visible in every worktree."""
from .store import FrameworkError, digest, validate_record


def validate_interfaces(store):
    records = store.all('interfaces')
    by_id = {r['id']: r for r in records}
    versions = set()
    checks = {c['name'] for c in store.policy()['checks']}
    for record in records:
        key = (record['name'], record['version'])
        if key in versions:
            raise FrameworkError('Duplicate interface name/version')
        versions.add(key)
        if not set(record['checks']) <= checks:
            raise FrameworkError(f"{record['id']}: unknown interface check")
        previous = by_id.get(record['supersedes'])
        if record['version'] == 1:
            if record['supersedes'] is not None:
                raise FrameworkError('Interface version 1 cannot supersede a revision')
        elif not (previous and previous['name'] == record['name']
                  and previous['version'] == record['version'] - 1):
            raise FrameworkError('Interface revision must supersede the preceding version')
    return records


def import_interface(store, record):
    validate_record('interfaces', record)
    # Preflight through a read-only overlay: invalid imports never persist.
    class Overlay:
        def all(self, kind):
            return store.all(kind) + [record]
        def policy(self):
            return store.policy()
    validate_interfaces(Overlay())
    store.put('interfaces', record, new=True)
    return record


def for_task(store, task):
    records = [store.get('interfaces', ident) for ident in task.get('interfaces', [])]
    if len({r['name'] for r in records}) != len(records):
        raise FrameworkError('Task cannot pin multiple versions of the same interface')
    return records


def references(records):
    return sorted(f"{r['id']}@{r['version']}:{digest(r)}" for r in records)


def validate_handoff(result, records):
    if sorted(result['acknowledged_interfaces']) != references(records):
        raise FrameworkError('Worker did not acknowledge the exact pinned interface revisions')
