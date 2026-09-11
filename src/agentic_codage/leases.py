"""Local cross-worktree leases. SQLite serializes acquisition, never code writes."""
from __future__ import annotations

import json
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

from .store import FrameworkError, Store, overlaps


@contextmanager
def database(store: Store):
    common = Path(store.git("rev-parse", "--git-common-dir"))
    if not common.is_absolute():
        common = store.root / common
    directory = common.resolve() / "agentic-codage"
    directory.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(directory / "leases.sqlite3", timeout=15)
    try:
        connection.execute("CREATE TABLE IF NOT EXISTS leases (task TEXT PRIMARY KEY, "
                           "owner TEXT NOT NULL, scope TEXT NOT NULL, resources TEXT NOT NULL, "
                           "expires REAL NOT NULL)")
        connection.execute("BEGIN IMMEDIATE")
        connection.execute("DELETE FROM leases WHERE expires <= ?", (time.time(),))
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def list_leases(store: Store) -> list[dict]:
    with database(store) as db:
        return [dict(task=t, owner=o, scope=json.loads(s), resources=json.loads(r), expires=e)
                for t, o, s, r, e in db.execute("SELECT * FROM leases ORDER BY task")]


def acquire(store: Store, task: dict, owner: str, ttl: int) -> dict:
    if ttl < 1 or ttl > 86400:
        raise FrameworkError("Lease ttl must be between 1 and 86400 seconds")
    if owner != task["owner"] or task["status"] in ("accepted", "cancelled"):
        raise FrameworkError("Only the owner of an unfinished task can reserve it")
    with database(store) as db:
        rows = list(db.execute("SELECT * FROM leases"))
        own = [row for row in rows if row[0] == task["id"]]
        if own and own[0][1] != owner:
            raise FrameworkError("Lease is owned by another actor")
        others = [row for row in rows if row[0] != task["id"]]
        if len(others) >= store.policy()["max_active_tasks"]:
            raise FrameworkError("Active task limit reached; finish or release a task")
        for other, _, scope, resources, _ in others:
            if (any(overlaps(a, b) for a in task["scope"] for b in json.loads(scope)) or
                    set(task["resources"]) & set(json.loads(resources))):
                raise FrameworkError(f"Scope or contract is already reserved by {other}")
        expiry = time.time() + ttl
        db.execute("INSERT OR REPLACE INTO leases VALUES (?, ?, ?, ?, ?)",
                   (task["id"], owner, json.dumps(task["scope"]),
                    json.dumps(task["resources"]), expiry))
    return {"task": task["id"], "owner": owner, "expires": expiry}


def require_lease(store: Store, task: dict) -> None:
    matching = [lease for lease in list_leases(store) if lease["task"] == task["id"]]
    if not matching or any(matching[0][k] != task[k] for k in ("owner", "scope", "resources")):
        raise FrameworkError("Acquire or renew a matching lease before starting/submitting")


def release(store: Store, ident: str, owner: str) -> None:
    with database(store) as db:
        row = db.execute("SELECT owner FROM leases WHERE task = ?", (ident,)).fetchone()
        if row and row[0] != owner:
            raise FrameworkError("Cannot release another actor's lease")
        db.execute("DELETE FROM leases WHERE task = ?", (ident,))
