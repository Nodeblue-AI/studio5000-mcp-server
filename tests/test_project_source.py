"""Tests for Studio 5000 project source detection/loading."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from studio5000_mcp_server.l5x_parser import load_l5x

FIXTURE = Path(__file__).parent / "fixtures" / "sample.l5x"


@pytest.fixture(autouse=True)
def _clear_cache():
    load_l5x.cache_clear()
    try:
        from studio5000_mcp_server.l5x_parser import load_project_source

        load_project_source.cache_clear()
    except ImportError:
        pass


class TestDetectProjectSource:
    def test_detect_l5x_file(self):
        from studio5000_mcp_server.project_source import ProjectSourceType, detect_project_source

        source_type, path = detect_project_source(str(FIXTURE))

        assert source_type == ProjectSourceType.L5X
        assert path == FIXTURE.resolve()

    def test_detect_exploded_root_directory(self, tmp_path):
        root = tmp_path / "RSLogix5000Content"
        root.mkdir()
        (root / "RSLogix5000Content.xml").write_text("<RSLogix5000Content />")

        from studio5000_mcp_server.project_source import ProjectSourceType, detect_project_source

        source_type, path = detect_project_source(str(root))

        assert source_type == ProjectSourceType.EXPLODED
        assert path == root.resolve()

    def test_detect_exploded_parent_directory(self, tmp_path):
        root = tmp_path / "RSLogix5000Content"
        root.mkdir()
        (root / "RSLogix5000Content.xml").write_text("<RSLogix5000Content />")

        from studio5000_mcp_server.project_source import ProjectSourceType, detect_project_source

        source_type, path = detect_project_source(str(tmp_path))

        assert source_type == ProjectSourceType.EXPLODED
        assert path == root.resolve()

    def test_unsupported_path_raises(self, tmp_path):
        from studio5000_mcp_server.project_source import detect_project_source

        with pytest.raises(FileNotFoundError, match="Not a supported Studio 5000 project source"):
            detect_project_source(str(tmp_path / "missing"))


class TestLoadProjectSource:
    def test_load_l5x_source(self):
        from studio5000_mcp_server.l5x_parser import load_project_source

        proj = load_project_source(str(FIXTURE))

        assert proj.name == "SampleController"

    def test_load_exploded_source_implodes_then_loads(self, monkeypatch, tmp_path):
        root = tmp_path / "RSLogix5000Content"
        root.mkdir()
        (root / "RSLogix5000Content.xml").write_text("<RSLogix5000Content />")
        calls = []

        def fake_implode(exploded_dir, l5x_path, force=False, timeout=300):
            calls.append((exploded_dir, l5x_path, force, timeout))
            shutil.copyfile(FIXTURE, l5x_path)
            return {"success": True}

        monkeypatch.setattr("studio5000_mcp_server.l5x_parser.implode_l5x", fake_implode)

        from studio5000_mcp_server.l5x_parser import load_project_source

        proj = load_project_source(str(root))

        assert proj.name == "SampleController"
        assert len(calls) == 1
        assert calls[0][0] == str(tmp_path.resolve())
        assert calls[0][2] is True

    def test_load_exploded_source_reports_implode_failure(self, monkeypatch, tmp_path):
        root = tmp_path / "RSLogix5000Content"
        root.mkdir()
        (root / "RSLogix5000Content.xml").write_text("<RSLogix5000Content />")

        monkeypatch.setattr(
            "studio5000_mcp_server.l5x_parser.implode_l5x",
            lambda *args, **kwargs: {"error": "l5xplode implode failed", "stderr": "boom"},
        )

        from studio5000_mcp_server.l5x_parser import load_project_source

        with pytest.raises(RuntimeError, match="l5xplode implode failed"):
            load_project_source(str(root))
