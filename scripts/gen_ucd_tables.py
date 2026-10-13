"""Generate the embedded Unicode property tables from the fetched UCD files.

Usage::

    python scripts/gen_ucd_tables.py            # rewrite src/zerowidth/_ucd_*.py
    python scripts/gen_ucd_tables.py --check    # exit 1 if the files are stale

Inputs live in ``data/ucd/``, which git ignores: ``python scripts/fetch_upstream.py``
fetches them as pinned in ``data/ucd/MANIFEST.json``. Each code point gets a packed code
(``BITS`` below, joining type at ``JOINING_SHIFT``, script at ``SCRIPT_SHIFT``), stored as
a palette of distinct codes and base-36 runs of ``palette index, length``.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UCD_DIR = ROOT / "data" / "ucd"
OUT_DIR = ROOT / "src" / "zerowidth"
MAX_CP = 0x10FFFF
LINE_WIDTH = 88
LINES_PER_PART = 180
DIGITS = "0123456789abcdefghijklmnopqrstuvwxyz"

BITS = {
    "DICP": 1 << 0,
    "CF": 1 << 1,
    "BIDI_CONTROL": 1 << 2,
    "VARIATION_SELECTOR": 1 << 3,
    "VISIBLE_FORMAT": 1 << 4,
    "EMOJI": 1 << 5,
    "EXT_PICT": 1 << 6,
    "EMOJI_MODIFIER": 1 << 7,
    "EMOJI_VS_BASE": 1 << 8,
    "PARAGRAPH": 1 << 9,
    "TRANSPARENT": 1 << 12,
    "LETTER": 1 << 13,
    "NONSPACING": 1 << 14,
    "COMBINING": 1 << 15,
    "VIRAMA": 1 << 16,
    "VOWEL_DEPENDENT": 1 << 17,
}
JOINING_SHIFT = 10
JOINING = {"L": 1, "R": 2, "D": 3}
SCRIPT_SHIFT = 18

_LINE = re.compile(r"^([0-9A-F]{4,6})(?:\.\.([0-9A-F]{4,6}))?\s*;\s*([^#]+?)\s*(?:#|$)")


def _ranges(path: Path) -> list[tuple[int, int, str]]:
    """Return ``(first, last, value)`` for every data line of a UCD file."""
    found: list[tuple[int, int, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = _LINE.match(line)
        if match:
            first = int(match.group(1), 16)
            last = int(match.group(2) or match.group(1), 16)
            found.append((first, last, match.group(3)))
    return found


def unicode_version(ucd_dir: Path = UCD_DIR) -> str:
    """Read the Unicode version from the DerivedCoreProperties.txt header."""
    head = (ucd_dir / "DerivedCoreProperties.txt").read_text(encoding="utf-8")[:500]
    match = re.search(r"DerivedCoreProperties-(\d+\.\d+\.\d+)\.txt", head)
    if match is None:
        raise ValueError("cannot find the Unicode version in DerivedCoreProperties.txt")
    return match.group(1)


def script_names(ucd_dir: Path = UCD_DIR) -> list[str]:
    """Return ``Unknown`` followed by every script of Scripts.txt in sorted order."""
    names = sorted({value for _, _, value in _ranges(ucd_dir / "Scripts.txt")})
    return ["Unknown", *names]


def property_codes(ucd_dir: Path = UCD_DIR) -> list[int]:
    """Return one packed property code per code point, built from the UCD files."""
    codes = [0] * (MAX_CP + 1)
    letters = {gc: BITS["LETTER"] for gc in ("Lu", "Ll", "Lt", "Lm", "Lo")}
    combining = {str(ccc): BITS["COMBINING"] for ccc in range(1, 256)}
    combining["9"] |= BITS["VIRAMA"]
    joining = {name: value << JOINING_SHIFT for name, value in JOINING.items()}
    scripts = {name: n << SCRIPT_SHIFT for n, name in enumerate(script_names(ucd_dir))}
    sources: dict[str, dict[str, int]] = {
        "DerivedCoreProperties.txt": {"Default_Ignorable_Code_Point": BITS["DICP"]},
        "DerivedGeneralCategory.txt": {"Cf": BITS["CF"], "Mn": BITS["NONSPACING"], **letters},
        "PropList.txt": {
            "Bidi_Control": BITS["BIDI_CONTROL"],
            "Variation_Selector": BITS["VARIATION_SELECTOR"],
            "Prepended_Concatenation_Mark": BITS["VISIBLE_FORMAT"],
        },
        "DerivedBidiClass.txt": {"B": BITS["PARAGRAPH"]},
        "emoji-data.txt": {
            "Emoji": BITS["EMOJI"],
            "Extended_Pictographic": BITS["EXT_PICT"],
            "Emoji_Modifier": BITS["EMOJI_MODIFIER"],
        },
        "IndicSyllabicCategory.txt": {"Vowel_Dependent": BITS["VOWEL_DEPENDENT"]},
        "DerivedJoiningType.txt": {"T": BITS["TRANSPARENT"], **joining},
        "DerivedCombiningClass.txt": combining,
        "Scripts.txt": scripts,
    }
    for file, wanted in sources.items():
        for first, last, value in _ranges(ucd_dir / file):
            bits = wanted.get(value, 0)
            for cp in range(first, last + 1) if bits else ():
                codes[cp] |= bits
    # Lines read "BASE FE0F ; emoji style;": the base has an emoji presentation sequence.
    sequences = (ucd_dir / "emoji-variation-sequences.txt").read_text(encoding="utf-8")
    for base in re.findall(r"^([0-9A-F]{4,6}) FE0F\s*;", sequences, re.M):
        codes[int(base, 16)] |= BITS["EMOJI_VS_BASE"]
    return codes


def _base36(number: int) -> str:
    return DIGITS[number] if number < 36 else _base36(number // 36) + DIGITS[number % 36]


def encode(codes: list[int]) -> tuple[list[int], list[str]]:
    """Return the palette of distinct codes and the run tokens ``PP<length>``."""
    palette = sorted(set(codes))
    if len(palette) > 36 * 36:
        raise ValueError("palette does not fit in two base-36 digits")
    slot = {code: number for number, code in enumerate(palette)}
    tokens: list[str] = []
    start = 0
    for cp in range(1, len(codes) + 1):
        if cp == len(codes) or codes[cp] != codes[start]:
            tokens.append(_base36(slot[codes[start]]).rjust(2, "0") + _base36(cp - start))
            start = cp
    return palette, tokens


def _wrap(items: list[str], sep: str) -> list[str]:
    lines: list[str] = []
    current = ""
    for item in items:
        if current and len(current) + len(item) + len(sep) > LINE_WIDTH:
            lines.append(current)
            current = ""
        current += item + sep
    return [*lines, current] if current else lines


def render(ucd_dir: Path = UCD_DIR) -> dict[str, str]:
    """Return ``{file name: source text}`` for every generated module."""
    palette, tokens = encode(property_codes(ucd_dir))
    lines = _wrap(tokens, " ")
    parts = [lines[i : i + LINES_PER_PART] for i in range(0, len(lines), LINES_PER_PART)]
    note = "# Generated by scripts/gen_ucd_tables.py from data/ucd/. Do not edit.\n"
    files: dict[str, str] = {}
    for number, chunk in enumerate(parts, start=1):
        body = "".join(f'    "{line}"\n' for line in chunk)
        files[f"_ucd_part{number}.py"] = (
            f'"""Run-length property data, part {number}."""\n\n{note}\nRUNS = (\n{body})\n'
        )
    numbers = range(1, len(parts) + 1)
    imports = "".join(f"from ._ucd_part{n} import RUNS as _R{n}\n" for n in numbers)
    joined = " + ".join(f"_R{n}" for n in numbers)
    codes = "".join(f'    "{line}"\n' for line in _wrap([_base36(c) for c in palette], " "))
    scripts = script_names(ucd_dir)
    bits = "".join(f"{name} = {value}\n" for name, value in BITS.items())
    files["_ucd_data.py"] = (
        '"""Index of the generated Unicode property data."""\n\n'
        f"{note}\nfrom __future__ import annotations\n\n{imports}\n"
        f'UNICODE_VERSION = "{unicode_version(ucd_dir)}"\n{bits}'
        f"JOINING_SHIFT = {JOINING_SHIFT}\nSCRIPT_SHIFT = {SCRIPT_SHIFT}\n"
        f"SCRIPT_COMMON = {scripts.index('Common')}\n"
        f"SCRIPT_INHERITED = {scripts.index('Inherited')}\n"
        f"CODES = (\n{codes})\nRUNS = {joined}\n"
    )
    return files


def main(argv: list[str]) -> int:
    if not (UCD_DIR / "DerivedCoreProperties.txt").is_file():
        print("data/ucd/ is not fetched; run python scripts/fetch_upstream.py", file=sys.stderr)
        return 0 if "--check" in argv else 1
    files = render()
    current = {p.name: p.read_text(encoding="utf-8") for p in OUT_DIR.glob("_ucd_*.py")}
    stale = [name for name, text in files.items() if current.get(name) != text]
    stale += sorted(name for name in current if name not in files)
    if "--check" in argv:
        print("".join(f"stale: {name}\n" for name in stale), end="", file=sys.stderr)
        return 1 if stale else 0
    for name, text in files.items():
        (OUT_DIR / name).write_text(text, encoding="utf-8", newline="\n")
    for name in current:
        if name not in files:
            (OUT_DIR / name).unlink()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
