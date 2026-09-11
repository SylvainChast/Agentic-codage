"""Deterministic data snapshot rendered into a self-contained offline HTML map."""
import json
import re

from .checks import check
from .costs import report
from .store import ASSETS, KINDS, FrameworkError, Store, atomic_write, digest, now


def snapshot(store: Store) -> dict:
    return dict(policy=store.policy(), fingerprint=store.fingerprint(),
                records={kind: store.all(kind) for kind in KINDS}, costs=report(store),
                validation=check(store))


def render(store: Store, check_only: bool = False) -> dict:
    path = store._contained(store.root / "docs" / "carte-du-code.html")
    content = snapshot(store)
    if check_only:
        if not path.exists():
            raise FrameworkError("Map missing; run framework map")
        match = re.search(r'<script id="map-data" type="application/json">(.*?)</script>',
                          path.read_text(encoding="utf-8"), re.S)
        try:
            saved = json.loads(match.group(1)) if match else {}
        except ValueError as exc:
            raise FrameworkError("Malformed map data; regenerate") from exc
        if saved.get("content") != content:
            raise FrameworkError("Map snapshot is stale; run framework map")
        return {"ok": True, "snapshot": digest(content), "path": str(path)}
    payload = dict(generated_at=now(), observed_head=store.head(), content=content)
    # Inert JSON still needs protection from HTML's closing-script parser.
    encoded = json.dumps(payload, ensure_ascii=False).replace("<", "\\u003c").replace("&", "\\u0026")
    template = (ASSETS / "map.html").read_text(encoding="utf-8")
    template = template.replace("__MAP_STYLE__", (ASSETS / "map.css").read_text(encoding="utf-8"))
    template = template.replace("__MAP_SCRIPT__", (ASSETS / "map.js").read_text(encoding="utf-8"))
    atomic_write(path, template.replace("__MAP_DATA__", encoded))
    return {"ok": True, "path": str(path), "snapshot": digest(content)}
