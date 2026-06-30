"""Optional external Rockwell CLI tool discovery and execution helpers."""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ToolRunResult:
    """Result from running an optional external executable."""

    command: list[str]
    returncode: int
    stdout: str
    stderr: str


def _find_tool(env_var: str, names: tuple[str, ...]) -> Path | None:
    """Find an optional executable from an explicit env var or PATH."""
    configured = os.getenv(env_var)
    if configured:
        candidate = Path(configured).expanduser()
        if candidate.exists():
            return candidate.resolve()

    for name in names:
        found = shutil.which(name)
        if found:
            return Path(found).resolve()

    return None


def find_l5xplode() -> Path | None:
    """Find Rockwell's l5xplode executable, if configured/available."""
    return _find_tool("L5XPLODE_EXE", ("l5xplode", "l5xplode.exe"))


def find_l5xgit() -> Path | None:
    """Find Rockwell's l5xgit executable, if configured/available."""
    return _find_tool("L5XGIT_EXE", ("l5xgit", "l5xgit.exe"))


def run_external_tool(command: list[str], timeout: int = 300) -> ToolRunResult:
    """Run an external command and capture its process result without raising on nonzero exit."""
    proc = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    return ToolRunResult(
        command=command,
        returncode=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
    )
