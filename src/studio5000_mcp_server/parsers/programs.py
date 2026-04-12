"""Program and task parser for L5X projects."""

from __future__ import annotations

from typing import Any

from studio5000_mcp_server.l5x_parser import L5XProject, get_description


def list_programs(project: L5XProject) -> list[dict[str, Any]]:
    """List all programs with their main routine and description."""
    results = []
    for prog in project.controller.findall("Programs/Program"):
        results.append({
            "name": prog.get("Name", ""),
            "mainRoutine": prog.get("MainRoutineName", ""),
            "description": get_description(prog),
        })
    return results


def list_tasks(project: L5XProject) -> list[dict[str, Any]]:
    """List all tasks with scheduling info."""
    results = []
    for task in project.controller.findall("Tasks/Task"):
        programs = [sp.get("Name", "") for sp in task.findall("ScheduledPrograms/ScheduledProgram")]
        results.append({
            "name": task.get("Name", ""),
            "type": task.get("Type", ""),
            "rate": task.get("Rate", ""),
            "priority": task.get("Priority", ""),
            "description": get_description(task),
            "programs": programs,
        })
    return results
