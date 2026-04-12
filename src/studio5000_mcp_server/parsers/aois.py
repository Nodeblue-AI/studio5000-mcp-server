"""Add-On Instruction parser for L5X projects."""

from __future__ import annotations

from typing import Any

from studio5000_mcp_server.l5x_parser import L5XProject
from studio5000_mcp_server.parsers.routines import get_routine as _get_routine_raw, _find_routines, _parse_rll, _parse_st


def list_aois(project: L5XProject) -> list[dict[str, Any]]:
    """List all Add-On Instructions with name, description, and revision."""
    results = []
    for aoi in project.controller.findall("AddOnInstructionDefinitions/AddOnInstruction"):
        results.append({
            "name": aoi.get("Name", ""),
            "description": aoi.get("Description", ""),
            "revision": aoi.get("Revision", ""),
        })
    return results


def get_aoi(project: L5XProject, name: str) -> dict[str, Any] | None:
    """Get AOI definition with parameters and internal logic."""
    for aoi in project.controller.findall("AddOnInstructionDefinitions/AddOnInstruction"):
        if aoi.get("Name") != name:
            continue

        params = []
        for p in aoi.findall("Parameters/Parameter"):
            entry: dict[str, Any] = {
                "name": p.get("Name", ""),
                "dataType": p.get("DataType", ""),
                "usage": p.get("Usage", ""),
            }
            desc = p.get("Description", "")
            if desc:
                entry["description"] = desc
            if p.get("Required") == "true":
                entry["required"] = True
            if p.get("Visible") == "false":
                entry["visible"] = False
            params.append(entry)

        local_tags = []
        for lt in aoi.findall("LocalTags/LocalTag"):
            lt_entry: dict[str, Any] = {
                "name": lt.get("Name", ""),
                "dataType": lt.get("DataType", ""),
            }
            desc = lt.get("Description", "")
            if desc:
                lt_entry["description"] = desc
            local_tags.append(lt_entry)

        aoi_routines = []
        for routine in aoi.findall("Routines/Routine"):
            rtype = routine.get("Type", "")
            r: dict[str, Any] = {"name": routine.get("Name", ""), "type": rtype}
            if rtype == "RLL":
                r["rungs"] = _parse_rll(routine)
            elif rtype == "ST":
                r["code"] = _parse_st(routine)
            aoi_routines.append(r)

        return {
            "name": aoi.get("Name", ""),
            "description": aoi.get("Description", ""),
            "revision": aoi.get("Revision", ""),
            "vendor": aoi.get("Vendor", ""),
            "parameters": params,
            "localTags": local_tags,
            "routines": aoi_routines,
        }
    return None
