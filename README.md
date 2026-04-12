# studio5000-mcp-server

> MCP server for Rockwell/Allen-Bradley Studio 5000 — parse L5X project exports and give AI agents structured access to PLC tags, UDTs, routines, and programs.

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/protocol-MCP-green.svg)](https://modelcontextprotocol.io/)

---

## What This Does

`studio5000-mcp-server` connects AI agents (Claude, GPT, local LLMs) to your Rockwell/Allen-Bradley PLC projects via the [Model Context Protocol](https://modelcontextprotocol.io/). It parses L5X project exports and gives the AI structured access to:

- **Tags** — controller-scoped and program-scoped tags with data types, descriptions, and values
- **UDTs** — User Defined Type definitions with member details
- **Routines** — ladder logic as compact NeutralText (not raw XML), Structured Text as-is
- **Programs & Tasks** — program structure, task scheduling, and assignments
- **Rung Comments** — per-rung documentation extracted alongside logic

### Smart Chunking

A single ladder rung can be hundreds of lines of verbose L5X XML. This server extracts the compact **NeutralText** representation instead:

```
// Raw XML: ~200 lines per rung
// NeutralText: 1 line
XIC(StartPB) XIO(StopPB) XIO(EmergencyStop) OTE(SystemRunning) ;
```

This keeps context windows small and gives LLMs something they can actually reason about.

Works with **L5X exports** from Studio 5000 Logix Designer v20+ and RSLogix 5000 v17+.

## Why This Exists

Studio 5000 has ~500,000+ active licenses and **zero AI tooling**. Rockwell's AI investment targets FactoryTalk Design Studio (their new cloud IDE) — not Studio 5000, which the vast majority of the installed base runs.

This server fills that gap. It's open-source, agent-agnostic, and works offline.

Part of [Project Automate](https://github.com/nodeblue-ai/project-automate) by [Nodeblue](https://www.nodeblue.ai).

---

## Installation

```bash
pip install studio5000-mcp-server
```

Or install from source:

```bash
git clone https://github.com/nodeblue-ai/studio5000-mcp-server.git
cd studio5000-mcp-server
pip install .
```

Requires Python 3.10+.

---

## Quick Start

### stdio (local — kiro-cli, Claude Desktop, Claude Code)

```bash
studio5000-mcp-server
```

### SSE (remote — server on one machine, agent on another)

```bash
studio5000-mcp-server --transport sse --port 8080
```

---

## Configuration

### kiro-cli

Add to your `~/.kiro/settings.json`:

```json
{
  "mcpServers": {
    "studio5000": {
      "command": "studio5000-mcp-server",
      "args": []
    }
  }
}
```

### Claude Desktop

Add to your Claude Desktop MCP config:

```json
{
  "mcpServers": {
    "studio5000": {
      "command": "studio5000-mcp-server",
      "args": []
    }
  }
}
```

### SSE (remote)

Start the server on your engineering workstation:

```bash
studio5000-mcp-server --transport sse --host 0.0.0.0 --port 8080
```

Connect from any MCP client using the SSE URL: `http://<host>:8080/sse`

---

## Available Tools

### `ping`
Health check. Returns `"pong"`.

### `load_project(l5x_path)`
Parse an L5X file and return a project summary — controller name, processor type, firmware version, programs, tasks, UDT count, tag count.

### `get_tags(l5x_path, scope?, data_type?)`
List tags from the project. Filter by scope (`"controller"` or a program name) and/or data type (`"BOOL"`, `"DINT"`, `"Motor_UDT"`, etc.).

```
get_tags("/path/to/project.l5x", "controller", "BOOL")
get_tags("/path/to/project.l5x", "MainProgram")
```

### `get_tag(l5x_path, tag_name)`
Get details for a specific tag — data type, description, scope, radix.

### `get_udts(l5x_path)`
List all User Defined Type names.

### `get_udt(l5x_path, udt_name?)`
Get UDT definition(s) with member details — name, data type, dimension, description.

### `get_routines(l5x_path, program?)`
List routines with type (RLL/ST/FBD/SFC) and size info. Filter by program name.

### `get_routine(l5x_path, program, routine_name)`
Get routine logic. Ladder routines return compact NeutralText with rung comments. Structured Text routines return raw code.

```
get_routine("/path/to/project.l5x", "MainProgram", "MainRoutine")
```

### `get_aois(l5x_path)`
List all Add-On Instructions with name, description, and revision.

### `get_aoi(l5x_path, aoi_name)`
Get an AOI definition with parameters (name, data type, usage), local tags, vendor info, and internal routine logic.

### `list_modules(l5x_path)`
List all I/O modules with catalog numbers, slot assignments, and descriptions.

### `search_logic(l5x_path, pattern)`
Search for a tag, AOI, or regex pattern across all routines and AOIs. Returns every rung/line that references matching symbols with full context.

```
search_logic("/path/to/project.l5x", "Motor_1")
search_logic("/path/to/project.l5x", "Motor_\\d")
```

Returns:
```json
{
  "program": "MainProgram",
  "name": "MainRoutine",
  "type": "RLL",
  "rungs": [
    {
      "number": 0,
      "comment": "System start/stop - start seals in, stop breaks circuit",
      "text": "[XIC(StartPB) ,XIC(SystemRunning) ][XIO(StopPB) XIO(EmergencyStop) OTE(SystemRunning) ];"
    }
  ]
}
```

---

## Example Conversation

```
You: Load the conveyor project and tell me what it does.

Agent calls: load_project("/projects/conveyor.l5x")

Agent: This is a CompactLogix 1769-L33ER project with 2 programs
(MainProgram and MotorProgram), 7 controller tags, and 2 UDTs.

You: What does MainRoutine do?

Agent calls: get_routine("/projects/conveyor.l5x", "MainProgram", "MainRoutine")

Agent: MainRoutine has 7 rungs:
- Rung 0: System start/stop latch (StartPB seals in, StopPB or E-stop breaks)
- Rung 1: Motor 1 control via Motor_Control AOI
- Rung 2: Fault detection — any motor fault sets FaultActive
- Rung 3: Fault counter increments on FaultActive rising edge
- Rungs 4-5: 1-second heartbeat timer
- Rung 6: Sets line speed to 60.0 when system running

You: Show me all Motor_UDT tags.

Agent calls: get_tags("/projects/conveyor.l5x", data_type="Motor_UDT")

Agent: There are 2 Motor_UDT tags:
- Motor_1 (controller scope) — Conveyor 1 drive motor
- Motor_2 (controller scope) — Conveyor 2 drive motor
```

---

## Roadmap

### v0.1 — Core L5X Parsing ✅
- [x] L5X XML parser with LRU caching
- [x] Controller-scoped and program-scoped tag extraction
- [x] UDT definitions with member details
- [x] Ladder logic as NeutralText + rung comments (smart chunking)
- [x] Structured Text routines returned as-is
- [x] Program and task structure
- [x] Structured error handling on all tools
- [x] 48 tests

### v0.2 — AOIs & Modules ✅
- [x] Add-On Instruction definitions with parameters, local tags, and internal logic
- [x] I/O module tree (catalog numbers, slot assignments)
- [x] 66 tests

### v0.3 — Cross-Reference Engine ✅
- [x] `search_logic(pattern)` — find all routines/rungs referencing a tag, AOI, or pattern
- [x] Tag→usage index built on first parse for instant queries
- [x] 79 tests

### v0.4 — Cross-Platform Intelligence
- [ ] Cross-reference Ignition tags with Studio 5000 L5X PLC logic
- [ ] "This alarm fires when tag X goes true — here's the PLC logic that drives X"

### Future
- [ ] FBD and SFC detailed parsing
- [ ] L5X fragment generation (code gen)
- [ ] Logix Designer SDK integration (live tag read/write, compilation)
- [ ] Local LLM support for air-gapped deployments

---

## Development

```bash
git clone https://github.com/nodeblue-ai/studio5000-mcp-server.git
cd studio5000-mcp-server
pip install -e .
python -m pytest tests/ -v
```

### Project Structure

```
src/studio5000_mcp_server/
├── __init__.py
├── __main__.py          # CLI entry point (stdio/SSE)
├── server.py            # FastMCP server with 13 tool definitions
├── l5x_parser.py        # Core L5X XML parser (LRU-cached)
└── parsers/
    ├── tags.py          # Controller + program-scoped tags
    ├── udts.py          # UDT definitions with members
    ├── routines.py      # Ladder NeutralText + ST code
    ├── programs.py      # Program/task structure
    ├── aois.py          # Add-On Instruction definitions
    ├── modules.py       # I/O module tree
    └── xref.py          # Cross-reference index (tag→usage)

tests/
├── test_server.py       # 79 tests — parsers, tools, error handling
└── fixtures/
    └── sample.l5x       # Synthetic L5X with all resource types
```

---

## License

MIT — see [LICENSE](LICENSE).

---

<p align="center">
  <i>Built by <a href="https://www.nodeblue.ai">Nodeblue</a> — Engineering-driven technology across software, industrial automation, and applied research.</i>
</p>
