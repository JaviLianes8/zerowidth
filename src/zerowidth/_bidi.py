"""Bidi controls left open or closing nothing, the raw material of Trojan Source."""

from __future__ import annotations

from ._finding import Finding
from ._props import PARAGRAPH, prop

_EMBEDDINGS = frozenset({0x202A, 0x202B, 0x202D, 0x202E})  # LRE, RLE, LRO, RLO
_ISOLATES = frozenset({0x2066, 0x2067, 0x2068})  # LRI, RLI, FSI
PDF = 0x202C
PDI = 0x2069


def unpaired_bidi(text: str) -> list[Finding]:
    """Return the bidi controls that are not paired within their paragraph.

    An opener (LRE, RLE, LRO, RLO, LRI, RLI, FSI) is unpaired when its paragraph or the
    text ends before it is closed; a closer (PDF, PDI) is unpaired when there is nothing
    for it to close. Matching follows UAX #9: a PDF closes the latest embedding or
    override only when no isolate was opened after it (X7), and a PDI closes the latest
    isolate together with every embedding opened inside it (X6a). Paragraphs end at
    characters of Bidi_Class B (line feed, carriage return, U+001C..U+001E, U+0085,
    U+2029), where every control is terminated (X8). Overflow past depth 125 is not
    modelled.
    """
    if not isinstance(text, str):
        raise TypeError(f"text must be str, not {type(text).__name__}")
    found: list[Finding] = []
    stack: list[tuple[int, int]] = []

    def close_paragraph() -> None:
        found.extend(Finding(index, cp, "bidi") for index, cp in stack)
        stack.clear()

    for index, char in enumerate(text):
        cp = ord(char)
        if cp in _EMBEDDINGS or cp in _ISOLATES:
            stack.append((index, cp))
        elif cp == PDF:
            if stack and stack[-1][1] in _EMBEDDINGS:
                stack.pop()
            else:
                found.append(Finding(index, cp, "bidi"))
        elif cp == PDI:
            opened = [n for n, (_, opener) in enumerate(stack) if opener in _ISOLATES]
            if opened:
                del stack[opened[-1] :]
            else:
                found.append(Finding(index, cp, "bidi"))
        elif cp < 0x2100 and prop(cp) & PARAGRAPH:
            close_paragraph()
    close_paragraph()
    found.sort(key=lambda item: item.index)
    return found
