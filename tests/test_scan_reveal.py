"""scan, kinds filtering, reveal and argument checking."""

from __future__ import annotations

import dataclasses
from collections.abc import Callable

import pytest

from zerowidth import (
    KINDS,
    Finding,
    find_invisible,
    has_invisible,
    reveal,
    scan,
    strip_invisible,
)

MIXED = "a\u200bb\u202ec\u200dd\ufe0fe\U000e0041f\u2800g\xadh\u034fi"


def test_scan_reports_index_code_point_and_kind() -> None:
    assert scan(MIXED) == [
        Finding(1, 0x200B, "zero-width"),
        Finding(3, 0x202E, "bidi"),
        Finding(5, 0x200D, "joiner"),
        Finding(7, 0xFE0F, "variation-selector"),
        Finding(9, 0xE0041, "tag"),
        Finding(11, 0x2800, "filler"),
        Finding(13, 0x00AD, "format"),
        Finding(15, 0x034F, "ignorable"),
    ]


def test_finding_exposes_char_label_and_name_and_is_frozen() -> None:
    item = Finding(0, 0x200B, "zero-width")
    assert (item.char, item.label, item.name) == ("\u200b", "U+200B", "ZERO WIDTH SPACE")
    assert Finding(0, 0xE0041, "tag").label == "U+E0041"
    assert Finding(0, 0x2065, "ignorable").name == "U+2065"  # reserved, no name
    with pytest.raises(dataclasses.FrozenInstanceError):
        item.index = 3  # type: ignore[misc]
    assert hash(item) == hash(Finding(0, 0x200B, "zero-width"))


def test_kinds_limit_every_function() -> None:
    assert [f.codepoint for f in scan(MIXED, kinds={"bidi"})] == [0x202E]
    assert find_invisible(MIXED, kinds=["tag", "filler"]) == [(9, 0xE0041), (11, 0x2800)]
    assert has_invisible("a\u200bb", kinds={"bidi"}) is False
    assert strip_invisible("a\u200bb\u202e", kinds={"bidi"}) == "a\u200bb"
    assert reveal("a\u200bb\u202e", kinds={"zero-width"}) == "a<U+200B>b\u202e"
    assert scan(MIXED, kinds=()) == []
    assert set(KINDS) == {f.kind for f in scan(MIXED)}


def test_unknown_or_badly_typed_kinds_are_rejected() -> None:
    with pytest.raises(ValueError, match="unknown kind"):
        scan("x", kinds={"bidi", "emoji"})  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="single string"):
        scan("x", kinds="bidi")  # type: ignore[arg-type]


def test_non_string_text_is_rejected_everywhere() -> None:
    functions: list[Callable[..., object]] = [
        scan,
        has_invisible,
        find_invisible,
        strip_invisible,
        reveal,
    ]
    for function in functions:
        with pytest.raises(TypeError, match="text must be str"):
            function(b"abc")
        with pytest.raises(TypeError):
            function(None)


def test_reveal_styles() -> None:
    text = "a\u200bb\U000e0041"
    assert reveal(text) == "a<U+200B>b<U+E0041>"
    assert reveal(text, style="escape") == "a\\u200bb\\U000e0041"
    assert reveal(text, style="name") == "a<ZERO WIDTH SPACE>b<TAG LATIN CAPITAL LETTER A>"
    assert reveal(text, style=lambda item: f"[{item.kind}]") == "a[zero-width]b[tag]"
    assert reveal("clean") == "clean"


def test_reveal_rejects_an_unknown_style() -> None:
    with pytest.raises(ValueError, match="unknown style"):
        reveal("a", style="html")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="unknown style"):
        reveal("a", style=3)  # type: ignore[arg-type]


def test_reveal_and_strip_agree_with_scan() -> None:
    marked = reveal(MIXED, style=lambda item: "\x00")
    assert marked.replace("\x00", "") == strip_invisible(MIXED) == "abcdefghi"
    assert [i for i, ch in enumerate(marked) if ch == "\x00"] == [f.index for f in scan(MIXED)]


def test_keep_options_apply_to_every_function() -> None:
    text = "\u2764\ufe0f\u200b"
    assert strip_invisible(text, keep_emoji=True) == "\u2764\ufe0f"
    assert reveal(text, keep_emoji=True) == "\u2764\ufe0f<U+200B>"
    assert find_invisible(text, keep_emoji=True) == [(2, 0x200B)]
    persian = "\u0647\u200c\u0627"
    assert has_invisible(persian, keep_joiners=True) is False
    assert has_invisible(persian, keep_emoji=True) is True


def test_narrow_mode_classifies_too() -> None:
    assert scan("\u202e\ufe0f", broad=False) == [Finding(0, 0x202E, "bidi")]
