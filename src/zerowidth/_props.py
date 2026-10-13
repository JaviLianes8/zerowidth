"""Lookup of the embedded Unicode 18.0.0 properties."""

from __future__ import annotations

from bisect import bisect_right

from . import _ucd_data as data

UNICODE_VERSION = data.UNICODE_VERSION
DICP = data.DICP
CF = data.CF
BIDI_CONTROL = data.BIDI_CONTROL
VARIATION_SELECTOR = data.VARIATION_SELECTOR
VISIBLE_FORMAT = data.VISIBLE_FORMAT
EMOJI = data.EMOJI
EXT_PICT = data.EXT_PICT
EMOJI_MODIFIER = data.EMOJI_MODIFIER
EMOJI_VS_BASE = data.EMOJI_VS_BASE
PARAGRAPH = data.PARAGRAPH
TRANSPARENT = data.TRANSPARENT
LETTER = data.LETTER
NONSPACING = data.NONSPACING
COMBINING = data.COMBINING
VIRAMA = data.VIRAMA
VOWEL_DEPENDENT = data.VOWEL_DEPENDENT
JOIN_LEFT = 1 << data.JOINING_SHIFT
JOIN_RIGHT = 2 << data.JOINING_SHIFT
JOIN_DUAL = 3 << data.JOINING_SHIFT


_PALETTE = [int(token, 36) for token in data.CODES.split()]


def _decode(runs: str) -> tuple[list[int], list[int]]:
    """Expand the run tokens into parallel lists of run starts and property codes."""
    starts: list[int] = []
    codes: list[int] = []
    position = 0
    for token in runs.split():
        starts.append(position)
        codes.append(_PALETTE[int(token[:2], 36)])
        position += int(token[2:], 36)
    if position != 0x110000:
        raise RuntimeError("embedded Unicode tables do not cover the code space")
    return starts, codes


_STARTS, _CODES = _decode(data.RUNS)


def prop(cp: int) -> int:
    """Return the packed property code of code point ``cp`` (see scripts/gen_ucd_tables.py)."""
    return _CODES[bisect_right(_STARTS, cp) - 1]


def joining(code: int) -> int:
    """Return the joining bits of a property code: 0, JOIN_LEFT, JOIN_RIGHT or JOIN_DUAL."""
    return code & JOIN_DUAL


def script(code: int) -> int:
    """Return the script index of a property code, or -1 for Common and Inherited."""
    index = code >> data.SCRIPT_SHIFT
    return -1 if index in (data.SCRIPT_COMMON, data.SCRIPT_INHERITED) else index
