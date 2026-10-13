"""Detect, reveal and strip zero-width and invisible characters in text."""

from __future__ import annotations

from ._bidi import unpaired_bidi
from ._chars import KINDS, Kind
from ._detect import Marker, Style, find_invisible, has_invisible, reveal, scan, strip_invisible
from ._finding import Finding
from ._props import UNICODE_VERSION

__version__ = "0.2.0"

__all__ = [
    "KINDS",
    "UNICODE_VERSION",
    "Finding",
    "Kind",
    "Marker",
    "Style",
    "find_invisible",
    "has_invisible",
    "reveal",
    "scan",
    "strip_invisible",
    "unpaired_bidi",
]
