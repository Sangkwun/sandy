# Sandy - MCP Scenario Player

## Project Overview

Sandy is a **deterministic workflow accelerator** for AI agents. Agents create MCP tool call sequences as scenarios, then replay them without LLM inference—saving tokens and time.

**Core Value:**
- Deterministic replay of MCP tool calls without LLM
- Reduced token costs for repetitive tasks
- Ideal for CI/CD pipelines and regression testing

**How Agents Use Sandy:**
1. Execute a workflow using MCP tools
2. Identify it as repeatable
3. Write the tool sequence as a scenario JSON
4. Replay via Sandy on future requests

## Tech Stack

- **Language**: Python 3.14
- **Core Dependencies**:
  - `mcp>=1.0.0` - MCP Python SDK
  - `websockets>=12.0` - WebSocket support
  - `jsonpath-ng>=1.6.0` - JSONPath output extraction
  - `python-dotenv>=1.0.0` - Environment variable loading

## Project Structure

```
sandy/
├── sandy-skill/                    # Main plugin/CLI implementation
│   ├── .claude-plugin/
│   │   └── plugin.json            # Claude Code plugin manifest
│   ├── .sandy/
│   │   └── config.json            # MCP server configuration
│   ├── skills/sandy/
│   │   └── SKILL.md               # Skill specification (for Claude Code)
│   ├── scripts/                   # Core Python implementation
│   │   ├── play.py               # CLI entry point
│   │   ├── player.py             # Scenario executor
│   │   ├── scenario.py           # Scenario parser & validator
│   │   ├── config.py             # Config auto-detection
│   │   ├── reporter.py           # Result formatting
│   │   └── clients/              # MCP transport implementations
│   │       ├── base.py           # Abstract base class
│   │       ├── stdio_client.py   # stdio transport
│   │       ├── sse_client.py     # SSE transport
│   │       ├── websocket_client.py
│   │       └── socket_client.py  # Unix socket
│   ├── assets/examples/          # Example scenarios
│   ├── references/schema.md      # JSON schema documentation
│   └── tests/                    # Unit tests
└── README.md
```

## Key Components

| Component | File | Responsibility |
|-----------|------|----------------|
| CLI Entry | `play.py` | Argument parsing, config/scenario loading, execution orchestration |
| Scenario Executor | `player.py` | Step execution, variable substitution, output extraction, error handling |
| Scenario Parser | `scenario.py` | JSON parsing, validation, v1.1→v2.1 conversion |
| Config Manager | `config.py` | Auto-detect MCP config from multiple sources |
| Reporter | `reporter.py` | Result formatting (console, JSON) |
| MCP Clients | `clients/` | Transport-specific implementations (stdio, SSE, WebSocket, socket) |

## Architecture & Patterns

### Execution Flow

```
CLI Input → parse arguments → load scenario → detect config
    → create player → execute steps → format result → report
```

### Scenario JSON Format (v2.1)

```json
{
  "version": "2.1",
  "metadata": { "name": "...", "description": "..." },
  "variables": { "VAR_NAME": "default" },
  "steps": [
    {
      "step": 1,
      "id": "unique_id",
      "tool": "mcp__server__tool_name",
      "params": { ... },
      "output": { "field": "$.json.path" },
      "on_error": "stop|skip|retry"
    }
  ]
}
```

### Variable Substitution System

| Pattern | Description | Example |
|---------|-------------|---------|
| `{{VAR}}` | Static variable | `"title": "{{TITLE}}"` |
| `{{step_id.field}}` | Reference previous step output | `"text": "Issue #{{create.number}}"` |
| JSONPath | Output extraction | `"items": "$[*].id"` |

### MCP Tool Naming

Format: `mcp__<server>__<tool_name>`
- `mcp__github__create_issue`
- `mcp__chrome-devtools__click`
- `mcp__supabase__query`

### Sandy Built-in Tools

Use `sandy__` prefix without MCP server:
- `sandy__wait` - Wait/delay
- `sandy__log` - Log output
- `sandy__append_file` - Save to JSONL/CSV/JSON
- `sandy__wait_for_element` - Wait for CSS selector
- `sandy__wait_until` - Wait for JavaScript expression

### Error Handling Strategy

Per-step error modes:
- `"stop"` - Stop execution (default)
- `"skip"` - Continue to next step
- `"retry"` - Retry with exponential backoff

### Transport Abstraction Pattern

`MCPClient` abstract class with implementations:
1. **StdioClient** - Subprocess stdin/stdout
2. **SSEClient** - HTTP SSE
3. **WebSocketClient** - WebSocket
4. **SocketClient** - Unix domain socket

Factory pattern auto-selects based on configuration.

## Development Guidelines

### Running Tests

```bash
cd sandy-skill
pytest tests/
```

### Config Auto-Detection Priority

1. `$SANDY_CONFIG` environment variable
2. `.sandy/config.json` (project local)
3. Claude Desktop settings
4. Cursor settings (`~/.cursor/mcp.json`)
5. `~/.sandy/config.json` (global user settings)

### Backward Compatibility

v1.1 scenarios (using `action` field) are automatically converted to v2.1.

## Code Conventions

- **Type Safety**: Define types with dataclass (`Step`, `Scenario`, `StepResult`, `PlayResult`, etc.)
- **Naming**: Use snake_case
- **Single Responsibility**: Each module follows single responsibility principle
- **JSONPath**: Use `jsonpath-ng` library for result parsing

## Important Notes

- When adding new MCP tools, check transport implementations in `clients/` directory
- Update `references/schema.md` when changing scenario schema
- Update `plugin.json` when changing plugin version
- Example scenarios are located in `assets/examples/`
- Scenario storage location: `.sandy/scenarios/` (project-local)
