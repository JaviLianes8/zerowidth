"""Find the hidden characters that belong to emoji sequences (UTS #51)."""

from __future__ import annotations

import re

from ._props import EMOJI, EMOJI_MODIFIER, EMOJI_VS_BASE, EXT_PICT, prop

ZWJ = 0x200D
VS15 = 0xFE0E
VS16 = 0xFE0F
KEYCAP = 0x20E3
BLACK_FLAG = 0x1F3F4
CANCEL_TAG = 0xE007F
# UTS #51 Annex C: a flag tag spec spells a CLDR subdivision id (a two-letter or
# three-digit region plus one to four letters or digits) or a three-digit region.
_SUBDIVISION = re.compile(r"(?:[a-z]{2}|[0-9]{3})[a-z0-9]{1,4}|[0-9]{3}")


def _tag_end(cps: list[int], start: int) -> int:
    """Return the index after a flag tag spec and its cancel tag at ``start``, or -1."""
    end = start
    while end < len(cps) and (0xE0030 <= cps[end] <= 0xE0039 or 0xE0061 <= cps[end] <= 0xE007A):
        end += 1
    if end - start > 7 or end >= len(cps) or cps[end] != CANCEL_TAG:
        return -1
    spec = "".join(chr(cp - 0xE0000) for cp in cps[start:end])
    return end + 1 if _SUBDIVISION.fullmatch(spec) else -1


def _element(cps: list[int], start: int, kept: set[int]) -> tuple[int, bool]:
    """Parse one emoji ZWJ element at ``start``.

    Returns the end index (``start`` when nothing parses) and whether a joiner may follow.
    The hidden characters of the element are added to ``kept``.
    """
    base = cps[start]
    code = prop(base)
    if not code & (EMOJI | EXT_PICT):
        return start, False
    end = start + 1
    after = cps[end] if end < len(cps) else -1
    if after in (VS15, VS16) and code & EMOJI_VS_BASE:
        kept.add(end)
        end += 1
        if after == VS15:
            return end, False
        if base < 0x80:
            return (end + 1 if end < len(cps) and cps[end] == KEYCAP else end), True
    elif base < 0x80:
        # A bare digit, '#' or '*' is an emoji character by property, but treating it as
        # a ZWJ element would let a joiner hide between ordinary digits.
        return start, False
    elif after >= 0 and prop(after) & EMOJI_MODIFIER and not code & EMOJI_MODIFIER:
        end += 1
    if base == BLACK_FLAG and end == start + 1:
        tags = _tag_end(cps, end)
        if tags > 0:
            kept.update(range(end, tags))
            end = tags
    return end, True


def emoji_kept(cps: list[int]) -> set[int]:
    """Return the indices of joiners, presentation selectors and tags inside emoji."""
    kept: set[int] = set()
    index = 0
    while index < len(cps):
        end, chainable = _element(cps, index, kept)
        if end == index:
            index += 1
            continue
        while chainable and end < len(cps) - 1 and cps[end] == ZWJ:
            pending: set[int] = set()
            after, next_chainable = _element(cps, end + 1, pending)
            if after == end + 1:
                break
            kept.add(end)
            kept |= pending
            end, chainable = after, next_chainable
        index = end
    return kept
