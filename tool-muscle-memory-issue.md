## Summary

A proposal to give Claude Code the native ability to **save and replay tool sequences as scenarios**. When the agent recognizes repetitive work, it can store the pattern and replay it without LLM inference next time.

## Problem

Claude Code executes the same micro-patterns repeatedly, but has no way to remember and reuse them:

```
User: "Click the submit button"

  Claude: [LLM] → take_snapshot()      # to see the page
  Claude: [LLM] → find "submit"        # to locate element
  Claude: [LLM] → click(uid)           # to click it

User: "Click the login button"

  Claude: [LLM] → take_snapshot()      # same pattern
  Claude: [LLM] → find "login"         # same pattern
  Claude: [LLM] → click(uid)           # same pattern
```

**The agent has no ability to say**: "This is the same snapshot→find→click pattern. Let me save it and reuse it."

## Proposed Solution

Give the agent two native capabilities:

### 1. Save Scenario

When the agent recognizes a repetitive micro-pattern, it can save the sequence:

```
Claude: "I keep doing snapshot→find→click. Saving as scenario: click-element"

Saved: {
  "name": "click-element",
  "steps": [
    { "tool": "mcp__chrome-devtools__take_snapshot" },
    { "tool": "mcp__chrome-devtools__click", "params": { "uid": "{{element_uid}}" } }
  ]
}
```

### 2. Replay Scenario

Next time, the agent can replay the pattern without LLM inference:

```
User: "Click the cancel button"

Claude: "Running click-element scenario..."
  → take_snapshot()            [no LLM]
  → click("cancel-btn")        [no LLM]

Claude: [LLM] "Done. The cancel button was clicked."
```

## Why Native Support Matters

I've built a proof-of-concept called **[Sandy](https://github.com/sangkwun/sandy)** that does exactly this.

**[Video Demo](https://www.youtube.com/watch?v=owgyGYL4SVs)**

**But Sandy has limitations because it's external:**

| Problem | Why It's Hacky |
|---------|----------------|
| Indirect MCP calls | Uses Python code in a skill to call MCP servers indirectly—a workaround, not a real integration |
| Native tool mocking | Has to mock native Claude Code tools to provide equivalent functionality |
| Low instruction priority | Skill instructions compete with other prompts, so scenarios may not trigger reliably |

**With native support, the agent could:**
- Save/replay scenarios as first-class tool calls
- Use Claude Code's existing MCP connections directly
- Trigger reliably without instruction priority issues
- No mocking or workarounds needed

## More Examples: Small Composable Patterns

### Pattern: Fill and Submit Form

```
Claude: "Saving form-submit pattern"

Saved: {
  "name": "form-submit",
  "steps": [
    { "tool": "mcp__chrome-devtools__fill", "params": { "uid": "{{field}}", "value": "{{value}}" } },
    { "tool": "mcp__chrome-devtools__click", "params": { "uid": "{{submit_btn}}" } },
    { "tool": "mcp__chrome-devtools__wait_for", "params": { "text": "{{success_text}}" } }
  ]
}
```

### Pattern: Navigate and Verify

```
Saved: {
  "name": "nav-verify",
  "steps": [
    { "tool": "mcp__chrome-devtools__navigate_page", "params": { "url": "{{url}}" } },
    { "tool": "mcp__chrome-devtools__wait_for", "params": { "text": "{{expected_text}}" } },
    { "tool": "mcp__chrome-devtools__take_screenshot" }
  ]
}
```

### Pattern: Git Status Check

```
Saved: {
  "name": "git-status",
  "steps": [
    { "tool": "bash", "params": { "command": "git status" } },
    { "tool": "bash", "params": { "command": "git diff --stat" } }
  ]
}
```

**These small patterns compose into larger workflows**, and each can be reused independently.

## Token Savings

| Stage | Without Scenarios | With Scenarios |
|-------|------------------|----------------|
| Tool decisions | ~2300 tokens | 0 tokens |
| Final analysis | ~2000 tokens | ~2000 tokens |
| **Total** | **~4300** | **~2000** |

**Up to 53% reduction** for repetitive workflows.

## Proposed API

```typescript
// Agent saves a scenario
await claude.saveScenario({
  name: "pr-review",
  steps: [...],
  variables: ["pr_number"]
});

// Agent replays a scenario
const results = await claude.replayScenario("pr-review", {
  pr_number: 456
});

// Agent lists available scenarios
const scenarios = await claude.listScenarios();
```

## Open Questions

1. **Storage**: Where to store scenarios? Per-project? Global?
   - *Initial thought*: `.claude/scenarios/` in project, `~/.claude/scenarios/` for global

2. **Sharing**: Can scenarios be shared across users/teams?
   - *Initial thought*: Export/import as JSON files

3. **Versioning**: What if MCP tools change?
   - *Initial thought*: Validate on replay, warn if tool signature changed

4. **Security**: Sensitive data in scenarios?
   - *Initial thought*: Store variable placeholders only, never actual values

## Summary

**The ask is simple:**

Give the agent the ability to save and replay tool sequences natively.

Sandy proves the concept works. Now it needs to be a first-class feature in Claude Code—not an external hack.

I'd love to hear the team's thoughts!
