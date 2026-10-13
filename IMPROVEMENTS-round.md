# zerowidth improvement round

Progress:
- [x] Brainstorm ranked improvements (this file)
- [ ] Pin the ground truth: UCD 18.0.0 files in a local folder with a tracked manifest
- [ ] Generated property tables and a generator check
- [ ] Coverage fixed against the UCD: Default_Ignorable_Code_Point, Cf, visible marks excluded
- [ ] Typed findings with kinds, filtering by kind, reveal mode
- [ ] Keep emoji sequences intact on request (UTS #51 grammar)
- [ ] Keep joiners in the contexts UTS #39 allows (A1, A2, B)
- [ ] Unpaired bidi controls (Trojan Source)
- [ ] Command line tool
- [ ] Contracts: UCD sweep, RGI emoji corpus, cited vectors, README examples
- [ ] Docs and packaging: README, CHANGELOG, metadata, installed-wheel e2e test
- [ ] Gates: ruff format, ruff check, mypy --strict, pytest
- [ ] Mutation run: removing guarded logic makes the suite fail
- [ ] Independent review findings fixed with regression tests
- [ ] Pull request opened, guard clean

## Starting point

`0.1.0` gives `has_invisible`, `strip_invisible` and `find_invisible` over a curated set
of 37 named code points plus the tag block, and a `broad` switch (on by default) that
adds every character whose general category is `Cf` according to the running Python.
Compared with the sources below:

- The broad mode depends on the Unicode version of the interpreter (Python 3.10 ships
  Unicode 13, newer ones ship later versions), so the same call gives different answers
  on different Pythons.
- It flags the Prepended_Concatenation_Mark characters (U+0600..U+0605, U+06DD, U+070F,
  U+0890..U+0891, U+08E2, U+110BD, U+110CD). They are `Cf`, but PropList.txt and the
  Default_Ignorable_Code_Point derivation single them out as format characters that are
  visible, and stripping them corrupts Arabic and Kaithi numbers.
- It misses the variation selectors (U+FE00..U+FE0F, U+E0100..U+E01EF, U+180B..U+180D,
  U+180F). They are Default_Ignorable_Code_Point, render nothing on their own and are a
  known channel to hide bytes behind an emoji. It also misses reserved code points that
  the UCD already marks as default ignorable (U+2065, U+FFF0..U+FFF8, U+E0080..U+E0FFF).
- Stripping always breaks emoji: the joiner inside a family or a profession, the
  presentation selector after a heart and the tag letters of the England flag all go.
- Stripping always breaks Persian, Malayalam or Sinhala words whose joiners are part of
  the spelling (UTS #39 section 3.1.1.1 gives the contexts where they are needed).
- Findings are bare `(index, code point)` tuples: no name, no class, no way to ask only
  for bidi controls.
- There is no reveal mode (show the hidden characters instead of deleting them), no
  check for the unpaired bidi controls behind Trojan Source, and no command line tool.
- The README examples are not executed by the tests, there is no installed-wheel test
  and `scripts/check.ps1` lints `src tests` only.

## Sources (fetched 2026-10-13)

- Unicode Character Database 18.0.0, https://www.unicode.org/Public/18.0.0/ucd/:
  DerivedCoreProperties.txt (Default_Ignorable_Code_Point and its derivation),
  extracted/DerivedGeneralCategory.txt (Cf, letters, Mn), PropList.txt (Bidi_Control,
  Variation_Selector, Join_Control, Prepended_Concatenation_Mark),
  extracted/DerivedBidiClass.txt (paragraph separators, class B),
  extracted/DerivedJoiningType.txt, extracted/DerivedCombiningClass.txt (Virama, ccc),
  IndicSyllabicCategory.txt (Vowel_Dependent), Scripts.txt, emoji/emoji-data.txt and
  emoji/emoji-variation-sequences.txt. Sizes and sha256 go in `data/ucd/MANIFEST.json`.
- Emoji 18.0, https://www.unicode.org/Public/18.0.0/emoji/: emoji-sequences.txt,
  emoji-zwj-sequences.txt and emoji-test.txt, used only as a test corpus.
- UTS #51 Unicode Emoji, revision 31 (2026-08-28),
  https://www.unicode.org/reports/tr51/tr51-31.html: ED-14a tag sequences, ED-14c keycaps,
  ED-15a ZWJ elements, ED-16 ZWJ sequences, Annex C (flag tag sequences use U+1F3F4 and
  lower-case letters and digits that spell a CLDR subdivision or a three-digit region).
- UTS #39 Unicode Security Mechanisms, revision 34 (2026-08-27),
  https://www.unicode.org/reports/tr39/tr39-34.html: Identifier_Type Default_Ignorable is
  restricted, section 3.1.1.1 limited contexts A1, A2 and B for ZWNJ and ZWJ with the
  single-script and NFC conditions, and the skeleton removes Default_Ignorable_Code_Point
  before mapping confusables.
- UAX #31 Identifiers, revision 45 (2026-09-01),
  https://www.unicode.org/reports/tr31/tr31-45.html: the emoji profile keeps ZWJ, FE0F and
  the tags inside emoji sequences, the default-ignorable exclusion profile, and the
  migration note that moved the joiner contexts to UTS #39.
- UAX #9 Bidirectional Algorithm, revision 52 (2026-09-01),
  https://www.unicode.org/reports/tr9/tr9-52.html: X6a and X7 (how PDI and PDF match),
  X8 (everything explicit ends at a paragraph separator), P1.
- UTS #55 Unicode Source Code Handling, revision 5,
  https://www.unicode.org/reports/tr55/tr55-5.html, and the Trojan Source paper,
  https://trojansource.codes/trojan-source.pdf: bidi controls left open inside comments
  and strings reorder what a reviewer sees.

The UCD and emoji files are not committed (rule: no third-party data in the repo or the
wheel): the manifest pins them, `scripts/fetch_upstream.py` fetches them into the ignored
`data/ucd/` folder, the generator turns them into run-length tables under `src/`, and the
tests that read them skip while they are absent. The Unicode licence ships as
`LICENSE-UNICODE` because the generated tables derive from the data.

## Ranked brainstorm

1. Pin the coverage to UCD 18.0.0 through generated tables, independent of the running
   Python. Broad mode becomes the curated set, plus Default_Ignorable_Code_Point, plus
   `Cf` minus the visible Prepended_Concatenation_Mark characters. Narrow mode keeps the
   curated list. Contract: every code point of the derived files is classified as the
   files say.
2. Typed findings: a frozen `Finding` with index, code point, character, kind and name,
   and `scan()` that returns them. Kinds: bidi, joiner, zero-width, tag,
   variation-selector, filler, format, ignorable. Every function takes `kinds=` to act on
   some kinds only (for example only bidi controls). `find_invisible` keeps its tuple
   shape.
3. Reveal mode: `reveal()` replaces each hidden character with a visible marker
   (`<U+200B>`, a `\u` escape, the name, or a callable).
4. `keep_emoji=True`: keep ZWJ, VS15/VS16 and tag characters only where they belong to an
   emoji sequence by the UTS #51 grammar. Tightened on purpose: the tag sequence must be a
   flag tag sequence of Annex C shape, a presentation selector must follow a character
   listed in emoji-variation-sequences.txt, and an ASCII digit, `#` or `*` only counts as
   an element when it carries FE0F. Variation selectors from the supplementary block
   (the emoji smuggling channel) are never kept. Contract: every RGI sequence and every
   line of emoji-test.txt survives, and without the flag the same sequences lose exactly
   their hidden characters.
5. `keep_joiners=True`: keep ZWNJ and ZWJ in the A1, A2 and B contexts of UTS #39 with
   the single-script and NFC conditions. Contract: the three figures of the standard.
6. `unpaired_bidi()`: openers (LRE, RLE, LRO, RLO, LRI, RLI, FSI) still open at a
   paragraph separator or at the end of text, and closers (PDF, PDI) with nothing to
   close, matched as UAX #9 X6a and X7 do. This is the check compilers added for Trojan
   Source.
7. Command line tool `zerowidth` (and `python -m zerowidth`): `check` reports
   `path:line:col U+XXXX NAME kind` with exit 1 on findings, `strip` and `reveal` write to
   stdout, bytes in and out so newlines and encodings are not rewritten.
8. Runnable docs: every `# ->` line in the README is executed by a test.
9. Packaging: console script, keywords, classifiers, `LICENSE-UNICODE` in the wheel, the
   sdist carries the manifest and scripts but no Unicode data, installed-wheel e2e test.

Considered and left out:

- Confusable detection (the full UTS #39 skeleton): it is a different job with a large
  data file; this library only covers the step the skeleton shares with it, removing
  default ignorables.
- Keeping standardized and ideographic variation sequences (CJK, Mongolian): it needs
  StandardizedVariants.txt and the Ideographic Variation Database. Callers who handle such
  text pass `kinds=` without `variation-selector`.
- Bidi overflow (depth 125) is not modelled: a text that deep is reported anyway.
