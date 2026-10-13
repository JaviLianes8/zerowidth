# Contributing

Thanks for taking the time. This project keeps a small, predictable shape.

## Setup

```
pip install -r requirements-dev.txt
```

## Before you open a pull request

- Keep public API in `src/zerowidth/__init__.py`; internals live in `_`-prefixed modules.
- Add a test for the behaviour you change. Tests inject time, disk and network; they
  never touch the real thing.
- Run `scripts/check.ps1` (format, lint, types, tests) and make sure it passes.
- One logical change per commit, imperative subject line.

## Unicode data

The property tables in `src/zerowidth/_ucd_*.py` are generated; never edit them by hand.

```
python scripts/fetch_upstream.py        # fetch the pinned UCD files into data/ucd/
python scripts/gen_ucd_tables.py        # regenerate the tables
python scripts/gen_ucd_tables.py --check
```

The data files stay out of git: `data/ucd/MANIFEST.json` records their URL, size, sha256
and licence. To move to a new Unicode version, update the URLs and hashes in the manifest,
fetch, regenerate, and let the tests that compare the library with the files guide the
rest. Without the files those tests skip.

Open an issue first if the change is large or shifts the public API.
