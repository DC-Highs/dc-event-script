import subprocess

import pytest

from scripts import build


def test_run_build_invokes_pyinstaller(monkeypatch, capsys):
    calls = []
    monkeypatch.setattr(build.subprocess, "run", lambda args, check: calls.append((args, check)))

    build.run_build()

    args, check = calls[0]
    assert check is True
    assert args[0] == "pyinstaller" and args[-1] == "src/main.py"
    assert "--onefile" in args and "--noconsole" in args
    assert "Build successful" in capsys.readouterr().out


def test_run_build_exits_when_the_build_fails(monkeypatch, capsys):
    def fail(args, check):
        raise subprocess.CalledProcessError(1, args)

    monkeypatch.setattr(build.subprocess, "run", fail)

    with pytest.raises(SystemExit) as error:
        build.run_build()

    assert error.value.code == 1
    assert "Build failed" in capsys.readouterr().out


def test_run_build_exits_when_pyinstaller_is_missing(monkeypatch, capsys):
    def missing(args, check):
        raise FileNotFoundError()

    monkeypatch.setattr(build.subprocess, "run", missing)

    with pytest.raises(SystemExit) as error:
        build.run_build()

    assert error.value.code == 1
    assert "PyInstaller not found" in capsys.readouterr().out
