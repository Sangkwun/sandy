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
    "delay": 500,
    "condition": "element_not_found"
  }
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `count` | number | 3 | Maximum retry attempts |
| `delay` | number | 500 | Delay between retries (ms) |
| `condition` | string | null | Only retry if error message contains this string |

The `condition` field enables selective retry - only retry when the error matches:

```json
{
  "step": 2,
  "tool": "mcp__chrome-devtools__click",
  "params": { "uid": "submit-btn" },
  "on_error": "retry",
  "retry": {
    "count": 3,
    "delay": 500,
    "condition": "not found"
  }
}
```

This step will only retry if the error contains "not found". Other errors (like network failures) will stop immediately.

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

## UI Interaction Best Practices

When creating scenarios that interact with web pages (using `chrome-devtools` MCP), follow these guidelines for stable and maintainable automation:

### Use UID-based Selection (Recommended)

Always prefer element identifiers (`uid`) over coordinate-based interactions:

```json
{
  "step": 1,
  "tool": "mcp__chrome-devtools__click",
  "params": {
    "uid": "submit-button"
  }
}
```

### Avoid Coordinate-based Clicks

**Do NOT use coordinate-based parameters** like `x`, `y`, or `coordinates`:

```json
// ❌ Bad - Fragile, breaks on layout changes
{
  "params": {
    "x": 150,
    "y": 320
  }
}

// ✅ Good - Stable, works across viewports
{
  "params": {
    "uid": "login-btn"
  }
}
```

### Why Avoid Coordinates?

| Issue | Impact |
|-------|--------|
| Viewport changes | Different screen sizes break the scenario |
| Layout shifts | Any UI update invalidates coordinates |
| Responsiveness | Mobile/desktop views differ |
| Maintenance | Hard to debug which element was targeted |
| Reproducibility | May work on one machine but fail on another |

### Recommended Interaction Patterns

| Action | Tool | Params |
|--------|------|--------|
| Click element | `click` | `{ "uid": "element-id" }` |
| Fill input | `fill` | `{ "uid": "input-id", "value": "text" }` |
| Submit form | `fill_form` | `{ "elements": [...] }` |
| Wait for element | `wait_for` | `{ "text": "Expected text" }` |
| Take snapshot | `take_snapshot` | `{}` (get UIDs from snapshot) |

### Finding Stable UIDs

1. Use `take_snapshot` to get the current page's accessibility tree
2. Look for semantic IDs, data-testid attributes, or ARIA labels
3. Prefer IDs that are unlikely to change (e.g., `login-form` over `div-47`)

## Sandy Internal Tools

Sandy provides built-in tools that don't require MCP servers. These tools use the `sandy__` prefix.

### sandy__wait

Wait for a specified duration.

```json
{
  "step": 1,
  "tool": "sandy__wait",
  "params": { "duration": 2.0 }
}
```

| Param | Type | Description |
|-------|------|-------------|
| `duration` | number | Wait time in seconds |

### sandy__log

Log a message (useful for debugging).

```json
{
  "step": 2,
  "tool": "sandy__log",
  "params": { "message": "Step completed" }
}
```

| Param | Type | Description |
|-------|------|-------------|
| `message` | string | Message to log |

### sandy__wait_for_element

Wait for an element to appear on the page. Requires `chrome-devtools` MCP server.

```json
{
  "step": 3,
  "tool": "sandy__wait_for_element",
  "params": {
    "selector": "button.submit",
    "timeout": 10,
    "interval": 0.5
  }
}
```

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `selector` | string | (required) | CSS selector to wait for |
| `timeout` | number | 10 | Maximum wait time in seconds |
| `interval` | number | 0.5 | Polling interval in seconds |
| `mcp_server` | string | "chrome-devtools" | MCP server to use for DOM access |

This tool is more efficient than writing custom JavaScript retry loops:

```json
// ❌ Before: Manual retry in JavaScript
{
  "tool": "mcp__chrome-devtools__evaluate_script",
  "params": {
    "function": "async () => { for(let i=0; i<10; i++) { const el = document.querySelector('button'); if(el) return true; await new Promise(r => setTimeout(r, 500)); } throw new Error('Not found'); }"
  }
}

// ✅ After: Built-in wait
{
  "tool": "sandy__wait_for_element",
  "params": { "selector": "button", "timeout": 5 }
}
```

### sandy__wait_until

Wait until a JavaScript expression evaluates to true. Requires `chrome-devtools` MCP server.

