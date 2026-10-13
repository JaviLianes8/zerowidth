"""Find the hidden characters that belong to emoji sequences (UTS #51)."""

from __future__ import annotations

from ._props import EMOJI, EMOJI_MODIFIER, EMOJI_VS_BASE, prop

ZWJ = 0x200D
VS15 = 0xFE0E
VS16 = 0xFE0F
KEYCAP = 0x20E3
BLACK_FLAG = 0x1F3F4
CANCEL_TAG = 0xE007F
# The RGI_Emoji_Tag_Sequence lines of emoji-sequences.txt (Emoji 18.0). UTS #51 Annex C
# allows any CLDR subdivision id, but accepting every id of the right shape would leave
# room for a few hidden bytes per flag, so only the recommended flags count.
RGI_FLAG_TAGS = frozenset({"gbeng", "gbsct", "gbwls"})


def _tag_end(cps: list[int], start: int) -> int:
    """Return the index after a flag tag spec and its cancel tag at ``start``, or -1."""
    end = start
    while end < len(cps) and 0xE0020 <= cps[end] <= 0xE007E:
        end += 1
    if end >= len(cps) or cps[end] != CANCEL_TAG:
        return -1
    spec = "".join(chr(cp - 0xE0000) for cp in cps[start:end])
    return end + 1 if spec in RGI_FLAG_TAGS else -1


def _element(cps: list[int], start: int, kept: set[int]) -> tuple[int, bool]:
    """Parse one emoji ZWJ element at ``start``.

    Returns the end index (``start`` when nothing parses) and whether a joiner may follow.
    The hidden characters of the element are added to ``kept``.
    """
    base = cps[start]
    code = prop(base)
    after = cps[start + 1] if start + 1 < len(cps) else -1
    if base < 0x80:
        # A digit, '#' or '*' is an emoji character by property, but it only renders as
        # an emoji in a keycap; anywhere else a selector or joiner could hide beside it.
        keycap = after == VS16 and start + 2 < len(cps) and cps[start + 2] == KEYCAP
        if not (code & EMOJI and keycap):
            return start, False
        kept.add(start + 1)
        return start + 3, True
    if not code & EMOJI:
        return start, False
    end = start + 1
    if after in (VS15, VS16) and code & EMOJI_VS_BASE:
        kept.add(end)
        end += 1
        if after == VS15:
            return end, False
    elif after >= 0 and prop(after) & EMOJI_MODIFIER:
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
