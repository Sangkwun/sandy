<div align="center">

# Sandy

### A Sandevistan for your AI Agent

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Claude Code Plugin](https://img.shields.io/badge/Claude_Code-Plugin-blueviolet)](https://github.com/Sangkwun/sandy)
[![MCP](https://img.shields.io/badge/MCP-Compatible-green)](https://modelcontextprotocol.io)

</div>

---

Sandy makes AI agents faster by letting them create and reuse MCP tool call sequences. Once a workflow is saved as a scenario, it replays without LLM inference—saving tokens and time.

## What is Sandy?

Sandy is a **workflow accelerator** for AI agents. When an agent identifies a repeatable workflow, Sandy can:

1. **Store** the tool call sequence as a scenario
2. **Parameterize** variable parts (URLs, IDs, search terms)
3. **Replay** the exact sequence without LLM reasoning

| Without Sandy | With Sandy |
|---------------|------------|
| LLM inference every time | Record once, replay infinitely |
| Token costs per execution | Zero-cost replay |
| Variable timing | Deterministic execution |

## How Agents Use Sandy

**Create scenarios**: When an agent completes a repeatable workflow, it writes the MCP tool sequence as a scenario JSON file.

**Reuse scenarios**: On similar requests, the agent finds existing scenarios and replays them instead of reasoning through the steps again.

**Judgment**: The agent decides when a workflow is worth saving and when to reuse existing scenarios.

### Example Flow

```
User: "Scrape HN top stories and save to database"

Agent (first time):
  1. Executes workflow: navigate → scrape → insert
  2. Recognizes pattern as reusable
  3. Writes scenario to .sandy/scenarios/hn-scrape-to-db.json

User: "Scrape HN again"

Agent (subsequent):
  1. Finds matching scenario
  2. Replays via Sandy
  3. Done—no LLM inference needed
```

## Demo

Watch what Sandy does and how it works:

<a href="https://www.youtube.com/watch?v=owgyGYL4SVs">
  <img src="https://img.youtube.com/vi/owgyGYL4SVs/hqdefault.jpg" alt="Sandy Demo" width="600">
</a>

## Installation

### As Claude Code Plugin

```shell
claude plugin marketplace add Sangkwun/sandy
claude plugin install sandy@sangkwun
```

**That's it.** Once installed:
- Use `/sandy` command to invoke the skill
- Agent can identify repeatable workflows
- Write them as scenario files
- Replay them without LLM inference

**Update existing installation:**
```shell
claude plugin marketplace update sangkwun
claude plugin update sandy@sangkwun
```

### As Standalone CLI

```bash
pip install mcp jsonpath-ng python-dotenv
python sandy-skill/scripts/play.py scenario.json --json
```

## Scenario Format

Scenarios are JSON files defining MCP tool sequences:

```json
{
  "version": "2.1",
  "metadata": { "name": "Query Database" },
  "variables": { "LIMIT": "5" },
  "steps": [
    {
      "step": 1,
      "tool": "mcp__supabase__query",
      "params": { "sql": "SELECT * FROM users LIMIT {{LIMIT}}" }
    }
  ]
}
```

**Full schema**: See [sandy-skill/references/schema.md](sandy-skill/references/schema.md)

## Supported Transports

| Config | Transport |
|--------|-----------|
| `command: ...` | stdio (spawn process) |
| `endpoint: http://...` | SSE |
| `endpoint: ws://...` | WebSocket |
| `claude-in-chrome` | Unix socket |

## Config Auto-Detection

Sandy finds MCP configuration from:

1. `$SANDY_CONFIG` environment variable
2. `.sandy/config.json` (project local)
3. Claude Desktop config
4. Cursor config (`~/.cursor/mcp.json`)
5. `~/.sandy/config.json` (global)

<details>
<summary>CLI Options (Advanced)</summary>

```bash
python sandy-skill/scripts/play.py <scenario.json> [options]
```

| Option | Description |
|--------|-------------|
| `--var KEY=VALUE` | Set variable (repeatable) |
| `--env FILE` | Load variables from .env |
| `--config FILE` | Specify MCP config path |
| `--start N` | Start from step N |
| `--end N` | End at step N |
| `--include-results MODE` | Include MCP results: `true`, `false`, `on_failure` |
| `--dry-run` | Validate without executing |
| `--debug` | Enable debug output |
| `--json` | Output as JSON |

</details>

## Documentation

| Resource | Description |
|----------|-------------|
| [Scenario Schema](sandy-skill/references/schema.md) | JSON format specification |
| [Example Scenarios](sandy-skill/assets/examples/) | Working examples |

## Cross-Platform Compatibility

Sandy follows the [Agent Skills](https://agentskills.io) open standard:

| Tool | Support |
|------|---------|
| Claude Code | Full |
| OpenAI Codex CLI | Full |
| Gemini CLI | Full |
| Cursor | Full |
| GitHub Copilot | Full |

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
