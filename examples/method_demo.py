"""Simulated product preparation and agents; real Git, readiness, tests and PR body."""
from pathlib import Path
import subprocess
import tempfile

from orchestration_demo import BRIDGE
from agentic_codage.bootstrap import initialize
from agentic_codage.store import Store, atomic_write, canonical
from agentic_codage.lifecycle import create_task, transition, record_run
from agentic_codage.leases import acquire
from agentic_codage.method import artifacts, workflow, shipping, templates
from agentic_codage.orchestration import engine, profiles
from agentic_codage.costs import task_report


def main():
    with tempfile.TemporaryDirectory(prefix='agentic-method-demo-') as directory:
        root = Path(directory)
        def git(*args):
            return subprocess.run(['git', '-C', str(root), *args], check=True, capture_output=True)
        git('init', '-q')
        git('config', 'user.name', 'Simulated method demo')
        git('config', 'user.email', 'demo@localhost')
        store = Store(root)
        initialize(store, 'Simulated product delivery', 'EUR')
        (root / '.gitignore').write_text('__pycache__/\n')
        (root / 'src').mkdir()
        (root / 'src/value.py').write_text('value = 0\n')
        bridge = root / 'bridge.py'
        bridge.write_text(BRIDGE)
        policy = store.policy()
        policy['checks'] = [dict(name='value-test', argv=['{python}', '-c',
                               'from src.value import value; assert value == 42'], timeout_seconds=10)]
        atomic_write(store.meta / 'policy.json', canonical(policy))
        profiles.initialize(store, 'SIMULATED-no-LLM', 'command', ['{python}', str(bridge)])
        task = create_task(store, title='Display the required value', owner='fixture-controller',
            scope=['src', 'docs'], criteria=['Value equals 42'], deliverables=['Working value'],
            budget_minor=100, max_runs=20, resources=[], decisions=[], depends_on=[])
        artifacts.initialize(store, task, 'product', True)
        artifacts.set_story(store, task, 'S-value', 2, ['Use an integer, not a formatted string'])
        acquire(store, task, task['owner'], 3600)
        task = transition(store, task, 'start', task['owner'])
        def cost(stage, purpose='coordination', actor='fixture-author'):
            return record_run(store, task=task['id'], actor=actor, model='SIMULATED-no-LLM',
                stage=stage, purpose=purpose, outcome='succeeded', currency='EUR', llm_cost_minor=1,
                infra_cost_minor=0, human_seconds=0, human_rate_minor=0, cost_source='estimate',
                cost_note='Fictitious demonstration amount, no provider call', input_tokens=None,
                output_tokens=None, summary='Scripted fixture step', next_step='Continue fixture')
        documents = {}
        for kind, inputs in [('prd', []), ('architecture', ['prd']), ('design-system', ['prd']),
                             ('stories', ['prd', 'architecture']), ('design', ['stories', 'design-system']),
                             ('plan', ['design', 'stories'])]:
            path = f'docs/{kind}.md'
            text = f'# SIMULATED {kind}\n\nS-value: the user receives the integer 42.\n'
            if kind in templates.KINDS:
                values = {k: text for k in templates.schema(kind)['properties'] if k not in ('kind', 'schema_version')}
                if kind == 'prd':
                    values.update(requirements='REQ-001: return integer 42', acceptance='AC-001: assert value == 42')
                else:
                    values.update(story='S-value: return 42', criteria='AC-001: assert value == 42',
                                  agent_notes='Use an integer, not a formatted string', complexity='Complexité: 2/5 — fixture')
                text = templates.render(kind, values)
            (root / path).write_text(text)
            documents[kind] = artifacts.register(store, task, kind, path, 'fixture-author',
                                                 [documents[k]['id'] for k in inputs])
            cost(kind)
        artifacts.review(store, task, documents['stories']['id'], 'fixture-reviewer',
                         'approve', 'SIMULATED readiness review', [])
        cost('story-review', 'review', 'fixture-reviewer')
        workflow.require_ready(store, task)
        git('add', '.')
        git('commit', '-qm', 'SIMULATED preparation')
        base = store.head()
        session = engine.run(store, task['id'])
        if not session['ok']:
            raise RuntimeError(session['message'])
        engine.integrate(store, session['id'], 'fixture-operator')
        task = store.get('tasks', task['id'])
        prepared = shipping.prepare(store, task, base, session['review'])
        costs = task_report(store, task['id'])
        print(canonical(dict(simulated=True, paid_calls=0, ready=workflow.status(store, task)['ready'],
            accepted=task['status']=='accepted', prepared_pr_body=Path(prepared['body_file']).exists(),
            pr_published=False, delivery=costs['delivery'], by_stage=costs['by_stage'])), end='')


if __name__ == '__main__':
    main()
