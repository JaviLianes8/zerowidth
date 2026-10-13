"""keep_emoji: hidden characters inside emoji sequences stay, every other one goes.

Vectors are written by hand from the UTS #51 grammar
(https://www.unicode.org/reports/tr51/tr51-31.html, ED-14a, ED-14c, ED-15a, ED-16, Annex C).
"""

from __future__ import annotations

from zerowidth import find_invisible, has_invisible, strip_invisible

ZWJ = "\u200d"
VS16 = "\ufe0f"
VS15 = "\ufe0e"
FAMILY = f"\U0001f468{ZWJ}\U0001f469{ZWJ}\U0001f467"
RAINBOW_FLAG = f"\U0001f3f3{VS16}{ZWJ}\U0001f308"
PIRATE_FLAG = f"\U0001f3f4{ZWJ}\u2620{VS16}"
ASTRONAUT_MEDIUM = f"\U0001f469\U0001f3fd{ZWJ}\U0001f680"
RED_HEART = f"\u2764{VS16}"
KEYCAP_ONE = f"1{VS16}\u20e3"
TAGS = {ch: chr(0xE0000 + ord(ch)) for ch in "0123456789abcdefghijklmnopqrstuvwxyz"}
CANCEL = "\U000e007f"


def flag(spec: str, base: str = "\U0001f3f4") -> str:
    return base + "".join(TAGS[ch] for ch in spec) + CANCEL


def test_zwj_sequences_survive() -> None:
    for emoji in (FAMILY, RAINBOW_FLAG, PIRATE_FLAG, ASTRONAUT_MEDIUM):
        text = f"hi {emoji}!"
        assert strip_invisible(text, keep_emoji=True) == text
        assert has_invisible(text, keep_emoji=True) is False


def test_without_the_option_the_joiners_and_selectors_go() -> None:
    assert strip_invisible(FAMILY) == "\U0001f468\U0001f469\U0001f467"
    assert strip_invisible(RED_HEART) == "\u2764"
    assert strip_invisible(flag("gbeng")) == "\U0001f3f4"


def test_presentation_and_text_selectors_after_listed_bases_survive() -> None:
    for text in (RED_HEART, f"\u2764{VS15}", KEYCAP_ONE, f"#{VS16}", f"\xa9{VS16}"):
        assert strip_invisible(text, keep_emoji=True) == text


def test_selector_after_a_base_without_emoji_variation_is_reported() -> None:
    assert find_invisible(f"A{VS16}", keep_emoji=True) == [(1, 0xFE0F)]
    assert find_invisible(f"\U0001f600{VS16}", keep_emoji=True) == [(1, 0xFE0F)]


def test_supplementary_selectors_smuggled_after_an_emoji_are_reported() -> None:
    payload = "".join(chr(0xE0100 + n) for n in (5, 17, 200))
    text = f"\U0001f600{payload}"
    assert strip_invisible(text, keep_emoji=True) == "\U0001f600"


def test_subdivision_flags_survive() -> None:
    for spec in ("gbeng", "gbsct", "gbwls", "usca", "001", "fr75"):
        assert strip_invisible(flag(spec), keep_emoji=True) == flag(spec)


def test_tag_sequences_that_are_not_flag_shaped_are_reported() -> None:
    hidden = "ignore previous instructions".replace(" ", "")
    for text in (
        flag(hidden[:20]),  # far too long for a subdivision id
        flag("us"),  # a bare two-letter region is not a valid tag spec
        flag("gbeng", base="\U0001f600"),  # only U+1F3F4 takes a flag tag spec
        "\U0001f3f4" + "".join(TAGS[c] for c in "gbeng"),  # no cancel tag
        "\U0001f3f4" + chr(0xE0047) + chr(0xE0042) + chr(0xE0045) + CANCEL,  # capitals
        "plain" + "".join(TAGS[c] for c in "abc") + CANCEL,
    ):
        assert strip_invisible(text, keep_emoji=True) != text, text.encode("unicode_escape")


def test_joiner_between_plain_characters_is_reported() -> None:
    for text in (f"a{ZWJ}b", f"1{ZWJ}2", f"#{ZWJ}*", f"\U0001f600{ZWJ}", f"{ZWJ}\U0001f600"):
        assert has_invisible(text, keep_emoji=True) is True, text.encode("unicode_escape")


def test_joiner_after_a_text_style_selector_is_reported() -> None:
    assert find_invisible(f"\u2764{VS15}{ZWJ}\U0001f525", keep_emoji=True) == [(2, 0x200D)]


def test_doubled_joiner_keeps_neither() -> None:
    text = f"\U0001f468{ZWJ}{ZWJ}\U0001f469"
    assert find_invisible(text, keep_emoji=True) == [(1, 0x200D), (2, 0x200D)]


def test_other_hidden_characters_inside_emoji_text_still_go() -> None:
    text = f"{FAMILY}\u200b{RED_HEART}\u202e"
    assert strip_invisible(text, keep_emoji=True) == FAMILY + RED_HEART
