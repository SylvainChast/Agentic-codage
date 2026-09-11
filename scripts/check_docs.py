#!/usr/bin/env python3
"""Catch broken local Markdown document links, without accessing the network."""
import re
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]


def main():
    errors = []
    for path in [ROOT / "README.md", ROOT / "CONTRIBUTING.md", ROOT / "SECURITY.md", *(ROOT / "docs").glob("*.md")]:
        for link in re.findall(r"(?<!!)\[[^\]]+\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
            if "://" in link or link.startswith("#"):
                continue
            target = unquote(link.split("#", 1)[0])
            if not (path.parent / target).exists():
                errors.append(f"{path.relative_to(ROOT)}: missing {target}")
    for error in errors:
        print(error)
    print(f"Documentation links: {len(errors)} error(s)")
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
