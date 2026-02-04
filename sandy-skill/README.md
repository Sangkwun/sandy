# Sandy

> A Sandevistan for your AI Agent

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

[![Sandy Demo](https://img.youtube.com/vi/owgyGYL4SVs/hqdefault.jpg)](https://www.youtube.com/watch?v=owgyGYL4SVs)

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
python scripts/play.py scenario.json --json
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

**Full schema**: See [references/schema.md](references/schema.md)

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
python scripts/play.py <scenario.json> [options]
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

## Project Structure

```
sandy-skill/
├── .claude-plugin/
│   └── plugin.json          # Plugin manifest
├── skills/sandy/
│   └── SKILL.md             # Skill specification
├── scripts/
│   ├── play.py              # CLI entry point
│   ├── player.py            # Scenario executor
│   └── clients/             # MCP transport clients
├── assets/examples/         # Example scenarios
├── references/
│   └── schema.md            # Full JSON schema
└── tests/
```

## Cross-Platform Compatibility

Sandy follows the [Agent Skills](https://agentskills.io) open standard:

| Tool | Support |
|------|---------|
| Claude Code | Full |
| OpenAI Codex CLI | Full |
| Gemini CLI | Full |
| Cursor | Full |
| GitHub Copilot | Full |

## License

Apache License 2.0
