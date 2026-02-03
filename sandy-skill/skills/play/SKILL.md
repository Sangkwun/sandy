---
name: play
description: Execute MCP scenarios deterministically without LLM. Use when user wants to run a scenario, execute automation, replay recorded sequences, or run multi-step MCP workflows.
allowed-tools: Bash, Read
argument-hint: [scenario.json] [--start N] [--end N] [--var KEY=VALUE]
---

# Sandy Play

Execute MCP scenarios without LLM inference (deterministic replay).

## Usage

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/play.py $ARGUMENTS --json
```

## Arguments

| Argument | Description |
|----------|-------------|
| `scenario.json` | Path to scenario file (required) |
| `--start N` | Start from step N (inclusive) |
| `--end N` | End at step N (inclusive) |
| `--var KEY=VALUE` | Set variable (repeatable) |
| `--env FILE` | Load variables from .env file |
| `--dry-run` | Validate without executing |
| `--debug` | Enable debug output |
| `--include-results MODE` | Include MCP results: `true`, `false`, `on_failure` |

## Examples

```bash
# Basic execution
/sandy:play scenario.json

# With variables
/sandy:play scenario.json --var TITLE="Bug Fix" --var REPO="org/repo"

# Partial execution (steps 2-4)
/sandy:play scenario.json --start 2 --end 4

# Resume from step 3 after failure
/sandy:play scenario.json --start 3

# Dry run validation
/sandy:play scenario.json --dry-run
```

## Example Scenarios

See `${CLAUDE_PLUGIN_ROOT}/assets/examples/` for ready-to-use scenarios:

- `supabase-query.json` - Database query
- `multi-mcp-github-slack.json` - GitHub to Slack notification
- `multi-mcp-web-to-db.json` - Web scraping to database

## Result Format

Returns JSON with:
- `success` - Overall execution status
- `passed_steps` / `total_steps` - Progress
- `outputs` - Extracted values via JSONPath
- `error` - Failure reason (if any)
- `step_results` - Per-step details

## Scenario Format (v2.1)

```json
{
  "version": "2.1",
  "metadata": { "name": "My Scenario" },
  "variables": { "VAR": "value" },
  "steps": [
    {
      "step": 1,
      "id": "step_id",
      "tool": "mcp__server__tool",
      "params": { "key": "{{VAR}}" },
      "output": { "result": "$.data" }
    }
  ]
}
```

## Variable Substitution

| Syntax | Description |
|--------|-------------|
| `{{VAR}}` | Static variable |
| `{{step_id.field}}` | Runtime result reference |

## Dependencies

Requires Python 3.10+ with:
```bash
pip install mcp jsonpath-ng python-dotenv
```

## For LLM: Result Interpretation

### On Success (`success: true`)

```json
{
  "success": true,
  "passed_steps": 3,
  "total_steps": 3,
  "outputs": {
    "step_id": { "field": "extracted_value" }
  }
}
```

**Next actions:**
- Use `outputs` values for subsequent tasks
- Report completion to user
- Chain with other tools if needed

### On Failure (`success: false`)

```json
{
  "success": false,
  "failed_step": 2,
  "error": "Connection refused",
  "passed_steps": 1,
  "total_steps": 3
}
```

**Recovery actions:**
1. Check `error` for root cause
2. If transient error: retry with `/sandy:play scenario.json --start <failed_step>`
3. If config error: check MCP server availability
4. Use `--include-results on_failure` for detailed debugging

### Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `Server not found` | MCP server not configured | Check config file |
| `Tool call failed` | Invalid parameters | Review scenario params |
| `Connection refused` | Server not running | Start the MCP server |
| `Missing variable` | Required var not provided | Add `--var KEY=VALUE` |
