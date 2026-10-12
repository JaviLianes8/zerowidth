"""Detect and strip zero-width and invisible characters from text."""

from __future__ import annotations

from ._detect import find_invisible, has_invisible, strip_invisible

__version__ = "0.1.0"

__all__ = ["find_invisible", "has_invisible", "strip_invisible"]
