"""Tag parser for L5X projects — controller-scoped and program-scoped tags."""

from __future__ import annotations

from typing import Any
from xml.etree.ElementTree import Element

from studio5000_mcp_server.l5x_parser import L5XProject


def _parse_tag(tag_el: Element, scope: str) -> dict[str, Any]:
    """Extract tag info from an XML Tag element."""
    entry: dict[str, Any] = {
        "name": tag_el.get("Name", ""),
        "dataType": tag_el.get("DataType", ""),
        "scope": scope,
    }
    desc = tag_el.get("Description", "")
    if desc:
        entry["description"] = desc
    radix = tag_el.get("Radix")
    if radix:
        entry["radix"] = radix
    if tag_el.get("Constant") == "true":
        entry["constant"] = True
    access = tag_el.get("ExternalAccess")
    if access:
        entry["externalAccess"] = access
    return entry


def list_tags(
    project: L5XProject, scope: str = "", data_type: str = ""
) -> list[dict[str, Any]]:
    """List tags, optionally filtered by scope and/or data type.

    Args:
        scope: "controller" for controller-scoped only, a program name for that program's tags,
               or empty for all tags.
        data_type: Filter by data type name (e.g. "BOOL", "Motor_UDT").
    """
    results: list[dict[str, Any]] = []

    if not scope or scope.lower() == "controller":
        for tag in project.controller.findall("Tags/Tag"):
            results.append(_parse_tag(tag, "controller"))

    for prog in project.controller.findall("Programs/Program"):
        prog_name = prog.get("Name", "")
        if scope and scope.lower() != "controller" and scope != prog_name:
            continue
        if scope and scope.lower() == "controller":
            continue
        for tag in prog.findall("Tags/Tag"):
            results.append(_parse_tag(tag, prog_name))

    if data_type:
        results = [t for t in results if t["dataType"] == data_type]

    return results


def get_tag(project: L5XProject, tag_name: str) -> dict[str, Any] | None:
    """Find a specific tag by name across all scopes."""
    for tag in project.controller.findall("Tags/Tag"):
        if tag.get("Name") == tag_name:
            return _parse_tag(tag, "controller")

    for prog in project.controller.findall("Programs/Program"):
        prog_name = prog.get("Name", "")
        for tag in prog.findall("Tags/Tag"):
            if tag.get("Name") == tag_name:
                return _parse_tag(tag, prog_name)

    return None
