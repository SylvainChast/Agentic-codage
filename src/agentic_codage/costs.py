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
        rows.append(dict(task=task["id"], title=task["title"], status=task["status"],
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
    return dict(currency=policy["currency"], tasks=rows, total_known_cost_minor=total,
                run_count=len(runs), executed_tasks=executed, accepted_tasks=accepted_tasks,
                accepted_deliverables=delivered, complete=complete,
                estimated_cost_runs=sum(row["estimated_cost_runs"] for row in rows),
                missing_cost_runs=sum(row["missing_cost_runs"] for row in rows),
                cost_per_executed_task_minor=total / executed if executed and complete else None,
                cost_per_accepted_task_minor=total / accepted_tasks if accepted_tasks and complete else None,
                cost_per_accepted_deliverable_minor=total / delivered if delivered and complete else None)
