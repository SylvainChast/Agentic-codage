"""Offline delegation demonstration: fake model, real subprocesses, Git and checks."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from agentic_codage.bootstrap import initialize
from agentic_codage.lifecycle import create_task
from agentic_codage.orchestration import engine, profiles
from agentic_codage.store import Store, canonical, atomic_write
from agentic_codage.costs import report

BRIDGE = '''import json, pathlib, sys
request = json.load(sys.stdin)
role, payload = request['role'], request['payload']
if role == 'orchestrator':
    result = dict(summary='SIMULATION: plan', items=[dict(id='value', title='Set value', scope=['src/value.py'], criteria=['value equals 42'], depends_on=[])])
elif role == 'worker':
    pathlib.Path('src/value.py').write_text('value = 42\\n')
    result = dict(summary='SIMULATION: deterministic file edit')
elif role == 'reviewer':
    assert pathlib.Path('src/value.py').read_text() == 'value = 42\\n'
    result = dict(summary='SIMULATION: scripted review, no independent LLM', verdict='approve', criteria=payload['task']['criteria'])
else:
    result = dict(summary='SIMULATION: arbitration')
print(json.dumps(dict(result=result, model=request['model'], usage=dict(cost_minor=1, currency='EUR', cost_source='estimate'))))
'''


def main():
    with tempfile.TemporaryDirectory(prefix='agentic-offline-') as directory:
        root = Path(directory)
        def git(*args):
            subprocess.run(['git', '-C', str(root), *args], check=True, capture_output=True)
        git('init', '-q')
        git('config', 'user.name', 'Offline demonstration')
        git('config', 'user.email', 'demo@localhost')
        store = Store(root)
        initialize(store, 'Offline simulated orchestration', 'EUR')
        (root / '.gitignore').write_text('__pycache__/\n', encoding='utf-8')
        (root / 'src').mkdir()
        (root / 'src/value.py').write_text('value = 0\n', encoding='utf-8')
        bridge = root / 'fake_bridge.py'
        bridge.write_text(BRIDGE, encoding='utf-8')
        policy = store.policy()
        policy['checks'] = [dict(name='actual-value-test', argv=['{python}', '-c',
                               'from src.value import value; assert value == 42'], timeout_seconds=10)]
        atomic_write(store.meta / 'policy.json', canonical(policy))
        profiles.initialize(store, 'SIMULATED-no-LLM', 'command', ['{python}', str(bridge)])
        task = create_task(store, title='Offline example', owner='demo-controller', scope=['src/value.py'],
            criteria=['Value equals 42'], deliverables=['Demo value'], budget_minor=100, max_runs=5,
            resources=[], decisions=[], depends_on=[])
        git('add', '.')
        git('commit', '-qm', 'Offline fixture')
        session = engine.run(store, task['id'])
        if not session['ok']:
            raise RuntimeError(session['message'])
        assert (root / 'src/value.py').read_text() == 'value = 0\n'
        engine.integrate(store, session['id'], 'SIMULATED-demo-operator')
        costs = report(store)
        print(canonical(dict(simulated=True, paid_calls=0, state='integrated',
              actual_product_checks='passed', invocations=costs['run_count'],
              fictitious_estimated_cost_minor=costs['total_known_cost_minor'])), end='')


if __name__ == '__main__':
    main()
