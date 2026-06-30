"""Studio 5000 project source detection helpers."""

from __future__ import annotations

from enum import Enum
from pathlib import Path


class ProjectSourceType(str, Enum):
    """Supported Studio 5000 project source formats."""

    L5X = "l5x"
    EXPLODED = "exploded"


def detect_project_source(path: str) -> tuple[ProjectSourceType, Path]:
    """Detect whether a path is a monolithic L5X file or an exploded project directory.

    Exploded directories may be provided either as the ``RSLogix5000Content`` root itself
    or as the parent directory containing ``RSLogix5000Content``.
    """
    p = Path(path).expanduser().resolve()

    if p.is_file() and p.suffix.lower() == ".l5x":
        return ProjectSourceType.L5X, p

    if p.is_dir():
        if (p / "RSLogix5000Content.xml").exists():
            return ProjectSourceType.EXPLODED, p

        nested = p / "RSLogix5000Content"
        if nested.is_dir() and (nested / "RSLogix5000Content.xml").exists():
            return ProjectSourceType.EXPLODED, nested.resolve()

    raise FileNotFoundError(f"Not a supported Studio 5000 project source: {path}")
