"""Wrappers around Rockwell's optional l5xgit CLI for ACD/L5X conversion."""

from __future__ import annotations

from typing import Any

from studio5000_mcp_server.external_tools import find_l5xgit, run_external_tool

_L5XGIT_REQUIREMENTS = [
    "Windows",
    "Studio 5000 Logix Designer",
    "Logix Designer SDK",
    ".NET 10 runtime or SDK",
    "RockwellAutomation/ra-logix-designer-vcs-custom-tools l5xgit build",
]


def _missing_l5xgit_error() -> dict[str, Any]:
    return {
        "error": "l5xgit executable not found. Set L5XGIT_EXE or add l5xgit to PATH.",
        "requires": _L5XGIT_REQUIREMENTS,
    }


def _failure(error: str, result: Any) -> dict[str, Any]:
    return {
        "error": error,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "command": result.command,
    }


def acd_to_l5x(acd_path: str, l5x_path: str, *, timeout: int = 900) -> dict[str, Any]:
    """Convert an ACD file to L5X using l5xgit."""
    exe = find_l5xgit()
    if exe is None:
        return _missing_l5xgit_error()

    command = [str(exe), "acd2l5x", "--acd", acd_path, "--l5x", l5x_path]
    result = run_external_tool(command, timeout=timeout)
    if result.returncode != 0:
        return _failure("l5xgit acd2l5x failed", result)

    return {
        "success": True,
        "acdPath": acd_path,
        "l5xPath": l5x_path,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "command": result.command,
    }


def l5x_to_acd(l5x_path: str, acd_path: str, *, timeout: int = 900) -> dict[str, Any]:
    """Convert an L5X file to ACD using l5xgit."""
    exe = find_l5xgit()
    if exe is None:
        return _missing_l5xgit_error()

    command = [str(exe), "l5x2acd", "--l5x", l5x_path, "--acd", acd_path]
    result = run_external_tool(command, timeout=timeout)
    if result.returncode != 0:
        return _failure("l5xgit l5x2acd failed", result)

    return {
        "success": True,
        "l5xPath": l5x_path,
        "acdPath": acd_path,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "command": result.command,
    }
