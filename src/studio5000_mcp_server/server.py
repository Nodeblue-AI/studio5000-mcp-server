"""Studio 5000 MCP Server — FastMCP server exposing L5X project tools."""

from __future__ import annotations

import json

from fastmcp import FastMCP

from studio5000_mcp_server.l5x_parser import load_project_source
from studio5000_mcp_server.l5xgit_tools import acd_to_l5x as convert_acd_to_l5x
from studio5000_mcp_server.l5xgit_tools import l5x_to_acd as convert_l5x_to_acd
from studio5000_mcp_server.l5xplode_tools import explode_l5x, implode_l5x
from studio5000_mcp_server.parsers import programs, routines, tags, udts, aois, modules, xref


def _error(msg: str) -> str:
    return json.dumps({"error": msg})


mcp = FastMCP(
    "Studio 5000 MCP Server",
    instructions=(
        "This server provides access to Rockwell/Allen-Bradley Studio 5000 L5X project exports and optional l5xplode exploded project folders. "
        "Use load_project to parse an L5X file or exploded RSLogix5000Content directory, then explore tags, UDTs, routines, and programs. "
        "Ladder logic is returned as compact NeutralText (e.g. 'XIC Motor_Start OTE Motor_Run') "
        "with rung comments — not raw XML. Structured Text is returned as-is."
    ),
)


@mcp.tool
def ping() -> str:
    """Health check — verify the server is running."""
    return "pong"


@mcp.tool
def explode_project(
    l5x_path: str,
    output_dir: str,
    force: bool = False,
    pretty_attributes: bool = True,
    unsafe_skip_dependency_check: bool = False,
) -> str:
    """Expand an L5X file into Rockwell's multi-file XML representation.

    Requires RockwellAutomation/ra-logix-designer-vcs-custom-tools `l5xplode`.
    Set L5XPLODE_EXE or add l5xplode to PATH.

    Args:
        l5x_path: Path to the L5X input file.
        output_dir: Directory where the exploded project should be written.
        force: Overwrite existing output files.
        pretty_attributes: Format XML attributes across lines for readability.
        unsafe_skip_dependency_check: Bypass missing dependency export checks.
    """
    result = explode_l5x(
        l5x_path=l5x_path,
        output_dir=output_dir,
        force=force,
        pretty_attributes=pretty_attributes,
        unsafe_skip_dependency_check=unsafe_skip_dependency_check,
    )
    return json.dumps(result, indent=2)


@mcp.tool
def implode_project(exploded_dir: str, l5x_path: str, force: bool = False) -> str:
    """Reconstitute an L5X file from a Rockwell exploded project directory.

    Requires RockwellAutomation/ra-logix-designer-vcs-custom-tools `l5xplode`.
    Set L5XPLODE_EXE or add l5xplode to PATH.

    Args:
        exploded_dir: Path to the RSLogix5000Content directory or exploded root.
        l5x_path: Path to the L5X output file.
        force: Overwrite existing output file.
    """
    result = implode_l5x(exploded_dir=exploded_dir, l5x_path=l5x_path, force=force)
    return json.dumps(result, indent=2)


@mcp.tool
def acd_to_l5x(acd_path: str, l5x_path: str) -> str:
    """Convert an ACD file to L5X using optional Rockwell l5xgit.

    Requires Windows, Studio 5000 Logix Designer, Logix Designer SDK, .NET 10,
    and RockwellAutomation/ra-logix-designer-vcs-custom-tools `l5xgit`.
    Set L5XGIT_EXE or add l5xgit to PATH.

    Args:
        acd_path: Path to the ACD input file.
        l5x_path: Path to the L5X output file.
    """
    result = convert_acd_to_l5x(acd_path=acd_path, l5x_path=l5x_path)
    return json.dumps(result, indent=2)


