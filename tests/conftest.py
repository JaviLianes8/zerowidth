"""Access to the Unicode data files that scripts/fetch_upstream.py fetches into data/ucd/.

The files are not committed: data/ucd/MANIFEST.json pins their URL, Unicode version, size
and sha256. Tests that read them skip while they are absent and fail if one differs.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

UCD = Path(__file__).resolve().parent.parent / "data" / "ucd"
MANIFEST: dict[str, dict[str, Any]] = json.loads(
    (UCD / "MANIFEST.json").read_text(encoding="utf-8")
)


def ucd_fetched() -> bool:
    """True when every file in the manifest is present."""
    return all((UCD / name).is_file() for name in MANIFEST)


needs_ucd = pytest.mark.skipif(
    not ucd_fetched(), reason="Unicode data not fetched; run python scripts/fetch_upstream.py"
)


def ucd_values(name: str) -> dict[int, list[str]]:
    """Map each code point listed in a UCD file to the values given for it."""
    found: dict[int, list[str]] = {}
    for line in (UCD / name).read_text(encoding="utf-8").splitlines():
        data = line.split("#", 1)[0].strip()
        if not data or ";" not in data:
            continue
        points, value = (part.strip() for part in data.split(";", 2)[:2])
        first, _, last = points.partition("..")
        if " " in first:
            continue
        for cp in range(int(first, 16), int(last or first, 16) + 1):
            found.setdefault(cp, []).append(value)
    return found


def with_value(name: str, value: str) -> set[int]:
    """Return the code points a UCD file lists with ``value``."""
    return {cp for cp, values in ucd_values(name).items() if value in values}
