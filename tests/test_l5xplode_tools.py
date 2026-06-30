"""Tests for l5xplode wrapper helpers."""

from __future__ import annotations

from pathlib import Path

from studio5000_mcp_server.external_tools import ToolRunResult


class TestExplodeL5X:
    def test_missing_l5xplode_returns_prerequisite_error(self, monkeypatch, tmp_path):
        monkeypatch.setattr("studio5000_mcp_server.l5xplode_tools.find_l5xplode", lambda: None)

        from studio5000_mcp_server.l5xplode_tools import explode_l5x

        result = explode_l5x(str(tmp_path / "in.L5X"), str(tmp_path / "out"))

        assert "error" in result
        assert "L5XPLODE_EXE" in result["error"]
        assert result["requires"]

    def test_explode_builds_expected_command(self, monkeypatch, tmp_path):
        exe = tmp_path / "l5xplode.exe"
        l5x = tmp_path / "in.L5X"
        out = tmp_path / "out"
        commands = []

        monkeypatch.setattr("studio5000_mcp_server.l5xplode_tools.find_l5xplode", lambda: exe)

        def fake_run(command, timeout=300):
            commands.append((command, timeout))
            return ToolRunResult(command, 0, "exploded", "")

        monkeypatch.setattr("studio5000_mcp_server.l5xplode_tools.run_external_tool", fake_run)

        from studio5000_mcp_server.l5xplode_tools import explode_l5x

        result = explode_l5x(
            str(l5x),
            str(out),
            force=True,
            pretty_attributes=True,
            unsafe_skip_dependency_check=True,
            timeout=999,
        )

        assert result["success"] is True
        assert result["outputDir"] == str(out)
        assert result["root"] == str(out / "RSLogix5000Content")
        assert commands == [
            (
                [
                    str(exe),
                    "explode",
                    "--l5x",
                    str(l5x),
                    "--dir",
                    str(out),
                    "--force",
                    "--pretty-attributes",
                    "--unsafe-skip-dependency-check",
                ],
                999,
            )
        ]

    def test_explode_nonzero_returns_error_details(self, monkeypatch, tmp_path):
        exe = tmp_path / "l5xplode.exe"
        monkeypatch.setattr("studio5000_mcp_server.l5xplode_tools.find_l5xplode", lambda: exe)
        monkeypatch.setattr(
            "studio5000_mcp_server.l5xplode_tools.run_external_tool",
            lambda command, timeout=300: ToolRunResult(command, 7, "out", "boom"),
        )

        from studio5000_mcp_server.l5xplode_tools import explode_l5x

        result = explode_l5x(str(tmp_path / "in.L5X"), str(tmp_path / "out"))

        assert result["error"] == "l5xplode explode failed"
        assert result["returncode"] == 7
        assert result["stderr"] == "boom"


class TestImplodeL5X:
    def test_implode_builds_expected_command(self, monkeypatch, tmp_path):
        exe = tmp_path / "l5xplode.exe"
        exploded = tmp_path / "exploded"
        l5x = tmp_path / "out.L5X"
        commands = []

        monkeypatch.setattr("studio5000_mcp_server.l5xplode_tools.find_l5xplode", lambda: exe)

        def fake_run(command, timeout=300):
            commands.append((command, timeout))
            return ToolRunResult(command, 0, "imploded", "")

        monkeypatch.setattr("studio5000_mcp_server.l5xplode_tools.run_external_tool", fake_run)

        from studio5000_mcp_server.l5xplode_tools import implode_l5x

        result = implode_l5x(str(exploded), str(l5x), force=True, timeout=111)

        assert result["success"] is True
        assert result["l5xPath"] == str(l5x)
        assert commands == [
            (
                [
                    str(exe),
                    "implode",
                    "--dir",
                    str(exploded),
                    "--l5x",
                    str(l5x),
                    "--force",
                ],
                111,
            )
        ]
