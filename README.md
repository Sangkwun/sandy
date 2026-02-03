<div align="center">

# Sandy 🦾

### A Sandevistan for your AI Agent

**Separate Thinking from Acting — Execute at Machine Speed**

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Claude Code Plugin](https://img.shields.io/badge/Claude_Code-Plugin-blueviolet)](https://github.com/Sangkwun/sandy)
[![MCP](https://img.shields.io/badge/MCP-Compatible-green)](https://modelcontextprotocol.io)

[Why Sandy?](#why-sandy) • [Installation](#installation) • [Features](#features) • [Scenario Format](#scenario-format) • [Documentation](#documentation)

</div>

---

## Why Sandy?

**What's the point of a browser automation bot that's slower than a human?**

The reason traditional agents are slow is simple: **they think before every action.**

Sandy solves this by **separating Reasoning from Action**.

<br>

### 🐢 Traditional Agent (Agentic Loop)

```
Observe ➔ 🧠 LLM Reasoning (slow...) ➔ Action ➔ Observe ➔ 🧠 LLM... (repeat)
```
> Stops to think before every click. Every. Single. Time.

<br>

### 🐇 Sandy (Scenario Replay)

```
1️⃣ Pilot:  First Run ➔ Capture Workflow ➔ Save as Scenario
2️⃣ Run:    Load Scenario ➔ ⚡ Execute at machine speed
```
> Once you've blazed the trail, just follow the path — no thinking required.

<br>

**The LLM only helps find the path once.** After that, Sandy replays the saved scenario deterministically.

<br>

### ▶️ See the Difference

> ⚠️ **The right side (Sandy) is real-time, NOT sped up — but faster than the agent alone.**

<a href="https://www.youtube.com/watch?v=nSKs8sy7o2c">
  <img src="https://img.youtube.com/vi/nSKs8sy7o2c/maxresdefault.jpg" alt="Sandy Demo" width="600">
</a>

<br>

### 📊 At a Glance

| | 🐢 Without Sandy | 🐇 With Sandy |
|:---:|:---|:---|
| **Cost** | Token costs on every execution | Zero tokens after first run |
| **Speed** | LLM inference latency per step | Instant, deterministic execution |
| **Consistency** | Variable LLM outputs | Reproducible results every time |
| **Use Case** | Exploration, first-time tasks | CI/CD, regression tests, repetitive workflows |

---

## How It Works

```
┌─────────────────┐      Pilot      ┌─────────────────┐
│   AI Agent      │ ───────────────▶│   Scenario      │
│  (with LLM)     │                 │    (.json)      │
└─────────────────┘                 └────────┬────────┘
                                            │
                                            │ Play (no LLM)
                                            ▼
┌─────────────────┐                 ┌─────────────────┐
│   MCP Servers   │ ◀───────────────│     Sandy       │
│ (GitHub, DB...) │   Direct calls  │   ⚡ Fast       │
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
/sandy play scenario.json
/sandy play scenario.json --var TITLE="Bug Fix"
/sandy list
/sandy new my-workflow
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

## Support

If you find Sandy useful, please consider supporting its development!

[![Support on Polar](https://img.shields.io/badge/Support-Polar-blue?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48Y2lyY2xlIGN4PSIxMiIgY3k9IjEyIiByPSIxMCIgZmlsbD0id2hpdGUiLz48L3N2Zz4=)](https://polar.sh/checkout/polar_c_jfPjDO6lpMcQHKl58MsxBWy9Yp9DZ9Iv9Xajy2XUj6V)

Your contributions help keep the project maintained and allow me to focus on building new features.

---

## Contributing

Contributions are welcome! Feel free to open issues and pull requests.

---

<div align="center">

**Apache License 2.0**

Made with the speed of a Sandevistan ⚡

</div>
