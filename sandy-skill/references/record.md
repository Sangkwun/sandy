# Sandy Record Mode (Phase 2)

> This prompt will be used in Phase 2 to enable AI agents to record their actions as replayable scenarios.

## Instructions

When the user asks you to record an action sequence, follow these guidelines:

### 1. Acknowledge Recording Mode

Let the user know you're in recording mode and will capture all MCP tool calls.

### 2. Perform the Task

Execute the requested task normally, making the necessary MCP tool calls.

### 3. Track Tool Calls

For each MCP tool call, record:
- The tool name (in `mcp__server__tool` format)
- The parameters passed
- The result (for output extraction)

### 4. Identify Variables

Look for values that should be parameterized:
- User-specific data (names, IDs)
- URLs that might change
- Timestamps
- Configuration values

Replace these with `{{VARIABLE_NAME}}` placeholders.

### 5. Extract Outputs

When a step's result is used by later steps:
- Assign an `id` to the step
- Define `output` with JSONPath expressions
- Reference in later steps as `{{step_id.field}}`

### 6. Generate Scenario

Create a v2.1 scenario JSON with:
- Meaningful metadata (name, description)
- All necessary variables
- Step sequence with proper error handling

### 7. Save the Scenario

Save the scenario to the appropriate location:
- User-specified path, or
- `scenarios/` directory with descriptive name

## Example Output

After recording a "create GitHub issue" task:

```json
{
  "version": "2.1",
  "metadata": {
    "name": "Create GitHub Issue",
    "description": "Creates an issue in a GitHub repository",
    "created_at": "2025-02-03T12:00:00Z",
    "created_by": "sandy-recorder"
  },
  "variables": {
    "REPO": "",
    "TITLE": "",
    "BODY": ""
  },
  "steps": [
    {
      "step": 1,
      "id": "create_issue",
      "tool": "mcp__github__create_issue",
      "params": {
        "repo": "{{REPO}}",
        "title": "{{TITLE}}",
        "body": "{{BODY}}"
      },
      "output": {
        "number": "$.number",
        "url": "$.html_url"
      },
      "description": "Create the GitHub issue"
    }
  ]
}
```

## Notes

- Always prefer explicit tool names over legacy actions
- Use meaningful step IDs when output extraction is needed
- Set appropriate `on_error` handling for each step
- Include `wait_after` for steps that need time to complete
