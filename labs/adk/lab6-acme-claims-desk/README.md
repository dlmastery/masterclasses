# Lab 6: Acme claims desk (MCP over stdio and HTTP, OpenAPI, tool errors)

Deck: Google ADK, chapter 6. One agent (`claims_desk`) gets tools from three sources:

| Source | File | Transport | Tools the model sees |
|---|---|---|---|
| Claims MCP server | `claims_agent/claims_server.py` | stdio (child process) | `claims_get_claim`, `claims_approve_claim`, `claims_login` |
| Claims handbook MCP server | `claims_agent/handbook_server.py` | streamable HTTP `:3000/mcp` | `handbook_search_policy`, `handbook_list_topics` |
| Claims-status REST API | `claims_api.py` | HTTP `:8081`, OpenAPI | `get_claim_status` |

`purge_claim` exists on the server, but `tool_filter` hides it from the model.
Payouts over $1,000 need a human "Confirm" (`require_confirmation`).

Pinned: Python 3.11+, google-adk 2.13.0, mcp 2.3.0. The APIs were checked against the
source tags (google/adk-python v2.13.0, modelcontextprotocol/python-sdk v2.3.0). The code
was not executed in this pass, so all output below is illustrative.

## Install (once)

```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install "google-adk[mcp]==2.13.0" "mcp==2.3.0" fastapi uvicorn
cp claims_agent/.env.example claims_agent/.env       # then put your key in it
```

`google-adk[mcp]` pulls in `mcp`; the explicit pin keeps the 2.x server names.

Environment variables (`claims_agent/.env`, read by `adk web` / `adk api_server`):

| Variable | Value |
|---|---|
| `GOOGLE_GENAI_USE_ENTERPRISE` | `0` = AI Studio key, `1` = Vertex AI / Agent Platform |
| `GOOGLE_API_KEY` | your key from aistudio.google.com |
| `CLAIMS_API_KEY` | `demo-key-123` (export it in terminal 1 too, for `claims_api.py`) |

## Folder

```text
lab6-acme-claims-desk/       run every command from here
├── claims_api.py            REST service :8081 (OpenAPI slides)
├── smoke_test.py            startup check (gotcha slides)
└── claims_agent/
    ├── __init__.py          from . import agent
    ├── .env                 the three variables above
    ├── agent.py             the three toolsets (final state of the lab)
    ├── agent_errors.py      optional plugin for servers you cannot edit
    ├── claims_server.py     stdio MCP server (no terminal: McpToolset starts it)
    └── handbook_server.py   HTTP MCP server :3000
```

The repo holds the final state. The slides show excerpts in build order: server,
filter and prefix, confirmation, HTTP server, tenant headers, OpenAPI, then agent-style
errors (which add the `login` tool to the server and to `tool_filter`).

## Run

```bash
# terminal 1: the REST service (agent.py fetches its spec at import)
CLAIMS_API_KEY=demo-key-123 uvicorn claims_api:app --port 8081
# terminal 2: the handbook MCP server
python claims_agent/handbook_server.py
# terminal 3: the agent (REST API + dev UI on 127.0.0.1:8000)
adk api_server --with_ui .
```

`adk web .` also works for the stdio and OpenAPI tools. The handbook toolset reads the
tenant from `user:tenant` state and fails closed when it is missing, so create each
session with its tenant first, then open it in the UI (app `claims_agent`):

```bash
curl -s -X POST 127.0.0.1:8000/apps/claims_agent/users/broker-b/sessions \
  -H "Content-Type: application/json" \
  -d '{"state": {"user:tenant": "broker-b"}}'
```

Checks you can run alone:

```bash
python claims_agent/claims_server.py < /dev/null   # import errors show on stderr; exits at end of input
python smoke_test.py                               # needs terminal 1 up
```

Windows: use WSL, or in cmd use `set CLAIMS_API_KEY=demo-key-123` and
`python claims_agent\claims_server.py < NUL`.

## Prompts and expected output (illustrative, not executed)

```text
[user]: Approve CLM-1001 for 1800
[claims_desk]: call claims_get_claim {"claim_id": "CLM-1001"}
[claims_desk]: result {"status": "error", "message": "Session expired. Call claims_login, then call claims_get_claim again."}
[claims_desk]: call claims_login {}
[claims_desk]: call claims_get_claim {"claim_id": "CLM-1001"}
[claims_desk]: result {"status": "ok", "amount": 1800.0, ...}
[claims_desk]: call adk_request_confirmation -> Confirm dialog in the UI
Confirm -> Claim CLM-1001 approved. Payout of $1,800.00 scheduled.
Reject  -> {"error": "This tool call is rejected."}

[user]: Is towing covered?
[claims_desk]: call handbook_search_policy {"topic": "towing"}
[claims_desk]: Towing is covered up to 50 miles per incident.

[user]: Status of CLM-1001?
[claims_desk]: call get_claim_status {"claim_id": "CLM-1001"}
[claims_desk]: An adjuster (R. Patel) is assigned. Next step 2026-10-26.

$ python smoke_test.py
OK ['approve_claim', 'get_claim', 'login']
```

## Common failures

| Symptom | Cause | Fix |
|---|---|---|
| `ImportError: cannot import name 'McpToolset' from 'google.adk.tools.mcp_tool'` | `mcp` is not installed | `pip install "google-adk[mcp]==2.13.0"` |
| `No module named 'mcp.server.fastmcp'. This is mcp 2.x, where FastMCP was renamed to MCPServer ...` | v1 server code on mcp 2.x | `from mcp.server.mcpserver import MCPServer`; host and port go to `run()` |
| `ConnectionError: Failed to create MCP session: ...` | a `print()` on stdout in a stdio server, or a slow start | log to stderr; raise `timeout` |
| Log: `Agent claims_desk will run without the tools from toolset McpToolset (prefix 'claims'), which failed to load: ...` | server crash, URL without `/mcp`, timeout | alert on the line; run `smoke_test.py` |
| `Execution Error: Blocked host: 127.0.0.1` | the OpenAPI SSRF guard | `allow_private_network_access=True` for dev or internal APIs only |
| `Execution Error: Status Code: 401` | wrong header or key | header `X-API-Key`, key from `CLAIMS_API_KEY` |

## Sources

- Codelab: Getting Started with MCP, ADK and A2A, https://codelabs.developers.google.com/getting-started-mcp-a2a-adk
- adk.dev MCP tools, https://adk.dev/tools-custom/mcp-tools/
- adk.dev OpenAPI tools, https://adk.dev/tools-custom/openapi-tools/
- adk.dev tool confirmation, https://adk.dev/tools-custom/confirmation/
- ADK sample `contributing/samples/mcp/mcp_streamablehttp_agent` (tag v2.13.0)
- MCP SDK v2 migration, https://py.sdk.modelcontextprotocol.io/v2/migration/#fastmcp-renamed-to-mcpserver
