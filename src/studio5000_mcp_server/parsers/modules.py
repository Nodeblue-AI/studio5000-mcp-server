"""I/O module parser for L5X projects."""

from __future__ import annotations

from typing import Any

from studio5000_mcp_server.l5x_parser import L5XProject, get_description


def list_modules(project: L5XProject) -> list[dict[str, Any]]:
    """List all I/O modules with catalog number, slot, and description."""
    results = []
    for mod in project.controller.findall("Modules/Module"):
        entry: dict[str, Any] = {
            "name": mod.get("Name", ""),
            "catalogNumber": mod.get("CatalogNumber", ""),
            "parentModule": mod.get("ParentModule", ""),
        }
        desc = get_description(mod)
        if desc:
            entry["description"] = desc
        # Get slot from Ports/Port Address
        port = mod.find("Ports/Port")
        if port is not None:
            entry["slot"] = port.get("Address", "")
        return_inhibited = mod.get("Inhibited")
        if return_inhibited == "true":
            entry["inhibited"] = True
        results.append(entry)
    return results
