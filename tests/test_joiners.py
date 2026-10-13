"""keep_joiners: ZWNJ and ZWJ survive only in the UTS #39 contexts A1, A2 and B.

The three spelled words are the code point sequences of Figures 1, 2 and 3 of UTS #39
revision 34, section 3.1.1.1 (https://www.unicode.org/reports/tr39/tr39-34.html).
The negative cases are written by hand from the same rules.
"""

from __future__ import annotations

from zerowidth import find_invisible, strip_invisible


def cps(*points: int) -> str:
    return "".join(map(chr, points))


# Figure 1: Persian "a letter", NOON ALEF MEEM HEH ZWNJ ALEF FARSI-YEH (context A1).
PERSIAN = cps(0x0646, 0x0627, 0x0645, 0x0647, 0x200C, 0x0627, 0x06CC)
# Figure 2: Malayalam "eyewitness", the ZWNJ after KA VIRAMA (context A2).
MALAYALAM = cps(0x0D26, 0x0D43, 0x0D15, 0x0D4D, 0x200C, 0x0D38, 0x0D3E, 0x0D15, 0x0D4D)
MALAYALAM += cps(0x0D37, 0x0D3F)
# Figure 3: Sinhala "Sri Lanka", the ZWJ after SHA AL-LAKUNA (context B).
SINHALA = cps(0x0DC1, 0x0DCA, 0x200D, 0x0DBB, 0x0DD3, 0x20, 0x0DBD, 0x0D82, 0x0D9A, 0x0DCF)


def test_the_three_figures_keep_their_joiner() -> None:
    for word in (PERSIAN, MALAYALAM, SINHALA):
        assert strip_invisible(word, keep_joiners=True) == word


def test_without_the_option_the_joiner_goes() -> None:
    assert find_invisible(PERSIAN) == [(4, 0x200C)]
    assert find_invisible(SINHALA) == [(2, 0x200D)]


def test_a1_needs_a_left_joining_letter_before_and_a_right_joining_one_after() -> None:
    # ALEF only joins to the right, so a ZWNJ after it breaks nothing.
    assert find_invisible(cps(0x0627, 0x200C, 0x0628), keep_joiners=True) == [(1, 0x200C)]
    # BEH ZWNJ space: nothing joins on the right.
    assert find_invisible(cps(0x0628, 0x200C, 0x20), keep_joiners=True) == [(1, 0x200C)]


def test_a1_skips_transparent_marks_before_the_zwnj() -> None:
    word = cps(0x0628, 0x064E, 0x0651, 0x200C, 0x0628)  # BEH FATHA SHADDA ZWNJ BEH
    assert strip_invisible(word, keep_joiners=True) == word


def test_a1_takes_no_marks_after_the_zwnj() -> None:
    # The fetched rule is /$LJ $T* ZWNJ $RJ/: nothing may sit between ZWNJ and the letter.
    word = cps(0x0628, 0x200C, 0x064E, 0x0628)
    assert find_invisible(word, keep_joiners=True) == [(1, 0x200C)]


def test_a2_and_b_need_a_virama() -> None:
    assert find_invisible(cps(0x0D15, 0x200C, 0x0D38), keep_joiners=True) == [(1, 0x200C)]
    assert find_invisible(cps(0x0DC1, 0x200D, 0x0DBB), keep_joiners=True) == [(1, 0x200D)]


def test_a2_needs_a_letter_after() -> None:
    assert find_invisible(cps(0x0D15, 0x0D4D, 0x200C, 0x20), keep_joiners=True) == [(2, 0x200C)]


def test_b_refuses_a_dependent_vowel_after_the_zwj() -> None:
    word = cps(0x0915, 0x094D, 0x200D, 0x093E)  # KA VIRAMA ZWJ VOWEL SIGN AA
    assert find_invisible(word, keep_joiners=True) == [(2, 0x200D)]
    assert strip_invisible(cps(0x0915, 0x094D, 0x200D), keep_joiners=True) == cps(
        0x0915, 0x094D, 0x200D
    )


def test_the_sequence_must_stay_in_one_script() -> None:
    mixed = cps(0x0915, 0x094D, 0x200C, 0x0D38)  # Devanagari conjunct, Malayalam letter
    assert find_invisible(mixed, keep_joiners=True) == [(2, 0x200C)]
    latin = cps(0x61, 0x094D, 0x200D)  # a Latin letter cannot carry the Devanagari virama
    assert find_invisible(latin, keep_joiners=True) == [(2, 0x200D)]


def test_the_sequence_must_be_nfc() -> None:
    # The two nonspacing marks (ccc 230 then 220) are out of canonical order.
    word = cps(0x0915, 0x094D, 0x0951, 0x0952, 0x200C, 0x0915)
    assert find_invisible(word, keep_joiners=True) == [(4, 0x200C)]
    ordered = cps(0x0915, 0x094D, 0x0952, 0x0951, 0x200C, 0x0915)
    assert find_invisible(ordered, keep_joiners=True) == []


def test_latin_joiners_are_still_reported() -> None:
    assert find_invisible("a\u200cb\u200dc", keep_joiners=True) == [(1, 0x200C), (3, 0x200D)]


def test_a1_takes_a_left_joining_letter_only_before_the_zwnj() -> None:
    # PHAGS-PA KA is dual joining, SUPERFIXED LETTER RA left joining (DerivedJoiningType).
    assert find_invisible(cps(0xA872, 0x200C, 0xA840), keep_joiners=True) == []
    assert find_invisible(cps(0xA840, 0x200C, 0xA872), keep_joiners=True) == [(1, 0x200C)]


def test_a2_skips_combining_marks_after_the_zwnj() -> None:
    # KA VIRAMA ZWNJ UDATTA KA: UDATTA is Mn with ccc 230 and script Inherited.
    word = cps(0x0915, 0x094D, 0x200C, 0x0951, 0x0915)
    assert find_invisible(word, keep_joiners=True) == []


def test_the_virama_must_be_the_last_mark_before_the_joiner_run() -> None:
    # KA VIRAMA KA ZWNJ KA: the virama belongs to an earlier cluster.
    assert find_invisible(cps(0x0915, 0x094D, 0x0915, 0x200C, 0x0915), keep_joiners=True) == [
        (3, 0x200C)
    ]
    # KA UDATTA ZWNJ KA: a combining mark that is not a virama does not open a conjunct.
    assert find_invisible(cps(0x0915, 0x0951, 0x200C, 0x0915), keep_joiners=True) == [(2, 0x200C)]


def test_the_virama_needs_a_letter_before_it() -> None:
    assert find_invisible(cps(0x31, 0x094D, 0x200D), keep_joiners=True) == [(2, 0x200D)]
    assert find_invisible(cps(0x094D, 0x200D), keep_joiners=True) == [(1, 0x200D)]
