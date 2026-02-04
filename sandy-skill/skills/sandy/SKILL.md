---
name: sandy
description: Deterministic MCP scenario replay - Agent creates and reuses MCP tool call sequences without LLM inference.
allowed-tools: Bash, Read, Write, Glob
---

# Sandy - Deterministic MCP Scenario Replay

Sandy replays MCP tool call sequences without LLM inference. When you identify a repeatable workflow, create a scenario to accelerate future executions.

## Why Sandy

| Benefit | Description |
|---------|-------------|
| **Token cost** | Zero LLM tokens for replay |
| **Speed** | Direct MCP calls, no reasoning overhead |
| **Consistency** | Identical execution every time |

### When NOT to Use

- One-time operations
- Tasks requiring dynamic decision-making
- Exploratory workflows

## When to Save a Scenario

Save when **any** of these apply:

- Same MCP tool sequence used 2+ times
- User mentions "repeat", "daily", "automate"
- Clear workflow pattern emerges (navigate → scrape → save)

### Variables to Extract

When saving, parameterize:

| Type | Example | Variable |
|------|---------|----------|
| User inputs | Issue title, search terms | `{{TITLE}}` |
| Identifiers | Repo name, PR number | `{{REPO}}`, `{{PR_NUMBER}}` |
| URLs | Target pages | `{{TARGET_URL}}` |
| Output paths | File destinations | `{{OUTPUT_PATH}}` |

## Finding Existing Scenarios

**Location**: `.sandy/scenarios/` (project-local)

**Search workflow**:

1. Use Glob to find scenarios:
   ```
   Glob pattern: .sandy/scenarios/**/*.json
   ```

2. Read each file and check:
   - `metadata.name` - Scenario name
   - `metadata.description` - What it does
   - `steps` - MCP tool sequence

3. Match against current task requirements

**Bundled examples**: `${CLAUDE_PLUGIN_ROOT}/assets/examples/`

## Creating Scenarios

### Workflow

1. **Execute** - Perform the workflow using actual MCP tools
2. **Track** - Note which tools were called and with what parameters
3. **Parameterize** - Identify values that should become variables
4. **Write** - Create scenario JSON based on the executed workflow
5. **Save** - Write to `.sandy/scenarios/<name>.json`
6. **Verify** - Run with `--dry-run` to validate

**Important**: Always test the workflow first before writing the scenario.

### Minimal Schema

```json
{
  "version": "2.1",
  "metadata": { "name": "...", "description": "..." },
  "variables": { "VAR_NAME": "default" },
  "steps": [
    {
      "step": 1,
      "id": "unique_id",
      "tool": "mcp__server__tool",
      "params": { "key": "{{VAR_NAME}}" },
      "output": { "field": "$.json.path" }
    }
  ]
}
```

**Full schema**: See `${CLAUDE_PLUGIN_ROOT}/references/schema.md`

### Tool Naming

Format: `mcp__<server>__<tool_name>`

Examples:
- `mcp__github__create_issue`
- `mcp__chrome-devtools__click`
- `mcp__supabase__query`

## Executing Scenarios

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/play.py <scenario.json> [options] --json
```

### Options

| Option | Description |
|--------|-------------|
| `--start N` | Start from step N |
| `--end N` | End at step N |
| `--var KEY=VALUE` | Set variable (repeatable) |
| `--env FILE` | Load variables from .env |
| `--dry-run` | Validate without executing |
| `--debug` | Enable debug output |
| `--json` | Output as JSON |

### Partial Execution

Run only specific steps when reusing part of a workflow:

```bash
# Steps 1-3 only (e.g., navigate and scrape, skip save)
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/play.py scenario.json --start 1 --end 3 --json
```

## Error Handling

### Result Interpretation

**Success**:
```json
{ "success": true, "passed_steps": 3, "total_steps": 3 }
```

**Failure**:
```json
{ "success": false, "failed_step": 2, "error": "Element not found" }
```

### Recovery Strategy

1. Analyze error (MCP response + step context)
2. Determine cause:
   - Transient: Retry with `--start <failed_step>`
   - Structural: Page/API changed, scenario needs update
3. Fix and re-run, or report to user

### Per-Step Error Modes

| Mode | Behavior |
|------|----------|
| `"stop"` | Stop execution (default) |
| `"skip"` | Continue to next step |
| `"retry"` | Retry with exponential backoff |

## Sandy Built-in Tools

Tools with `sandy__` prefix don't require MCP servers.

| Tool | Purpose |
|------|---------|
| `sandy__wait` | Wait for duration (no MCP timeout limit) |
| `sandy__log` | Log message to output |
| `sandy__append_file` | Save data to file (jsonl/csv/json) |
| `sandy__wait_for_element` | Wait for CSS selector |
| `sandy__wait_until` | Wait for JS expression to be true |

**Details**: See `${CLAUDE_PLUGIN_ROOT}/references/schema.md#sandy-internal-tools`

## Reference

- **Schema**: `${CLAUDE_PLUGIN_ROOT}/references/schema.md`
- **Examples**: `${CLAUDE_PLUGIN_ROOT}/assets/examples/`
- **Scenario storage**: `.sandy/scenarios/` (project-local)
