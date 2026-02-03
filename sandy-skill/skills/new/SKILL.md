---
name: new
description: Create a new Sandy scenario from template. Use when user wants to create an automation, record a workflow, or build a multi-step MCP task.
allowed-tools: Read, Write
argument-hint: [scenario-name]
---

# Sandy New

Create a new MCP scenario from template.

## Usage

Create a scenario file based on user requirements.

## Scenario Schema (v2.1)

```json
{
  "version": "2.1",
  "metadata": {
    "name": "Scenario Name",
    "description": "What this scenario does",
    "created_by": "sandy"
  },
  "variables": {
    "VAR_NAME": "default_value",
    "REQUIRED_VAR": ""
  },
  "steps": [
    {
      "step": 1,
      "id": "unique_step_id",
      "tool": "mcp__server__tool_name",
      "params": {
        "param1": "{{VAR_NAME}}",
        "param2": "literal_value"
      },
      "output": {
        "extracted_field": "$.json.path"
      },
      "description": "What this step does"
    }
  ]
}
```

## Step Fields Reference

| Field | Required | Description |
|-------|----------|-------------|
| `step` | Yes | Step number (1, 2, 3...) |
| `tool` | Yes | MCP tool in `mcp__server__tool` format |
| `params` | Yes | Tool parameters (supports `{{VAR}}` substitution) |
| `id` | No | Unique ID for referencing output in later steps |
| `output` | No | JSONPath expressions to extract from result |
| `description` | No | Human-readable step description |
| `on_error` | No | `"stop"` (default), `"skip"`, or `"retry"` |
| `retry` | No | `{"count": 3, "delay": 500}` (ms) |
| `wait_after` | No | Seconds to wait after step |
| `condition` | No | Condition expression for conditional execution |

## Variable Substitution

| Syntax | Description | Example |
|--------|-------------|---------|
| `{{VAR}}` | Static variable from `variables` | `{{REPO}}` |
| `{{step_id.field}}` | Output from previous step | `{{create.id}}` |

## Common MCP Servers & Tools

### chrome-devtools
- `mcp__chrome-devtools__navigate_page` - Navigate to URL
- `mcp__chrome-devtools__click` - Click element
- `mcp__chrome-devtools__fill` - Fill input field
- `mcp__chrome-devtools__take_screenshot` - Capture screenshot

### supabase
- `mcp__supabase__query` - Execute SQL query

### github
- `mcp__github__create_issue` - Create issue
- `mcp__github__get_pull_request` - Get PR details

### slack
- `mcp__slack__send_message` - Send message to channel

## Template Examples

### Single MCP Query

```json
{
  "version": "2.1",
  "metadata": { "name": "$ARGUMENTS" },
  "steps": [
    {
      "step": 1,
      "tool": "mcp__server__tool",
      "params": {}
    }
  ]
}
```

### Multi-MCP Workflow

```json
{
  "version": "2.1",
  "metadata": { "name": "$ARGUMENTS" },
  "variables": {},
  "steps": [
    {
      "step": 1,
      "id": "source",
      "tool": "mcp__source__get_data",
      "params": {},
      "output": { "data": "$.result" }
    },
    {
      "step": 2,
      "tool": "mcp__target__send_data",
      "params": { "payload": "{{source.data}}" }
    }
  ]
}
```

## Instructions

1. Ask user what they want to automate
2. Identify required MCP servers and tools
3. Design step sequence with proper output chaining
4. Generate scenario JSON
5. Save to user-specified path or `scenarios/<name>.json`
6. Suggest testing with `/sandy:play <path> --dry-run`

## For LLM

When creating scenarios:
- Use meaningful `id` values when output is referenced later
- Set empty string `""` for required variables user must provide
- Add `description` to each step for clarity
- Consider `on_error: "skip"` for non-critical steps
- Use `wait_after` for steps that need time (e.g., page loads)
