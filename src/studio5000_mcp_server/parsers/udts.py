"""UDT (User Defined Type) parser for L5X projects."""

from __future__ import annotations

from typing import Any

from studio5000_mcp_server.l5x_parser import L5XProject


def list_udts(project: L5XProject) -> list[str]:
    """List all user-defined data type names."""
    return [
        dt.get("Name", "")
        for dt in project.controller.findall("DataTypes/DataType")
        if dt.get("Family") == "NoFamily"
    ]


def get_udt(project: L5XProject, name: str = "") -> list[dict[str, Any]]:
    """Get UDT definition(s) with members. If name is empty, returns all."""
    results = []
    for dt in project.controller.findall("DataTypes/DataType"):
        if dt.get("Family") != "NoFamily":
            continue
        dt_name = dt.get("Name", "")
        if name and dt_name != name:
            continue
        members = []
        for m in dt.findall("Members/Member"):
            if m.get("Hidden") == "true":
                continue
            member: dict[str, Any] = {
                "name": m.get("Name", ""),
                "dataType": m.get("DataType", ""),
            }
            dim = m.get("Dimension", "0")
            if dim != "0":
                member["dimension"] = int(dim)
            desc = m.get("Description", "")
            if desc:
                member["description"] = desc
            radix = m.get("Radix")
            if radix:
                member["radix"] = radix
            members.append(member)
        entry: dict[str, Any] = {
            "name": dt_name,
            "description": dt.get("Description", ""),
            "members": members,
        }
        results.append(entry)
    return results
