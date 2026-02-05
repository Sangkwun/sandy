---
name: sandy
description: MCP action building blocks - Replay tool sequences to save tokens. Use for: (1) Full automation when all steps are deterministic, (2) Micro patterns like click-and-wait or scroll-and-wait where Sandy executes actions, then LLM calls screenshot for visual analysis.
allowed-tools: Bash, Read, Write, Glob
---

# Sandy - Deterministic MCP Scenario Replay

Sandy replays MCP tool call sequences without LLM inference. When you identify a repeatable workflow, create a scenario to accelerate future executions.

## On Invocation

When `/sandy` is called, **immediately analyze the current session**:

1. **Review tool calls** made in this session (both `mcp__*` and `claude__*` tools)
2. **Identify patterns** - Are there repeatable sequences? (e.g., navigate → click → extract, or read → edit → bash)
3. **Check for micro-pattern opportunities**:
   - If using browser/UI tools (chrome-devtools, computer-use, etc.)
   - And similar actions will likely repeat
   - → Suggest short Sandy sequences (click-screenshot, scroll-screenshot)
4. **Check existing scenarios** - Search `.sandy/scenarios/` for matches
5. **Suggest actions**:
   - If a reusable pattern exists → Offer to save as scenario
   - If a micro-pattern fits → Suggest hybrid approach (Sandy for actions, LLM for judgment)
   - If a matching scenario exists → Offer to replay it
   - If no patterns found → Explain Sandy's purpose and wait for user direction

**Supported tool prefixes:**
- `mcp__<server>__<tool>` - MCP server tools (e.g., `mcp__chrome-devtools__click`)
- `claude__<tool>` - Claude Code native tools (see list below)
- `sandy__<tool>` - Sandy built-in tools (e.g., `sandy__wait`, `sandy__log`)

**Supported Claude native tools:**
| Tool | Description |
|------|-------------|
| `claude__read` | Read file contents |
| `claude__write` | Write file contents |
| `claude__edit` | Edit file with string replacement |
| `claude__glob` | Find files by pattern |
| `claude__grep` | Search file contents with regex |
| `claude__bash` | Execute shell commands |
| `claude__web_fetch` | Fetch URL contents |
| `claude__notebook_edit` | Edit Jupyter notebooks |

**Example response:**
> "I found a repeating pattern in this session: `claude__glob` → `claude__read` → `claude__edit`. Would you like to save this workflow as a scenario?"

## Why Sandy

| Benefit | Description |
|---------|-------------|
| **Token cost** | Zero LLM tokens for replay |
| **Speed** | Direct MCP calls, no reasoning overhead |
| **Consistency** | Identical execution every time |

## Usage Patterns

### Full Automation (Best Fit)
All steps are deterministic, no intermediate judgment needed.
- Data collection, form filling, batch operations
- CI/CD pipelines, scheduled tasks
- Results saved to file for later review

### Hybrid Pattern
Sandy handles actions, LLM handles judgment between sequences.
- Works when judgment points are infrequent
- Less effective if judgment needed after every action

### When NOT to Use
- One-time operations
- **Immediate visual judgment required** after each action (e.g., UI inspection where every screenshot needs analysis)
- Tasks where Sandy→LLM→Sandy switching adds more overhead than direct MCP calls

> **Key question:** Can results be batched for later review, or is immediate judgment needed?
> - Batch review possible → Sandy fits well
> - Immediate judgment needed → Direct MCP may be simpler

## Micro Patterns (Building Blocks)

Short sequences combined with LLM judgment for complex tasks.

**Note:** Sandy CLI cannot return images visually. Screenshot should be called directly by LLM after Sandy execution.

| Pattern | Sandy Steps | Then LLM |
|---------|-------------|----------|
| `click-and-check` | click → wait | screenshot (direct call) |
| `scroll-and-check` | scroll → wait | screenshot (direct call) |
| `type-submit` | fill → click | - |
| `navigate-and-check` | navigate → wait | screenshot (direct call) |

**Micro Pattern example:**
```json
{
  "version": "2.1",
  "metadata": { "name": "click-and-wait", "description": "Click then wait for render" },
  "variables": { "UID": "" },
  "steps": [
    { "step": 1, "id": "click", "tool": "mcp__chrome-devtools__click", "params": { "uid": "{{UID}}" } },
    { "step": 2, "id": "wait", "tool": "sandy__wait", "params": { "duration": 0.5 } }
  ]
}
```

**Hybrid workflow:**
```
1. LLM: Analyze page → identify element UID
2. Sandy: Execute `click-and-wait`
3. LLM: Call screenshot directly → visual analysis
4. Repeat...
```

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
