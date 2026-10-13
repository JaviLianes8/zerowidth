"""Build the real wheel, install it into a throwaway venv and drive the installed script.

Nothing is mocked: this needs network access for pip to fetch the build backend.
"""

from __future__ import annotations

import os
import subprocess
import sys
import venv
import zipfile
from pathlib import Path

import pytest

import zerowidth

ROOT = Path(__file__).resolve().parent.parent
FAMILY = "\U0001f468\u200d\U0001f469\u200d\U0001f467"


def _run(cmd: list[str], stdin: bytes = b"") -> subprocess.CompletedProcess[bytes]:
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(cmd, input=stdin, capture_output=True, env=env, timeout=600, check=False)


@pytest.mark.e2e
def test_wheel_installs_and_the_script_works(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    built = _run(
        [sys.executable, "-m", "pip", "wheel", "--no-deps", "-q", "-w", str(dist), str(ROOT)]
    )
    assert built.returncode == 0, built.stderr.decode(errors="replace")
    wheels = list(dist.glob("zerowidth-*.whl"))
    assert [w.name for w in wheels] == [f"zerowidth-{zerowidth.__version__}-py3-none-any.whl"]
    names = zipfile.ZipFile(wheels[0]).namelist()
    assert "zerowidth/py.typed" in names and "zerowidth/_ucd_part1.py" in names
    assert any(n.endswith("licenses/LICENSE-UNICODE") for n in names)
    assert not [n for n in names if n.startswith(("data/", "tests/", "scripts/"))]
    assert not [n for n in names if n.endswith(".txt") and ".dist-info/" not in n]

    env_dir = tmp_path / "venv"
    venv.EnvBuilder(with_pip=True, clear=True).create(env_dir)
    bindir = env_dir / ("Scripts" if os.name == "nt" else "bin")
    python = bindir / ("python.exe" if os.name == "nt" else "python")
    script = bindir / ("zerowidth.exe" if os.name == "nt" else "zerowidth")
    installed = _run([str(python), "-m", "pip", "install", "-q", "--no-index", str(wheels[0])])
    assert installed.returncode == 0, installed.stderr.decode(errors="replace")
    assert script.is_file()

    text = f"ok\nhe\u200bllo {FAMILY}\n\u202eevil\n".encode()
    done = _run([str(script), "check", "--keep-emoji"], text)
    assert done.returncode == 1
    assert done.stdout.decode().splitlines() == [
        "<stdin>:2:3: U+200B ZERO WIDTH SPACE (zero-width)",
        "<stdin>:3:1: U+202E RIGHT-TO-LEFT OVERRIDE (bidi)",
    ]
    done = _run([str(script), "strip", "--keep-emoji"], text)
    assert (done.returncode, done.stdout) == (0, f"ok\nhello {FAMILY}\nevil\n".encode())
    done = _run([str(script), "check", "--bidi"], text)
    assert done.stdout == b"<stdin>:3:1: U+202E RIGHT-TO-LEFT OVERRIDE (unpaired bidi)\n"
    done = _run([str(python), "-m", "zerowidth", "reveal"], "a\u2060b\r\n".encode())
    assert done.stdout == b"a<U+2060>b\r\n"
    failed = _run([str(script), "check"], b"\xff")
    assert failed.returncode == 2 and b"UTF-8" in failed.stderr and failed.stdout == b""
    version = _run([str(script), "--version"])
    assert version.stdout.strip() == f"zerowidth {zerowidth.__version__}".encode()

    probe = "import zerowidth; print(zerowidth.UNICODE_VERSION, zerowidth.__file__)"
    shown = _run([str(python), "-c", probe]).stdout.decode()
    assert shown.startswith(f"{zerowidth.UNICODE_VERSION} ") and str(env_dir) in shown
