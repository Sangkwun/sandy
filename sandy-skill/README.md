# Sandy

> A Sandevistan for your AI Agent - Record & Play MCP Tool calls

Sandy accelerates AI agents by recording MCP tool call sequences and replaying them without LLM inference. Think of it as a "macro recorder" for AI actions.

## Why Sandy?

| Without Sandy | With Sandy |
|---------------|------------|
| LLM inference every time | Record once, replay infinitely |
| Token costs per execution | Zero cost replay |
| Variable timing | Deterministic execution |
| Requires AI reasoning | Direct MCP calls |

Sandy is ideal for:
- Repetitive automation tasks
- CI/CD pipelines
- Regression testing
- Cost-sensitive operations

## Installation

### As Claude Code Plugin (Recommended)

```shell
# Add marketplace
/plugin marketplace add sangkwun/sandy-skill

# Install plugin
/plugin install sandy@sangkwun-sandy-skill
```

Then use:
```shell
/sandy:play scenario.json
/sandy:play scenario.json --var TITLE="Bug Fix"
/sandy:play scenario.json --start 2 --end 4
```

### As Standalone CLI

```bash
# Install dependencies
pip install mcp jsonpath-ng python-dotenv

# Run directly
python scripts/play.py scenario.json --json
```

## Quick Start

### 1. Create a scenario

```json
{
  "version": "2.1",
  "metadata": { "name": "Query Database" },
  "steps": [
    {
      "step": 1,
      "id": "query",
      "tool": "mcp__supabase__query",
      "params": { "sql": "SELECT * FROM users LIMIT 5" },
      "output": { "users": "$" }
    }
  ]
}
```

### 2. Run it

```shell
/sandy:play scenarios/my-scenario.json
```

Or via CLI:
```bash
python scripts/play.py scenarios/my-scenario.json --json
```

## Scenario Format (v2.1)

```json
{
  "version": "2.1",
  "metadata": {
    "name": "Create GitHub Issue",
    "description": "Creates an issue and notifies Slack"
  },
  "variables": {
    "REPO": "owner/repo",
    "TITLE": ""
  },
  "steps": [
    {
      "step": 1,
      "id": "create_issue",
      "tool": "mcp__github__create_issue",
      "params": {
        "repo": "{{REPO}}",
        "title": "{{TITLE}}"
      },
      "output": {
        "number": "$.number",
        "url": "$.html_url"
      }
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

### Variable Substitution

| Syntax | Description | Example |
|--------|-------------|---------|
| `{{VAR}}` | Static variable | `{{REPO}}` |
| `{{step_id.field}}` | Runtime result reference | `{{create_issue.number}}` |

### Step Fields

| Field | Required | Description |
|-------|----------|-------------|
| `step` | Yes | Step number |
| `tool` | Yes | MCP tool name (`mcp__server__tool`) |
| `params` | Yes | Tool parameters |
| `id` | No | Identifier for result references |
| `output` | No | JSONPath expressions to extract results |
| `description` | No | Human-readable description |
| `on_error` | No | Error handling: `"stop"`, `"skip"`, `"retry"` |
| `retry` | No | Retry config: `{"count": 3, "delay": 500}` |
| `wait_after` | No | Delay after step (seconds) |
| `condition` | No | Conditional execution expression |

## CLI Options

```bash
python scripts/play.py <scenario.json> [options]
```

| Option | Description |
|--------|-------------|
| `--var KEY=VALUE` | Set variable (repeatable) |
| `--env FILE` | Load variables from .env file |
| `--config FILE` | Specify MCP config file path |
| `--start N` | Start from step N (inclusive) |
| `--end N` | End at step N (inclusive) |
| `--include-results MODE` | Include MCP results: `true`, `false`, `on_failure` |
| `--dry-run` | Validate without executing |
| `--debug` | Enable debug output |
| `--json` | Output result as JSON |

## Supported Transports

| Config | Transport | Description |
|--------|-----------|-------------|
| `command: ...` | stdio | Spawn server process |
| `endpoint: http://...` | SSE | Server-Sent Events |
| `endpoint: ws://...` | WebSocket | WebSocket connection |
| `claude-in-chrome` | Socket | Unix socket |

## Config Auto-Detection

Sandy automatically detects MCP configuration from:

1. `$SANDY_CONFIG` environment variable
2. `.sandy/config.json` (project local)
3. Claude Desktop config
4. Cursor config (`~/.cursor/mcp.json`)
5. `~/.sandy/config.json` (global)

## Project Structure

```
sandy-skill/
├── .claude-plugin/
│   ├── plugin.json          # Plugin manifest
│   └── marketplace.json     # Marketplace manifest
├── skills/
│   └── play/
│       └── SKILL.md         # /sandy:play skill
├── scripts/
│   ├── play.py              # CLI entry point
│   ├── player.py            # Scenario executor
│   ├── scenario.py          # Scenario parser
│   ├── config.py            # Config detection
│   ├── reporter.py          # Output formatting
│   └── clients/             # MCP transport clients
├── assets/
│   └── examples/            # Example scenarios
├── references/              # Documentation
└── tests/                   # Unit tests
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

MIT
