"""The command line tool, driven in process with byte streams and real files."""

from __future__ import annotations

import io
from pathlib import Path

import pytest

import zerowidth
from zerowidth._cli import main


def run(args: list[str], stdin: bytes = b"") -> tuple[int, bytes]:
    out = io.BytesIO()
    status = main(args, stdin=io.BytesIO(stdin), stdout=out)
    return status, out.getvalue()


def test_check_reports_path_line_column_and_exits_one(tmp_path: Path) -> None:
    path = tmp_path / "notes.txt"
    path.write_bytes("ok\nab\u200bc \u202e\n".encode())
    status, out = run(["check", str(path)])
    assert status == 1
    assert out.decode().splitlines() == [
        f"{path}:2:3: U+200B ZERO WIDTH SPACE (zero-width)",
        f"{path}:2:6: U+202E RIGHT-TO-LEFT OVERRIDE (bidi)",
    ]


def test_check_columns_restart_on_every_line() -> None:
    status, out = run(["check"], "\u200b\n\n x\u200b\nyy\u2060".encode())
    assert out.decode().splitlines() == [
        "<stdin>:1:1: U+200B ZERO WIDTH SPACE (zero-width)",
        "<stdin>:3:3: U+200B ZERO WIDTH SPACE (zero-width)",
        "<stdin>:4:3: U+2060 WORD JOINER (zero-width)",
    ]
    assert status == 1


def test_check_clean_input_exits_zero_and_prints_nothing() -> None:
    assert run(["check", "-"], b"all clear\n") == (0, b"")


def test_check_options_reach_the_scan() -> None:
    heart = "\u2764\ufe0f".encode()
    assert run(["check", "--keep-emoji"], heart) == (0, b"")
    assert run(["check"], heart)[0] == 1
    assert run(["check", "--narrow"], heart) == (0, b"")
    assert run(["check", "--kind", "bidi"], "a\u200b".encode()) == (0, b"")
    assert run(["check", "--keep-joiners"], "\u0647\u200c\u0627".encode()) == (0, b"")


def test_check_bidi_reports_only_unpaired_controls() -> None:
    text = "a\u202eb\u202c c\u2067d\n\u200b".encode()
    status, out = run(["check", "--bidi"], text)
    assert status == 1
    assert out == b"<stdin>:1:7: U+2067 RIGHT-TO-LEFT ISOLATE (unpaired bidi)\n"
    assert run(["check", "--bidi"], "a\u202eb\u202c\u200b".encode()) == (0, b"")


def test_strip_and_reveal_write_bytes_and_keep_newlines() -> None:
    text = "a\u200bb\r\nc\U000e0041\n".encode()
    assert run(["strip"], text) == (0, b"ab\r\nc\n")
    assert run(["reveal"], text) == (0, b"a<U+200B>b\r\nc<U+E0041>\n")
    assert run(["reveal", "--style", "escape"], text) == (0, b"a\\u200bb\r\nc\\U000e0041\n")
    assert run(["strip", "--keep-emoji"], "\u2764\ufe0f\u200b".encode()) == (
        0,
        "\u2764\ufe0f".encode(),
    )


def test_byte_order_mark_is_reported_not_swallowed() -> None:
    status, out = run(["check"], b"\xef\xbb\xbfhi")
    assert status == 1 and b"U+FEFF" in out


def test_invalid_utf8_is_an_error(capsys: pytest.CaptureFixture[str]) -> None:
    assert run(["check"], b"ok \xff") == (2, b"")
    assert "not valid UTF-8 at byte 3" in capsys.readouterr().err


def test_missing_file_is_an_error(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert run(["strip", str(tmp_path / "nope.txt")]) == (2, b"")
    assert "nope.txt" in capsys.readouterr().err


def test_usage_errors_exit_two(capsys: pytest.CaptureFixture[str]) -> None:
    for args in ([], ["check", "--kind", "emoji"], ["reveal", "--style", "html"], ["fix"]):
        with pytest.raises(SystemExit) as raised:
            run(args)
        assert raised.value.code == 2


def test_version_and_help(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        run(["--version"])
    assert capsys.readouterr().out.strip() == f"zerowidth {zerowidth.__version__}"
    with pytest.raises(SystemExit):
        run(["--help"])
    assert "exit status" in capsys.readouterr().out


def test_check_counts_lines_ended_by_cr_lf_or_lone_cr() -> None:
    zwsp = chr(0x200B).encode()
    text = b"a\rb" + zwsp + b"\r\nc" + zwsp + b"\n" + zwsp
    _, out = run(["check"], text)
    rows = [row.split(": ")[0] for row in out.decode().splitlines()]
    assert rows == ["<stdin>:2:2", "<stdin>:3:2", "<stdin>:4:1"]


def test_bidi_refuses_the_scan_options(capsys: pytest.CaptureFixture[str]) -> None:
    for option in (["--kind", "joiner"], ["--narrow"], ["--keep-emoji"], ["--keep-joiners"]):
        with pytest.raises(SystemExit) as raised:
            run(["check", "--bidi", *option], chr(0x202E).encode())
        assert raised.value.code == 2
    assert "--bidi" in capsys.readouterr().err


def test_strip_and_reveal_exit_zero_even_when_they_change_the_text() -> None:
    assert run(["strip"], "a\u200b".encode()) == (0, b"a")
    assert run(["reveal"], "a\u200b".encode())[0] == 0
