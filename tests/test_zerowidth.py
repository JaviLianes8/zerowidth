from zerowidth import find_invisible, has_invisible, strip_invisible

ZWSP = "​"
BOM = "﻿"
SOFT_HYPHEN = "­"
RLO = "‮"
WORD_JOINER = "⁠"


def test_detects_zero_width_space() -> None:
    assert has_invisible(f"he{ZWSP}llo") is True


def test_detects_byte_order_mark() -> None:
    assert has_invisible(f"{BOM}data") is True


def test_detects_soft_hyphen() -> None:
    assert has_invisible(f"soft{SOFT_HYPHEN}hyphen") is True


def test_detects_directional_override() -> None:
    assert has_invisible(f"file{RLO}txt.exe") is True


def test_clean_text_has_no_invisibles() -> None:
    assert has_invisible("plain ascii text") is False


def test_strip_removes_invisibles() -> None:
    assert strip_invisible(f"he{ZWSP}l{BOM}lo{WORD_JOINER}") == "hello"


def test_strip_keeps_normal_whitespace() -> None:
    text = "line one\tindented\nline two\r\nend"
    assert strip_invisible(text) == text


def test_strip_keeps_letters_and_leaves_clean_text_unchanged() -> None:
    text = "The quick brown fox jumps over the lazy dog."
    assert strip_invisible(text) == text


def test_find_reports_positions_and_code_points() -> None:
    assert find_invisible(f"a{ZWSP}b{SOFT_HYPHEN}") == [(1, 0x200B), (3, 0x00AD)]


def test_find_on_clean_text_is_empty() -> None:
    assert find_invisible("nothing hidden here") == []


def test_empty_string_is_clean() -> None:
    assert has_invisible("") is False
    assert strip_invisible("") == ""
    assert find_invisible("") == []


def test_broad_option_catches_other_format_chars() -> None:
    arabic_number_sign = "؀"  # category Cf, outside the curated set
    assert has_invisible(arabic_number_sign) is True
    assert has_invisible(arabic_number_sign, broad=False) is False


def test_narrow_mode_still_catches_curated_set() -> None:
    assert has_invisible(ZWSP, broad=False) is True
    assert strip_invisible(f"x{ZWSP}y", broad=False) == "xy"


def test_braille_blank_is_treated_as_invisible() -> None:
    braille_blank = "⠀"
    assert has_invisible(braille_blank) is True
    assert has_invisible(braille_blank, broad=False) is True


def test_tag_characters_are_detected() -> None:
    tag = "\U000e0041"
    assert has_invisible(tag, broad=False) is True
    assert strip_invisible(f"ok{tag}") == "ok"
