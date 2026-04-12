"""Core L5X XML parser — load and cache Rockwell L5X project files."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any


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
