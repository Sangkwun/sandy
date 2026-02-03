# Sandy

> A Sandevistan for your AI Agent - Record & Play MCP Tool calls

Sandy records MCP (Model Context Protocol) tool call sequences and replays them without LLM inference, dramatically reducing cost and latency.

## Why Sandy?

| Without Sandy | With Sandy |
|---------------|------------|
| LLM inference every time | Record once, replay infinitely |
| Token costs per execution | Zero cost replay |
| Variable timing | Deterministic execution |

## Architecture

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

## Installation

### As Claude Code Plugin (Recommended)

```bash
# Add marketplace
/plugin marketplace add Sangkwun/sandy

# Install plugin
/plugin install sandy@Sangkwun-sandy
```

Then use:
```bash
/sandy:play scenario.json
/sandy:play scenario.json --var TITLE="Bug Fix"
```

### As Standalone CLI

```bash
# Install dependencies
pip install -r sandy-skill/requirements.txt

# Run scenario
python sandy-skill/scripts/play.py scenario.json

# With variables
python sandy-skill/scripts/play.py scenario.json --var TITLE="Bug fix"

# Partial execution
python sandy-skill/scripts/play.py scenario.json --start 2 --end 4
```

## Scenario Format (v2.1)

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

## Features

- **Multi-Transport**: stdio, SSE, WebSocket, Unix socket
- **Config Auto-Detection**: Claude Desktop, Cursor, Sandy configs
- **Variable Substitution**: `{{VAR}}`, `{{step_id.field}}`
- **Output Extraction**: JSONPath expressions
- **Error Handling**: retry, skip, stop strategies
- **Partial Execution**: `--start`, `--end` for debugging

## Documentation

- [Sandy Skill README](sandy-skill/README.md) - Detailed usage
- [Scenario Schema](sandy-skill/references/schema.md) - JSON format spec
- [Example Scenarios](sandy-skill/assets/examples/) - Working examples

## Contributing

Contributions are welcome!

## License

Apache License 2.0