@mcp.tool
def l5x_to_acd(l5x_path: str, acd_path: str) -> str:
    """Convert an L5X file to ACD using optional Rockwell l5xgit.

    Requires Windows, Studio 5000 Logix Designer, Logix Designer SDK, .NET 10,
    and RockwellAutomation/ra-logix-designer-vcs-custom-tools `l5xgit`.
    Set L5XGIT_EXE or add l5xgit to PATH.

    Args:
        l5x_path: Path to the L5X input file.
        acd_path: Path to the ACD output file.
    """
    result = convert_l5x_to_acd(l5x_path=l5x_path, acd_path=acd_path)
    return json.dumps(result, indent=2)


@mcp.tool
def load_project(l5x_path: str) -> str:
    """Parse an L5X file or exploded project directory and return a project summary.

    Args:
        l5x_path: Path to a .L5X file or exploded RSLogix5000Content directory.
    """
    try:
        proj = load_project_source(l5x_path)
        progs = programs.list_programs(proj)
        tasks = programs.list_tasks(proj)
        udt_names = udts.list_udts(proj)
        aoi_list = aois.list_aois(proj)
        mod_list = modules.list_modules(proj)
        tag_count = len(tags.list_tags(proj))
        return json.dumps({
            "controller": proj.name,
            "processorType": proj.processor_type,
            "description": proj.description,
            "firmware": f"{proj.major_rev}.{proj.minor_rev}",
            "programs": progs,
            "tasks": tasks,
            "udtCount": len(udt_names),
            "udts": udt_names,
            "aoiCount": len(aoi_list),
            "aois": [a["name"] for a in aoi_list],
            "moduleCount": len(mod_list),
            "tagCount": tag_count,
        }, indent=2)
    except FileNotFoundError as e:
        return _error(str(e))
    except Exception as e:
        return _error(f"Failed to load project: {e}")


@mcp.tool
def get_tags(l5x_path: str, scope: str = "", data_type: str = "") -> str:
    """List tags from an L5X project, optionally filtered by scope and data type.

    Args:
        l5x_path: Path to a .L5X file or exploded RSLogix5000Content directory.
        scope: "controller" for controller-scoped, a program name for program-scoped, or empty for all.
        data_type: Filter by data type (e.g. "BOOL", "DINT", "Motor_UDT").
    """
    try:
        proj = load_project_source(l5x_path)
        result = tags.list_tags(proj, scope, data_type)
        return json.dumps(result, indent=2)
    except FileNotFoundError as e:
        return _error(str(e))
    except Exception as e:
        return _error(f"Failed to read tags: {e}")


@mcp.tool
def get_tag(l5x_path: str, tag_name: str) -> str:
    """Get details for a specific tag by name.

    Args:
        l5x_path: Path to a .L5X file or exploded RSLogix5000Content directory.
        tag_name: Tag name to look up (searches all scopes).
    """
    try:
        proj = load_project_source(l5x_path)
        result = tags.get_tag(proj, tag_name)
        if result is None:
            return _error(f"Tag '{tag_name}' not found")
        return json.dumps(result, indent=2)
    except FileNotFoundError as e:
        return _error(str(e))
    except Exception as e:
        return _error(f"Failed to read tag: {e}")


@mcp.tool
def get_udts(l5x_path: str) -> str:
    """List all User Defined Type names in an L5X project.

    Args:
        l5x_path: Path to a .L5X file or exploded RSLogix5000Content directory.
    """
    try:
        proj = load_project_source(l5x_path)
        return json.dumps(udts.list_udts(proj), indent=2)
    except FileNotFoundError as e:
        return _error(str(e))
    except Exception as e:
        return _error(f"Failed to list UDTs: {e}")


@mcp.tool
def get_udt(l5x_path: str, udt_name: str = "") -> str:
    """Get UDT definition(s) with member details.

    Args:
        l5x_path: Path to a .L5X file or exploded RSLogix5000Content directory.
        udt_name: UDT name. If empty, returns all UDTs.
    """
    try:
        proj = load_project_source(l5x_path)
        result = udts.get_udt(proj, udt_name)
        return json.dumps(result, indent=2)
    except FileNotFoundError as e:
        return _error(str(e))
    except Exception as e:
        return _error(f"Failed to read UDT: {e}")


