"""The curated set of invisible characters and the kind of each hidden character."""

from __future__ import annotations

from typing import Literal, get_args

from ._props import BIDI_CONTROL, CF, DICP, VARIATION_SELECTOR, VISIBLE_FORMAT, prop

Kind = Literal[
    "bidi",
    "joiner",
    "zero-width",
    "tag",
    "variation-selector",
    "filler",
    "format",
    "ignorable",
]
KINDS: tuple[Kind, ...] = get_args(Kind)

# Code points that render with no glyph or zero advance width and are routinely used to
# smuggle data into text or to defeat copy-paste and search. Each is listed by name so the
# set stays auditable and does not move with Unicode versions. Broad mode adds the
# Unicode data on top of it (see ``is_hidden``); the braille blank is the one entry the
# data does not cover, since it is a visible-width symbol that merely draws no dots.
_NAMED: dict[int, str] = {
    0x00AD: "soft hyphen",
    0x034F: "combining grapheme joiner",
    0x061C: "arabic letter mark",
    0x115F: "hangul choseong filler",
    0x1160: "hangul jungseong filler",
    0x17B4: "khmer vowel inherent aq",
    0x17B5: "khmer vowel inherent aa",
    0x180E: "mongolian vowel separator",
    0x200B: "zero width space",
    0x200C: "zero width non-joiner",
    0x200D: "zero width joiner",
    0x200E: "left-to-right mark",
    0x200F: "right-to-left mark",
    0x202A: "left-to-right embedding",
    0x202B: "right-to-left embedding",
    0x202C: "pop directional formatting",
    0x202D: "left-to-right override",
    0x202E: "right-to-left override",
    0x2060: "word joiner",
    0x2061: "function application",
    0x2062: "invisible times",
    0x2063: "invisible separator",
    0x2064: "invisible plus",
    0x2066: "left-to-right isolate",
    0x2067: "right-to-left isolate",
    0x2068: "first strong isolate",
    0x2069: "pop directional isolate",
    0x206A: "inhibit symmetric swapping",
    0x206B: "activate symmetric swapping",
    0x206C: "inhibit arabic form shaping",
    0x206D: "activate arabic form shaping",
    0x206E: "national digit shapes",
    0x206F: "nominal digit shapes",
    0x2800: "braille pattern blank",
    0x3164: "hangul filler",
    0xFEFF: "zero width no-break space",
    0xFFA0: "halfwidth hangul filler",
}

# The tag block: a well-known steganography channel. U+E0001 and U+E0020..U+E007F are Cf;
# the rest of the block is reserved.
_TAGS = range(0xE0000, 0xE0080)

INVISIBLE: frozenset[int] = frozenset(_NAMED) | frozenset(_TAGS)

_JOINERS = frozenset({0x200C, 0x200D})
_ZERO_WIDTH = frozenset({0x200B, 0x2060, 0xFEFF})
_FILLERS = frozenset({0x115F, 0x1160, 0x2800, 0x3164, 0xFFA0})


def is_hidden(cp: int, broad: bool) -> bool:
    """Tell whether ``cp`` is a hidden character in narrow or broad mode."""
    if cp in INVISIBLE:
        return True
    if not broad:
        return False
    code = prop(cp)
    # Prepended concatenation marks are Cf but draw a visible sign over the digits.
    return bool(code & DICP) or (bool(code & CF) and not code & VISIBLE_FORMAT)


def kind_of(cp: int) -> Kind:
    """Classify a hidden code point; the first matching rule wins."""
    code = prop(cp)
    if code & BIDI_CONTROL:
        return "bidi"
    if cp in _JOINERS:
        return "joiner"
    if cp in _ZERO_WIDTH:
        return "zero-width"
    if cp == 0xE0001 or 0xE0020 <= cp <= 0xE007F:
        return "tag"
    if code & VARIATION_SELECTOR:
        return "variation-selector"
    if cp in _FILLERS:
        return "filler"
    return "format" if code & CF else "ignorable"
