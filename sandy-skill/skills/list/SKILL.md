---
name: list
description: List available Sandy scenarios in the project. Use when user asks what scenarios exist, wants to see available automations, or needs to find a scenario to run.
allowed-tools: Bash, Read, Glob
---

# Sandy List

List available MCP scenarios in the project.

## Usage

Search for scenario files:

```bash
find ${CLAUDE_PLUGIN_ROOT}/assets/examples -name "*.json" -type f 2>/dev/null | head -20
```

Also check common project locations:

```bash
find . -path "./.venv" -prune -o -path "./node_modules" -prune -o -name "*.json" -type f -print 2>/dev/null | xargs grep -l '"version".*"2\.' 2>/dev/null | head -20
```

## Output Format

For each scenario found, show:
- **File path**
- **Name** (from metadata.name)
- **Description** (from metadata.description)
- **Step count**

## Example Output

```
Available Scenarios:

1. assets/examples/supabase-query.json
   Name: Query Supabase Database
   Steps: 1

2. assets/examples/multi-mcp-github-slack.json
   Name: GitHub to Slack Notification
   Description: Create GitHub issue and notify Slack
   Steps: 2

3. scenarios/my-workflow.json
   Name: My Custom Workflow
   Steps: 5
```

## For LLM

After listing scenarios:
- Suggest `/sandy:play <path>` to run one
- Offer to show scenario details with Read tool
- Suggest `/sandy:new` if user wants to create a new one
