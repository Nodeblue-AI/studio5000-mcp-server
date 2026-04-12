"""Routine parser for L5X projects — ladder NeutralText + ST code extraction."""

from __future__ import annotations

from typing import Any
from xml.etree.ElementTree import Element

from studio5000_mcp_server.l5x_parser import L5XProject, get_description


def _find_routines(project: L5XProject, program: str = "") -> list[tuple[str, Element]]:
    """Find routine elements, optionally filtered by program name.

    Returns list of (program_name, routine_element) tuples.
    """
    results = []
    for prog in project.controller.findall("Programs/Program"):
        prog_name = prog.get("Name", "")
        if program and prog_name != program:
            continue
        for routine in prog.findall("Routines/Routine"):
            results.append((prog_name, routine))
    return results


def list_routines(
    project: L5XProject, program: str = ""
) -> list[dict[str, Any]]:
    """List routines with type and rung count."""
    results = []
    for prog_name, routine in _find_routines(project, program):
        rtype = routine.get("Type", "")
        rung_count = len(routine.findall("RLLContent/Rung")) if rtype == "RLL" else 0
        line_count = len(routine.findall("STContent/Line")) if rtype == "ST" else 0
        entry: dict[str, Any] = {
            "program": prog_name,
            "name": routine.get("Name", ""),
            "type": rtype,
            "description": get_description(routine),
        }
        if rtype == "RLL":
            entry["rungCount"] = rung_count
        elif rtype == "ST":
            entry["lineCount"] = line_count
        results.append(entry)
    return results


def get_routine(
    project: L5XProject, program: str, routine_name: str
) -> dict[str, Any] | None:
    """Get routine logic — NeutralText for ladder, raw code for ST."""
    for prog_name, routine in _find_routines(project, program):
        if routine.get("Name") != routine_name:
            continue
        rtype = routine.get("Type", "")
        result: dict[str, Any] = {
            "program": prog_name,
            "name": routine_name,
            "type": rtype,
            "description": get_description(routine),
        }
        if rtype == "RLL":
            result["rungs"] = _parse_rll(routine)
        elif rtype == "ST":
            result["code"] = _parse_st(routine)
        else:
            result["note"] = f"{rtype} detailed parsing not yet supported"
        return result
    return None


def _parse_rll(routine: Element) -> list[dict[str, Any]]:
    """Extract NeutralText + comments from ladder rungs."""
    rungs = []
    for rung in routine.findall("RLLContent/Rung"):
        entry: dict[str, Any] = {"number": int(rung.get("Number", "0"))}
        comment = rung.get("Comment", "")
        if comment:
            entry["comment"] = comment
        text_el = rung.find("Text")
        entry["text"] = text_el.text.strip() if text_el is not None and text_el.text else ""
        rungs.append(entry)
    return rungs


def _parse_st(routine: Element) -> str:
    """Extract Structured Text code from ST routine."""
    lines = []
    for line in routine.findall("STContent/Line"):
        lines.append(line.text if line.text else "")
    return "\n".join(lines)