```json
{
  "step": 4,
  "tool": "sandy__wait_until",
  "params": {
    "expression": "document.querySelector('.loading') === null",
    "timeout": 30,
    "interval": 0.5
  }
}
```

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `expression` | string | (required) | JavaScript expression that should evaluate to true |
| `timeout` | number | 30 | Maximum wait time in seconds |
| `interval` | number | 0.5 | Polling interval in seconds |
| `mcp_server` | string | "chrome-devtools" | MCP server to use for script execution |

Use cases:
- Wait for loading spinner to disappear: `document.querySelector('.loading') === null`
- Wait for API response: `window.apiData !== undefined`
- Wait for element count: `document.querySelectorAll('.item').length >= 5`

### sandy__append_file

Append data to a file in various formats. Useful for collecting scraped data or logging results.

```json
{
  "step": 3,
  "tool": "sandy__append_file",
  "params": {
    "path": "/tmp/products.jsonl",
    "format": "jsonl",
    "data": "{{scrape_result.items}}"
  }
}
```

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `path` | string | Yes | Target file path |
| `format` | string | No | Output format: `jsonl` (default), `csv`, `json` |
| `data` | any | Yes | Data to append (single item or array) |

#### Supported Formats

| Format | Behavior |
|--------|----------|
| `jsonl` | Append each item as a single JSON line (JSON Lines format) |
| `csv` | Append as CSV rows; header is written on first append only |
| `json` | Append to JSON array (reads entire file, modifies, writes back) |

#### Example: Web Scraping to File

```json
{
  "version": "2.1",
  "metadata": { "name": "Scrape Products to File" },
  "variables": {
    "TARGET_URL": "https://shop.example.com/products",
    "OUTPUT_PATH": "/tmp/products.jsonl"
  },
  "steps": [
    {
      "step": 1,
      "tool": "mcp__chrome-devtools__navigate_page",
      "params": { "url": "{{TARGET_URL}}" },
      "wait_after": 2.0
    },
    {
      "step": 2,
      "id": "scrape",
      "tool": "mcp__chrome-devtools__evaluate_script",
      "params": {
        "function": "() => Array.from(document.querySelectorAll('.product')).map(el => ({ name: el.querySelector('.name')?.innerText, price: el.querySelector('.price')?.innerText }))"
      },
      "output": { "items": "$" }
    },
    {
      "step": 3,
      "tool": "sandy__append_file",
      "params": {
        "path": "{{OUTPUT_PATH}}",
        "format": "jsonl",
        "data": "{{scrape.items}}"
      }
    }
  ]
}
```

## Claude Native Tools

Sandy provides implementations of Claude Code's native tools that don't require MCP servers. These tools use the `claude__` prefix and behave identically to their Claude Code counterparts.

### claude__read

Read file contents with optional line offset and limit.

```json
{
  "step": 1,
  "id": "read_config",
  "tool": "claude__read",
  "params": {
    "file_path": "/path/to/file.txt",
    "offset": 10,
    "limit": 50
  },
  "output": { "content": "$.content" }
}
```

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `file_path` | string | Yes | Absolute path to the file |
| `offset` | number | No | Line number to start reading from (1-based) |
| `limit` | number | No | Number of lines to read |

### claude__write

Write content to a file. Creates parent directories if needed.

```json
{
  "step": 2,
  "tool": "claude__write",
  "params": {
    "file_path": "/path/to/output.txt",
    "content": "File content here"
  }
}
```

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `file_path` | string | Yes | Absolute path to the file |
| `content` | string | Yes | Content to write |

### claude__edit

Edit a file by replacing a string.

```json
{
  "step": 3,
  "tool": "claude__edit",
  "params": {
    "file_path": "/path/to/file.py",
    "old_string": "def old_function():",
    "new_string": "def new_function():",
    "replace_all": false
  }
}
```

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `file_path` | string | Yes | Absolute path to the file |
| `old_string` | string | Yes | Text to replace (must be unique unless replace_all) |
| `new_string` | string | Yes | Replacement text |
| `replace_all` | boolean | No | Replace all occurrences (default: false) |

### claude__glob

Find files matching a glob pattern.

```json
{
  "step": 4,
  "id": "find_tests",
  "tool": "claude__glob",
  "params": {
    "pattern": "**/*_test.py",
    "path": "/project/src"
  },
  "output": { "files": "$.files" }
}
```

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `pattern` | string | Yes | Glob pattern (e.g., `**/*.py`) |
| `path` | string | No | Directory to search in (default: current directory) |

### claude__grep

Search file contents with regex.

