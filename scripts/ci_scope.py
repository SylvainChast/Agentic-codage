#!/usr/bin/env python3
"""Validate a PR scope using its platform-supplied base SHA and structured body line."""
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from agentic_codage.checks import check
from agentic_codage.store import FrameworkError, Store, canonical


def assess(store, event):
    pr = event["pull_request"]
    base = pr["base"]["sha"]
    body = pr.get("body") or ""
    planning = re.search(r"^Type:\s*planning\s*$", body, re.M | re.I)
    if planning:
        changed = set(store.git("diff", "--name-only", "--no-renames", "-z", base, "--").split("\x00")) - {""}
        allowed = (".framework/tasks/", ".framework/decisions/", ".framework/findings/", "docs/")
        outside = [p for p in changed if not p.startswith(allowed)]
        result = check(store)
        if outside:
            result["errors"].extend(f"Planning PR cannot change: {p}" for p in sorted(outside))
            result["ok"] = False
        # Planning may create contracts, but cannot declare old/new work accepted.
        for task in store.all("tasks"):
            path = f".framework/tasks/{task['id']}.json"
            if path in changed and task["status"] != "planned":
                result["errors"].append(f"Planning task must remain planned: {task['id']}")
                result["ok"] = False
        return result
    match = re.search(r"^(?:Task|Tâche):\s*(T-[A-Za-z0-9_-]+)\s*$", body, re.M)
    if not match:
        raise FrameworkError("PR body requires 'Task: T-ID' or 'Type: planning' on its own line")
    return check(store, base, match.group(1))


def main():
    try:
        event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text(encoding="utf-8"))
        result = assess(Store(Path.cwd()), event)
        print(canonical(result))
        return 0 if result["ok"] else 1
    except (FrameworkError, KeyError, OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
