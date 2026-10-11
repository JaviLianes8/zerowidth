# zerowidth

Detect and strip zero-width and invisible characters from text.

## Install

```
pip install zerowidth
```

## Usage

```python
from zerowidth import has_invisible, strip_invisible, find_invisible

pasted = "in​vo﻿ice"

has_invisible(pasted)       # True
strip_invisible(pasted)     # "invoice"
find_invisible(pasted)      # [(2, 8203), (5, 65279)]
```

`strip_invisible` leaves ordinary whitespace (space, tab, newline, carriage return)
untouched, so only the hidden characters go:

```python
strip_invisible("line one\tword\nline two")   # unchanged
```

By default every function also flags any Unicode format character (category `Cf`) beyond
the named set. Pass `broad=False` to match only the curated code points:

```python
has_invisible("؀", broad=False)   # False, Cf but not curated
has_invisible("​", broad=False)   # True, zero width space
```

### What it covers

The curated set is explicit and auditable: the zero-width space, non-joiner and joiner,
the word joiner, the byte-order mark (zero-width no-break space), the soft hyphen, the
bidirectional marks, embeddings, overrides and isolates, the invisible math operators, the
Hangul and Mongolian fillers, the combining grapheme joiner, the braille blank and the
deprecated tag characters. With `broad=True` (the default) any other format character is
caught through its Unicode category. `find_invisible` returns the position and code point
of each one, which is enough to audit pasted text or to spot steganography and homoglyph
tricks.

## Why

Hidden characters slip into text through copy-paste, rich editors and deliberate
tampering, and they break search, deduplication and comparison while staying invisible on
screen. The existing options do not fit: `gremlinc` is years stale and stego-oriented,
`zwsp-steg-py` is a steganography codec rather than a sanitizer, and the common
`\p{Cf}` recipe needs the third-party `regex` module. This is a small, typed, zero-dependency
library focused on one job: a curated set of invisible code points plus an optional broad
category fallback, with no runtime dependencies.

## License

MIT. See [LICENSE](LICENSE).

## Links

- Website: https://lianes8studio.com
- GitHub: https://github.com/JaviLianes8
- LinkedIn: https://www.linkedin.com/in/jlianes/
