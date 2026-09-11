"""Strict records, safe paths, atomic writes and candidate fingerprints."""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import subprocess
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

ASSETS = Path(__file__).parent / "assets"
KINDS = ("tasks", "runs", "decisions", "findings", "exceptions", "evidence", "reviews", "orchestrations")
PREFIXES = dict(zip(KINDS, ("T", "R", "D", "F", "X", "E", "V", "O")))


class FrameworkError(Exception):
    """An actionable user or validation error."""


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def uid(kind: str) -> str:
    return f"{PREFIXES[kind]}-{uuid.uuid4().hex[:12]}"


def parse_time(value: str) -> datetime:
    try:
        result = datetime.fromisoformat(value)
        if result.tzinfo is None:
            raise ValueError("timezone required")
        return result
    except ValueError as exc:
        raise FrameworkError(f"Invalid timestamp: {value}") from exc


def safe_relative(value: str) -> str:
    path = PurePosixPath(value)
    if (not value or value.startswith("/") or "\\" in value or
            any(p in (".", "..", ".git") for p in value.split("/")) or
            any(c in value for c in "*?[]:\x00\n\r") or str(path) != value):
        raise FrameworkError(f"Use a literal relative file/directory path: {value!r}")
    return value


def covers(scope: str, path: str) -> bool:
    return path == scope or path.startswith(scope + "/")


def overlaps(left: str, right: str) -> bool:
    return covers(left, right) or covers(right, left)


def read_json(path: Path):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"duplicate key {key}")
            result[key] = value
        return result
    try:
        return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs,
                          parse_constant=lambda s: (_ for _ in ()).throw(ValueError(s)))
    except (OSError, ValueError) as exc:
        raise FrameworkError(f"Cannot read {path}: {exc}") from exc


def canonical(data) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n"


def digest(data) -> str:
    return hashlib.sha256(canonical(data).encode()).hexdigest()


def validate(data, schema: dict, at: str = "record") -> None:
    """Validate the documented JSON Schema subset used by our bundled schemas."""
    types = {"object": dict, "array": list, "string": str, "integer": int,
             "number": (int, float), "boolean": bool, "null": type(None)}
    expected = schema.get("type")
    if expected:
        expected = [expected] if isinstance(expected, str) else expected
        if not any(isinstance(data, types[t]) and
                   not (isinstance(data, bool) and t in ("number", "integer")) for t in expected):
            raise FrameworkError(f"{at}: expected {expected}")
    if isinstance(data, float) and not math.isfinite(data):
        raise FrameworkError(f"{at}: finite number required")
    if "enum" in schema and data not in schema["enum"]:
        raise FrameworkError(f"{at}: expected one of {schema['enum']}")
    if isinstance(data, dict):
        props = schema.get("properties", {})
        for key in schema.get("required", []):
            if key not in data:
                raise FrameworkError(f"{at}: missing {key}")
        for key, value in data.items():
            if key in props:
                validate(value, props[key], f"{at}.{key}")
            elif schema.get("additionalProperties") is False:
                raise FrameworkError(f"{at}: unknown field {key}")
    if isinstance(data, list):
        if len(data) < schema.get("minItems", 0):
            raise FrameworkError(f"{at}: too few items")
        if schema.get("uniqueItems") and len({canonical(v) for v in data}) != len(data):
            raise FrameworkError(f"{at}: duplicate items")
        for i, value in enumerate(data):
            validate(value, schema.get("items", {}), f"{at}[{i}]")
    if isinstance(data, str):
        if len(data.strip()) < schema.get("minLength", 0):
            raise FrameworkError(f"{at}: empty string")
        if "pattern" in schema and not re.fullmatch(schema["pattern"], data):
            raise FrameworkError(f"{at}: invalid format")
    if isinstance(data, (int, float)) and "minimum" in schema and data < schema["minimum"]:
        raise FrameworkError(f"{at}: must be >= {schema['minimum']}")


def validate_record(kind: str, data: dict) -> None:
    validate(data, read_json(ASSETS / "schemas" / f"{kind}.json"), kind)
    for key in ("created_at", "expires_at"):
        if key in data:
            parse_time(data[key])
    for key in ("scope", "paths"):
        for path in data.get(key, []):
            safe_relative(path)


def atomic_write(path: Path, content: str, *, exclusive: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise FrameworkError(f"Refusing symlink: {path}")
    fd, temp = tempfile.mkstemp(dir=path.parent, prefix=".tmp-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        if exclusive:
            os.link(temp, path)  # atomic create without overwriting another process
        else:
            os.replace(temp, path)
    except FileExistsError as exc:
        raise FrameworkError(f"Already exists: {path}") from exc
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


class Store:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.meta = self.root / ".framework"
        self._contained(self.meta)

    def _contained(self, path: Path) -> Path:
        if not path.resolve().is_relative_to(self.root):
            raise FrameworkError(f"Path escapes project: {path}")
        if path.is_symlink():
            raise FrameworkError(f"Refusing symlink: {path}")
        return path

    def policy(self) -> dict:
        data = read_json(self._contained(self.meta / "policy.json"))
        validate_record("policy", data)
        return data

    def path(self, kind: str, ident: str) -> Path:
        if kind not in KINDS or not re.fullmatch(rf"{PREFIXES[kind]}-[A-Za-z0-9_-]+", ident):
            raise FrameworkError(f"Invalid {kind} identifier: {ident}")
        return self._contained(self.meta / kind / f"{ident}.json")

    def get(self, kind: str, ident: str) -> dict:
        data = read_json(self.path(kind, ident))
        validate_record(kind, data)
        if data["id"] != ident:
            raise FrameworkError(f"Filename and id differ: {ident}")
        return data

    def all(self, kind: str) -> list[dict]:
        directory = self._contained(self.meta / kind)
        return [self.get(kind, p.stem) for p in sorted(directory.glob("*.json"))]

    def put(self, kind: str, data: dict, *, new: bool = False) -> None:
        validate_record(kind, data)
        atomic_write(self.path(kind, data["id"]), canonical(data), exclusive=new)

    def git(self, *args: str) -> str:
        result = subprocess.run(["git", "-C", str(self.root), *args],
                                capture_output=True, text=True)
        if result.returncode:
            raise FrameworkError(result.stderr.strip() or "Git command failed")
        return result.stdout.rstrip("\n")

    def head(self) -> str:
        try:
            return self.git("rev-parse", "--verify", "HEAD")
        except FrameworkError:
            return "unborn"

    def fingerprint(self) -> str:
        """Hash Git-visible candidate files, excluding lifecycle records and map."""
        raw = self.git("ls-files", "-z", "--cached", "--others", "--exclude-standard")
        excluded = tuple(f".framework/{kind}/" for kind in KINDS if kind != "decisions")
        result = []
        for name in sorted(set(raw.split("\x00")) - {""}):
            if name.startswith(excluded) or name.startswith(".framework/local/") or name == "docs/carte-du-code.html":
                continue
            path = self.root / name
            if path.is_symlink():
                result.append((name, "symlink", os.readlink(path)))
            elif path.is_file():
                result.append((name, bool(path.stat().st_mode & 0o111),
                               hashlib.sha256(path.read_bytes()).hexdigest()))
            elif path.exists():
                raise FrameworkError(f"Unsupported candidate entry (submodule?): {name}")
            else:
                result.append((name, "deleted"))
        return digest(result)


def task_contract(task: dict) -> str:
    return digest({k: v for k, v in task.items() if k not in ("status", "acceptance")})
