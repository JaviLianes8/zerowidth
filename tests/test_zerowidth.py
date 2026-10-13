from zerowidth import find_invisible, has_invisible, strip_invisible

ZWSP = "\u200b"
BOM = "\ufeff"
SOFT_HYPHEN = "\xad"
RLO = "\u202e"
WORD_JOINER = "\u2060"


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
    text = "line one\tindented\nline two\r\nend\xa0\u2028\u3000"
    assert strip_invisible(text) == text


def test_strip_keeps_letters_and_leaves_clean_text_unchanged() -> None:
    text = "The quick brown fox jumps over the lazy dog. \xe9\u4f60\u0645"
    assert strip_invisible(text) == text


def test_find_reports_positions_and_code_points() -> None:
    assert find_invisible(f"a{ZWSP}b{SOFT_HYPHEN}") == [(1, 0x200B), (3, 0x00AD)]


def test_find_counts_code_points_not_utf16_units() -> None:
    assert find_invisible(f"\U0001f600{ZWSP}") == [(1, 0x200B)]


def test_find_on_clean_text_is_empty() -> None:
    assert find_invisible("nothing hidden here") == []


def test_empty_string_is_clean() -> None:
    assert has_invisible("") is False
    assert strip_invisible("") == ""
    assert find_invisible("") == []


def test_broad_option_catches_other_format_chars() -> None:
    begin_beam = "\U0001d173"  # MUSICAL SYMBOL BEGIN BEAM: Cf, outside the curated set
    assert has_invisible(begin_beam) is True
    assert has_invisible(begin_beam, broad=False) is False


def test_broad_option_skips_the_visible_prepended_concatenation_marks() -> None:
    # PropList.txt 18.0.0 lists these as Prepended_Concatenation_Mark: Cf, but drawn.
    for mark in "\u0600\u0605\u06dd\u070f\u0890\u08e2\U000110bd\U000110cd":
        assert has_invisible(mark) is False, hex(ord(mark))


def test_broad_option_catches_variation_selectors_and_reserved_ignorables() -> None:
    for cp in (0xFE0F, 0xE0100, 0xE01EF, 0x180F, 0x2065, 0xFFF0, 0xE0FFF):
        assert has_invisible(chr(cp)) is True, hex(cp)
        assert has_invisible(chr(cp), broad=False) is False, hex(cp)


def test_broad_mode_ignores_ordinary_marks_and_symbols() -> None:
    for cp in (0x0301, 0x094D, 0x20E3, 0x1F3FB, 0x2800 + 1, 0xFFFD, 0x10FFFF):
        assert has_invisible(chr(cp)) is False, hex(cp)


def test_narrow_mode_still_catches_curated_set() -> None:
    assert has_invisible(ZWSP, broad=False) is True
    assert strip_invisible(f"x{ZWSP}y", broad=False) == "xy"


def test_braille_blank_is_treated_as_invisible() -> None:
    braille_blank = "\u2800"
    assert has_invisible(braille_blank) is True
    assert has_invisible(braille_blank, broad=False) is True


def test_tag_characters_are_detected() -> None:
    tag = "\U000e0041"
    assert has_invisible(tag, broad=False) is True
    assert strip_invisible(f"ok{tag}") == "ok"
