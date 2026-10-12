"""The curated set of zero-width and invisible characters."""

from __future__ import annotations

# Code points that render with no glyph or zero advance width and are routinely used to
# smuggle data into text or to defeat copy-paste and search. Each is listed by name so the
# set stays auditable. Most carry Unicode category Cf (format), which the broad option
# detects on its own; the fillers, the combining grapheme joiner and the braille blank are
# not Cf and are why this set is curated rather than category-derived.
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

# Deprecated tag characters: a well-known steganography channel. All carry category Cf.
_TAGS = range(0xE0000, 0xE0080)

INVISIBLE: frozenset[int] = frozenset(_NAMED) | frozenset(_TAGS)
