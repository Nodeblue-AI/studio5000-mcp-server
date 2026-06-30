"""Tests for optional Rockwell external CLI tool discovery/execution."""

from __future__ import annotations

import subprocess
from pathlib import Path


class TestToolDiscovery:
    def test_find_l5xplode_from_env(self, monkeypatch, tmp_path):
        exe = tmp_path / "l5xplode.exe"
        exe.write_text("")
        monkeypatch.setenv("L5XPLODE_EXE", str(exe))

        from studio5000_mcp_server.external_tools import find_l5xplode

        assert find_l5xplode() == exe.resolve()

    def test_find_l5xgit_from_env(self, monkeypatch, tmp_path):
        exe = tmp_path / "l5xgit.exe"
        exe.write_text("")
        monkeypatch.setenv("L5XGIT_EXE", str(exe))

        from studio5000_mcp_server.external_tools import find_l5xgit

        assert find_l5xgit() == exe.resolve()

    def test_find_l5xplode_from_path(self, monkeypatch, tmp_path):
        exe = tmp_path / "l5xplode.exe"
        exe.write_text("")
        monkeypatch.delenv("L5XPLODE_EXE", raising=False)
        monkeypatch.setattr("shutil.which", lambda name: str(exe) if name == "l5xplode" else None)

        from studio5000_mcp_server.external_tools import find_l5xplode

        assert find_l5xplode() == exe.resolve()

    def test_missing_tool_returns_none(self, monkeypatch):
        monkeypatch.delenv("L5XPLODE_EXE", raising=False)
        monkeypatch.setattr("shutil.which", lambda name: None)

        from studio5000_mcp_server.external_tools import find_l5xplode

        assert find_l5xplode() is None


class TestRunExternalTool:
    def test_run_external_tool_captures_result(self, monkeypatch):
        completed = subprocess.CompletedProcess(
            args=["tool", "arg"],
            returncode=2,
            stdout="out",
            stderr="err",
        )
        calls = []

        def fake_run(command, **kwargs):
            calls.append((command, kwargs))
            return completed

        monkeypatch.setattr(subprocess, "run", fake_run)

        from studio5000_mcp_server.external_tools import run_external_tool

        result = run_external_tool(["tool", "arg"], timeout=123)

        assert result.command == ["tool", "arg"]
        assert result.returncode == 2
        assert result.stdout == "out"
        assert result.stderr == "err"
        assert calls == [
            (
                ["tool", "arg"],
                {
                    "capture_output": True,
                    "text": True,
                    "timeout": 123,
                    "check": False,
                },
            )
        ]
