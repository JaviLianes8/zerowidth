# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-10-13

### Added

- `scan()` returns a frozen `Finding` (index, code point, kind, plus `char`, `label` and
  `name`) for each hidden character; `KINDS` and the `Kind` type list the eight kinds.
- `kinds=` on every function to act on some kinds only, such as bidi controls.
- `reveal()` shows hidden characters as `<U+200B>`, `\u200b`, `<ZERO WIDTH SPACE>` or
  whatever a callable returns.
- `keep_emoji=True` keeps the joiners, presentation selectors and tags that belong to an
  emoji sequence; `keep_joiners=True` keeps ZWNJ and ZWJ in the word contexts of UTS #39.
- `unpaired_bidi()` reports bidi controls left open in a paragraph or closing nothing.
- A `zerowidth` command (`check`, `strip`, `reveal`) and `python -m zerowidth`.
- `UNICODE_VERSION`: the tables follow Unicode 18.0.0, generated from the Unicode
  Character Database by `scripts/gen_ucd_tables.py`.

### Changed

- Behaviour change: the default broad mode now reports and strips variation selectors, so
  `has_invisible` on a red heart with its emoji presentation selector turns from False to
  True. Pass `keep_emoji=True` to keep selectors, joiners and tags that belong to emoji.
- Broad mode no longer depends on the running Python's Unicode version, and now covers
  every Default_Ignorable_Code_Point, including the variation selectors (so a bare
  emoji presentation selector is reported unless `keep_emoji=True`) and reserved
  default-ignorable code points.

### Fixed

- Broad mode no longer reports the Prepended_Concatenation_Mark characters (U+0600..U+0605,
  U+06DD, U+070F, U+0890..U+0891, U+08E2, U+110BD, U+110CD): they are format characters
  that display a visible sign.

## [0.1.0]

- First release: `has_invisible`, `strip_invisible` and `find_invisible` over a curated set
  of zero-width and invisible code points, with an optional broad Unicode format-category
  fallback and ordinary whitespace left untouched.
