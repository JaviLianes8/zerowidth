"""What counts as hidden, checked over the whole code space against the UCD files."""

from __future__ import annotations

from conftest import needs_ucd, with_value

from zerowidth import KINDS, scan
from zerowidth._chars import INVISIBLE

EVERY = "".join(map(chr, range(0x110000)))
JOIN_CONTROLS = {0x200C, 0x200D}
TAGS = {0xE0001, *range(0xE0020, 0xE0080)}


def test_narrow_mode_is_exactly_the_curated_set() -> None:
    assert {item.codepoint for item in scan(EVERY, broad=False)} == set(INVISIBLE)
    assert len(INVISIBLE) == 37 + 128


@needs_ucd
def test_broad_mode_is_curated_plus_ignorables_plus_invisible_format_characters() -> None:
    ignorable = with_value("DerivedCoreProperties.txt", "Default_Ignorable_Code_Point")
    formats = with_value("DerivedGeneralCategory.txt", "Cf")
    visible = with_value("PropList.txt", "Prepended_Concatenation_Mark")
    found = scan(EVERY)
    assert {item.codepoint for item in found} == set(INVISIBLE) | ignorable | (formats - visible)
    assert [item.index for item in found] == [item.codepoint for item in found]


@needs_ucd
def test_every_kind_follows_its_rule() -> None:
    bidi = with_value("PropList.txt", "Bidi_Control")
    selectors = with_value("PropList.txt", "Variation_Selector")
    formats = with_value("DerivedGeneralCategory.txt", "Cf")
    assert with_value("PropList.txt", "Join_Control") == JOIN_CONTROLS
    seen = set()
    for item in scan(EVERY):
        cp = item.codepoint
        seen.add(item.kind)
        if cp in bidi:
            assert item.kind == "bidi"
        elif cp in JOIN_CONTROLS:
            assert item.kind == "joiner"
        elif cp in (0x200B, 0x2060, 0xFEFF):
            assert item.kind == "zero-width"
        elif cp in TAGS:
            assert item.kind == "tag"
        elif cp in selectors:
            assert item.kind == "variation-selector"
        elif cp in (0x115F, 0x1160, 0x2800, 0x3164, 0xFFA0):
            assert item.kind == "filler"
        else:
            assert item.kind == ("format" if cp in formats else "ignorable"), hex(cp)
    assert seen == set(KINDS)


def test_ascii_and_common_text_is_never_hidden() -> None:
    assert scan("".join(map(chr, range(0xAD)))) == []
    assert scan("caf\xe9 na\xefve \u4f60\u597d \u0645\u0631\u062d\u0628\u0627 \U0001f600") == []
