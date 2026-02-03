# Sandy Scenario Schema v2.1

This document describes the JSON schema for Sandy scenarios.

## Overview

Sandy scenarios define a sequence of MCP tool calls that can be replayed without LLM inference.

## Root Schema

```json
{
  "version": "2.1",
  "metadata": { ... },
  "variables": { ... },
  "environment": { ... },
  "steps": [ ... ]
}
```

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `version` | string | Yes | Schema version (currently "2.1") |
| `metadata` | object | Yes | Scenario metadata |
| `variables` | object | No | Variable definitions |
| `environment` | object | No | Recording environment info |
| `steps` | array | Yes | Sequence of steps to execute |

## Metadata Schema

```json
{
  "name": "Scenario Name",
  "description": "What this scenario does",
  "created_at": "2025-02-03T12:00:00Z",
  "created_by": "sandy-recorder",
  "target_url": "https://example.com",
  "instruction": "Original instruction"
}
```

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Human-readable scenario name |
| `description` | string | No | Detailed description |
| `created_at` | string | No | ISO 8601 creation timestamp |
| `created_by` | string | No | Creator identifier |
| `target_url` | string | No | Primary target URL (for web scenarios) |
| `instruction` | string | No | Original user instruction |

## Variables Schema

```json
{
  "REPO": "owner/repo",
  "TITLE": "",
  "CHANNEL": "#general"
}
```

Variables with empty values are considered "required" and must be provided at runtime.

### Variable Substitution

Variables can be referenced in step params using `{{VAR_NAME}}` syntax:

```json
{
  "params": {
    "title": "{{TITLE}}",
    "repo": "{{REPO}}"
  }
}
```

## Environment Schema

```json
{
  "mcp": "chrome-devtools",
  "viewport": { "width": 1280, "height": 720 },
  "recorded_at": "2025-02-03T12:00:00Z"
}
```

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `mcp` | string | MCP server used for recording |
| `viewport` | object | Browser viewport dimensions |
| `recorded_at` | string | Recording timestamp |

## Step Schema

```json
{
  "step": 1,
  "id": "unique_id",
  "tool": "mcp__server__tool_name",
  "params": { ... },
  "output": { ... },
  "description": "What this step does",
  "wait_after": 1.0,
  "on_error": "stop",
  "retry": { ... },
  "condition": "..."
}
```

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `step` | number | Yes | Step number (execution order) |
| `tool` | string | Yes | MCP tool name in `mcp__server__tool` format |
| `params` | object | Yes | Tool parameters |
| `id` | string | No | Unique identifier for result references |
| `output` | object | No | JSONPath expressions to extract results |
| `description` | string | No | Human-readable description |
| `wait_after` | number | No | Delay after step completion (seconds) |
| `on_error` | string | No | Error handling strategy |
| `retry` | object | No | Retry configuration |
| `condition` | string | No | Conditional execution expression |

### Tool Name Format

Tool names follow the pattern: `mcp__<server>__<tool>`

Examples:
- `mcp__github__create_issue`
- `mcp__chrome-devtools__click`
- `mcp__supabase__query`
- `mcp__slack__post_message`

### Output Schema

The `output` field defines JSONPath expressions to extract values from tool results:

```json
{
  "output": {
    "issue_number": "$.number",
    "issue_url": "$.html_url",
    "full_response": "$"
  }
}
```

| JSONPath | Description |
|----------|-------------|
| `$` | Full result |
| `$.field` | Top-level field |
| `$.data.name` | Nested field |
| `$.items[0]` | Array element |
| `$.items[*].id` | All IDs in array |

Extracted values can be referenced in later steps using `{{step_id.field_name}}`:

```json
{
  "step": 2,
  "tool": "mcp__slack__post_message",
  "params": {
    "text": "Issue #{{create_issue.issue_number}} created"
  }
}
```

### Error Handling

The `on_error` field controls behavior when a step fails:

| Value | Behavior |
|-------|----------|
| `"stop"` | Stop execution (default) |
| `"skip"` | Skip to next step |
| `"retry"` | Retry with config |

### Retry Configuration

```json
{
  "retry": {
    "count": 3,
    "delay": 500
  }
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `count` | number | 3 | Maximum retry attempts |
| `delay` | number | 500 | Delay between retries (ms) |

### Conditional Execution

The `condition` field supports simple expressions:

```json
{
  "condition": "{{create_issue.number}} != \"\""
}
```

Supported operators:
- `==` - Equality
- `!=` - Inequality

## Legacy v1.1 Compatibility

Sandy supports v1.1 scenarios with `action` field instead of `tool`:

```json
{
  "version": "1.1",
  "steps": [
    {
      "step": 1,
      "action": "navigate",
      "params": { "url": "https://example.com" }
    }
  ]
}
```

Actions are automatically converted to chrome-devtools tools:

| v1.1 Action | v2.1 Tool |
|-------------|-----------|
| `navigate` | `mcp__chrome-devtools__navigate_page` |
| `click` | `mcp__chrome-devtools__click` |
| `fill` | `mcp__chrome-devtools__fill` |
| `type` | `mcp__chrome-devtools__press_key` |
| `key` | `mcp__chrome-devtools__press_key` |
| `screenshot` | `mcp__chrome-devtools__take_screenshot` |
| `wait` | `mcp__chrome-devtools__evaluate_script` |
| `wait_for_text` | `mcp__chrome-devtools__wait_for` |
| `scroll` | `mcp__chrome-devtools__evaluate_script` |
| `hover` | `mcp__chrome-devtools__hover` |

## Complete Example

```json
{
  "version": "2.1",
  "metadata": {
    "name": "Create Issue and Notify",
    "description": "Creates a GitHub issue and posts to Slack",
    "created_at": "2025-02-03T12:00:00Z"
  },
  "variables": {
    "REPO": "owner/repo",
    "TITLE": "",
    "SLACK_CHANNEL": "#dev"
  },
  "steps": [
    {
      "step": 1,
      "id": "create_issue",
      "tool": "mcp__github__create_issue",
      "params": {
        "repo": "{{REPO}}",
        "title": "{{TITLE}}",
        "body": "Automated issue creation"
      },
      "output": {
        "number": "$.number",
        "url": "$.html_url"
      },
      "description": "Create GitHub issue",
      "on_error": "stop"
    },
    {
      "step": 2,
      "tool": "mcp__slack__post_message",
      "params": {
        "channel": "{{SLACK_CHANNEL}}",
        "text": "New issue #{{create_issue.number}}: {{create_issue.url}}"
      },
      "description": "Post to Slack",
      "on_error": "skip"
    }
  ]
}
```
