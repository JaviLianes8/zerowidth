"""The ``zerowidth`` command: check, strip or reveal hidden characters in files."""

from __future__ import annotations

import argparse
import re
import sys
from bisect import bisect_right
from collections.abc import Sequence
from typing import Any, BinaryIO

from . import __version__
from ._bidi import unpaired_bidi
from ._chars import KINDS
from ._detect import reveal, scan, strip_invisible
from ._finding import Finding

EPILOG = """examples:
  zerowidth check notes.txt main.py      report hidden characters, exit 1 if any
  zerowidth check --bidi main.c           only bidi controls left unpaired
  zerowidth strip --keep-emoji < in.txt   copy stdin to stdout without them
  zerowidth reveal --style name in.txt    show them as <ZERO WIDTH SPACE>

exit status: check gives 0 when nothing is found and 1 when something is; strip and
reveal give 0; every command gives 2 on a usage or input error"""
_LINE_END = re.compile(r"\r\n|\r|\n")


class InputError(Exception):
    """A file that cannot be read or is not UTF-8."""


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="zerowidth",
        description="Check, strip or reveal zero-width and invisible characters (UTF-8 input).",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"zerowidth {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)
    for name, text in (
        ("check", "report each hidden character as path:line:col"),
        ("strip", "write the text without hidden characters to stdout"),
        ("reveal", "write the text with hidden characters shown as markers"),
    ):
        sub = commands.add_parser(name, help=text, description=text)
        sub.add_argument("files", nargs="*", metavar="FILE", help="files to read; '-' is stdin")
        sub.add_argument("--narrow", action="store_true", help="only the curated set")
        sub.add_argument("--keep-emoji", action="store_true", help="keep emoji sequences")
        sub.add_argument("--keep-joiners", action="store_true", help="keep joiners in words")
        sub.add_argument("--kind", action="append", choices=KINDS, help="only this kind")
        if name == "check":
            sub.add_argument("--bidi", action="store_true", help="only unpaired bidi controls")
        if name == "reveal":
            sub.add_argument(
                "--style", choices=("codepoint", "escape", "name"), default="codepoint"
            )
    return parser


def _read(name: str, stdin: BinaryIO) -> str:
    try:
        if name == "-":
            data = stdin.read()
        else:
            with open(name, "rb") as handle:
                data = handle.read()
    except OSError as error:
        raise InputError(f"{name}: {error.strerror or error}") from error
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise InputError(f"{name}: not valid UTF-8 at byte {error.start}") from error


def _report(name: str, text: str, found: list[Finding], out: BinaryIO, unpaired: bool) -> None:
    # Lines end at CR LF, CR or LF; columns count code points from 1.
    starts = [0, *(match.end() for match in _LINE_END.finditer(text))]
    what = "unpaired " if unpaired else ""
    for item in found:
        line = bisect_right(starts, item.index)
        column = item.index - starts[line - 1] + 1
        row = f"{name}:{line}:{column}: {item.label} {item.name} ({what}{item.kind})"
        out.write(row.encode("utf-8", "replace") + b"\n")


def main(argv: Sequence[str] | None = None, stdin: Any = None, stdout: Any = None) -> int:
    """Run the command line tool and return its exit status."""
    parser = _parser()
    args = parser.parse_args(argv)
    if getattr(args, "bidi", False) and (
        args.narrow or args.keep_emoji or args.keep_joiners or args.kind
    ):
        parser.error("--bidi checks bidi pairing only and takes no other option")
    source: BinaryIO = stdin if stdin is not None else sys.stdin.buffer
    out: BinaryIO = stdout if stdout is not None else sys.stdout.buffer
    options = {
        "broad": not args.narrow,
        "keep_emoji": args.keep_emoji,
        "keep_joiners": args.keep_joiners,
        "kinds": args.kind,
    }
    names = args.files or ["-"]
    try:
        texts = [(name, _read(name, source)) for name in names]
    except InputError as error:
        sys.stderr.write(f"zerowidth: error: {error}\n")
        return 2
    if args.command != "check":
        for _, text in texts:
            if args.command == "strip":
                result = strip_invisible(text, **options)
            else:
                result = reveal(text, style=args.style, **options)
            out.write(result.encode("utf-8"))
        return 0
    found_any = False
    for name, text in texts:
        found = unpaired_bidi(text) if args.bidi else scan(text, **options)
        _report("<stdin>" if name == "-" else name, text, found, out, args.bidi)
        found_any = found_any or bool(found)
    return 1 if found_any else 0
