"""Core L5X XML parser — load and cache Rockwell L5X project files."""

from __future__ import annotations

import hashlib
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

from studio5000_mcp_server.l5xplode_tools import implode_l5x
from studio5000_mcp_server.project_source import ProjectSourceType, detect_project_source


@dataclass
class L5XProject:
    """Parsed L5X project with controller metadata and XML tree."""

    root: ET.Element
    controller: ET.Element
    name: str
    processor_type: str
    description: str
    major_rev: str
    minor_rev: str

    @property
    def target_name(self) -> str:
        return self.root.get("TargetName", self.name)


def get_description(el: ET.Element) -> str:
    """Get description from an element — handles both attribute and child element forms.

    Real L5X exports use <Description><![CDATA[...]]></Description> child elements.
    Some simplified exports use Description="..." attributes.
    """
    desc = el.get("Description", "")
    if not desc:
        desc_el = el.find("Description")
        if desc_el is not None and desc_el.text:
            desc = desc_el.text.strip()
    return desc


@lru_cache(maxsize=16)
def load_l5x(path: str) -> L5XProject:
    """Parse an L5X file and return a cached L5XProject.

    Results are cached — repeated calls with the same resolved path return the same instance.
    """
    p = Path(path).resolve()
    if not p.exists():
        raise FileNotFoundError(f"L5X file not found: {path}")
    if not p.is_file():
        raise FileNotFoundError(f"Path is not a file: {path}")

    tree = ET.parse(str(p))
    root = tree.getroot()

    if root.tag != "RSLogix5000Content":
        raise ValueError(f"Not an L5X file (root element is <{root.tag}>, expected <RSLogix5000Content>): {path}")

    ctrl = root.find("Controller")
    if ctrl is None:
        raise ValueError(f"No <Controller> element found in {path}")

    # Description can be an attribute or a child element
    desc = get_description(ctrl)

    return L5XProject(
        root=root,
        controller=ctrl,
        name=ctrl.get("Name", ""),
        processor_type=ctrl.get("ProcessorType", ""),
        description=desc,
        major_rev=ctrl.get("MajorRev", ""),
        minor_rev=ctrl.get("MinorRev", ""),
    )


def _exploded_tree_signature(root: Path) -> str:
    """Build a cache signature for an exploded project tree."""
    newest_mtime = 0
    file_count = 0
    for child in root.rglob("*"):
        if child.is_file():
            file_count += 1
            newest_mtime = max(newest_mtime, child.stat().st_mtime_ns)
    payload = f"{root}|{file_count}|{newest_mtime}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _imploded_cache_path(root: Path) -> Path:
    cache_dir = Path(tempfile.gettempdir()) / "studio5000_mcp_server" / "imploded"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / f"{root.name}-{_exploded_tree_signature(root)}.L5X"


def _l5xplode_project_dir(root: Path) -> Path:
    """Return the directory shape expected by `l5xplode implode`.

    The MCP API accepts either the RSLogix5000Content folder itself or its parent,
    but l5xplode's --dir option expects the parent directory containing
    RSLogix5000Content.
    """
    if root.name == "RSLogix5000Content" and (root / "RSLogix5000Content.xml").exists():
        return root.parent
    return root


@lru_cache(maxsize=16)
def load_project_source(path: str) -> L5XProject:
    """Load a Studio 5000 project source from a .L5X file or exploded directory.

    Exploded project directories are normalized by invoking l5xplode implode into a
    temporary cached .L5X file, then parsed through the existing L5X parser.
    """
    source_type, source_path = detect_project_source(path)

    if source_type == ProjectSourceType.L5X:
        return load_l5x(str(source_path))

    cache_path = _imploded_cache_path(source_path)
    if not cache_path.exists():
        result = implode_l5x(str(_l5xplode_project_dir(source_path)), str(cache_path), force=True)
        if not result.get("success"):
            detail = result.get("stderr") or result.get("error") or result
            raise RuntimeError(f"l5xplode implode failed: {detail}")

    return load_l5x(str(cache_path))
