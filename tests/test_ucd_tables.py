"""The embedded tables against the fetched UCD files and a fresh generator run."""

from __future__ import annotations

import hashlib
import importlib.util
import re
from pathlib import Path
from types import ModuleType

from conftest import MANIFEST, UCD, needs_ucd, ucd_values, with_value

from zerowidth import _props as p

ROOT = Path(__file__).resolve().parent.parent
PACKAGE = ROOT / "src" / "zerowidth"
EVERY = range(0x110000)


def _generator() -> ModuleType:
    spec = importlib.util.spec_from_file_location("gen", ROOT / "scripts" / "gen_ucd_tables.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _bit(bit: int) -> set[int]:
    return {cp for cp in EVERY if p.prop(cp) & bit}


@needs_ucd
def test_committed_tables_equal_generator_output() -> None:
    files = _generator().render(UCD)
    assert set(files) == {path.name for path in PACKAGE.glob("_ucd_*.py")}
    for name, text in files.items():
        assert (PACKAGE / name).read_text(encoding="utf-8") == text, f"{name} is stale"
        assert len(text.splitlines()) <= 200


@needs_ucd
def test_snapshot_files_match_the_manifest_and_one_version() -> None:
    assert {path.name for path in UCD.glob("*.txt")} == set(MANIFEST)
    for name, entry in MANIFEST.items():
        data = (UCD / name).read_bytes()
        assert (len(data), hashlib.sha256(data).hexdigest()) == (entry["size"], entry["sha256"])
        head = data[:600].decode("utf-8")
        assert re.search(r"(-18\.0\.0\.txt|Version: 18\.0)", head), name


@needs_ucd
def test_flag_bits_equal_the_ucd_files() -> None:
    pairs = [
        (p.DICP, "DerivedCoreProperties.txt", "Default_Ignorable_Code_Point"),
        (p.CF, "DerivedGeneralCategory.txt", "Cf"),
        (p.NONSPACING, "DerivedGeneralCategory.txt", "Mn"),
        (p.BIDI_CONTROL, "PropList.txt", "Bidi_Control"),
        (p.VARIATION_SELECTOR, "PropList.txt", "Variation_Selector"),
        (p.VISIBLE_FORMAT, "PropList.txt", "Prepended_Concatenation_Mark"),
        (p.PARAGRAPH, "DerivedBidiClass.txt", "B"),
        (p.EMOJI, "emoji-data.txt", "Emoji"),
        (p.EXT_PICT, "emoji-data.txt", "Extended_Pictographic"),
        (p.EMOJI_MODIFIER, "emoji-data.txt", "Emoji_Modifier"),
        (p.TRANSPARENT, "DerivedJoiningType.txt", "T"),
        (p.VIRAMA, "DerivedCombiningClass.txt", "9"),
        (p.VOWEL_DEPENDENT, "IndicSyllabicCategory.txt", "Vowel_Dependent"),
    ]
    for bit, name, value in pairs:
        assert _bit(bit) == with_value(name, value), (name, value)
    letters = {cp for cp, v in ucd_values("DerivedGeneralCategory.txt").items() if v[0][0] == "L"}
    assert _bit(p.LETTER) == letters
    combining = {cp for cp, v in ucd_values("DerivedCombiningClass.txt").items() if v[0] != "0"}
    assert _bit(p.COMBINING) == combining


@needs_ucd
def test_joining_types_and_emoji_selector_bases_equal_the_ucd_files() -> None:
    expected = {"L": p.JOIN_LEFT, "R": p.JOIN_RIGHT, "D": p.JOIN_DUAL}
    types = ucd_values("DerivedJoiningType.txt")
    for cp in EVERY:
        assert p.joining(p.prop(cp)) == expected.get(types.get(cp, ["U"])[0], 0), hex(cp)
    text = (UCD / "emoji-variation-sequences.txt").read_text(encoding="utf-8")
    bases = {int(base, 16) for base in re.findall(r"^(\w+) FE0F ", text, re.M)}
    assert _bit(p.EMOJI_VS_BASE) == bases and len(bases) > 300


@needs_ucd
def test_scripts_equal_the_ucd_file() -> None:
    scripts = ucd_values("Scripts.txt")
    names = sorted({values[0] for values in scripts.values()})
    for cp in EVERY:
        name = scripts.get(cp, ["Unknown"])[0]
        index = p.script(p.prop(cp))
        if name in ("Common", "Inherited"):
            assert index == -1, hex(cp)
        else:
            assert index == (0 if name == "Unknown" else names.index(name) + 1), hex(cp)


def test_spot_properties_without_the_data_files() -> None:
    assert p.UNICODE_VERSION == "18.0.0"
    assert p.prop(0x200B) & p.DICP and p.prop(0x200B) & p.CF
    assert p.prop(0x0600) & p.CF and p.prop(0x0600) & p.VISIBLE_FORMAT
    assert not p.prop(0x0600) & p.DICP
    assert p.prop(0x202E) & p.BIDI_CONTROL and p.prop(0xFE0F) & p.VARIATION_SELECTOR
    assert p.prop(0x2764) & p.EMOJI_VS_BASE and not p.prop(0x41) & p.EMOJI_VS_BASE
    assert p.prop(0x0A) & p.PARAGRAPH and p.prop(0x2029) & p.PARAGRAPH
    assert not p.prop(0x2028) & p.PARAGRAPH
    assert p.joining(p.prop(0x0628)) == p.JOIN_DUAL and p.joining(p.prop(0x0627)) == p.JOIN_RIGHT
    assert p.prop(0x064B) & p.TRANSPARENT and p.prop(0x094D) & p.VIRAMA
    assert p.prop(0x093E) & p.VOWEL_DEPENDENT and p.prop(0x0915) & p.LETTER
    assert p.script(p.prop(0x41)) != p.script(p.prop(0x0915)) and p.script(p.prop(0x20)) == -1
    assert p.prop(0x10FFFF) == p.prop(0x10FFFE)
