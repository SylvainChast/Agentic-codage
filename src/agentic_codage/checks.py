"""Cross-record invariants and optional diff-scope enforcement."""
from __future__ import annotations

from datetime import datetime, timezone

from .costs import report
from .evidence import validate_logs
from .store import FrameworkError, Store, covers, parse_time, task_contract


def check(store: Store, base: str | None = None, task_id: str | None = None) -> dict:
    policy = store.policy()
    records = {kind: {r["id"]: r for r in store.all(kind)} for kind in
               ("tasks", "runs", "decisions", "findings", "exceptions", "evidence", "reviews", "orchestrations")}
    errors, warnings = [], []

    def require(condition, message):
        if not condition:
            errors.append(message)

    tasks, decisions = records["tasks"], records["decisions"]
    for task in tasks.values():
        ident = task["id"]
        for dependency in task["depends_on"]:
            require(dependency in tasks and dependency != ident, f"{ident}: invalid dependency {dependency}")
            if task["status"] in ("active", "submitted", "accepted") and dependency in tasks:
                require(tasks[dependency]["status"] == "accepted", f"{ident}: dependency not accepted")
        for decision in task["decisions"]:
            require(decision in decisions, f"{ident}: unknown decision {decision}")
            if decision in decisions and task["status"] not in ("accepted", "cancelled"):
                require(decisions[decision]["status"] == "active", f"{ident}: decision {decision} is not active")
        own_runs = [r for r in records["runs"].values() if r["task"] == ident]
        if task["status"] in ("submitted", "accepted"):
            require(bool(own_runs), f"{ident}: missing cost/handoff run")
        if len(own_runs) > task["max_runs"]:
            warnings.append(f"{ident}: run budget exceeded; recorded costs retained")
        acceptance = task["acceptance"]
        require((task["status"] == "accepted") == (acceptance is not None), f"{ident}: inconsistent acceptance")
        if acceptance:
            review = records["reviews"].get(acceptance["review"])
            evidence = records["evidence"].get(acceptance["evidence"])
            require(bool(review and evidence), f"{ident}: missing acceptance evidence/review")
            require(acceptance["contract"] == task_contract(task), f"{ident}: accepted contract was modified")
            if review and evidence:
                require(review["task"] == ident and evidence["task"] == ident, f"{ident}: foreign acceptance records")
                require(review["verdict"] == "approve" and evidence["passed"], f"{ident}: acceptance not approved/passed")
                require(review["evidence"] == evidence["id"], f"{ident}: acceptance review/evidence mismatch")
                require(acceptance["fingerprint"] == review["fingerprint"] == evidence["fingerprint"],
                        f"{ident}: inconsistent accepted fingerprint")
                require(acceptance["contract"] == review["contract"] == evidence["contract"],
                        f"{ident}: inconsistent accepted contract")
    # DFS detects cyclic plans, even before execution.
    visited, visiting = set(), set()
    def visit(ident):
        if ident in visiting:
            errors.append(f"Dependency cycle at {ident}")
            return
        if ident in visited or ident not in tasks:
            return
        visiting.add(ident)
        for other in tasks[ident]["depends_on"]:
            visit(other)
        visiting.remove(ident)
        visited.add(ident)
    for ident in tasks:
        visit(ident)
    for run in records["runs"].values():
        require(run["task"] in tasks, f"{run['id']}: unknown task")
        require(run["currency"] == policy["currency"], f"{run['id']}: wrong currency")
        require((run["cost_source"] == "unknown") == (run["llm_cost_minor"] is None),
                f"{run['id']}: inconsistent cost source")
    if (store.meta / "orchestration.json").exists():
        from .orchestration.profiles import load
        try:
            load(store)
        except FrameworkError as exc:
            errors.append(str(exc))
    for session in records["orchestrations"].values():
        require(session["task"] in tasks, f"{session['id']}: unknown task")
        from .orchestration.profiles import validate_profile
        try:
            validate_profile(session["profile"])
        except FrameworkError as exc:
            errors.append(f"{session['id']}: {exc}")
        require(len({s["run"] for s in session["steps"]}) == len(session["steps"]),
                f"{session['id']}: duplicate invocation")
        for step in session["steps"]:
            run = records["runs"].get(step["run"])
            require(bool(run and run.get("orchestration") == session["id"] and run["task"] == session["task"]),
                    f"{session['id']}: missing/foreign invocation")
            if run:
                require(all(step[s] == run.get(r) for s, r in
                            (("role", "role"), ("item", "work_item"), ("requested_model", "requested_model"),
                             ("observed_models", "observed_models"), ("identity", "identity_status"),
                             ("outcome", "outcome"))), f"{session['id']}: invocation/run disagreement")
        if session['status'] in ('ready', 'integrated'):
            proof = records['evidence'].get(session['evidence'])
            rev = records['reviews'].get(session['review'])
            require(bool(proof and rev and proof['task'] == rev['task'] == session['task']
                         and proof['passed'] and rev['verdict'] == 'approve'
                         and rev['evidence'] == proof['id']
                         and proof['fingerprint'] == session['candidate_fingerprint']),
                    f"{session['id']}: incomplete approved candidate")
    for run in records["runs"].values():
        if "orchestration" in run:
            require(run["orchestration"] in records["orchestrations"], f"{run['id']}: unknown orchestration")
    check_names = {c["name"] for c in policy["checks"]}
    require(len(check_names) == len(policy["checks"]), "Duplicate check names")
    for decision in decisions.values():
        require(set(decision["checks"]) <= check_names, f"{decision['id']}: unknown check")
        if decision["status"] == "superseded":
            target = decisions.get(decision["superseded_by"])
            require(bool(target and target["status"] == "active" and target["id"] != decision["id"]),
                    f"{decision['id']}: invalid replacement")
        else:
            require(decision["superseded_by"] is None, f"{decision['id']}: unexpected replacement")
    for finding in records["findings"].values():
        require(finding["status"] != "resolved" or bool(finding["resolution"]),
                f"{finding['id']}: missing resolution evidence")
    for exception in records["exceptions"].values():
        finding = records["findings"].get(exception["finding"])
        require(bool(finding and finding["status"] == "open"), f"{exception['id']}: finding absent/resolved")
        require(parse_time(exception["expires_at"]) > datetime.now(timezone.utc), f"{exception['id']}: expired exception")
    for evidence in records["evidence"].values():
        require(evidence["task"] in tasks, f"{evidence['id']}: unknown task")
        try:
            validate_logs(store, evidence)
        except FrameworkError as exc:
            errors.append(str(exc))
    for review in records["reviews"].values():
        task = tasks.get(review["task"])
        evidence = records["evidence"].get(review["evidence"])
        require(bool(task and evidence), f"{review['id']}: unknown task/evidence")
        if task and evidence:
            implementers = {task["owner"]} | {r["actor"] for r in records["runs"].values()
                                             if r["task"] == task["id"] and r["purpose"] == "implementation"}
            require(review["reviewer"] not in implementers, f"{review['id']}: self-review")
            require(evidence["task"] == task["id"] and review["fingerprint"] == evidence["fingerprint"]
                    and review["contract"] == evidence["contract"], f"{review['id']}: inconsistent evidence")
            # Historical reviews of earlier contracts are retained, not rewritten.
            if review["contract"] == task_contract(task):
                require(set(review["criteria"]) == set(task["criteria"]), f"{review['id']}: incomplete review")
    for path in (store.root / "src").rglob("*.py"):
        if path.is_symlink():
            errors.append(f"Source symlink: {path.relative_to(store.root)}")
            continue
        lines = len(path.read_text(encoding="utf-8").splitlines())
        require(lines <= policy["max_file_lines"], f"{path.relative_to(store.root)}: {lines} lines exceeds policy")
    if base is not None:
        if not task_id:
            raise FrameworkError("--base requires --task (one mission per change)")
        errors.extend(check_scope(store, base, store.get("tasks", task_id)))
    try:
        economics = report(store)
        for row in economics["tasks"]:
            if row["over_budget"]:
                warnings.append(f"{row['task']}: known cost exceeds budget")
        if economics["missing_cost_runs"]:
            warnings.append("Some execution costs are unknown; unit costs are incomplete")
    except FrameworkError as exc:
        errors.append(str(exc))
    return {"ok": not errors, "errors": errors, "warnings": warnings}


