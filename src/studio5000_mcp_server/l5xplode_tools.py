"""Wrappers around Rockwell's optional l5xplode CLI."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from studio5000_mcp_server.external_tools import find_l5xplode, run_external_tool

_L5XPLODE_REQUIREMENTS = [
    ".NET 10 runtime or SDK",
    "RockwellAutomation/ra-logix-designer-vcs-custom-tools l5xplode build",
]


def _missing_l5xplode_error() -> dict[str, Any]:
    return {
        "error": "l5xplode executable not found. Set L5XPLODE_EXE or add l5xplode to PATH.",
        "requires": _L5XPLODE_REQUIREMENTS,
    }


def _failure(error: str, result: Any) -> dict[str, Any]:
    return {
        "error": error,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "command": result.command,
    }


def explode_l5x(
    l5x_path: str,
    output_dir: str,
    *,
    force: bool = False,
    pretty_attributes: bool = True,
    unsafe_skip_dependency_check: bool = False,
    timeout: int = 300,
) -> dict[str, Any]:
    """Explode an L5X file into Rockwell's multi-file representation."""
    exe = find_l5xplode()
    if exe is None:
        return _missing_l5xplode_error()

    command = [str(exe), "explode", "--l5x", l5x_path, "--dir", output_dir]
    if force:
        command.append("--force")
    if pretty_attributes:
        command.append("--pretty-attributes")
    if unsafe_skip_dependency_check:
        command.append("--unsafe-skip-dependency-check")

    result = run_external_tool(command, timeout=timeout)
    if result.returncode != 0:
        return _failure("l5xplode explode failed", result)

    root = Path(output_dir) / "RSLogix5000Content"
    return {
        "success": True,
        "outputDir": output_dir,
        "root": str(root),
        "stdout": result.stdout,
        "stderr": result.stderr,
        "command": result.command,
    }


def implode_l5x(
    exploded_dir: str,
    l5x_path: str,
    *,
    force: bool = False,
    timeout: int = 300,
) -> dict[str, Any]:
    """Reconstitute an L5X file from Rockwell's exploded representation."""
    exe = find_l5xplode()
    if exe is None:
        return _missing_l5xplode_error()

    command = [str(exe), "implode", "--dir", exploded_dir, "--l5x", l5x_path]
    if force:
        command.append("--force")

    result = run_external_tool(command, timeout=timeout)
    if result.returncode != 0:
        return _failure("l5xplode implode failed", result)

    return {
        "success": True,
        "explodedDir": exploded_dir,
        "l5xPath": l5x_path,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "command": result.command,
    }
