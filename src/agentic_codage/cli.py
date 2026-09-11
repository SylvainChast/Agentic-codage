"""Provider-independent command line; structured output and stable failure codes."""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

from . import __version__, leases
from .bootstrap import initialize, sync_adapters
from .checks import check
from .context import context
from .costs import report
from .evidence import accept, review, verify
from .lifecycle import create_task, record_run, transition
from .store import ASSETS, KINDS, FrameworkError, Store, canonical, read_json


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="framework", description="Portable agent tasks, costs and quality evidence")
    p.add_argument("--version", action="version", version=__version__)
    p.add_argument("--root", type=Path, default=Path.cwd(), help="Target project root (default: current directory)")
    commands = p.add_subparsers(dest="command", required=True)
    from .orchestration.cli import register
    register(commands)
    init = commands.add_parser("init", help="Initialize safely; never replace existing instructions")
    init.add_argument("--name", required=True)
    init.add_argument("--currency", default="EUR", help="Single project currency, two decimal minor units")
    adapters = commands.add_parser("adapters", help="Generate missing adapters or detect drift")
    adapters.add_argument("--check", action="store_true")
    schema = commands.add_parser("schema", help="Print a bundled JSON Schema")
    schema.add_argument("kind", choices=("policy", *KINDS))
    imp = commands.add_parser("import", help="Validate and append a decision/finding/exception JSON record")
    imp.add_argument("kind", choices=("decisions", "findings", "exceptions"))
    imp.add_argument("file", type=Path)
    ctx = commands.add_parser("context", help="Get relevant tasks, decisions, risks and handoffs")
    ctx.add_argument("path")
    commands.add_parser("costs", help="Per-task and portfolio costs, including failures and unknowns")
    mapper = commands.add_parser("map", help="Build the offline HTML snapshot")
    mapper.add_argument("--check", action="store_true", help="Fail if snapshot data differs from current records")
    validator = commands.add_parser("check", help="Validate records; optionally enforce a trusted diff scope")
    validator.add_argument("--base")
    validator.add_argument("--task")
    proof = commands.add_parser("verify", help="Execute configured checks; preserve logs and candidate hash")
    proof.add_argument("task")
    task = commands.add_parser("task", help="Create, inspect and progress task contracts")
    actions = task.add_subparsers(dest="action", required=True)
    create = actions.add_parser("create")
    for field in ("title", "owner"):
        create.add_argument(f"--{field}", required=True)
    for field in ("scope", "criterion", "deliverable"):
        create.add_argument(f"--{field}", action="append", required=True)
    for field in ("resource", "decision", "depends-on"):
        create.add_argument(f"--{field}", action="append", default=[])
    create.add_argument("--budget-minor", type=int, required=True, help="Budget in cents (e.g. 2000 = EUR 20)")
    create.add_argument("--max-runs", type=int, default=5)
    actions.add_parser("list")
    show = actions.add_parser("show")
    show.add_argument("task")
    for action in ("start", "submit", "cancel", "accept"):
        sub = actions.add_parser(action)
        sub.add_argument("task")
        sub.add_argument("--actor", required=True)
        if action == "accept":
            sub.add_argument("--review", required=True)
    lease = commands.add_parser("lease", help="Atomic leases shared by worktrees in one Git clone")
    lease_actions = lease.add_subparsers(dest="action", required=True)
    lease_actions.add_parser("list")
    for action in ("acquire", "release"):
        sub = lease_actions.add_parser(action)
        sub.add_argument("task")
        sub.add_argument("--owner", required=True)
        if action == "acquire":
            sub.add_argument("--ttl", type=int, default=3600)
    run = commands.add_parser("run", help="Record each execution, its costs and journal")
    run_actions = run.add_subparsers(dest="action", required=True)
    record = run_actions.add_parser("record")
    record.add_argument("task")
    for field in ("actor", "model", "summary", "next-step", "cost-note"):
        record.add_argument(f"--{field}", required=True)
    record.add_argument("--purpose", choices=("implementation", "review", "coordination"), default="implementation")
    record.add_argument("--outcome", choices=("succeeded", "failed", "blocked", "cancelled"), required=True)
    record.add_argument("--currency", help="Defaults to project currency")
    record.add_argument("--cost-source", choices=("actual", "estimate", "unknown"), required=True)
    for field in ("llm-cost-minor", "input-tokens", "output-tokens"):
        record.add_argument(f"--{field}", type=int)
    for field in ("infra-cost-minor", "human-seconds", "human-rate-minor"):
        record.add_argument(f"--{field}", type=int, default=0)
    reviewer = commands.add_parser("review", help="Record independent review of current evidence")
    review_actions = reviewer.add_subparsers(dest="action", required=True)
    record = review_actions.add_parser("record")
    record.add_argument("task")
    for field in ("reviewer", "summary", "evidence"):
        record.add_argument(f"--{field}", required=True)
    record.add_argument("--verdict", choices=("approve", "request_changes"), required=True)
    record.add_argument("--criterion", action="append", required=True)
    return p


