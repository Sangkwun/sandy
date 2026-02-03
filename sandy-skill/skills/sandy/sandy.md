---
name: sandy
description: MCP Scenario Player - Record & Play MCP tool calls without LLM. Supports play (execute), list (find scenarios), and new (create scenario) subcommands.
allowed-tools: Bash, Read, Write, Glob
argument-hint: <play|list|new> [options]
---

# Sandy - MCP Scenario Player

Execute, list, or create MCP scenarios without LLM inference.

## Subcommands

| Command | Description |
|---------|-------------|
| `play <scenario.json>` | Execute a scenario |
| `list` | Find available scenarios |
| `new <name>` | Create a new scenario |

---

## play - Execute Scenario

Run MCP scenarios deterministically without LLM.

### Usage

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/play.py <scenario.json> [options] --json
```

### Options

| Option | Description |
|--------|-------------|
| `--start N` | Start from step N (inclusive) |
| `--end N` | End at step N (inclusive) |
| `--var KEY=VALUE` | Set variable (repeatable) |
| `--env FILE` | Load variables from .env file |
| `--dry-run` | Validate without executing |
| `--debug` | Enable debug output |

### Examples

```bash
/sandy play scenario.json
/sandy play scenario.json --var TITLE="Bug Fix" --var REPO="org/repo"
/sandy play scenario.json --start 2 --end 4
/sandy play scenario.json --dry-run
```

### Result Interpretation

**Success:**
```json
{
  "success": true,
  "passed_steps": 3,
  "total_steps": 3,
  "outputs": { "step_id": { "field": "value" } }
}
```

**Failure:**
```json
{
  "success": false,
  "failed_step": 2,
  "error": "Connection refused"
}
```

Recovery: `/sandy play scenario.json --start <failed_step>`

---

## list - Find Scenarios

Search for scenario files.

### Usage

Search in Sandy scenarios folder (user-created):

```bash
find ${CLAUDE_PLUGIN_ROOT}/skills/sandy/scenarios -name "*.json" -type f 2>/dev/null
```

Search in examples folder (bundled):

```bash
find ${CLAUDE_PLUGIN_ROOT}/assets/examples -name "*.json" -type f 2>/dev/null
```

### Output Format

For each scenario found, show:
- **File path**
- **Name** (from metadata.name)
- **Description** (from metadata.description)
- **Step count**

---

## new - Create Scenario

Create a new MCP scenario from template.

### Scenario Schema (v2.1)

```json
{
  "version": "2.1",
  "metadata": {
    "name": "Scenario Name",
    "description": "What this scenario does"
  },
  "variables": {
    "VAR_NAME": "default_value"
  },
  "steps": [
    {
      "step": 1,
      "id": "unique_step_id",
      "tool": "mcp__server__tool_name",
      "params": {
        "param1": "{{VAR_NAME}}"
      },
      "output": {
        "extracted_field": "$.json.path"
      }
    }
  ]
}
```

### Step Fields

| Field | Required | Description |
|-------|----------|-------------|
| `step` | Yes | Step number (1, 2, 3...) |
| `tool` | Yes | MCP tool: `mcp__server__tool` |
| `params` | Yes | Tool parameters |
| `id` | No | ID for output reference |
| `output` | No | JSONPath extractions |
| `on_error` | No | `stop`, `skip`, `retry` |

### Variable Substitution

| Syntax | Description |
|--------|-------------|
| `{{VAR}}` | Static variable |
| `{{step_id.field}}` | Previous step output |

### Common MCP Tools

**chrome-devtools:**
- `mcp__chrome-devtools__navigate_page`
- `mcp__chrome-devtools__click`
- `mcp__chrome-devtools__fill`

**supabase:**
- `mcp__supabase__query`

**github:**
- `mcp__github__create_issue`

### Instructions

1. Ask user what to automate
2. Identify MCP servers and tools
3. Generate scenario JSON
4. Save to `${CLAUDE_PLUGIN_ROOT}/skills/sandy/scenarios/<name>.json`
5. Suggest `/sandy play ${CLAUDE_PLUGIN_ROOT}/skills/sandy/scenarios/<name>.json --dry-run`

---

## Scenario Locations

| Location | Description |
|----------|-------------|
| `${CLAUDE_PLUGIN_ROOT}/skills/sandy/scenarios/` | User-created scenarios |
| `${CLAUDE_PLUGIN_ROOT}/assets/examples/` | Bundled examples |

### Bundled Examples

- `supabase-query.json` - Database query
- `multi-mcp-github-slack.json` - GitHub to Slack
- `multi-mcp-web-to-db.json` - Web scraping to DB
