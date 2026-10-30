# agentic-workflows

Composed deployments (docker-compose) and run proofs for n8n, Flowise, Dify,
Trigger.dev, LangGraph core, and CrewAI, all driven against one local
OpenAI-compatible model router through one MCP server.

## Layout
- `designers/<tool>/` - compose files (+ app code for langgraph/crewai).
- `mcp/agentic_mcp.py` - the single MCP server; keychain-scoped key reads.
- `results/*.json` - HTTP-level run evidence per designer (append-only).
- `scripts/` - env generation from keychain + deploy orchestration.

## Verify

```bash
grep -h "HELLO-AGENT" results/*.json    # the recorded proof tokens
```

## Rules
- No literal secrets, no tailnet IPs (`$RIG_HOST` placeholder).
- Evidence files are immutable history; add new runs instead of editing.
