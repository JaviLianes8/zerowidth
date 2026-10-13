"""Detection, removal and display of zero-width and invisible characters."""

from __future__ import annotations

from collections.abc import Callable, Collection
from typing import Literal

from ._chars import KINDS, Kind, is_hidden, kind_of
from ._emoji import emoji_kept
from ._finding import Finding
from ._joiners import joiners_kept

Style = Literal["codepoint", "escape", "name"]
Marker = Style | Callable[[Finding], str]
# No hidden character sits below the soft hyphen, so plain ASCII text is skipped cheaply.
_FIRST_HIDDEN = 0xAD


def _check(text: object, kinds: Collection[Kind] | None) -> frozenset[Kind] | None:
    if not isinstance(text, str):
        raise TypeError(f"text must be str, not {type(text).__name__}")
    if kinds is None:
        return None
    if isinstance(kinds, str):
        raise TypeError("kinds must be a collection of kind names, not a single string")
    wanted = frozenset(kinds)
    unknown = sorted(str(kind) for kind in wanted if kind not in KINDS)
    if unknown:
        raise ValueError(f"unknown kind(s): {', '.join(unknown)}; expected {', '.join(KINDS)}")
    return wanted


def scan(
    text: str,
    *,
    broad: bool = True,
    keep_emoji: bool = False,
    keep_joiners: bool = False,
    kinds: Collection[Kind] | None = None,
) -> list[Finding]:
    """Return a ``Finding`` for every hidden character, in text order.

    ``broad`` adds every Unicode 18.0 default-ignorable and format character to the
    curated set. ``keep_emoji`` leaves out the joiners, presentation selectors and tags
    that are part of an emoji sequence; ``keep_joiners`` leaves out the joiners that UTS
    #39 allows between letters. ``kinds`` limits the result to those kinds.
    """
    wanted = _check(text, kinds)
    found = [
        Finding(index, ord(char), kind_of(ord(char)))
        for index, char in enumerate(text)
        if ord(char) >= _FIRST_HIDDEN and is_hidden(ord(char), broad)
    ]
    if wanted is not None:
        found = [item for item in found if item.kind in wanted]
    if found and (keep_emoji or keep_joiners):
        cps = [ord(char) for char in text]
        kept = (emoji_kept(cps) if keep_emoji else set()) | (
            joiners_kept(cps) if keep_joiners else set()
        )
        found = [item for item in found if item.index not in kept]
    return found


def has_invisible(
    text: str,
    *,
    broad: bool = True,
    keep_emoji: bool = False,
    keep_joiners: bool = False,
    kinds: Collection[Kind] | None = None,
) -> bool:
    """Report whether the text holds any hidden character (same options as ``scan``)."""
    return bool(
        scan(text, broad=broad, keep_emoji=keep_emoji, keep_joiners=keep_joiners, kinds=kinds)
    )


def find_invisible(
    text: str,
    *,
    broad: bool = True,
    keep_emoji: bool = False,
    keep_joiners: bool = False,
    kinds: Collection[Kind] | None = None,
) -> list[tuple[int, int]]:
    """List the ``(index, code point)`` of each hidden character (same options as ``scan``)."""
    found = scan(text, broad=broad, keep_emoji=keep_emoji, keep_joiners=keep_joiners, kinds=kinds)
    return [(item.index, item.codepoint) for item in found]


def _replace(text: str, found: list[Finding], marker: Callable[[Finding], str]) -> str:
    parts: list[str] = []
    last = 0
    for item in found:
        parts.append(text[last : item.index])
        parts.append(marker(item))
        last = item.index + 1
    parts.append(text[last:])
    return "".join(parts)


def strip_invisible(
    text: str,
    *,
    broad: bool = True,
    keep_emoji: bool = False,
    keep_joiners: bool = False,
    kinds: Collection[Kind] | None = None,
) -> str:
    """Return the text without its hidden characters (same options as ``scan``)."""
    found = scan(text, broad=broad, keep_emoji=keep_emoji, keep_joiners=keep_joiners, kinds=kinds)
    return _replace(text, found, lambda item: "")


def _escape(item: Finding) -> str:
    return f"\\u{item.codepoint:04x}" if item.codepoint <= 0xFFFF else f"\\U{item.codepoint:08x}"


_STYLES: dict[str, Callable[[Finding], str]] = {
    "codepoint": lambda item: f"<{item.label}>",
    "escape": _escape,
    "name": lambda item: f"<{item.name}>",
}


def reveal(
    text: str,
    *,
    style: Marker = "codepoint",
    broad: bool = True,
    keep_emoji: bool = False,
    keep_joiners: bool = False,
    kinds: Collection[Kind] | None = None,
) -> str:
    """Return the text with each hidden character replaced by a visible marker.

    ``style`` is ``"codepoint"`` (``<U+200B>``), ``"escape"`` (``\\u200b``), ``"name"``
    (``<ZERO WIDTH SPACE>``) or a callable that receives the ``Finding``.
    """
    if callable(style):
        marker = style
    elif isinstance(style, str) and style in _STYLES:
        marker = _STYLES[style]
    else:
        raise ValueError(f"unknown style {style!r}; expected codepoint, escape or name")
    found = scan(text, broad=broad, keep_emoji=keep_emoji, keep_joiners=keep_joiners, kinds=kinds)
    return _replace(text, found, marker)