```json
{
  "step": 5,
  "id": "search",
  "tool": "claude__grep",
  "params": {
    "pattern": "def\\s+\\w+\\(",
    "path": "/project/src",
    "glob": "*.py",
    "output_mode": "files_with_matches"
  },
  "output": { "files": "$.files" }
}
```

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `pattern` | string | Yes | Regex pattern to search for |
| `path` | string | No | File or directory to search |
| `glob` | string | No | Glob pattern to filter files |
| `output_mode` | string | No | `content`, `files_with_matches` (default), or `count` |
| `context` | number | No | Lines of context around matches |
| `head_limit` | number | No | Limit number of results |
| `case_insensitive` | boolean | No | Case insensitive search |

### claude__bash

Execute a shell command.

```json
{
  "step": 6,
  "id": "run_tests",
  "tool": "claude__bash",
  "params": {
    "command": "pytest tests/ -v",
    "timeout": 300000
  },
  "output": {
    "stdout": "$.stdout",
    "exit_code": "$.exit_code"
  }
}
```

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `command` | string | Yes | Command to execute |
| `timeout` | number | No | Timeout in milliseconds (default: 120000) |

### claude__web_fetch

Fetch content from a URL.

```json
{
  "step": 7,
  "id": "fetch_api",
  "tool": "claude__web_fetch",
  "params": {
    "url": "https://api.example.com/data"
  },
  "output": { "content": "$.content" }
}
```

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `url` | string | Yes | URL to fetch |

**Note:** Requires `httpx` package. HTML content is automatically converted to markdown if `markdownify` is installed.

### claude__notebook_edit

Edit a Jupyter notebook cell.

```json
{
  "step": 8,
  "tool": "claude__notebook_edit",
  "params": {
    "notebook_path": "/path/to/notebook.ipynb",
    "cell_id": "abc123",
    "new_source": "print('Hello World')",
    "edit_mode": "replace"
  }
}
```

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `notebook_path` | string | Yes | Absolute path to the notebook |
| `new_source` | string | Yes | New source content |
| `cell_id` | string | Depends | Cell ID (required for replace/delete) |
| `cell_type` | string | Depends | `code` or `markdown` (required for insert) |
| `edit_mode` | string | No | `replace` (default), `insert`, or `delete` |

**Note:** Requires `nbformat` package.

### Example: Mixed MCP and Claude Tools

```json
{
  "version": "2.1",
  "metadata": { "name": "Test and Report" },
  "variables": {
    "TEST_DIR": "/project/tests",
    "REPORT_CHANNEL": "#ci"
  },
  "steps": [
    {
      "step": 1,
      "id": "find_tests",
      "tool": "claude__glob",
      "params": { "pattern": "**/*_test.py", "path": "{{TEST_DIR}}" },
      "output": { "count": "$.count" }
    },
    {
      "step": 2,
      "id": "run_tests",
      "tool": "claude__bash",
      "params": { "command": "pytest {{TEST_DIR}} --json-report" },
      "output": { "exit_code": "$.exit_code" }
    },
    {
      "step": 3,
      "id": "read_report",
      "tool": "claude__read",
      "params": { "file_path": "/project/.report.json" },
      "output": { "content": "$.content" }
    },
    {
      "step": 4,
      "tool": "mcp__slack__post_message",
      "params": {
        "channel": "{{REPORT_CHANNEL}}",
        "text": "Tests completed: {{find_tests.count}} files, exit code: {{run_tests.exit_code}}"
      }
    }
  ]
}
```

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

## CLI Debug Options

The `play.py` CLI provides several debug options for troubleshooting scenarios.

### Screenshot on Failure

Automatically capture screenshots when a step fails. Requires `chrome-devtools` MCP server.

```bash
python play.py scenario.json --screenshot-on-failure --screenshot-dir ./debug-screenshots
```

| Option | Default | Description |
|--------|---------|-------------|
| `--screenshot-on-failure` | false | Enable automatic screenshot capture on step failure |
| `--screenshot-dir` | `./screenshots` | Directory to save failure screenshots |

Screenshots are saved with the pattern: `step{N}_failure_{timestamp}.png`

### Debug Mode

Enable verbose debug output:

```bash
python play.py scenario.json --debug --include-results on_failure
```

| Option | Description |
|--------|-------------|
| `--debug` | Show detailed execution logs including params and results |
| `--include-results true` | Always include MCP raw results in output |
| `--include-results on_failure` | Include results only when step fails |
| `--include-results false` | Never include results (default, saves tokens) |

### Partial Execution

Run specific steps for debugging:

```bash
# Run only steps 3-5
python play.py scenario.json --start 3 --end 5

# Dry run (validate without executing)
python play.py scenario.json --dry-run
```
