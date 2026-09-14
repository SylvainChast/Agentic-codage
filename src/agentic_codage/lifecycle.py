"""Explicit task state transitions and append-only run records."""
from . import leases
from .costs import report
from .store import FrameworkError, Store, now, uid


def create_task(store: Store, *, title: str, owner: str, scope: list[str],
                criteria: list[str], deliverables: list[str], budget_minor: int,
                max_runs: int, resources: list[str], decisions: list[str], depends_on: list[str],
                interfaces: list[str] | None = None) -> dict:
    task = dict(id=uid("tasks"), created_at=now(), title=title, owner=owner, scope=scope,
                resources=resources, decisions=decisions, depends_on=depends_on, criteria=criteria,
                deliverables=deliverables, budget_minor=budget_minor, max_runs=max_runs,
                status="planned", acceptance=None)
    if interfaces:
        task['interfaces'] = interfaces
        from .interfaces import for_task
        for_task(store, task)
        task['resources'] = list(dict.fromkeys(resources + [f"interface:{r['name']}" for r in for_task(store, task)]))
    for dependency in depends_on:
        store.get("tasks", dependency)
    for decision in decisions:
        if store.get("decisions", decision)["status"] != "active":
            raise FrameworkError("Task decisions must be active")
    store.put("tasks", task, new=True)
    return task


def transition(store: Store, task: dict, action: str, actor: str) -> dict:
    if actor != task["owner"]:
        raise FrameworkError("Only the declared owner can change task execution state")
    allowed = {"start": ("planned", "active", "submitted"), "submit": ("active",),
               "cancel": ("planned", "active", "submitted")}
    if task["status"] not in allowed[action]:
        raise FrameworkError(f"Cannot {action} a {task['status']} task")
    if action in ("start", "submit"):
        leases.require_lease(store, task)
    if action == "start":
        for dependency in task["depends_on"]:
            if store.get("tasks", dependency)["status"] != "accepted":
                raise FrameworkError(f"Dependency {dependency} is not accepted")
        row = next(row for row in report(store)["tasks"] if row["task"] == task["id"])
        if row["runs"] >= task["max_runs"] or row["known_cost_minor"] >= task["budget_minor"]:
            raise FrameworkError("Run or monetary budget exhausted; revise the task contract before continuing")
    if action == "submit" and not any(r["task"] == task["id"] for r in store.all("runs")):
        raise FrameworkError("Record cost and handoff before submitting")
    task["status"] = {"start": "active", "submit": "submitted", "cancel": "cancelled"}[action]
    store.put("tasks", task)
    if action == "cancel":
        leases.release(store, task["id"], actor)
    return task


def record_run(store: Store, **fields) -> dict:
    task = store.get("tasks", fields["task"])
    if task["status"] == "planned":
        raise FrameworkError("Start the task before recording an execution")
    if fields["currency"] != store.policy()["currency"]:
        raise FrameworkError("Cost currency must match the project")
    if (fields["cost_source"] == "unknown") != (fields["llm_cost_minor"] is None):
        raise FrameworkError("Unknown costs need source=unknown and no amount; other sources need an amount")
    record = dict(id=uid("runs"), created_at=now(), **fields)
    store.put("runs", record, new=True)
    return record
