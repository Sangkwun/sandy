---
name: sandy
description: MCP Scenario Player - Record & Play MCP tool calls without LLM. Supports play (execute), list (find scenarios), and new (test & record workflow) subcommands.
allowed-tools: Bash, Read, Write, Glob
argument-hint: <play|list|new> [options]
---

# Sandy - MCP Scenario Player

Execute, list, or record MCP scenarios without LLM inference.

## Subcommands

| Command | Description |
|---------|-------------|
| `play <scenario.json>` | Execute a scenario |
| `list` | Find available scenarios |
| `new <name>` | Test & record a workflow as scenario |

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
| `--json` | Output result as JSON |

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

Search in project scenarios folder (user-created):

```bash
find .sandy/scenarios -name "*.json" -type f 2>/dev/null
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

## new - Test & Record Scenario

Test workflows that users request or that would benefit from repeated reuse, then save the tested process as a replayable scenario.

**Usage:** `/sandy new <name>` where `<name>` is the scenario identifier (used as filename and metadata name).

**Why test first?** Scenarios created without testing may not work. By executing the workflow first, you ensure the scenario is based on a verified, working process.

### When to Use

- User explicitly requests automation (`/sandy new`)
- A workflow will be repeated multiple times
- Consistent, deterministic execution is needed
- Reducing LLM inference costs for repetitive tasks

### Instructions

**CRITICAL: You MUST test the workflow first, then create the scenario from the tested process.**

1. **Understand** - Ask user what workflow they want to automate
2. **Test** - Execute the workflow by actually performing the requested task
3. **Record** - Track all MCP tool calls made during the test:
   - Tool name (e.g., `mcp__chrome-devtools__click`)
   - Parameters used
   - Results received
4. **Parameterize** - Identify values that should become variables:
   - User inputs (names, IDs, search terms)
   - Environment-specific values (URLs, paths)
   - Data that changes between runs
5. **Generate** - Create scenario JSON from the recorded process
6. **Save** - Write to `.sandy/scenarios/<name>.json` in the current project (create directories if needed)
7. **Verify** - Suggest `/sandy play .sandy/scenarios/<name>.json --dry-run`

**DO NOT** write scenarios without first testing the workflow. The scenario must reflect actual, verified tool calls.

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

---

## Scenario Locations

| Location | Description |
|----------|-------------|
| `.sandy/scenarios/` | Project-local scenarios (user-created) |
| `${CLAUDE_PLUGIN_ROOT}/assets/examples/` | Bundled examples |

### Bundled Examples

- `supabase-query.json` - Database query
- `multi-mcp-github-slack.json` - GitHub to Slack
- `multi-mcp-web-to-db.json` - Web scraping to DB

### Note

User-created scenarios are stored in the project directory (`.sandy/scenarios/`), not in the plugin folder. This ensures scenarios are:
- Version controlled with the project
- Not lost during plugin updates
- Shareable with team members
