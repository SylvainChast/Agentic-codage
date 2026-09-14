"""Focused machine-readable context; no full HTML ingestion required."""
from .store import Store, overlaps, safe_relative


def context(store: Store, path: str) -> dict:
    safe_relative(path)
    related = lambda scopes: any(overlaps(scope, path) for scope in scopes)
    tasks = [task for task in store.all("tasks") if related(task["scope"])]
    identifiers = {task["id"] for task in tasks}
    return dict(path=path, head=store.head(),
                artifacts=[a for a in store.all("artifacts") if a["task"] in identifiers or
                           any(a["id"] in t.get("method", {}).get("artifacts", []) for t in tasks)],
                interfaces=[i for i in store.all("interfaces") if related(i["paths"]) or
                            any(i["id"] in t.get("interfaces", []) for t in tasks)],
                decisions=[d for d in store.all("decisions") if related(d["paths"]) and d["status"] == "active"],
                findings=[f for f in store.all("findings") if related(f["paths"]) and f["status"] == "open"],
                tasks=tasks, handoffs=[r for r in store.all("runs") if r["task"] in identifiers],
                exceptions=[x for x in store.all("exceptions") if related(x["paths"])])
