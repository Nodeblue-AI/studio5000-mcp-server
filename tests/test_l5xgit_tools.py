"""Tests for l5xgit wrapper helpers."""

from __future__ import annotations

from studio5000_mcp_server.external_tools import ToolRunResult


class TestAcdToL5x:
    def test_missing_l5xgit_returns_prerequisite_error(self, monkeypatch, tmp_path):
        monkeypatch.setattr("studio5000_mcp_server.l5xgit_tools.find_l5xgit", lambda: None)

        from studio5000_mcp_server.l5xgit_tools import acd_to_l5x

        result = acd_to_l5x(str(tmp_path / "in.ACD"), str(tmp_path / "out.L5X"))

        assert "error" in result
        assert "L5XGIT_EXE" in result["error"]
        assert "Studio 5000 Logix Designer" in result["requires"]

    def test_acd_to_l5x_builds_expected_command(self, monkeypatch, tmp_path):
        exe = tmp_path / "l5xgit.exe"
        acd = tmp_path / "in.ACD"
        l5x = tmp_path / "out.L5X"
        commands = []
        monkeypatch.setattr("studio5000_mcp_server.l5xgit_tools.find_l5xgit", lambda: exe)

        def fake_run(command, timeout=900):
            commands.append((command, timeout))
            return ToolRunResult(command, 0, "converted", "")

        monkeypatch.setattr("studio5000_mcp_server.l5xgit_tools.run_external_tool", fake_run)

        from studio5000_mcp_server.l5xgit_tools import acd_to_l5x

        result = acd_to_l5x(str(acd), str(l5x), timeout=123)

        assert result["success"] is True
        assert result["l5xPath"] == str(l5x)
        assert commands == [([str(exe), "acd2l5x", "--acd", str(acd), "--l5x", str(l5x)], 123)]


class TestL5xToAcd:
    def test_l5x_to_acd_builds_expected_command(self, monkeypatch, tmp_path):
        exe = tmp_path / "l5xgit.exe"
        l5x = tmp_path / "in.L5X"
        acd = tmp_path / "out.ACD"
        commands = []
        monkeypatch.setattr("studio5000_mcp_server.l5xgit_tools.find_l5xgit", lambda: exe)

        def fake_run(command, timeout=900):
            commands.append((command, timeout))
            return ToolRunResult(command, 0, "converted", "")

        monkeypatch.setattr("studio5000_mcp_server.l5xgit_tools.run_external_tool", fake_run)

        from studio5000_mcp_server.l5xgit_tools import l5x_to_acd

        result = l5x_to_acd(str(l5x), str(acd), timeout=456)

        assert result["success"] is True
        assert result["acdPath"] == str(acd)
        assert commands == [([str(exe), "l5x2acd", "--l5x", str(l5x), "--acd", str(acd)], 456)]
