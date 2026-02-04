# Example Scenarios

Reference scenarios demonstrating Sandy's capabilities.

## Single MCP

| File | MCP Server | Description |
|------|------------|-------------|
| `supabase-query.json` | supabase | Database query with output extraction |
| `chrome-test.json` | chrome-devtools | Page listing and snapshot |
| `web-navigate.json` | chrome-devtools | URL navigation |
| `filesystem-test.json` | filesystem | File read/write operations |
| `memory-test.json` | memory | Knowledge graph storage |
| `fetch-test.json` | fetch | HTTP requests |

## Multi-MCP

| File | MCP Servers | Description |
|------|-------------|-------------|
| `multi-mcp-github-slack.json` | github → slack | Create issue, notify Slack |
| `multi-mcp-web-to-db.json` | chrome-devtools → supabase | Scrape page, save to DB |
| `multi-mcp-db-report-slack.json` | supabase → slack | Query stats, post report |
| `multi-mcp-pr-review-notify.json` | github → slack | PR info, review, notify |
| `multi-mcp-form-submit-log.json` | chrome-devtools → supabase | Fill form, log to DB |

## Usage

```bash
# Run directly
python scripts/play.py assets/examples/supabase-query.json --json

# With variables
python scripts/play.py assets/examples/multi-mcp-github-slack.json \
  --var REPO="owner/repo" \
  --var ISSUE_TITLE="Bug report" \
  --json
```

## Schema Reference

See [references/schema.md](../../references/schema.md) for full JSON schema documentation.
