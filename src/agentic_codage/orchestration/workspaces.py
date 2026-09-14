"""Private Git candidates; explicit patch integration without moving the user's branch."""
from pathlib import Path
import shutil
import subprocess

from ..store import FrameworkError, Store, covers, atomic_write


def local(store):
    common = Path(store.git('rev-parse', '--git-common-dir'))
    if not common.is_absolute():
        common = store.root / common
    result = common.resolve() / 'agentic-codage' / 'orchestration'
    result.mkdir(parents=True, exist_ok=True)
    return result


def workspace(store, session, name, commit):
    path = local(store) / session / name
    store.git('worktree', 'add', '--detach', str(path), commit)
    return Store(path)


def changes(store, base='HEAD'):
    names = set(store.git('diff', '--name-only', '--no-renames', '-z', base, '--').split('\0'))
    names.update(store.git('ls-files', '--others', '--exclude-standard', '-z').split('\0'))
    return sorted(names - {''})


def allowed(name, scopes):
    protected = ('.git', '.framework', '.agents', '.claude', '.cursor', '.windsurf', '.gemini')
    return (not name.startswith(protected) and name not in ('AGENTS.md', 'CLAUDE.md', 'GEMINI.md')
            and name != 'docs/carte-du-code.html' and any(covers(s, name) for s in scopes))


def commit_worker(store, base, scopes, managed=False):
    if store.head() != base:
        raise FrameworkError('Worker changed Git HEAD')
    names = changes(store)
    if managed:
        from ..store import KINDS
        names = [n for n in names if not any(n.startswith(f".framework/{k}/") for k in KINDS)]
    framing_paths = {r['path'] for r in store.all('artifacts')}
    for name in names:
        if name in framing_paths:
            raise FrameworkError(f'Worker modified a registered framing document: {name}; revise preparation first')
        if not allowed(name, scopes):
            raise FrameworkError(f'Worker exceeded scope: {name}')
        if (store.root / name).is_symlink():
            raise FrameworkError(f'Worker created a symlink: {name}')
    if not names:
        return base
    store.git('add', '--all', '--', *names)
    store.git('-c', 'user.name=Agentic controller', '-c', 'user.email=controller@localhost',
              '-c', 'core.hooksPath=/dev/null', '-c', 'commit.gpgSign=false', 'commit', '-m', 'Orchestration candidate')
    return store.head()


def patch(store, base, head):
    result = subprocess.run(['git', '-C', str(store.root), 'diff', '--binary', '--no-ext-diff',
                             '--no-renames', base, head, '--'], capture_output=True, check=True)
    return result.stdout


def apply(store, data):
    if not data:
        return
    for flags in (['--check'], []):
        result = subprocess.run(['git', '-C', str(store.root), 'apply', *flags, '-'],
                                input=data, capture_output=True)
        if result.returncode:
            raise FrameworkError('Candidate patch cannot be applied: ' + result.stderr.decode(errors='replace'))


def sync_records(source, target):
    # Only framework-managed records, never policy/config or source instructions.
    for kind in ('tasks', 'runs', 'decisions', 'findings', 'exceptions', 'reviews', 'evidence', 'orchestrations', 'artifact_reviews'):
        directory = source.meta / kind
        if directory.exists():
            for path in directory.iterdir():
                if path.is_file() and not path.is_symlink():
                    atomic_write(target._contained(target.meta / kind / path.name), path.read_text(encoding="utf-8"))


def copy_evidence(source, target, record):
    target.put('evidence', record, new=True)
    for check in record['checks']:
        path = target._contained(target.root / check['log'])
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source._contained(source.root / check['log']), path)


def seal(store):
    """Include lifecycle metadata to detect edits by a read-only agent as well."""
    import hashlib
    digest = hashlib.sha256(store.head().encode())
    names = store.git('ls-files', '--cached', '--others', '--exclude-standard', '-z').split('\0')
    for name in sorted(set(names) - {''}):
        path = store.root / name
        digest.update(name.encode())
        digest.update(str(path.lstat().st_mode).encode() if path.exists() else b'missing')
        if path.is_file():
            digest.update(path.read_bytes())
    return digest.hexdigest()


def prepare_candidate(source, target, base):
    """Preserve a clean checkout's exact bytes despite Git EOL/smudge conversion."""
    from ..store import KINDS
    def runtime(name):
        return (name == 'docs/carte-du-code.html' or name.startswith('.framework/local/')
                or any(name.startswith(f'.framework/{kind}/') for kind in KINDS if kind not in ('decisions', 'interfaces', 'artifacts')))
    if any(not runtime(name) for name in changes(source, base)):
        raise FrameworkError('Commit source/config changes before orchestration; lifecycle records may remain dirty')
    for name in source.git('ls-files', '--cached', '-z').split('\0'):
        if not name or runtime(name):
            continue
        original = source._contained(source.root / name)
        destination = target._contained(target.root / name)
        if original.is_file():
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(original, destination)
