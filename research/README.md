# Sandy Research

Research documentation and materials for the Sandy project.

## Documents

| Document | Description |
|----------|-------------|
| [EXPERIMENTS.md](./EXPERIMENTS.md) | Experiment design and methodology |
| [DEVELOPMENT_PLAN.md](./DEVELOPMENT_PLAN.md) | Implementation roadmap |
| [../RESEARCH.md](../RESEARCH.md) | Full research plan (root level) |

## Research Questions

| RQ | Question |
|----|----------|
| RQ1 | How much cost/time does Procedure-level Replay save? |
| RQ2 | Which MCP tool types are most suitable for replay? |
| RQ3 | How often does Selective Reasoning occur, and at what cost? |
| RQ4 | How effectively does LLM Fallback handle unpredictable situations? |
| RQ5 | How flexible is Procedure-level abstraction compared to alternatives? |

## Key Contributions

1. **Procedure-level Replay** - Optimal balance between workflow-level and API-level reuse
2. **Selective Reasoning** - LLM as universal fallback instead of complex rule-based systems

## Structure

```
research/
├── EXPERIMENTS.md        # Experiment design
├── DEVELOPMENT_PLAN.md   # Implementation plan
├── papers/               # Paper submissions (if any)
└── README.md             # This file
```

## Related Work

See [RESEARCH.md](../RESEARCH.md) for comprehensive related work analysis including:
- AgentRR, Memento, ToolCaching comparisons
- MCP ecosystem papers
- Web automation and RPA literature
