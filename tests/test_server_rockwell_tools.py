"""Tests for server-level Rockwell CLI MCP tools."""

from __future__ import annotations

import json


class TestProjectSourceServerIntegration:
    def test_existing_tools_use_project_source_loader(self, monkeypatch):
        from studio5000_mcp_server import server
        from studio5000_mcp_server.l5x_parser import load_l5x

        calls = []

        def fake_load_project_source(path):
            calls.append(path)
            return load_l5x("tests/fixtures/sample.l5x")

        monkeypatch.setattr(server, "load_project_source", fake_load_project_source)

        result = json.loads(server.load_project("exploded-directory"))

        assert result["controller"] == "SampleController"
        assert calls == ["exploded-directory"]


class TestL5xplodeMcpTools:
    def test_explode_project_returns_wrapper_result(self, monkeypatch):
        from studio5000_mcp_server import server

        expected = {"success": True, "root": "out/RSLogix5000Content"}
        calls = []

        def fake_explode_l5x(**kwargs):
            calls.append(kwargs)
            return expected

        monkeypatch.setattr(server, "explode_l5x", fake_explode_l5x)

        result = json.loads(
            server.explode_project(
                "in.L5X",
                "out",
                force=True,
                pretty_attributes=False,
                unsafe_skip_dependency_check=True,
            )
        )

        assert result == expected
        assert calls == [
            {
                "l5x_path": "in.L5X",
                "output_dir": "out",
                "force": True,
                "pretty_attributes": False,
                "unsafe_skip_dependency_check": True,
            }
        ]

    def test_implode_project_returns_wrapper_result(self, monkeypatch):
        from studio5000_mcp_server import server

        expected = {"success": True, "l5xPath": "out.L5X"}
        monkeypatch.setattr(server, "implode_l5x", lambda **kwargs: expected)

        result = json.loads(server.implode_project("exploded", "out.L5X", force=True))

        assert result == expected


class TestL5xgitMcpTools:
    def test_acd_to_l5x_project_returns_wrapper_result(self, monkeypatch):
        from studio5000_mcp_server import server

        expected = {"success": True, "l5xPath": "out.L5X"}
        monkeypatch.setattr(server, "convert_acd_to_l5x", lambda **kwargs: expected)

        result = json.loads(server.acd_to_l5x("in.ACD", "out.L5X"))

        assert result == expected

    def test_l5x_to_acd_project_returns_wrapper_result(self, monkeypatch):
        from studio5000_mcp_server import server

        expected = {"success": True, "acdPath": "out.ACD"}
        monkeypatch.setattr(server, "convert_l5x_to_acd", lambda **kwargs: expected)

        result = json.loads(server.l5x_to_acd("in.L5X", "out.ACD"))

        assert result == expected