def check_scope(store: Store, base: str, task: dict) -> list[str]:
    """Compare candidate to a trusted base, including uncommitted/untracked files."""
    commit = store.git("rev-parse", "--verify", f"{base}^{{commit}}")
    errors = []
    try:
        import json
        original = json.loads(store.git("show", f"{commit}:.framework/tasks/{task['id']}.json"))
    except FrameworkError:
        return ["Task must be registered on the trusted base before implementation; use a planning PR"]
    if task_contract(original) != task_contract(task):
        errors.append("Task contract differs from trusted base; revise it in a separate planning change")
    changed = set(store.git("diff", "--name-only", "--no-renames", "-z", commit, "--").split("\x00"))
    changed.update(store.git("ls-files", "--others", "--exclude-standard", "-z").split("\x00"))
    for name in sorted(changed - {""}):
        if name == f".framework/tasks/{task['id']}.json" or name == "docs/carte-du-code.html":
            continue
        if name.startswith((".framework/runs/", ".framework/reviews/", ".framework/evidence/", ".framework/orchestrations/")):
            kind = name.split("/")[1]
            if name.endswith(".json"):
                record = store.get(kind, name.rsplit("/", 1)[1][:-5])
                if record["task"] == task["id"]:
                    continue
            elif name.endswith(".log") and any(c["log"] == name for e in store.all("evidence")
                                               if e["task"] == task["id"] for c in e["checks"]):
                continue
        if not any(covers(scope, name) for scope in original["scope"]):
            errors.append(f"Outside declared scope: {name}")
    return errors
