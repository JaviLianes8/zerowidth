"""unpaired_bidi: the matching rules of UAX #9 (X6a, X7, X8), vectors written by hand.

The Trojan Source shapes follow the examples of https://trojansource.codes/trojan-source.pdf
(an override or isolate opened inside a comment or string and never closed).
"""

from __future__ import annotations

import pytest

from zerowidth import Finding, unpaired_bidi

LRE, RLE, PDF, LRO, RLO = "\u202a", "\u202b", "\u202c", "\u202d", "\u202e"
LRI, RLI, FSI, PDI = "\u2066", "\u2067", "\u2068", "\u2069"


def where(text: str) -> list[tuple[int, int]]:
    return [(item.index, item.codepoint) for item in unpaired_bidi(text)]


def test_balanced_text_is_clean() -> None:
    assert where(f"a{RLO}b{PDF}c {LRI}d{PDI} {RLE}{LRI}x{PDI}{PDF}") == []
    assert where("no controls at all") == []


def test_commenting_out_shape_reports_the_open_isolates() -> None:
    line = f"/*{RLO} }} {LRI}if (isAdmin){PDI} {LRI} begin admins only */\n"
    assert where(line) == [(2, 0x202E), (21, 0x2066)]


def test_every_opener_left_open_is_reported() -> None:
    for opener in (LRE, RLE, LRO, RLO, LRI, RLI, FSI):
        assert where(f"x{opener}y") == [(1, ord(opener))]


def test_a_paragraph_separator_terminates_everything() -> None:
    for separator in ("\n", "\r", "\x1c", "\x1d", "\x1e", "\x85", "\u2029"):
        text = f"{RLO}a{separator}b{PDF}"
        assert where(text) == [(0, 0x202E), (4, 0x202C)], repr(separator)


def test_line_separator_and_tab_do_not_end_a_paragraph() -> None:
    assert where(f"{RLO}a\u2028b\tc\x0bd{PDF}") == []


def test_stray_closers_are_reported() -> None:
    assert where(f"a{PDF}b{PDI}") == [(1, 0x202C), (3, 0x2069)]


def test_pdf_does_not_close_an_embedding_across_an_isolate() -> None:
    # X7: with an isolate on top of the stack, a PDF matches nothing.
    assert where(f"{RLE}{LRI}a{PDF}") == [(0, 0x202B), (1, 0x2066), (3, 0x202C)]


def test_pdi_closes_the_embeddings_opened_inside_its_isolate() -> None:
    # X6a: the PDI pops everything back to and including the latest isolate.
    assert where(f"{RLI}a{RLO}b{PDI}") == []
    assert where(f"{RLO}{RLI}{PDI}") == [(0, 0x202E)]


def test_pdi_matches_the_latest_isolate_only() -> None:
    assert where(f"{LRI}{RLI}a{PDI}") == [(0, 0x2066)]


def test_findings_are_typed_and_sorted() -> None:
    found = unpaired_bidi(f"{RLO}a{PDF}{PDF}{LRI}")
    assert found == [Finding(3, 0x202C, "bidi"), Finding(4, 0x2066, "bidi")]
    assert found[0].name == "POP DIRECTIONAL FORMATTING"


def test_rejects_non_strings() -> None:
    with pytest.raises(TypeError):
        unpaired_bidi(b"\xe2\x80\xae")  # type: ignore[arg-type]
