"""Every ``expression  # -> value`` line in the README must hold."""

from __future__ import annotations

import ast
import re
from pathlib import Path

from zerowidth import scan

ROOT = Path(__file__).resolve().parent.parent
BLOCK = re.compile(r"```python\n(.*?)```", re.S)


def test_documented_results_are_true() -> None:
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    namespace: dict[str, object] = {}
    checked = 0
    for block in BLOCK.findall(text):
        lines: list[str] = []
        for line in block.splitlines():
            if "  # -> " in line:
                exec("\n".join(lines), namespace)
                lines = []
                code, expected = line.split("  # -> ", 1)
                assert eval(code, namespace) == ast.literal_eval(expected), line
                checked += 1
            else:
                lines.append(line)
        exec("\n".join(lines), namespace)
    assert checked >= 18


def test_readme_has_no_raw_hidden_characters() -> None:
    assert scan((ROOT / "README.md").read_text(encoding="utf-8")) == []
