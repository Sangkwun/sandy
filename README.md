# Sandy

> A Sandevistan for your AI Agent - Accelerating LLM Agents via Deterministic Replay

Sandy is a framework that records MCP (Model Context Protocol) tool call sequences and replays them without LLM inference, dramatically reducing cost and latency.

## Key Ideas

**1. Procedure-level Replay**

Instead of replaying entire workflows (inflexible) or caching individual API calls (loses context), Sandy introduces **Procedures** - reusable sequences of tool calls that LLMs can select and compose.

```
┌─────────────────────────────────────────────────────────┐
│              Reuse Granularity Spectrum                  │
│                                                         │
│  Individual API      Procedure        Full Workflow     │
│  (ToolCaching)       (Sandy)          (AgentRR)         │
│       │                 │                  │            │
│       ▼                 ▼                  ▼            │
│  Flexibility: High ◄───────────────► Low               │
│  Efficiency:  Low  ◄───────────────► High              │
│                         ▲                               │
│                    Sandy: Optimal Balance               │
└─────────────────────────────────────────────────────────┘
```

**2. Selective Reasoning**

When deterministic replay fails (dynamic elements, unexpected situations), Sandy falls back to LLM reasoning - but only when necessary.

```
Level 1: Exact Match (cost: 0)     → Most API calls succeed here
Level 2: Simple Heuristic (cost: 0) → Text/aria-label matching
Level 3: LLM Fallback (cost: $)    → Universal problem solver
         ├── Find dynamic elements
         ├── Ask user questions
         ├── Handle unexpected dialogs
         └── Recover from errors
```

## Architecture

```
┌─────────────────┐     Record      ┌─────────────────┐
│   AI Agent      │ ───────────────▶│   Procedure     │
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

## Project Structure

```
sandy/
├── sandy-skill/          # Sandy Skill implementation
│   ├── scripts/          # Python core (player, config, clients)
│   ├── skills/           # Claude Code skill definitions
│   └── assets/examples/  # Example scenarios
│
├── research/             # Research documentation
│   └── EXPERIMENTS.md    # Experiment design
│
├── scenarios/            # User scenarios
│
├── RESEARCH.md           # Full research plan
└── SANDY_PLAN.md         # Development plan
```

## Quick Start

### As CLI

```bash
# Install
pip install -r sandy-skill/requirements.txt

# Run scenario
python sandy-skill/scripts/play.py scenario.json

# With variables
python sandy-skill/scripts/play.py scenario.json --var TITLE="Bug fix"

# Partial execution
python sandy-skill/scripts/play.py scenario.json --start 2 --end 4
```

### As Claude Code Plugin

```shell
/plugin marketplace add sangkwun/sandy-skill
/plugin install sandy@sangkwun-sandy-skill

/sandy:play scenario.json
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
- [Research Plan](RESEARCH.md) - Academic research details
- [Experiments](research/EXPERIMENTS.md) - Experiment design

## Research

Sandy is a research project exploring the optimal balance between deterministic execution and LLM reasoning in AI agents.

**Research Questions:**
- RQ1: How much cost/time does Procedure-level Replay save?
- RQ2: Which MCP tool types are most suitable for replay?
- RQ3: How often does Selective Reasoning occur, and at what cost?
- RQ4: How effectively does LLM Fallback handle unpredictable situations?
- RQ5: How flexible is Procedure-level abstraction compared to alternatives?

<!-- Paper link will be added after arXiv submission -->

## Contributing

Contributions are welcome! Please see the [research documentation](RESEARCH.md) for context on the project goals.

## License

Apache License 2.0
