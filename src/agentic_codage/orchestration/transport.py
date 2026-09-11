"""Bounded subprocess transport with foreground cancellation and local private logs."""
import os
import signal
import subprocess
import time

from ..store import FrameworkError

LIMIT = 4 * 1024 * 1024


def kill(process):
    if os.name == 'posix':
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    else:
        process.kill()
    process.wait()


def execute(argv, text, root, scratch, timeout, cancelled):
    scratch.mkdir(parents=True, exist_ok=True)
    stdin = scratch / 'input.json'
    stdin.write_text(text, encoding='utf-8')
    out, err = scratch / 'stdout.log', scratch / 'stderr.log'
    started = time.monotonic()
    with stdin.open('rb') as incoming, out.open('wb') as stdout, err.open('wb') as stderr:
        process = subprocess.Popen(argv, cwd=root, stdin=incoming, stdout=stdout, stderr=stderr,
                                   start_new_session=os.name == 'posix')
        try:
            while process.poll() is None:
                if cancelled():
                    raise FrameworkError('Execution cancelled')
                if time.monotonic() - started > timeout:
                    raise FrameworkError('Execution timeout')
                if out.stat().st_size > LIMIT or err.stat().st_size > LIMIT:
                    raise FrameworkError('Adapter output exceeds 4 MiB limit')
                time.sleep(.05)
        except BaseException:
            kill(process)
            raise
    if out.stat().st_size > LIMIT or err.stat().st_size > LIMIT:
        raise FrameworkError('Adapter output exceeds 4 MiB limit')
    if process.returncode:
        raise FrameworkError(f'Adapter exited {process.returncode}; inspect local stderr.log')
    return out.read_text(encoding='utf-8')
