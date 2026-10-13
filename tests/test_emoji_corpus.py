"""Every sequence of the Emoji 18.0 data files survives keep_emoji intact."""

from __future__ import annotations

import re

from conftest import UCD, needs_ucd

from zerowidth import scan, strip_invisible

HIDDEN_IN_EMOJI = {0x200D, 0xFE0E, 0xFE0F, *range(0xE0020, 0xE0080)}


def _sequences() -> list[str]:
    found: list[str] = []
    for name in ("emoji-sequences.txt", "emoji-zwj-sequences.txt", "emoji-test.txt"):
        for line in (UCD / name).read_text(encoding="utf-8").splitlines():
            match = re.match(r"^([0-9A-F]{4,6}(?:(?: |\.\.)[0-9A-F]{4,6})*)\s*;", line)
            if not match:
                continue
            points = match.group(1)
            if ".." in points:
                first, last = (int(part, 16) for part in points.split(".."))
                found.extend(chr(cp) for cp in range(first, last + 1))
            else:
                found.append("".join(chr(int(part, 16)) for part in points.split()))
    return found


@needs_ucd
def test_every_listed_sequence_survives_keep_emoji() -> None:
    sequences = _sequences()
    assert len(sequences) > 9000
    broken = [s for s in sequences if strip_invisible(f"x{s}y", keep_emoji=True) != f"x{s}y"]
    assert broken == []


@needs_ucd
def test_every_listed_sequence_survives_back_to_back() -> None:
    text = "".join(_sequences())
    assert scan(text, keep_emoji=True) == []


@needs_ucd
def test_without_keep_emoji_exactly_the_hidden_characters_go() -> None:
    for sequence in _sequences():
        expected = "".join(ch for ch in sequence if ord(ch) not in HIDDEN_IN_EMOJI)
        assert strip_invisible(sequence) == expected