@mcp.tool
def get_routines(l5x_path: str, program: str = "") -> str:
    """List routines in an L5X project with type and size info.

    Args:
        l5x_path: Path to a .L5X file or exploded RSLogix5000Content directory.
        program: Filter by program name. Empty returns routines from all programs.
    """
    try:
        proj = load_project_source(l5x_path)
        result = routines.list_routines(proj, program)
        return json.dumps(result, indent=2)
    except FileNotFoundError as e:
        return _error(str(e))
    except Exception as e:
        return _error(f"Failed to list routines: {e}")


@mcp.tool
def get_routine(l5x_path: str, program: str, routine_name: str) -> str:
    """Get routine logic — NeutralText for ladder, raw code for Structured Text.

    Ladder rungs are returned as compact NeutralText with rung comments, not raw XML.
    A single rung like 'XIC Motor_Start XIO Motor_Fault OTE Motor_Run' replaces
    hundreds of lines of verbose XML.

    Args:
        l5x_path: Path to a .L5X file or exploded RSLogix5000Content directory.
        program: Program name containing the routine.
        routine_name: Routine name.
    """
    try:
        proj = load_project_source(l5x_path)
        result = routines.get_routine(proj, program, routine_name)
        if result is None:
            return _error(f"Routine '{routine_name}' not found in program '{program}'")
        return json.dumps(result, indent=2)
    except FileNotFoundError as e:
        return _error(str(e))
    except Exception as e:
        return _error(f"Failed to read routine: {e}")


@mcp.tool
def get_aois(l5x_path: str) -> str:
    """List all Add-On Instructions in an L5X project.

    Args:
        l5x_path: Path to a .L5X file or exploded RSLogix5000Content directory.
    """
    try:
        proj = load_project_source(l5x_path)
        return json.dumps(aois.list_aois(proj), indent=2)
    except FileNotFoundError as e:
        return _error(str(e))
    except Exception as e:
        return _error(f"Failed to list AOIs: {e}")


@mcp.tool
def get_aoi(l5x_path: str, aoi_name: str) -> str:
    """Get an Add-On Instruction definition with parameters and internal logic.

    Args:
        l5x_path: Path to a .L5X file or exploded RSLogix5000Content directory.
        aoi_name: AOI name.
    """
    try:
        proj = load_project_source(l5x_path)
        result = aois.get_aoi(proj, aoi_name)
        if result is None:
            return _error(f"AOI '{aoi_name}' not found")
        return json.dumps(result, indent=2)
    except FileNotFoundError as e:
        return _error(str(e))
    except Exception as e:
        return _error(f"Failed to read AOI: {e}")


@mcp.tool
def list_modules(l5x_path: str) -> str:
    """List all I/O modules in an L5X project with catalog numbers and slot assignments.

    Args:
        l5x_path: Path to a .L5X file or exploded RSLogix5000Content directory.
    """
    try:
        proj = load_project_source(l5x_path)
        return json.dumps(modules.list_modules(proj), indent=2)
    except FileNotFoundError as e:
        return _error(str(e))
    except Exception as e:
        return _error(f"Failed to list modules: {e}")


@mcp.tool
def search_logic(l5x_path: str, pattern: str) -> str:
    """Search for a tag, AOI, or pattern across all routines in an L5X project.

    Returns every routine/rung/line that references the matching symbol(s).
    Supports regex patterns. Use this to answer "Where is this tag used?" or
    "Which routines reference this AOI?"

    Args:
        l5x_path: Path to a .L5X file or exploded RSLogix5000Content directory.
        pattern: Tag name, AOI name, or regex pattern to search for.
    """
    try:
        proj = load_project_source(l5x_path)
        result = xref.search_xref(proj, pattern)
        return json.dumps(result, indent=2)
    except FileNotFoundError as e:
        return _error(str(e))
    except Exception as e:
        return _error(f"Failed to search logic: {e}")
