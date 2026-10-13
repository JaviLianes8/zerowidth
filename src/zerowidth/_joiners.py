"""Find the joiners that UTS #39 section 3.1.1.1 allows (contexts A1, A2 and B)."""

from __future__ import annotations

import unicodedata

from ._props import (
    COMBINING,
    JOIN_DUAL,
    JOIN_LEFT,
    JOIN_RIGHT,
    LETTER,
    NONSPACING,
    TRANSPARENT,
    VIRAMA,
    VOWEL_DEPENDENT,
    joining,
    prop,
    script,
)

ZWNJ = 0x200C
ZWJ = 0x200D


def _mark1(code: int) -> bool:
    # $M1 of UTS #39: a nonspacing mark with a non-zero combining class.
    return bool(code & NONSPACING and code & COMBINING)


def _conjunct_start(codes: list[int], joiner: int) -> int:
    """Match ``$L $M* $V $M1*`` ending just before ``joiner``; return its start or -1."""
    virama = joiner - 1
    while virama >= 0:
        if codes[virama] & VIRAMA:
            letter = virama - 1
            while letter >= 0 and codes[letter] & NONSPACING:
                letter -= 1
            if letter >= 0 and codes[letter] & LETTER:
                return letter
        if not _mark1(codes[virama]):
            return -1
        virama -= 1
    return -1


def _a1(codes: list[int], joiner: int) -> int:
    """Match ``$LJ $T* ZWNJ $RJ`` around ``joiner``; return the start of the match or -1."""
    after = joiner + 1
    if after >= len(codes) or joining(codes[after]) not in (JOIN_RIGHT, JOIN_DUAL):
        return -1
    before = joiner - 1
    while before >= 0 and codes[before] & TRANSPARENT:
        before -= 1
    if before < 0 or joining(codes[before]) not in (JOIN_LEFT, JOIN_DUAL):
        return -1
    return before


def _a2_end(codes: list[int], joiner: int) -> int:
    """The ``$M1* $L`` tail after a ZWNJ; return the index after the letter or -1."""
    after = joiner + 1
    while after < len(codes) and _mark1(codes[after]):
        after += 1
    return after + 1 if after < len(codes) and codes[after] & LETTER else -1


def _acceptable(cps: list[int], codes: list[int], start: int, end: int) -> bool:
    """The global conditions: a single script (Common and Inherited aside) and NFC."""
    scripts = {script(code) for code in codes[start:end]} - {-1}
    text = "".join(map(chr, cps[start:end]))
    return len(scripts) <= 1 and unicodedata.is_normalized("NFC", text)


def joiners_kept(cps: list[int]) -> set[int]:
    """Return the indices of ZWNJ and ZWJ that sit in an allowed context."""
    codes: list[int] | None = None
    kept: set[int] = set()
    for index, cp in enumerate(cps):
        if cp not in (ZWNJ, ZWJ):
            continue
        if codes is None:
            codes = [prop(c) for c in cps]
        spans: list[tuple[int, int]] = []
        if cp == ZWNJ:
            spans.append((_a1(codes, index), index + 2))
            spans.append((_conjunct_start(codes, index), _a2_end(codes, index)))
        else:
            follows = index + 1 < len(codes) and codes[index + 1] & VOWEL_DEPENDENT
            spans.append((_conjunct_start(codes, index), -1 if follows else index + 1))
        if any(s >= 0 and e >= 0 and _acceptable(cps, codes, s, e) for s, e in spans):
            kept.add(index)
    return kept
