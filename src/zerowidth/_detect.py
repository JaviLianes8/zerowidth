"""Detection and removal of zero-width and invisible characters."""

from __future__ import annotations

import unicodedata

from ._chars import INVISIBLE


def _is_invisible(char: str, broad: bool) -> bool:
    if ord(char) in INVISIBLE:
        return True
    return broad and unicodedata.category(char) == "Cf"


def has_invisible(text: str, *, broad: bool = True) -> bool:
    """Report whether the text holds any zero-width or invisible character."""
    return any(_is_invisible(char, broad) for char in text)


def strip_invisible(text: str, *, broad: bool = True) -> str:
    """Return the text with every zero-width or invisible character removed."""
    return "".join(char for char in text if not _is_invisible(char, broad))


def find_invisible(text: str, *, broad: bool = True) -> list[tuple[int, int]]:
    """List the (index, code point) of each zero-width or invisible character."""
    return [(index, ord(char)) for index, char in enumerate(text) if _is_invisible(char, broad)]