def dispatch(args) -> object:
    store = Store(args.root)
    command = args.command
    if command == "init":
        return initialize(store, args.name, args.currency)
    if command == "schema":
        return read_json(ASSETS / "schemas" / f"{args.kind}.json")
    if command == "adapters":
        return sync_adapters(store, args.check)
    store.policy()
    if command == "orchestration":
        from .orchestration.cli import dispatch as orchestration_dispatch
        return orchestration_dispatch(store, args)
    if command == "import":
        data = read_json(args.file)
        store.put(args.kind, data, new=True)
        return data
    if command == "context":
        return context(store, args.path)
    if command == "costs":
        return report(store)
    if command == "check":
        return check(store, args.base, args.task)
    if command == "map":
        from .map import render
        return render(store, args.check)
    if command == "verify":
        result = check(store)
        if not result["ok"]:
            raise FrameworkError("Fix record validation before verification: " + "; ".join(result["errors"]))
        return verify(store, args.task)
    if command == "task":
        if args.action == "create":
            return create_task(store, title=args.title, owner=args.owner, scope=args.scope,
                               criteria=args.criterion, deliverables=args.deliverable,
                               budget_minor=args.budget_minor, max_runs=args.max_runs,
                               resources=args.resource, decisions=args.decision, depends_on=args.depends_on)
        if args.action == "list":
            return store.all("tasks")
        task = store.get("tasks", args.task)
        if args.action == "show":
            return task
        if args.action == "accept":
            validation = check(store)
            if not validation["ok"]:
                raise FrameworkError("Fix validation before accepting: " + "; ".join(validation["errors"]))
            result = accept(store, task, args.review, args.actor)
            leases.release(store, args.task, task["owner"])
            return result
        return transition(store, task, args.action, args.actor)
    if command == "lease":
        if args.action == "list":
            return leases.list_leases(store)
        if args.action == "acquire":
            return leases.acquire(store, store.get("tasks", args.task), args.owner, args.ttl)
        leases.release(store, args.task, args.owner)
        return {"ok": True, "released": args.task}
    if command == "run":
        fields = {key: value for key, value in vars(args).items() if key not in ("root", "command", "action")}
        fields["currency"] = args.currency or store.policy()["currency"]
        return record_run(store, **fields)
    if command == "review":
        return review(store, store.get("tasks", args.task), args.reviewer, args.verdict,
                      args.summary, args.criterion, args.evidence)
    raise FrameworkError("Unknown command")


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    try:
        result = dispatch(args)
        print(canonical(result), end="")
        if isinstance(result, dict) and (result.get("ok") is False or result.get("passed") is False):
            return 1
        return 0
    except (FrameworkError, OSError, sqlite3.Error) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
