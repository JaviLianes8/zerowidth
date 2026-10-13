# zerowidth

Detect, reveal and strip zero-width and invisible characters in text: zero-width spaces
and joiners, bidi controls, tag characters, variation selectors, fillers and every other
default-ignorable or format character of Unicode 18.0, with emoji and real words kept
intact when you ask.

## Install

```
pip install zerowidth
```

## Usage

```python
from zerowidth import find_invisible, has_invisible, reveal, scan, strip_invisible

pasted = "in\u200bvo\ufeffice"

has_invisible(pasted)  # -> True
strip_invisible(pasted)  # -> 'invoice'
find_invisible(pasted)  # -> [(2, 8203), (5, 65279)]
reveal(pasted)  # -> 'in<U+200B>vo<U+FEFF>ice'
reveal(pasted, style="name")  # -> 'in<ZERO WIDTH SPACE>vo<ZERO WIDTH NO-BREAK SPACE>ice'
```

Ordinary whitespace (space, tab, newline, carriage return, no-break space) is left alone:

```python
strip_invisible("line one\tword\r\nline two")  # -> 'line one\tword\r\nline two'
```

### Findings and kinds

`scan` returns a frozen `Finding` per hidden character: the code point index in the
string, the code point, its kind, and `char`, `label` and `name` helpers.

```python
item = scan("file\u202etxt.exe")[0]
(item.index, item.label, item.kind, item.name)  # -> (4, 'U+202E', 'bidi', 'RIGHT-TO-LEFT OVERRIDE')
```

Every hidden character belongs to exactly one kind:

| kind | what it covers |
| --- | --- |
| `bidi` | the Bidi_Control characters: marks, embeddings, overrides, isolates |
| `joiner` | ZERO WIDTH NON-JOINER and ZERO WIDTH JOINER |
| `zero-width` | ZERO WIDTH SPACE, WORD JOINER, ZERO WIDTH NO-BREAK SPACE (the BOM) |
| `tag` | the tag characters U+E0001 and U+E0020..U+E007F |
| `variation-selector` | U+FE00..U+FE0F, U+E0100..U+E01EF and the Mongolian selectors |
| `filler` | the Hangul fillers and the braille blank |
| `format` | any other format character (soft hyphen, invisible math operators, ...) |
| `ignorable` | any other default-ignorable code point, reserved ones included |

Every function takes `kinds=` to act on some kinds only, for example to deal with bidi
controls and nothing else:

```python
strip_invisible("a\u200bb\u202ec", kinds={"bidi"}) == "a\u200bbc"  # -> True
```

### What counts as hidden

With `broad=True` (the default) the set is the curated list below plus every code point
that Unicode 18.0.0 marks Default_Ignorable_Code_Point, plus every format character
(`Cf`) except the Prepended_Concatenation_Mark ones such as U+0600 ARABIC NUMBER SIGN,
which draw a visible sign. The answer comes from tables generated from the Unicode data
files, so it is the same on every Python version.

```python
has_invisible("\u0600\u0661")  # -> False
has_invisible("\U0001d173")  # -> True
```

With `broad=False` only the curated list counts: the zero-width space, non-joiner and
joiner, the word joiner, the byte order mark, the soft hyphen, the bidi marks,
embeddings, overrides and isolates, the invisible math operators, the deprecated format
controls, the Hangul, Khmer and Mongolian invisibles, the combining grapheme joiner, the
braille blank and the tag block. Variation selectors are not in it.

```python
has_invisible("\ufe0f", broad=False)  # -> False
has_invisible("\u200b", broad=False)  # -> True
```

### Keeping emoji and words intact

`keep_emoji=True` keeps the joiners, presentation selectors and tag characters that are
part of an emoji sequence (the UTS #51 grammar), and still reports the ones that are not.
The rule is strict on purpose: a selector must follow a character that has an emoji
variation sequence (a digit, `#` or `*` only inside a keycap), a tag sequence must be one
of the recommended (RGI) subdivision flags, England, Scotland or Wales, and selectors from
the supplementary block, a known way to hide bytes behind an emoji, never count.

```python
family = "\U0001f468\u200d\U0001f469\u200d\U0001f467"
strip_invisible(family) == "\U0001f468\U0001f469\U0001f467"  # -> True
strip_invisible(family, keep_emoji=True) == family  # -> True
strip_invisible("\U0001f600\U000e0105\U000e0111", keep_emoji=True) == "\U0001f600"  # -> True
```

`keep_joiners=True` keeps ZWNJ and ZWJ where UTS #39 (section 3.1.1.1) says a word needs
them: breaking a cursive join in Arabic-script words, and after a virama in Indic
conjuncts. The sequence must be in one script and in NFC (checked with the running
Python's normalization data).

```python
persian = "\u0646\u0627\u0645\u0647\u200c\u0627\u06cc"
strip_invisible(persian, keep_joiners=True) == persian  # -> True
strip_invisible("a\u200cb", keep_joiners=True)  # -> 'ab'
```

### Trojan Source

`unpaired_bidi` returns the bidi controls left open at the end of a paragraph (or of
the text) and the closers that close nothing, matched the way UAX #9 does; an embedding
that a PDI cuts short is reported too, since it never got its PDF. Those are the controls
that make code or text display in a different order than it reads.

```python
from zerowidth import unpaired_bidi

source = "/*\u202e } \u2066if (admin)\u2069 \u2066 */\n"
[f.label for f in unpaired_bidi(source)]  # -> ['U+202E', 'U+2066']
```

## Command line

```
zerowidth check notes.txt main.py      # path:line:col U+XXXX NAME (kind), exit 1 if any
zerowidth check --bidi main.c          # only unpaired bidi controls
zerowidth strip --keep-emoji < in.txt  # stdin to stdout, newlines untouched
zerowidth reveal --style name in.txt
```

Every command takes `--narrow`, `--keep-emoji`, `--keep-joiners` and `--kind KIND`
(repeatable); `check --bidi` takes none of them. Input is read as UTF-8 bytes and output
written as UTF-8 bytes. Lines end at CR LF, CR or LF and columns count code points from 1.
Files are named one by one (the tool does not expand wildcards). Exit status: `check`
gives 0 when nothing is found and 1 when something is, `strip` and `reveal` give 0, and
every command gives 2 on a usage or input error. `python -m zerowidth` works too.

## Why

Hidden characters slip into text through copy-paste, rich editors and deliberate
tampering, and they break search, deduplication and comparison while staying invisible
on screen; bidi controls can make source code read differently from how it runs. The
common recipes either strip too little (a hand-made list), too much (every `Cf`,
including visible number signs, every joiner, including those in emoji and Persian
words), or depend on the interpreter's Unicode version. This library is typed, has no
runtime dependencies, follows the Unicode data and standards, and ships with tests that
check it against them.

## Unicode data

The tables in `src/zerowidth/_ucd_*.py` are generated from the Unicode Character
Database 18.0.0 by `scripts/gen_ucd_tables.py`. The data files themselves are not in the
repository: `python scripts/fetch_upstream.py` downloads them into `data/ucd/`, checked
against the sizes and hashes in `data/ucd/MANIFEST.json`, and the tests that compare the
library with them skip until then.

## License

MIT. See [LICENSE](LICENSE). The generated tables derive from Unicode data, distributed
under the Unicode License v3: see [LICENSE-UNICODE](LICENSE-UNICODE).

## Links

- Website: https://lianes8studio.com
- GitHub: https://github.com/JaviLianes8
- LinkedIn: https://www.linkedin.com/in/jlianes/
