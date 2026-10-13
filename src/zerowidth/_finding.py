"""The typed record for one hidden character."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass

from ._chars import Kind


@dataclass(frozen=True)
class Finding:
    """One hidden character: where it is, what it is and which kind it belongs to.

    ``index`` counts code points (Python ``str`` positions). ``name`` comes from the
    running Python's Unicode database and falls back to the ``U+XXXX`` label for code
    points that database does not name (reserved ones, or ones newer than it).
    """

    index: int
    codepoint: int
    kind: Kind

    @property
    def char(self) -> str:
        """The character itself."""
        return chr(self.codepoint)

    @property
    def label(self) -> str:
        """The code point as ``U+XXXX``."""
        return f"U+{self.codepoint:04X}"

    @property
    def name(self) -> str:
        """The Unicode name, or the label when the name is not known."""
        return unicodedata.name(self.char, "") or self.label
