# Changelog

## [0.4.0] - 2026-04-12

### Added
- **Cross-platform intelligence** — new [bridge-mcp-server](https://github.com/nodeblue-ai/bridge-mcp-server) package correlates Ignition OPC tags with Studio 5000 L5X PLC logic end-to-end. See the bridge package for `correlate_projects`, `trace_tag`, and `find_unmapped_tags` tools.

## [0.3.1] - 2026-04-12

### Fixed
- **Description parsing** — all parsers now handle `<Description>` as both XML attribute and child element (real L5X exports use child elements with CDATA). Added `get_description()` helper used across all parsers.
- **Cross-reference cache** — moved from `setattr` on dataclass instance to module-level dict keyed by project identity. Cleaner and avoids mutating frozen-ish dataclass.
- **Input validation** — `load_l5x()` now validates root element is `<RSLogix5000Content>` and raises clear `ValueError` for non-L5X XML files and missing `<Controller>` elements.
- **Unused imports** — removed dead imports in `aois.py` (`get_routine`, `_find_routines`).
- **`py.typed` marker** — added for downstream type checking support.
- 3 new tests: invalid XML, wrong root element, missing Controller (82 total).

## [0.3.0] - 2026-04-12

### Added
- **`search_logic(l5x_path, pattern)`** — cross-reference engine. Search for any tag, AOI, or regex pattern across all routines and AOIs. Returns every rung/line that references the matching symbol(s) with full context.
- **Cross-reference index** — built once on first parse, cached on the project instance. Scans all NeutralText (ladder) and Structured Text code across programs and AOI definitions. Indexes both dotted references (`Motor_1.Faulted`) and base tags (`Motor_1`).
- 13 new tests: cross-program search, AOI internal search, ST code search, regex patterns, caching, context inclusion (79 total).

## [0.2.0] - 2026-04-12

### Added
- **`get_aois(l5x_path)`** — list all Add-On Instructions with name, description, and revision.
- **`get_aoi(l5x_path, aoi_name)`** — get AOI definition with parameters (name, data type, usage), local tags, vendor, and internal routine logic (NeutralText for ladder).
- **`list_modules(l5x_path)`** — list all I/O modules with catalog numbers, slot assignments, parent module, and descriptions.
- `load_project` now includes AOI count, AOI names, and module count in the project summary.
- 18 new tests: AOI listing, AOI parameters/usage/local tags/logic, module listing/catalog/slots (66 total).

## [0.1.0] - 2026-04-12

### Added
- **L5X parser** — core XML parser with LRU caching (maxsize=16). Extracts controller metadata (name, processor type, firmware, description) from Rockwell L5X project exports.
- **`load_project(l5x_path)`** — parse an L5X file and return a project summary with programs, tasks, UDT count, and tag count.
- **`get_tags(l5x_path, scope?, data_type?)`** — list controller-scoped and program-scoped tags with optional filtering by scope and data type.
- **`get_tag(l5x_path, tag_name)`** — get details for a specific tag across all scopes.
- **`get_udts(l5x_path)`** / **`get_udt(l5x_path, udt_name?)`** — list and inspect User Defined Type definitions with member details.
- **`get_routines(l5x_path, program?)`** / **`get_routine(l5x_path, program, routine_name)`** — list and read routine logic. Ladder routines return compact NeutralText with rung comments (smart chunking). Structured Text routines return raw code.
- **`ping()`** — health check.
- Structured error handling — all tools return `{"error": "..."}` JSON instead of raw exceptions.
- CLI entry point with `--transport stdio|sse`, `--host`, `--port`.
- Synthetic L5X test fixture with 2 programs, 7 controller tags, 2 UDTs, 3 routines (2 ladder + 1 ST), 1 AOI, 2 tasks, 3 modules.
- 48 tests covering all parsers, MCP tools, error handling, and caching.
