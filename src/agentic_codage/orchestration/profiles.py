"""User-selected role configurations; no model tier lists or implicit fallback."""
from pathlib import Path
import shutil
import sys

from ..store import FrameworkError, Store, atomic_write, canonical, read_json, validate_record

ROLES = ("orchestrator", "worker", "reviewer", "arbiter")


def path(store: Store) -> Path:
    return store._contained(store.meta / "orchestration.json")


def load(store: Store) -> dict:
    profile = read_json(path(store))
    validate_profile(profile)
    return profile


def validate_profile(profile):
    validate_record("orchestration-config", profile)
    if profile["max_parallel"] > 16 or profile["max_items"] > 64 or profile["max_rounds"] > 20:
        raise FrameworkError("Local controller limits: parallel <= 16, items <= 64, rounds <= 20")
    if profile["timeout_seconds"] > 3600:
        raise FrameworkError("Invocation timeout must be <= 3600 seconds")
    for role in profile["roles"].values():
        if role["model"] not in role["accepted_models"]:
            raise FrameworkError("accepted_models must include the exact requested model")
        if role["adapter"] != "command" and len(role["command"]) != 1:
            raise FrameworkError("Native adapters accept one executable, not extra CLI flags")
    return profile


def initialize(store: Store, model: str, adapter: str, command: list[str] | None) -> dict:
    config = dict(schema_version=1, roles={name: dict(adapter=adapter, model=model,
                  command=command or [adapter], accepted_models=[model]) for name in ROLES},
                  max_parallel=2, max_rounds=2, max_items=8, timeout_seconds=600,
                  require_model_report=False)
    if adapter == "command" and not command:
        raise FrameworkError("A command adapter requires an explicit executable argv")
    validate_profile(config)
    if path(store).exists():
        raise FrameworkError("Orchestration already configured; use set-role or edit explicitly")
    atomic_write(path(store), canonical(config), exclusive=True)
    return load(store)


def set_role(store: Store, name: str, model: str, adapter: str, command: list[str] | None,
             accepted: list[str]) -> dict:
    profile = load(store)
    if adapter == "command" and not command:
        raise FrameworkError("Command adapter requires --command-json")
    profile["roles"][name] = dict(adapter=adapter, model=model, command=command or [adapter],
                                  accepted_models=list(dict.fromkeys([model, *accepted])))
    validate_profile(profile)
    atomic_write(path(store), canonical(profile))
    return load(store)


def executable(command: list[str], root: Path) -> str:
    first = sys.executable if command[0] == "{python}" else command[0]
    if Path(first).is_absolute():
        resolved = first if Path(first).is_file() else None
    elif "/" in first or "\\" in first:
        resolved = str(root / first) if (root / first).is_file() else None
    else:
        resolved = shutil.which(first)
    if not resolved:
        raise FrameworkError(f"Executable unavailable: {first}; no fallback was attempted")
    return resolved


def doctor(store: Store) -> dict:
    profile = load(store)
    checks = []
    for name, role in profile["roles"].items():
        try:
            binary = executable(role["command"], store.root)
            checks.append(dict(role=name, model=role["model"], executable=binary, available=True))
        except FrameworkError as exc:
            checks.append(dict(role=name, model=role["model"], available=False, error=str(exc)))
    return dict(ok=all(c["available"] for c in checks), roles=checks,
                note="Executable presence only; credentials, account model access and usage are not tested.")
