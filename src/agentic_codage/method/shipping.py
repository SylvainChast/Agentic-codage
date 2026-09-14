"""Prepare a reviewable PR body locally; publication is an explicit host action."""
from ..checks import check
from ..costs import task_report
from ..evidence import current_evidence
from ..store import FrameworkError, atomic_write
from .workflow import require_ready


def prepare(store, task, base, review_id):
    require_ready(store, task)
    if task['status'] not in ('submitted', 'accepted'):
        raise FrameworkError('Submit and review the implementation before shipping')
    verdict = store.get('reviews', review_id)
    if verdict['task'] != task['id'] or verdict['verdict'] != 'approve':
        raise FrameworkError('Shipping requires an approving implementation review')
    proof = current_evidence(store, task, verdict['evidence'])
    if verdict['contract'] != proof['contract'] or verdict['fingerprint'] != proof['fingerprint']:
        raise FrameworkError('Shipping review is stale')
    result = check(store, base, task['id'])
    if not result['ok']:
        raise FrameworkError('Shipping checks failed: ' + '; '.join(result['errors']))
    diff = store.git('diff', '--stat', base, '--')
    if not diff and not store.git('ls-files', '--others', '--exclude-standard'):
        raise FrameworkError('No change to prepare for shipping')
    costs = task_report(store, task['id'])
    body = (f"# {task['title']}\n\nTask: {task['id']}\n\n"
            "## Result and acceptance criteria\n\n" + '\n'.join(f'- {c}' for c in task['criteria']) +
            f"\n\n## Validation\n\nEvidence: {proof['id']}\nReview: {verdict['id']}\n"
            f"Candidate fingerprint: {proof['fingerprint']}\n\n"
            "## Recorded cost\n\n" +
            f"Known minor units: {costs['known_cost_minor']} {costs['currency']}; "
            f"missing LLM amounts: {costs['missing_cost_runs']}; estimates: {costs['estimated_cost_runs']}.\n\n"
            "## Change summary\n\n```text\n" + diff + '\n```\n')
    from ..orchestration.workspaces import local
    path = local(store) / 'shipping' / task['id'] / 'pr-body.md'
    atomic_write(path, body)
    return dict(ok=True, body_file=str(path), fingerprint=proof['fingerprint'],
                publication='not_started', ci='not_observed',
                next='Inspect and refine the result description, commit scoped changes, then create a draft PR within existing authorization. Recheck after code changes; merging and deployment are separate.')
