"""Execute bounded local checks and bind results/reviews to a candidate."""
from __future__ import annotations

import hashlib
import os
import signal
import sys
import subprocess
import time

from .store import FrameworkError, Store, now, task_contract, uid


def verify(store: Store, ident: str) -> dict:
    task = store.get("tasks", ident)
    if task["status"] not in ("active", "submitted"):
        raise FrameworkError("Verify an active or submitted task")
    from .method.workflow import require_ready
    require_ready(store, task)
    policy = store.policy()
    record = dict(id=uid("evidence"), created_at=now(), task=ident,
                  fingerprint=store.fingerprint(), contract=task_contract(task),
                  head=store.head(), checks=[], passed=False)
    for index, check in enumerate(policy["checks"]):
        relative = f".framework/evidence/{record['id']}-{index}.log"
        path = store._contained(store.root / relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        started = time.monotonic()
        with path.open("xb") as log:
            try:
                argv = list(check["argv"])
                if argv[0] == "{python}":
                    argv[0] = sys.executable
                process = subprocess.Popen(argv, cwd=store.root,
                                           stdout=log, stderr=subprocess.STDOUT,
                                           start_new_session=os.name == "posix")
                try:
                    code = process.wait(timeout=check["timeout_seconds"])
                except subprocess.TimeoutExpired:
                    if os.name == "posix":
                        os.killpg(process.pid, signal.SIGKILL)
                    else:
                        process.kill()
                    process.wait()
                    code = 124
                    log.write(b"\nFramework: timeout\n")
            except OSError as exc:
                code = 127
                log.write(str(exc).encode())
        # Keep reports bounded; full output is not a secret store.
        with path.open("rb") as stream:
            content = stream.read(1_048_577)
        if len(content) > 1_048_576:
            content = content[:1_048_576] + b"\n[output truncated]\n"
            path.write_bytes(content)
        record["checks"].append(dict(name=check["name"], argv=check["argv"], exit_code=code,
                                     duration_ms=int((time.monotonic() - started) * 1000),
                                     log=relative, log_sha256=hashlib.sha256(content).hexdigest()))
    record["passed"] = (all(c["exit_code"] == 0 for c in record["checks"]) and
                        record["fingerprint"] == store.fingerprint())
    store.put("evidence", record, new=True)
    return record


def current_evidence(store: Store, task: dict, ident: str) -> dict:
    from .method.workflow import require_ready
    require_ready(store, task)
    evidence = store.get("evidence", ident)
    if (evidence["task"] != task["id"] or not evidence["passed"] or
            evidence["fingerprint"] != store.fingerprint() or
            evidence["contract"] != task_contract(task)):
        raise FrameworkError("Evidence failed, belongs to another task or is stale; verify again")
    expected = [(c["name"], c["argv"]) for c in store.policy()["checks"]]
    if [(c["name"], c["argv"]) for c in evidence["checks"]] != expected:
        raise FrameworkError("Evidence does not cover current required checks")
    validate_logs(store, evidence)
    return evidence


def validate_logs(store: Store, evidence: dict) -> None:
    if evidence["passed"] and any(c["exit_code"] != 0 for c in evidence["checks"]):
        raise FrameworkError("Evidence claims success despite failed checks")
    for index, check in enumerate(evidence["checks"]):
        expected = f".framework/evidence/{evidence['id']}-{index}.log"
        if check["log"] != expected:
            raise FrameworkError("Unexpected evidence log path")
        path = store._contained(store.root / expected)
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != check["log_sha256"]:
            raise FrameworkError(f"Missing or altered log: {expected}")


def review(store: Store, task: dict, reviewer: str, verdict: str, summary: str,
           criteria: list[str], evidence_id: str) -> dict:
    if task["status"] != "submitted":
        raise FrameworkError("Submit the task before review")
    implementers = {task["owner"]} | {r["actor"] for r in store.all("runs")
                                     if r["task"] == task["id"] and r["purpose"] == "implementation"}
    if reviewer in implementers:
        raise FrameworkError("Reviewer must differ from all declared implementers")
    if set(criteria) != set(task["criteria"]):
        raise FrameworkError("Review must address every acceptance criterion exactly")
    evidence = current_evidence(store, task, evidence_id)
    record = dict(id=uid("reviews"), created_at=now(), task=task["id"], reviewer=reviewer,
                  verdict=verdict, summary=summary, criteria=criteria,
                  fingerprint=evidence["fingerprint"], contract=task_contract(task), evidence=evidence_id)
    store.put("reviews", record, new=True)
    return record


def accept(store: Store, task: dict, review_id: str, actor: str) -> dict:
    if task["status"] != "submitted":
        raise FrameworkError("Only submitted tasks can be accepted")
    record = store.get("reviews", review_id)
    if record["task"] != task["id"] or record["verdict"] != "approve":
        raise FrameworkError("An approving review for this task is required")
    evidence = current_evidence(store, task, record["evidence"])
    if record["fingerprint"] != evidence["fingerprint"] or record["contract"] != task_contract(task):
        raise FrameworkError("Review is stale")
    if not any(r["task"] == task["id"] for r in store.all("runs")):
        raise FrameworkError("Record execution cost and handoff before acceptance (unknown is allowed)")
    task["status"] = "accepted"
    task["acceptance"] = dict(review=review_id, evidence=evidence["id"],
                              fingerprint=evidence["fingerprint"], contract=task_contract(task),
                              accepted_by=actor, accepted_at=now(),
                              run_ids=sorted(r["id"] for r in store.all("runs") if r["task"] == task["id"]))
    store.put("tasks", task)
    return task
