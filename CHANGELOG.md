# Changelog

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
