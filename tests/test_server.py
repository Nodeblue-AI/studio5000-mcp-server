"""Tests for studio5000-mcp-server v0.1.0."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from studio5000_mcp_server.l5x_parser import L5XProject, load_l5x
from studio5000_mcp_server.parsers import programs, routines, tags, udts

FIXTURE = Path(__file__).parent / "fixtures" / "sample.l5x"


@pytest.fixture(autouse=True)
def _clear_cache():
    load_l5x.cache_clear()


# ── Core Parser ─────────────────────────────────────────────


class TestL5XParser:
    def test_load(self):
        proj = load_l5x(str(FIXTURE))
        assert isinstance(proj, L5XProject)
        assert proj.name == "SampleController"

    def test_processor_type(self):
        proj = load_l5x(str(FIXTURE))
        assert proj.processor_type == "1769-L33ER"

    def test_description(self):
        proj = load_l5x(str(FIXTURE))
        assert "testing" in proj.description.lower()

    def test_firmware(self):
        proj = load_l5x(str(FIXTURE))
        assert proj.major_rev == "33"
        assert proj.minor_rev == "1"

    def test_cache(self):
        a = load_l5x(str(FIXTURE))
        b = load_l5x(str(FIXTURE))
        assert a is b

    def test_not_found(self):
        with pytest.raises(FileNotFoundError):
            load_l5x("/nonexistent/file.l5x")

    def test_not_a_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_l5x(str(tmp_path))


# ── Programs & Tasks ────────────────────────────────────────


class TestPrograms:
    @pytest.fixture
    def proj(self):
        return load_l5x(str(FIXTURE))

    def test_list_programs(self, proj):
        result = programs.list_programs(proj)
        names = [p["name"] for p in result]
        assert "MainProgram" in names
        assert "MotorProgram" in names
        assert len(result) == 2

    def test_main_routine(self, proj):
        result = programs.list_programs(proj)
        main = next(p for p in result if p["name"] == "MainProgram")
        assert main["mainRoutine"] == "MainRoutine"

    def test_list_tasks(self, proj):
        result = programs.list_tasks(proj)
        names = [t["name"] for t in result]
        assert "MainTask" in names
        assert "EventTask" in names

    def test_task_type(self, proj):
        result = programs.list_tasks(proj)
        main = next(t for t in result if t["name"] == "MainTask")
        assert main["type"] == "CONTINUOUS"
        assert "MainProgram" in main["programs"]

    def test_event_task(self, proj):
        result = programs.list_tasks(proj)
        event = next(t for t in result if t["name"] == "EventTask")
        assert event["type"] == "EVENT"
        assert event["programs"] == []


# ── Tags ────────────────────────────────────────────────────


class TestTags:
    @pytest.fixture
    def proj(self):
        return load_l5x(str(FIXTURE))

    def test_all_tags(self, proj):
        result = tags.list_tags(proj)
        names = [t["name"] for t in result]
        assert "SystemClock" in names
        assert "Motor_1" in names
        assert "StartPB" in names  # program-scoped

    def test_controller_scope(self, proj):
        result = tags.list_tags(proj, scope="controller")
        names = [t["name"] for t in result]
        assert "SystemClock" in names
        assert "Motor_1" in names
        assert "StartPB" not in names  # program-scoped

    def test_program_scope(self, proj):
        result = tags.list_tags(proj, scope="MainProgram")
        names = [t["name"] for t in result]
        assert "StartPB" in names
        assert "StopPB" in names
        assert "SystemClock" not in names

    def test_filter_data_type(self, proj):
        result = tags.list_tags(proj, data_type="BOOL")
        assert all(t["dataType"] == "BOOL" for t in result)
        names = [t["name"] for t in result]
        assert "EmergencyStop" in names

    def test_filter_udt_type(self, proj):
        result = tags.list_tags(proj, data_type="Motor_UDT")
        names = [t["name"] for t in result]
        assert "Motor_1" in names
        assert "Motor_2" in names
        assert len(result) == 2

    def test_get_tag(self, proj):
        result = tags.get_tag(proj, "Motor_1")
        assert result is not None
        assert result["dataType"] == "Motor_UDT"
        assert result["scope"] == "controller"
        assert "description" in result

    def test_get_program_tag(self, proj):
        result = tags.get_tag(proj, "StartPB")
        assert result is not None
        assert result["scope"] == "MainProgram"

    def test_get_tag_not_found(self, proj):
        result = tags.get_tag(proj, "NonexistentTag")
        assert result is None

    def test_combined_filter(self, proj):
        result = tags.list_tags(proj, scope="MotorProgram", data_type="REAL")
        assert len(result) == 1
        assert result[0]["name"] == "VFD_SpeedRef"


# ── UDTs ────────────────────────────────────────────────────


class TestUDTs:
    @pytest.fixture
    def proj(self):
        return load_l5x(str(FIXTURE))

    def test_list_udts(self, proj):
        result = udts.list_udts(proj)
        assert "Motor_UDT" in result
        assert "Valve_UDT" in result
        assert len(result) == 2

    def test_get_all(self, proj):
        result = udts.get_udt(proj)
        assert len(result) == 2

    def test_get_motor_udt(self, proj):
        result = udts.get_udt(proj, "Motor_UDT")
        assert len(result) == 1
        motor = result[0]
        assert motor["name"] == "Motor_UDT"
        member_names = [m["name"] for m in motor["members"]]
        assert "Running" in member_names
        assert "Faulted" in member_names
        assert "Speed" in member_names
        assert "RunCommand" in member_names
        assert "RunTime" in member_names

    def test_member_types(self, proj):
        result = udts.get_udt(proj, "Motor_UDT")
        members = {m["name"]: m for m in result[0]["members"]}
        assert members["Running"]["dataType"] == "BOOL"
        assert members["Speed"]["dataType"] == "REAL"
        assert members["RunTime"]["dataType"] == "DINT"

    def test_member_descriptions(self, proj):
        result = udts.get_udt(proj, "Motor_UDT")
        members = {m["name"]: m for m in result[0]["members"]}
        assert "RPM" in members["Speed"]["description"]

    def test_nonexistent(self, proj):
        result = udts.get_udt(proj, "Nonexistent_UDT")
        assert result == []

    def test_valve_udt(self, proj):
        result = udts.get_udt(proj, "Valve_UDT")
        assert len(result) == 1
        member_names = [m["name"] for m in result[0]["members"]]
        assert "Open" in member_names
        assert "Position" in member_names


# ── Routines ────────────────────────────────────────────────


class TestRoutines:
    @pytest.fixture
    def proj(self):
        return load_l5x(str(FIXTURE))

    def test_list_all(self, proj):
        result = routines.list_routines(proj)
        names = [(r["program"], r["name"]) for r in result]
        assert ("MainProgram", "MainRoutine") in names
        assert ("MainProgram", "FaultHandler") in names
        assert ("MotorProgram", "MotorControl") in names
        assert len(result) == 3

    def test_list_by_program(self, proj):
        result = routines.list_routines(proj, "MainProgram")
        names = [r["name"] for r in result]
        assert "MainRoutine" in names
        assert "FaultHandler" in names
        assert len(result) == 2

    def test_routine_type(self, proj):
        result = routines.list_routines(proj)
        types = {r["name"]: r["type"] for r in result}
        assert types["MainRoutine"] == "RLL"
        assert types["FaultHandler"] == "ST"
        assert types["MotorControl"] == "RLL"

    def test_rung_count(self, proj):
        result = routines.list_routines(proj)
        main = next(r for r in result if r["name"] == "MainRoutine")
        assert main["rungCount"] == 7

    def test_line_count(self, proj):
        result = routines.list_routines(proj)
        fault = next(r for r in result if r["name"] == "FaultHandler")
        assert fault["lineCount"] == 15

    def test_get_ladder_routine(self, proj):
        result = routines.get_routine(proj, "MainProgram", "MainRoutine")
        assert result is not None
        assert result["type"] == "RLL"
        assert len(result["rungs"]) == 7

    def test_ladder_neutral_text(self, proj):
        result = routines.get_routine(proj, "MainProgram", "MainRoutine")
        rung0 = result["rungs"][0]
        assert rung0["number"] == 0
        assert "XIC(StartPB)" in rung0["text"]
        assert "OTE(SystemRunning)" in rung0["text"]

    def test_ladder_comments(self, proj):
        result = routines.get_routine(proj, "MainProgram", "MainRoutine")
        rung0 = result["rungs"][0]
        assert "start" in rung0["comment"].lower()

    def test_aoi_call_in_rung(self, proj):
        result = routines.get_routine(proj, "MainProgram", "MainRoutine")
        rung1 = result["rungs"][1]
        assert "Motor_Control" in rung1["text"]

    def test_get_st_routine(self, proj):
        result = routines.get_routine(proj, "MainProgram", "FaultHandler")
        assert result is not None
        assert result["type"] == "ST"
        assert "IF Motor_1.Faulted THEN" in result["code"]
        assert "FaultCount := FaultCount + 1" in result["code"]

    def test_get_motor_control(self, proj):
        result = routines.get_routine(proj, "MotorProgram", "MotorControl")
        assert result is not None
        assert len(result["rungs"]) == 4
        assert "VFD_Running" in result["rungs"][0]["text"]

    def test_not_found(self, proj):
        result = routines.get_routine(proj, "MainProgram", "Nonexistent")
        assert result is None


# ── Server Error Handling ───────────────────────────────────


class TestErrorHandling:
    def test_load_bad_path(self):
        from studio5000_mcp_server.server import load_project
        result = json.loads(load_project("/nonexistent/file.l5x"))
        assert "error" in result

    def test_get_tags_bad_path(self):
        from studio5000_mcp_server.server import get_tags
        result = json.loads(get_tags("/nonexistent/file.l5x"))
        assert "error" in result

    def test_get_tag_not_found(self):
        from studio5000_mcp_server.server import get_tag
        result = json.loads(get_tag(str(FIXTURE), "NonexistentTag"))
        assert "error" in result

    def test_get_routine_not_found(self):
        from studio5000_mcp_server.server import get_routine
        result = json.loads(get_routine(str(FIXTURE), "MainProgram", "Nonexistent"))
        assert "error" in result


# ── Server Integration ──────────────────────────────────────


class TestServerIntegration:
    def test_load_project(self):
        from studio5000_mcp_server.server import load_project
        result = json.loads(load_project(str(FIXTURE)))
        assert result["controller"] == "SampleController"
        assert result["processorType"] == "1769-L33ER"
        assert result["tagCount"] > 0
        assert result["udtCount"] == 2
        assert len(result["programs"]) == 2

    def test_get_tags_tool(self):
        from studio5000_mcp_server.server import get_tags
        result = json.loads(get_tags(str(FIXTURE), scope="controller"))
        names = [t["name"] for t in result]
        assert "Motor_1" in names

    def test_get_udt_tool(self):
        from studio5000_mcp_server.server import get_udt
        result = json.loads(get_udt(str(FIXTURE), "Motor_UDT"))
        assert len(result) == 1
        assert result[0]["name"] == "Motor_UDT"

    def test_get_routine_tool(self):
        from studio5000_mcp_server.server import get_routine
        result = json.loads(get_routine(str(FIXTURE), "MainProgram", "MainRoutine"))
        assert result["type"] == "RLL"
        assert len(result["rungs"]) == 7
