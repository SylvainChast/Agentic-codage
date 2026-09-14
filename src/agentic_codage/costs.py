"""Delivery economics with explicit missing amounts and no currency conversion."""
from decimal import Decimal, ROUND_HALF_UP

from .store import FrameworkError, Store, task_contract
from .evidence import validate_logs


def run_cost(run: dict) -> int:
    human = (Decimal(run["human_seconds"]) * run["human_rate_minor"] / 3600).quantize(
        Decimal("1"), rounding=ROUND_HALF_UP)
    return (run["llm_cost_minor"] or 0) + run["infra_cost_minor"] + int(human)


def report(store: Store) -> dict:
    policy = store.policy()
    tasks, runs = store.all("tasks"), store.all("runs")
    if any(r["currency"] != policy["currency"] for r in runs):
        raise FrameworkError("Mixed currencies: convert explicitly before recording costs")
    if any(r["task"] not in {t["id"] for t in tasks} for r in runs):
        raise FrameworkError("Run references an unknown task")
    rows = []
    for task in tasks:
        own = [r for r in runs if r["task"] == task["id"]]
        known = sum(run_cost(r) for r in own)
        missing = sum(r["llm_cost_minor"] is None for r in own)
        estimated = sum(r["cost_source"] == "estimate" for r in own)
        accepted = 0
        if task["status"] == "accepted":
            approval = task["acceptance"]
            if not approval:
                raise FrameworkError(f"{task['id']}: acceptance record missing")
            rev = store.get("reviews", approval["review"])
            proof = store.get("evidence", approval["evidence"])
            implementers = {task["owner"]} | {r["actor"] for r in own if r["purpose"] == "implementation"}
            if not (rev["task"] == proof["task"] == task["id"] and rev["verdict"] == "approve"
                    and proof["passed"] and rev["reviewer"] not in implementers
                    and rev["evidence"] == proof["id"]
                    and approval["fingerprint"] == rev["fingerprint"] == proof["fingerprint"]
                    and approval["contract"] == rev["contract"] == proof["contract"] == task_contract(task)
                    and set(rev["criteria"]) == set(task["criteria"])):
                raise FrameworkError(f"{task['id']}: inconsistent acceptance cannot count as delivery")
            validate_logs(store, proof)
            accepted = len(task["deliverables"])
        complete = bool(own) and missing == 0
        delivery = delivery_cost(task, own)
        rows.append(dict(task=task["id"], title=task["title"], status=task["status"],
                         delivery=delivery,
                         runs=len(own), failed_runs=sum(r["outcome"] == "failed" for r in own),
                         known_cost_minor=known, missing_cost_runs=missing,
                         estimated_cost_runs=estimated, complete=complete,
                         budget_minor=task["budget_minor"], over_budget=known > task["budget_minor"],
                         accepted_deliverables=accepted,
                         cost_per_accepted_deliverable_minor=known / accepted if accepted and complete else None))
    total = sum(row["known_cost_minor"] for row in rows)
    executed = sum(row["runs"] > 0 for row in rows)
    accepted_tasks = sum(t["status"] == "accepted" for t in tasks)
    delivered = sum(row["accepted_deliverables"] for row in rows)
    complete = bool(runs) and all(row["complete"] for row in rows if row["runs"] or row["status"] == "accepted")
    return dict(currency=policy["currency"], tasks=rows, by_role=group_costs(runs, "role"),
                by_orchestration=group_costs(runs, "orchestration"), by_stage=group_costs(runs, "stage"), total_known_cost_minor=total,
                run_count=len(runs), executed_tasks=executed, accepted_tasks=accepted_tasks,
                accepted_deliverables=delivered, complete=complete,
                estimated_cost_runs=sum(row["estimated_cost_runs"] for row in rows),
                missing_cost_runs=sum(row["missing_cost_runs"] for row in rows),
                cost_per_executed_task_minor=total / executed if executed and complete else None,
                cost_per_accepted_task_minor=total / accepted_tasks if accepted_tasks and complete else None,
                cost_per_accepted_deliverable_minor=total / delivered if delivered and complete else None)


def group_costs(runs, key):
    result = []
    for label in sorted({r[key] for r in runs if r.get(key) is not None}):
        own = [r for r in runs if r.get(key) == label]
        result.append(dict(name=label, runs=len(own), known_cost_minor=sum(run_cost(r) for r in own),
                           missing_cost_runs=sum(r['llm_cost_minor'] is None for r in own),
                           estimated_cost_runs=sum(r['cost_source'] == 'estimate' for r in own)))
    return result


def delivery_cost(task, runs):
    """Accepted scope is frozen by run ids; later accounting remains separately visible."""
    approval = task['acceptance'] if task['status'] == 'accepted' else None
    ids = approval.get('run_ids') if approval else None
    if ids is not None and not set(ids) <= {r['id'] for r in runs}:
        raise FrameworkError(f"{task['id']}: missing delivery execution")
    own = [r for r in runs if r['id'] in ids] if ids is not None else runs
    # Old acceptances have no execution snapshot; do not invent a historical cutoff.
    frozen = ids is not None
    known = sum(run_cost(r) for r in own)
    missing = sum(r['llm_cost_minor'] is None for r in own)
    estimated = sum(r['cost_source'] == 'estimate' for r in own)
    complete = bool(own) and missing == 0
    state = 'in_progress' if not approval else ('incomplete' if not complete else
            'estimated' if estimated else 'recorded')
    if task['status'] == 'cancelled':
        state = 'cancelled'
    return dict(state=state, accepted_at=approval['accepted_at'] if approval else None,
                frozen_run_scope=frozen, run_ids=sorted(r['id'] for r in own),
                runs=len(own), known_cost_minor=known, missing_cost_runs=missing,
                estimated_cost_runs=estimated, complete=complete,
                total_cost_minor=known if approval and complete else None,
                later_recorded_runs=len(runs) - len(own),
                later_known_cost_minor=sum(run_cost(r) for r in runs) - known)


def task_report(store, ident):
    store.get('tasks', ident)
    result = report(store)
    row = next(row for row in result['tasks'] if row['task'] == ident)
    runs = [r for r in store.all('runs') if r['task'] == ident]
    delivery_ids = set(row['delivery']['run_ids'])
    included = [r for r in runs if r['id'] in delivery_ids]
    llm = sum(r['llm_cost_minor'] or 0 for r in included)
    infra = sum(r['infra_cost_minor'] for r in included)
    human = sum(run_cost(r) for r in included) - llm - infra
    return dict(currency=result['currency'], **row,
                unstaged_runs=sum('stage' not in r for r in included),
                unstaged_known_cost_minor=sum(run_cost(r) for r in included if 'stage' not in r),
                components=dict(llm_known_minor=llm, infrastructure_minor=infra, human_minor=human),
                by_stage=group_costs(included, 'stage'), by_purpose=group_costs(included, 'purpose'), by_role=group_costs(included, 'role'),
                by_model=group_costs(included, 'model'), by_work_item=group_costs(included, 'work_item'),
                by_orchestration=group_costs(included, 'orchestration'))
