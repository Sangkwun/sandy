<div align="center">

# Sandy

### A Sandevistan for your AI Agent

**Record & Play MCP Tool calls without LLM inference**

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Claude Code Plugin](https://img.shields.io/badge/Claude_Code-Plugin-blueviolet)](https://github.com/Sangkwun/sandy)
[![MCP](https://img.shields.io/badge/MCP-Compatible-green)](https://modelcontextprotocol.io)

[Installation](#installation) • [Features](#features) • [Scenario Format](#scenario-format) • [Documentation](#documentation)

</div>

---

## Why Sandy?

Sandy records MCP (Model Context Protocol) tool call sequences and replays them **without LLM inference**, dramatically reducing cost and latency.

| | Without Sandy | With Sandy |
|:---:|:---|:---|
| **Cost** | Token costs every execution | Zero cost replay |
| **Speed** | LLM inference latency | Instant execution |
| **Consistency** | Variable outputs | Deterministic results |

---

## How It Works

```
┌─────────────────┐     Record      ┌─────────────────┐
│   AI Agent      │ ───────────────▶│   Scenario      │
│  (with LLM)     │                 │    (.json)      │
└─────────────────┘                 └────────┬────────┘
                                             │
                                             │ Play
                                             ▼
┌─────────────────┐                 ┌─────────────────┐
│   MCP Servers   │ ◀───────────────│     Sandy       │
│ (GitHub, DB...) │   Direct calls  │   (no LLM)      │
└─────────────────┘                 └─────────────────┘
```

---

## Installation

### Claude Code Plugin (Recommended)

```bash
# 1. Add marketplace
/plugin marketplace add Sangkwun/sandy

# 2. Install plugin
/plugin install sandy@Sangkwun-sandy
```

**Usage:**
```bash
/sandy:play scenario.json
/sandy:play scenario.json --var TITLE="Bug Fix"
```

### Standalone CLI

```bash
# Install dependencies
pip install -r sandy-skill/requirements.txt

# Run scenario
python sandy-skill/scripts/play.py scenario.json

# With variables
python sandy-skill/scripts/play.py scenario.json --var TITLE="Bug fix"

# Partial execution (for debugging)
python sandy-skill/scripts/play.py scenario.json --start 2 --end 4
```

---

## Features

| Feature | Description |
|---------|-------------|
| **Multi-Transport** | stdio, SSE, WebSocket, Unix socket |
| **Config Auto-Detection** | Claude Desktop, Cursor, Sandy configs |
| **Variable Substitution** | `{{VAR}}`, `{{step_id.field}}` |
| **Output Extraction** | JSONPath expressions |
| **Error Handling** | retry, skip, stop strategies |
| **Partial Execution** | `--start`, `--end` flags for debugging |

---

## Scenario Format

Sandy uses JSON scenarios (v2.1) to define tool call sequences:

```json
{
  "version": "2.1",
  "metadata": { "name": "Create Issue and Notify" },
  "steps": [
    {
      "step": 1,
      "id": "create_issue",
      "tool": "mcp__github__create_issue",
      "params": { "repo": "{{REPO}}", "title": "{{TITLE}}" },
      "output": { "number": "$.number", "url": "$.html_url" }
    },
    {
      "step": 2,
      "tool": "mcp__slack__post_message",
      "params": {
        "channel": "#dev",
        "text": "Issue #{{create_issue.number}} created: {{create_issue.url}}"
      }
    }
  ]
}
```

**Key concepts:**
- **Variables**: `{{VAR}}` - passed via `--var` flag
- **Step outputs**: `{{step_id.field}}` - reference previous results
- **JSONPath**: Extract specific fields from tool responses

---

## Documentation

| Resource | Description |
|----------|-------------|
| [Sandy Skill README](sandy-skill/README.md) | Detailed usage guide |
| [Scenario Schema](sandy-skill/references/schema.md) | JSON format specification |
| [Example Scenarios](sandy-skill/assets/examples/) | Working examples |

---

## Contributing

Contributions are welcome! Feel free to open issues and pull requests.

---

<div align="center">

**Apache License 2.0**

Made with the speed of a Sandevistan

</div>
