"""Jaminan entry point selftest tidak menyentuh runtime GUI/jaringan."""

import os
from pathlib import Path
import subprocess
import sys

import pytest

from island_linux import selftest


def test_cli_runs_with_only_standard_library():
    root = Path(__file__).resolve().parents[1]
    env = {key: value for key, value in os.environ.items()
           if key not in ("DISPLAY", "WAYLAND_DISPLAY", "DBUS_SESSION_BUS_ADDRESS")}
    result = subprocess.run([sys.executable, "-S", "-O", str(root / "island.py"), "--selftest"],
                            cwd=root, env=env, capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.count("PASS:") == 2


def test_selftest_reports_failure_and_nonzero_exit(monkeypatch, capsys):
    def broken():
        raise RuntimeError("simulasi gagal")
    monkeypatch.setattr(selftest, "check_mpris", broken)
    assert selftest.run() == 1
    assert "FAIL: MPRIS" in capsys.readouterr().out


@pytest.mark.parametrize("options", [["--selftest", "--demo"], ["--inspect", "--demo"]])
def test_cli_rejects_conflicting_modes(options):
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run([sys.executable, str(root / "island.py"), *options],
                            capture_output=True, text=True, timeout=10)
    assert result.returncode == 2
