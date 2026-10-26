# Hands-on labs: ADK tools and protocols (MCP, A2A, Skills, Plugins, Confirmation, Auth, OpenAPI, Built-ins)

Research date: 2026-10-23. Deck: "Building agents with Google ADK 2.0" (google-adk 2.13.0).
Scope of this file: 9 runnable labs for the tools/protocols chapter. Each lab names a business scenario, gives full code, the commands to run it, an output sample, the key lines, real error messages with fixes, one best practice and an extension.

**How this file was verified.** No code here was run: pip/PyPI downloads are blocked on this machine. Every import path, class name, parameter and default was read from library **source** at these exact tags:
- `google/adk-python` at tag **v2.13.0** (commit `d68ca857`, 2026-10-23), shallow-cloned
- `modelcontextprotocol/python-sdk` at tag **v2.3.0**
- `a2aproject/a2a-python` at tag **v1.2.3** (raw file)
- `google/adk-docs` main (2026-10-23)

File paths below are relative to `src/google/adk/` unless noted. All "Expected output" blocks are **illustrative**: they are shaped like ADK's own fixtures and log formats, not captured from a run. Anything I could not verify is marked **[UNVERIFIED]**.

This file does not repeat `research/05-tools-mcp-a2a.md`, which covers the taxonomy, the protocol background and the deploy commands. It adds runnable code and the 2.13-specific gotchas that file does not have.

---

## 0. Version pins (PyPI JSON, read 2026-10-23)

| Package | Latest | Released | Note |
|---|---|---|---|
| `google-adk` | **2.13.0** | 2026-10-23 | `requires_python >=3.11` (not 3.10 as older docs say) |
| `mcp` | **2.3.0** | 2026-10-02 | ADK pins `mcp>=1.24,<3` (pyproject `optional-dependencies.mcp`) |
| `a2a-sdk` | **1.2.3** | 2026-10-19 | ADK extra `a2a` pins `a2a-sdk[http-server]>=0.3.4,<2` |
| `google-genai` | 2.33.0 | 2026-10-23 | ADK pins `>=2.30,<3` |
| `uvicorn` | 0.54.0 | 2026-09-25 | base dependency of ADK |

Three install facts that break old tutorials:
1. **MCP is no longer in the base install.** In 2.13.0 `mcp` sits in the `mcp` extra (`pyproject.toml`, `optional-dependencies.mcp = ["aiohttp!=3.14.2", "anyio>=4.9,<5", "mcp>=1.24,<3"]`). Install `pip install "google-adk[mcp]==2.13.0"`. **[UNVERIFIED: the release that moved it out of base. The CHANGELOG has no explicit entry.]**
2. **MCP Python SDK 2.x renamed `FastMCP`.** It is now `from mcp.server.mcpserver import MCPServer`. `mcp/server/fastmcp.py` in v2.3.0 only raises: *"No module named 'mcp.server.fastmcp'. This is mcp 2.x, where FastMCP was renamed to MCPServer (from mcp.server.mcpserver import MCPServer) and other APIs changed; see the migration guide at https://py.sdk.modelcontextprotocol.io/v2/migration/#fastmcp-renamed-to-mcpserver or pin 'mcp<2' to keep running v1 code."* In 2.x, `host`/`port` go to `run()`, not the constructor (`mcpserver/server.py` L386-402). ADK resolves both majors in `dependencies/_mcp.py`.
3. **Default model.** `LlmAgent.DEFAULT_MODEL = 'gemini-3.5-flash'` (`agents/llm_agent.py` L289). `adk create` offers `gemini-3.5-flash` and `gemini-3.8-flash` (`cli/cli_create.py` L172-181). The labs pin `gemini-3.5-flash` explicitly.

Common env (`.env` next to each agent package; same format `adk create` writes, `cli/cli_create.py` L130-141):
```bash
GOOGLE_GENAI_USE_ENTERPRISE=0        # 0 = Gemini API key; 1 = Agent Platform (Vertex AI)
GOOGLE_API_KEY=your-key
# for Agent Platform instead: GOOGLE_GENAI_USE_ENTERPRISE=1, GOOGLE_CLOUD_PROJECT=..., GOOGLE_CLOUD_LOCATION=us-central1
```
`google-genai` still reads the legacy `GOOGLE_GENAI_USE_VERTEXAI`. If both are set with conflicting values it warns and `GOOGLE_GENAI_USE_ENTERPRISE` wins (`google/genai/_api_client.py` L871-890).

Stability in 2.13 (`features/_feature_registry.py`):
- **STABLE**: `SKILL_TOOLSET`, `TOOL_CONFIRMATION`, `AUTHENTICATED_FUNCTION_TOOL`, `PLUGGABLE_AUTH`.
- **EXPERIMENTAL** (on by default): `MCP_AGENT_SERVER` (`to_mcp_server`).
- **EXPERIMENTAL, off by default**: `_MCP_MODERN_PROTOCOL` and `SKILL_LIFECYCLE`. Enable the latter with `ADK_ENABLE_SKILL_LIFECYCLE=1`.
- A2A uses its own `@a2a_experimental` decorator (`a2a/experimental.py`).
- The adk.dev pages for Skills and Confirmation still say "Experimental". The source is newer than the docs; teach the source.

Lab map (one scenario per lab):

| # | Lab | Scenario | Key API |
|---|---|---|---|
| 1 | MCP over stdio | Insurance claims desk | `McpToolset` + `StdioConnectionParams`, `tool_filter`, `tool_name_prefix`, toolset `require_confirmation` |
| 2 | MCP over streamable HTTP | Multi-tenant HR policy search | `StreamableHTTPConnectionParams`, `header_provider`, `tool_list_cache_ttl_seconds` |
| 3 | Agent as MCP server | Refund-policy agent used from Claude Code / IDEs | `to_mcp_server(...).run(transport="streamable-http")` |
| 4 | A2A | Support triage delegating to a remote refund agent | `to_a2a`, agent card, `RemoteA2aAgent` |
| 5 | Agent Skills | Refund-policy skill with reference + script | `SkillToolset`, `load_skill_from_dir`, `adk_additional_tools` |
| 6 | Plugins | Global refund-limit guard + PII redaction + self-healing retries | `BasePlugin`, `App(plugins=...)`, `ReflectAndRetryToolPlugin` |
| 7 | Confirmation + long-running | Refund approvals: inline yes/no, then a manager ticket | `require_confirmation`, `adk_request_confirmation`, `LongRunningFunctionTool` |
| 8 | OpenAPI + auth | Order-status REST API with an API key; OAuth flow | `OpenAPIToolset`, `token_to_scheme_credential`, `allow_private_network_access`, `adk_request_credential` |
| 9 | Built-ins | Competitor price research with search + code | `google_search`, `BuiltInCodeExecutor`, `AgentTool`, Gemini 3 rule |

---

## Lab 1: Insurance claims desk, a local MCP server over stdio

> **VERIFIED against google-adk 2.13.0 source (tag v2.13.0, commit d68ca857), re-checked by the verifier on 2026-10-23: every import path, class/function name and parameter in the code.** Also verified against mcp 2.3.0 source (`MCPServer`, `run()` defaults, `fastmcp.py` error text). Still [UNVERIFIED]: which ADK release moved `mcp` into the extra. Expected-output blocks stay illustrative (nothing was executed).

**Goal.** Build a Python MCP server for claims (stdio) and connect an ADK agent to it. Expose only safe tools, namespace them, and require a human "yes" for payouts above $1,000.

**Prerequisites.**
```bash
python -m venv .venv && source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install "google-adk[mcp]==2.13.0" "mcp==2.3.0"
# .env in claims_agent/: GOOGLE_GENAI_USE_ENTERPRISE=0, GOOGLE_API_KEY=...
```
Layout: `claims_agent/__init__.py` (`from . import agent`), `claims_agent/agent.py`, `claims_agent/claims_server.py`.

**Code: `claims_agent/claims_server.py`** (MCP SDK 2.3.0)
```python
import logging
import sys

from mcp.server.mcpserver import MCPServer

# stdio servers must never write to stdout: it carries the JSON-RPC stream.
logging.basicConfig(stream=sys.stderr, level=logging.INFO)
mcp = MCPServer("claims-server")

CLAIMS = {
    "CLM-1001": {"policy": "AUTO-77", "status": "open", "amount": 1800.0},
    "CLM-1002": {"policy": "HOME-12", "status": "open", "amount": 420.0},
}


@mcp.tool()
def get_claim(claim_id: str) -> dict:
    """Return policy, status and claimed amount (USD) for a claim id like CLM-1001."""
    claim = CLAIMS.get(claim_id)
    if claim is None:
        return {"status": "error", "message": f"Unknown claim {claim_id}"}
    return {"status": "ok", "claim_id": claim_id, **claim}


@mcp.tool()
def approve_claim(claim_id: str, approved_amount: float) -> dict:
    """Approve a claim and schedule a payout of approved_amount USD."""
    claim = CLAIMS[claim_id]
    claim["status"] = "approved"
    logging.info("approved %s for %.2f", claim_id, approved_amount)
    return {"status": "ok", "claim_id": claim_id, "paid": approved_amount}


@mcp.tool()
def purge_claim(claim_id: str) -> dict:
    """Permanently delete a claim record (admin only)."""
    CLAIMS.pop(claim_id, None)
    return {"status": "ok"}


if __name__ == "__main__":
    mcp.run()  # transport defaults to "stdio"
```

**Code: `claims_agent/agent.py`**
```python
import pathlib
import sys

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import McpToolset, StdioConnectionParams
from mcp import StdioServerParameters

SERVER = pathlib.Path(__file__).parent / "claims_server.py"


def payout_needs_human(**kwargs) -> bool:
    """Toolset-wide confirmation rule: only big payouts need a human."""
    return float(kwargs.get("approved_amount", 0)) > 1000


claims_tools = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command=sys.executable,           # same venv as the agent
            args=[str(SERVER)],
        ),
        timeout=10.0,                          # default is 5.0 s
    ),
    tool_filter=["get_claim", "approve_claim"],  # purge_claim never reaches the model
    tool_name_prefix="claims",                 # model sees claims_get_claim, ...
    require_confirmation=payout_needs_human,
)

root_agent = LlmAgent(
    name="claims_desk",
    model="gemini-3.5-flash",
    instruction=(
        "You help claims adjusters. Look up a claim before approving it. "
        "Never approve more than the claimed amount."
    ),
    tools=[claims_tools],
)
```

**Run.**
```bash
adk web .          # open http://localhost:8000, pick claims_desk
# or headless:
adk run claims_agent
```
Prompts: `What is the status of CLM-1002?`, then `Approve CLM-1001 for 1800`.

**Expected output (illustrative).**
```text
[user]: Approve CLM-1001 for 1800
[claims_desk]: function_call claims_get_claim {"claim_id": "CLM-1001"}
[claims_desk]: function_response {"status": "ok", "claim_id": "CLM-1001", "policy": "AUTO-77", "status": "open", "amount": 1800.0}
[claims_desk]: function_call adk_request_confirmation {"originalFunctionCall": {"name": "claims_approve_claim", ...},
               "toolConfirmation": {"hint": "Please approve or reject the tool call claims_approve_claim() by responding with a FunctionResponse with an expected ToolConfirmation payload.", "confirmed": false}}
# adk web shows a confirm dialog; after "Confirm":
[claims_desk]: Claim CLM-1001 is approved and a payout of $1,800.00 is scheduled.
```
The hint text is verbatim from `tools/mcp_tool/mcp_tool.py` L590-595.

**Key lines.**
1. `StdioConnectionParams(server_params=..., timeout=10.0)`: prefer this to a bare `StdioServerParameters`. The docstring says the bare form "does not support timeout" (`mcp_toolset.py` L150-200). Default `timeout: float = 5.0` (`mcp_session_manager.py` L309).
2. `command=sys.executable`: launches the server with the agent's interpreter, so `mcp` is importable. A bare `"python"` on Windows often resolves to a different interpreter.
3. `tool_filter=[...]`: filters on the server's **original** names (`base_toolset.py` `_is_tool_selected` L217-229). The prefix is applied afterwards (`get_tools_with_prefix` L122-175) as `f"{prefix}_{tool.name}"`.
4. `require_confirmation=payout_needs_human`: a toolset-wide callable. `McpTool._prepare_callable_args` passes the call's args, filtered to the callable's signature unless it takes `**kwargs`, and adds `tool_context` when the callable accepts it (`mcp_tool.py` L525-571). With `**kwargs`, one rule works across all tools.
5. `mcp.run()`: MCP SDK 2.x `MCPServer.run(transport="stdio")` is the default (`mcpserver/server.py` L404-425).

**Common errors.**
- `ImportError: cannot import name 'McpToolset' from 'google.adk.tools.mcp_tool'`. Cause: `mcp` is not installed. `tools/mcp_tool/__init__.py` wraps its imports in `try/except ImportError` and only logs at debug, so you get this opaque error. Fix: `pip install "google-adk[mcp]==2.13.0"`.
- `ModuleNotFoundError: No module named 'mcp.server.fastmcp'. This is mcp 2.x, where FastMCP was renamed to MCPServer ...`. Cause: v1 server code on mcp 2.3.0. Fix: `from mcp.server.mcpserver import MCPServer`, or pin `mcp<2`.
- Session dies right after start, or `ConnectionError: Failed to create MCP session: ...` (`mcp_session_manager.py` L1531). Cause: a `print()` in the server corrupted stdout, or startup took longer than `timeout`. Fix: log to stderr, raise `timeout`, and test the server alone with `python claims_server.py < /dev/null`.
- **Silent failure.** The agent answers "I can't access claims", and the log shows `Agent claims_desk will run without the tools from toolset McpToolset (prefix 'claims'), which failed to load: ...` (`agents/llm_agent.py` L217-229). ADK keeps running without the toolset's tools. Fix: alert on this log line, and add a startup smoke test that calls `await claims_tools.get_tools()`.

**Best practice.** Least privilege at three layers:
- `tool_filter` hides what the model must not see.
- `require_confirmation` gates what it may only do with a human.
- The server keeps its own authorization, because MCP clients other than ADK can call it.

This matters in practice. arXiv 2610.22301 (Oct 2026) found that 16.4% of 4,806 triaged MCP servers expose filesystem capabilities despite a non-filesystem function. Client-side approval "grants the underlying server process broad host filesystem permissions."

**Variation.** Replace the Python server with the reference filesystem server, `StdioServerParameters(command="npx", args=["-y", "@modelcontextprotocol/server-filesystem", "/srv/claims-docs"])`, with `tool_filter=["read_file","list_directory"]` (pattern from adk.dev/tools-custom/mcp-tools). Or add `use_mcp_resources=True`: ADK then adds a `load_mcp_resource` tool and lists the server's resources in context (`mcp_toolset.py` docstring).

---

## Lab 2: Multi-tenant HR policy search over streamable HTTP

> **VERIFIED against google-adk 2.13.0 source (tag v2.13.0, commit d68ca857), re-checked by the verifier on 2026-10-23: every import path, class/function name and parameter in the code.** Also verified against mcp 2.3.0 (`run(transport="streamable-http", host, port, streamable_http_path)`). Still [UNVERIFIED]: the exact `TypeError` text. Expected-output blocks stay illustrative (nothing was executed).

**Goal.** Run an HR-policy MCP server over HTTP on port 3000. Connect to it with `StreamableHTTPConnectionParams`, send a per-tenant header from session state, and cache `tools/list`.

**Prerequisites.** `pip install "google-adk[mcp]==2.13.0" "mcp==2.3.0"`, plus `.env` as in Lab 1. Adapted from ADK sample `contributing/samples/mcp/mcp_streamablehttp_agent/` (agent.py + filesystem_server.py) and `mcp_dynamic_header_agent/agent.py`.

**Code: `hr_server.py`**
```python
from mcp.server.mcpserver import MCPServer

mcp = MCPServer("hr-policy-server")

POLICIES = {
    "pto": "Full-time staff accrue 1.67 PTO days per month; max carry-over 10 days.",
    "parental": "Primary caregivers get 16 weeks paid leave; secondary get 6 weeks.",
    "remote": "Employees may work remotely up to 3 days per week with manager approval.",
}


@mcp.tool()
def search_policy(topic: str) -> str:
    """Search the HR handbook. topic is one of: pto, parental, remote."""
    return POLICIES.get(topic.lower(), f"No policy found for '{topic}'.")


@mcp.tool()
def list_topics() -> list[str]:
    """List HR handbook topics that search_policy understands."""
    return sorted(POLICIES)


if __name__ == "__main__":
    # mcp 2.x: bind address goes to run(); path defaults to /mcp
    mcp.run(transport="streamable-http", host="127.0.0.1", port=3000)
```

**Code: `hr_agent/agent.py`**
```python
from google.adk.agents import LlmAgent
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.tools.mcp_tool import McpToolset, StreamableHTTPConnectionParams


def tenant_headers(ctx: ReadonlyContext) -> dict[str, str]:
    # user:-scoped state survives across sessions for the same user
    return {"X-Tenant-ID": ctx.state.get("user:tenant", "acme")}


hr_tools = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="http://127.0.0.1:3000/mcp",
        timeout=5.0,            # connect timeout (default 5.0)
        sse_read_timeout=300.0,  # read timeout for streamed responses (default 300)
    ),
    tool_filter=["search_policy", "list_topics"],
    header_provider=tenant_headers,
    tool_list_cache_ttl_seconds=300,  # reuse tools/list for 5 minutes
)

root_agent = LlmAgent(
    name="hr_helper",
    model="gemini-3.5-flash",
    instruction=(
        "Answer HR questions only from search_policy results. "
        "Quote the policy text and say which topic it came from."
    ),
    tools=[hr_tools],
)
```

**Run.**
```bash
python hr_server.py            # terminal 1: Uvicorn running on http://127.0.0.1:3000
adk web .                      # terminal 2
```
Prompt: `How many remote days can I take?`

**Expected output (illustrative).**
```text
[hr_helper]: function_call search_policy {"topic": "remote"}
[hr_helper]: function_response {"result": "Employees may work remotely up to 3 days per week with manager approval."}
[hr_helper]: Per the "remote" policy: employees may work remotely up to 3 days per week, with manager approval.
```

**Key lines.**
1. `StreamableHTTPConnectionParams(url=..., timeout=5.0, sse_read_timeout=300.0)`: defaults `timeout=5.0`, `sse_read_timeout=300.0`, `terminate_on_close=True` (`mcp_session_manager.py` L504-530). The old name `StreamableHTTPServerParams` is still an alias (L1610).
2. `header_provider=tenant_headers`: called with a `ReadonlyContext` per session and may be async (`mcp_toolset.py` L150-170). Sessions are **pooled per header identity**.
3. `tool_list_cache_ttl_seconds=300`: per the docstring, entries are keyed like the session pool, so each `header_provider` identity gets its own. Also: *"ADK does not subscribe to `notifications/tools/list_changed`, so a tool the server adds or removes goes unnoticed until the entry expires."* A value `<= 0` raises `ValueError("tool_list_cache_ttl_seconds must be positive, got ...")`.
4. `mcp.run(transport="streamable-http", host=..., port=...)`: MCPServer defaults are `host="127.0.0.1"`, `port=8000`, `streamable_http_path="/mcp"`, `stateless_http=False` (`mcpserver/server.py` L1113-1127).

**Common errors.**
- `TypeError: MCPServer.__init__() got an unexpected keyword argument 'port'`. Cause: v1 style `FastMCP("x", host=..., port=...)` on mcp 2.x. The constructor has no `host`/`port` (`server.py` L158-183). Fix: pass them to `run()`. The ADK sample does this with a `_BINDS_AT_RUN` switch. (The error text follows standard Python TypeError format; I did not run it.)
- Wrong URL or path (for example `http://127.0.0.1:3000/` without `/mcp`). The toolset fails to load, ADK logs `... will run without the tools from toolset McpToolset ...`, and the model answers without tools. Fix: use the exact `/mcp` path, and add a `get_tools()` health check at startup.
- `ValueError: tool_list_cache_ttl_seconds must be positive, got 0.` Fix: use `None` to disable the cache.

**Best practice.** Carry identity in headers from `header_provider`, never in the prompt. Pin `tool_filter` so a server-side tool addition cannot widen the agent's action space without a code review.

Two recent papers support this:
- arXiv 2610.23449 (GatewayBench, Oct 2026) evaluates seven MCP gateways while injecting task-irrelevant tools from a pool of 11,118 real tools. A growing tool surface affects both capability and security.
- arXiv 2610.14334 (Oct 2026) analyzed metadata of 367,174 MCP tools. It found that **parameter-schema changes produce the largest selection shifts**: "models tend to favor separate top-level parameters over grouped or composite forms". So design schemas flat.

**Variation.** Send OAuth on this connection: pass `auth_scheme=` and `auth_credential=` to `McpToolset` (sample `mcp/mcp_toolset_auth/`). ADK then emits `adk_request_credential` before **listing** tools; see Lab 8 for the client loop. For mTLS, see sample `mcp_sse_mtls_agent`. The `mcp` extra pulls `aiohttp`, otherwise ADK "falls back to plain TLS" (pyproject comment).

---

## Lab 3: Expose the refund-policy agent as an MCP server (Claude Code, IDEs, any MCP host)

> **VERIFIED against google-adk 2.13.0 source (tag v2.13.0, commit d68ca857), re-checked by the verifier on 2026-10-23: every import path, class/function name and parameter in the code.** Still [UNVERIFIED]: the Claude Code `claude mcp add` syntax and the v1-era `AttributeError` text. Expected-output blocks stay illustrative (nothing was executed).

**Goal.** Turn an ADK `LlmAgent` into an MCP server with one call and serve it over streamable HTTP. Then consume it from another ADK agent, or from an MCP host such as Claude Code.

**Prerequisites.** `pip install "google-adk[mcp]==2.13.0" "mcp==2.3.0"` and `.env`. Source: `tools/mcp_tool/_agent_to_mcp.py` (`to_mcp_server`, `@experimental(FeatureName.MCP_AGENT_SERVER)` at L169).

**Code: `refund_mcp_server.py`**
```python
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import to_mcp_server


def lookup_order(order_id: str) -> dict:
    """Return order date, amount (USD) and item category for an order id."""
    orders = {
        "A-100": {"days_since_purchase": 12, "amount": 79.0, "category": "apparel"},
        "A-200": {"days_since_purchase": 45, "amount": 640.0, "category": "electronics"},
    }
    return orders.get(order_id, {"error": f"unknown order {order_id}"})


refund_agent = LlmAgent(
    name="refund_policy",
    model="gemini-3.5-flash",
    description="Decides whether an order is refundable under ACME policy.",
    instruction=(
        "Policy: apparel 30 days, electronics 14 days, refunds over $500 need a "
        "manager. Call lookup_order, then answer REFUNDABLE / NOT_REFUNDABLE / "
        "NEEDS_MANAGER with one sentence of reasoning."
    ),
    tools=[lookup_order],
)

server = to_mcp_server(
    refund_agent,
    instructions="Ask about refund eligibility by order id, e.g. 'Can A-100 be refunded?'",
)

if __name__ == "__main__":
    server.run(transport="streamable-http", host="127.0.0.1", port=8090)
```

**Code: `consumer/agent.py`** (an ADK agent that uses the MCP-exposed agent as a tool)
```python
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import McpToolset, StreamableHTTPConnectionParams

root_agent = LlmAgent(
    name="cs_frontline",
    model="gemini-3.5-flash",
    instruction="For any refund question call the refund_policy tool with the user's request.",
    tools=[
        McpToolset(
            connection_params=StreamableHTTPConnectionParams(
                url="http://127.0.0.1:8090/mcp",
                sse_read_timeout=120.0,   # the remote agent may think for a while
            ),
            tool_filter=["refund_policy"],
        )
    ],
)
```

**Run.**
```bash
python refund_mcp_server.py          # terminal 1
adk run consumer                     # terminal 2 -> "Can order A-200 be refunded?"
# From Claude Code instead (Claude Code CLI syntax, not ADK) [UNVERIFIED this pass]:
claude mcp add --transport http refund-policy http://127.0.0.1:8090/mcp
```

**Expected output (illustrative).**
```text
[cs_frontline]: function_call refund_policy {"request": "Can order A-200 be refunded?"}
[cs_frontline]: function_response {"content": [{"type": "text", "text": "NOT_REFUNDABLE: electronics have a 14-day window and A-200 was bought 45 days ago."}]}
[cs_frontline]: Sorry, order A-200 is past the 14-day electronics return window, so it can't be refunded.
```

**Key lines.**
1. `to_mcp_server(agent, *, name=None, instructions=None, runner=None) -> FastMCP` (L170-176). It registers **one** MCP tool named after the agent. The tool takes a single `request: str` and its description is `agent.description` (L208-227).
2. `server.run(transport="streamable-http", ...)`: the docstring says "The caller chooses the transport". On mcp 2.x the returned object is `MCPServer`, so the `run()` kwargs from Lab 2 apply.
3. Sessions: "One ADK session is kept per MCP connection, so successive tool calls on the same connection form a single multi-turn conversation" (L185-186). The map is a `WeakKeyDictionary` keyed on the connection (L215).
4. Output mapping: final-response text becomes `TextContent`, `image/*` becomes `ImageContent`, `audio/*` becomes `AudioContent`, and other blobs become `EmbeddedResource` (`_part_to_content`, L50-80). Intermediate text is sent as MCP **progress notifications**, which "is a no-op unless the host requested it."
5. `runner=None`: you get in-memory session, artifact, memory and credential services (`_build_runner`). Pass your own `Runner` in production to persist sessions.

**Common errors.**
- `AttributeError: 'MCPServer' object has no attribute 'settings'` (or similar) when v1-era code sets `server.settings.port = ...`. **[UNVERIFIED exact text]** Fix: pass host and port to `run()` (mcp 2.x).
- The host times out on long answers. The whole agent run happens inside one MCP `call_tool`. Fix: raise the client read timeout (`sse_read_timeout` in ADK; host-specific elsewhere) and keep the exposed agent fast.
- An experimental warning at import. Fix: set `ADK_SUPPRESS_EXPERIMENTAL_FEATURE_WARNINGS=1` (honored since 2.13.0, CHANGELOG "honor ADK_SUPPRESS_EXPERIMENTAL_FEATURE_WARNINGS").

**Best practice.** Write `description=` as a tool contract: input, output enum, when to use it. MCP hosts see only that string. Keep internal policy in `instruction`, which is never exported.

**Variation.** The other direction is to expose individual ADK tools instead of the whole agent. Use `adk_to_mcp_tool_type(tool)` from `google.adk.tools.mcp_tool` inside a hand-built server (adk.dev "agent-as-server"). It is cheaper and deterministic, with no LLM inside the call.

---

## Lab 4: Support triage delegates refunds over A2A (`to_a2a`, agent card, `RemoteA2aAgent`)

> **VERIFIED against google-adk 2.13.0 source (tag v2.13.0, commit d68ca857), re-checked by the verifier on 2026-10-23: every import path, class/function name and parameter in the code.** Also verified against a2a-sdk 1.2.3 (`AGENT_CARD_WELL_KNOWN_PATH = '/.well-known/agent-card.json'`). Still [UNVERIFIED]: the exact A2A 1.0 card JSON shape and the mounted-sub-app 404. Expected-output blocks stay illustrative (nothing was executed).

**Goal.** Serve the refund agent as an A2A service on port 8001 and inspect its auto-generated Agent Card. Then add it as a remote sub-agent of a support-triage agent.

**Prerequisites.** `pip install "google-adk[a2a]==2.13.0"` (this pulls `a2a-sdk[http-server]` 1.2.3) and `.env`. Adapted from ADK sample `contributing/samples/a2a/a2a_basic/` and the adk.dev quickstarts "Exposing" / "Consuming" (https://adk.dev/a2a/quickstart-exposing/, https://adk.dev/a2a/quickstart-consuming/). Codelab for context: "Getting Started with MCP, ADK and A2A", https://codelabs.developers.google.com/getting-started-mcp-a2a-adk (the URL returned HTTP 200 on 2026-10-23, so the page exists; it was written against older APIs).

**Code: `refund_service/a2a_server.py`**
```python
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.agents import LlmAgent


def lookup_order(order_id: str) -> dict:
    """Return days since purchase, amount (USD) and category for an order id."""
    orders = {
        "A-100": {"days_since_purchase": 12, "amount": 79.0, "category": "apparel"},
        "A-200": {"days_since_purchase": 45, "amount": 640.0, "category": "electronics"},
    }
    return orders.get(order_id, {"error": f"unknown order {order_id}"})


refund_agent = LlmAgent(
    name="refund_agent",
    model="gemini-3.5-flash",
    description="Checks refund eligibility for an order id under ACME policy.",
    instruction="Apparel 30 days, electronics 14 days. Use lookup_order. Be brief.",
    tools=[lookup_order],
)

# host/port are written into the card's URL: they MUST match how you serve it
a2a_app = to_a2a(refund_agent, host="localhost", port=8001)
```

**Code: `triage/agent.py`**
```python
from google.adk.agents import LlmAgent
from google.adk.agents.remote_a2a_agent import AGENT_CARD_WELL_KNOWN_PATH, RemoteA2aAgent

refund_remote = RemoteA2aAgent(
    name="refund_agent",
    agent_card=f"http://localhost:8001{AGENT_CARD_WELL_KNOWN_PATH}",
    description="Remote refund-eligibility agent (owned by the Payments team).",
    timeout=60.0,   # default DEFAULT_TIMEOUT = 600.0 seconds
)

root_agent = LlmAgent(
    name="support_triage",
    model="gemini-3.5-flash",
    instruction=(
        "Classify the ticket. Refund or return questions: transfer to refund_agent "
        "and include the order id in your message. Everything else: answer yourself."
    ),
    sub_agents=[refund_remote],
)
```

**Run.**
```bash
uvicorn refund_service.a2a_server:a2a_app --host localhost --port 8001     # terminal 1
curl -s http://localhost:8001/.well-known/agent-card.json | python -m json.tool
adk web .                                                                 # terminal 2 -> support_triage
```
Prompt: `I want to return order A-100, it doesn't fit.`

**Expected agent card (illustrative, built from `a2a/utils/agent_card_builder.py`).**
```json
{
  "name": "refund_agent",
  "description": "Checks refund eligibility for an order id under ACME policy.",
  "url": "http://localhost:8001/",
  "version": "0.0.1",
  "capabilities": {"streaming": true},
  "skills": [
    {"id": "refund_agent", "name": "model", "description": "Checks refund eligibility ...", "tags": ["llm"]},
    {"id": "refund_agent-lookup_order", "name": "lookup_order",
     "description": "Return days since purchase, amount (USD) and category for an order id.", "tags": ["llm", "tools"]}
  ]
}
```
The JSON field layout differs between A2A 0.3 and 1.0 cards. ADK's `_compat.py` builds whichever the installed SDK expects. The exact v1.0 JSON shape is **[UNVERIFIED]**; the field values come from the builder.

**Key lines.**
1. `to_a2a(agent, *, host="localhost", port=8000, protocol="http", rpc_path="", agent_card=None, task_store=None, runner=None, lifespan=None, security_schemes=None, default_skill_security=None, ...) -> Starlette` (`a2a/utils/agent_to_a2a.py` L80-97). It also accepts a `Workflow`.
2. `rpc_url = f"{protocol}://{host}:{port}{prefix}/"` is the URL written into the card (L222-226). The default port is **8000**, which collides with `adk web`. Always pass the port you serve on.
3. The card is built in the app **lifespan** (`setup_a2a` inside `_combined_lifespan`, L258-290). The card description comes from `agent.description`, "never from its instructions", because the card is served without auth (builder L167-169).
4. `AGENT_CARD_WELL_KNOWN_PATH`: with a2a-sdk 1.2.3 this is `'/.well-known/agent-card.json'` (a2a-python `src/a2a/utils/constants.py`). If an older SDK lacks the constant, `RemoteA2aAgent` falls back to `"/.well-known/agent.json"` (`a2a/agent/_remote_a2a_agent.py` L44-48).
5. `RemoteA2aAgent(name, agent_card, *, description="", timeout=600.0, a2a_client_factory=None, context_builder=None, full_history_when_stateless=False, auth_scheme=None, auth_credential=None, ...)` (L689-716). `agent_card` may be an `AgentCard`, a URL or a file path.

**Common errors.**
- `ModuleNotFoundError: No module named 'a2a'`. Fix: `pip install "google-adk[a2a]==2.13.0"`.
- The card loads but sends fail with `httpx.ConnectError: All connection attempts failed`. Cause: the card advertises `http://localhost:8000/` (default port) while uvicorn listens on 8001. Fix: `to_a2a(..., port=8001)`. For Cloud Run, pass `host=<service host>, protocol="https", port=443`, or pass a hand-written `agent_card=`. The code path is verified; the exact message is httpx's standard text.
- A 404 on `/.well-known/agent-card.json` after you mount `a2a_app` inside another Starlette or FastAPI app. Cause: routes are attached in the sub-app's lifespan, and mounted sub-apps don't run their lifespans by default **[UNVERIFIED for every host framework]**. Fix: serve `a2a_app` as the top-level ASGI app, or use `rpc_path=` to prefix it.
- The remote agent "forgets" values you put in state. This is expected: "Session state is local to each side of an A2A boundary... state deltas from a remote peer are not applied to the caller's session" (class docstring, L653-660). Fix: put needed values in the message text or use `context_builder`.
- You assumed `security_schemes=` protects the endpoint. It does not: "Populates metadata on the card only and is not enforced at runtime by the Starlette application" (L127-137). Fix: enforce auth in front of the service (Cloud Run IAM, API gateway, or Starlette middleware), and give the client `auth_scheme`/`auth_credential`.

**Best practice.** Treat A2A as a trust boundary.
- arXiv 2609.10871 (A2ABreak, Sep/Oct 2026) extracts a 37-state, 76-transition model from the A2A spec. It finds **11 protocol-level vulnerabilities** exploitable by a spec-compliant adversary, including "cross-client context injection through unprotected context identifiers" and "credential harvesting via multi-hop identity loss in delegation chains."
- So authenticate every hop, never trust a peer-supplied `contextId` as an authorization signal, and log task ids.
- arXiv 2609.01693 (Sep 2026) adds a data-handling warning: in an MCP-to-A2A chain, a "PUBLIC - OK TO SHARE" label was associated with **more** verbatim data egress.

**Variation.** Persist tasks with `to_a2a(agent, task_store=DatabaseTaskStore(engine), lifespan=...)` (the example is in the docstring, L166-179). Or use the CLI: `adk api_server --a2a --port 8001 path/to/remote_agents_dir`. That needs a hand-written `agent.json` card per agent, as in `a2a_basic/remote_a2a/check_prime_agent/agent.json`.

---

## Lab 5: A refund-policy Agent Skill (`SkillToolset`, progressive disclosure, scripts)

> **VERIFIED against google-adk 2.13.0 source (tag v2.13.0, commit d68ca857), re-checked by the verifier on 2026-10-23: every import path, class/function name and parameter in the code.** Correction applied: `ADK_ENABLE_SKILL_LIFECYCLE=1` is needed for `unload_skill` and for pruning evicted skills from the prompt; the BOUNDED cap bookkeeping runs without it. Expected-output blocks stay illustrative (nothing was executed).

**Goal.** Package the refund policy as an Agent Skill. It has a `SKILL.md` with frontmatter and steps, a reference file, and a proration script. The skill unlocks the `lookup_order` tool only once it loads. The agent pays the context cost only when a refund question arrives.

**Prerequisites.** `pip install "google-adk==2.13.0"` and `.env`. Adapted from ADK sample `contributing/samples/environment_and_skills/skills_agent/` and adk.dev "Skills for ADK agents" (https://adk.dev/skills/). Spec: https://agentskills.io/specification.

Layout:
```text
refund_skill_agent/
  __init__.py                 # from . import agent
  agent.py
  skills/refund-policy/
    SKILL.md
    references/policy.md
    scripts/prorate.py
```

**`skills/refund-policy/SKILL.md`**
```markdown
---
name: refund-policy
description: Decide refund eligibility and partial-refund amounts for ACME orders. Use for any refund, return or chargeback question.
metadata:
  adk_additional_tools:
    - lookup_order
---
Step 1: Call `lookup_order` with the order id.
Step 2: Read `references/policy.md` for the return windows.
Step 3: If the order is past the full-refund window but inside 60 days, run
`scripts/prorate.py` with args {"amount": <amount>, "days": <days_since_purchase>}.
Step 4: Answer FULL_REFUND, PARTIAL_REFUND <amount>, or NO_REFUND with one reason.
```

**`skills/refund-policy/references/policy.md`**
```markdown
- Apparel: full refund within 30 days.
- Electronics: full refund within 14 days.
- Days 31-60 (any category): partial refund, prorated by prorate.py.
- After 60 days: no refund.
```

**`skills/refund-policy/scripts/prorate.py`**
```python
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--amount", type=float, required=True)
parser.add_argument("--days", type=int, required=True)
a = parser.parse_args()
share = max(0.0, (60 - a.days) / 30)          # 100% at day 30 -> 0% at day 60
print(f"{round(a.amount * min(share, 1.0), 2)}")
```

**`agent.py`**
```python
import pathlib

from google.adk.agents import LlmAgent
from google.adk.code_executors import UnsafeLocalCodeExecutor
from google.adk.skills import load_skill_from_dir
from google.adk.tools.skill_toolset import SkillToolset

HERE = pathlib.Path(__file__).parent


def lookup_order(order_id: str) -> dict:
    """Return days since purchase, amount (USD) and category for an order id."""
    orders = {"A-300": {"days_since_purchase": 42, "amount": 120.0, "category": "apparel"}}
    return orders.get(order_id, {"error": f"unknown order {order_id}"})


refund_skill = load_skill_from_dir(HERE / "skills" / "refund-policy")

skills = SkillToolset(
    skills=[refund_skill],
    additional_tools=[lookup_order],          # only exposed once the skill is loaded
    code_executor=UnsafeLocalCodeExecutor(),  # DEV ONLY: runs scripts in-process
)

root_agent = LlmAgent(
    name="refund_skill_agent",
    model="gemini-3.5-flash",
    instruction="You are ACME customer support. Use skills when they match the request.",
    tools=[skills],
)
```

**Run.** `adk web .`, then prompt: `Order A-300 is a jacket I bought 42 days ago. Can I get money back?`

**Expected tool trace (illustrative).**
```text
list_skills {}                                   -> [{"name":"refund-policy","description":"Decide refund ..."}]
load_skill {"skill_name":"refund-policy"}        -> SKILL.md body (L2)
lookup_order {"order_id":"A-300"}                -> {"days_since_purchase":42,"amount":120.0,"category":"apparel"}
load_skill_resource {"skill_name":"refund-policy","file_path":"references/policy.md"}
run_skill_script {"skill_name":"refund-policy","file_path":"scripts/prorate.py","args":{"amount":120.0,"days":42}}
                                                 -> stdout "72.0"
[agent]: PARTIAL_REFUND 72.00 - the jacket is past the 30-day window but inside 60 days.
```

**Key lines.**
1. `load_skill_from_dir(path)` resolves the path, parses the frontmatter, and loads `references/`, `assets/` and `scripts/` (`skills/_utils.py` L206-251). It **raises if the directory name differs from `name`**.
2. `SkillToolset(skills, *, registry=None, code_executor=None, environment=None, additional_tools=None, discovery_mode=SkillDiscoveryMode.LAZY, lifecycle_config=None, script_timeout=300, ...)` (`tools/skill_toolset.py` L2115-2130). Its tools are `list_skills` (LAZY mode only), `load_skill`, `load_skill_resource` and `run_skill_script`. `search_skills` is added when a registry is given, and `unload_skill` when lifecycle is enabled (L2245-2259).
3. `metadata.adk_additional_tools` must be a **list of strings** (`skills/models.py` `_validate_metadata`). Names are resolved against `additional_tools` when the skill is activated (L2310-2334).
4. `run_skill_script` `args` takes an object, rendered as long options (`--amount 120.0`), or a list of strings (L1853-1863). That is why the script uses `argparse`.
5. Script execution uses the toolset's executor first, then the agent's `code_executor`. If neither exists, the tool returns an error instead of running (L2043-2056).

**Common errors.**
- `ValueError: Skill name 'refund_policy' does not match directory name 'refund-policy'.` (`_utils.py` L229-233). Fix: rename one to match.
- Name validation fails with `name must be lowercase kebab-case (a-z, 0-9, hyphens), with no leading, trailing, or consecutive delimiters`. snake_case is accepted only with the experimental `SNAKE_CASE_SKILL_NAME` feature (`models.py` L95-115). The other limits: description at most 1024 characters, name at most 64.
- The script tool returns `{"error": "Neither Environment nor CodeExecutor is configured. An environment or code executor is required to run scripts.", "error_code": "NO_CODE_EXECUTOR"}`. Fix: pass `code_executor=` or `environment=`. Passing both raises `ValueError("Cannot have both code_executor and environment")`.
- `ValueError: adk_additional_tools must be a list of strings` when the YAML has `adk_additional_tools: lookup_order`. Fix: use a YAML list.

**Best practice.** Use `UnsafeLocalCodeExecutor` only on a laptop. Its docstring says scripts are executed via `exec()` in-process, and `script_timeout` "Does not apply to Python scripts executed via exec()" (L2141-2143). In production use a container or sandbox environment (samples `e2b_env_skill_toolset`, `local_env_skill_toolset`, or `ContainerCodeExecutor`/`GkeCodeExecutor`).

Treat third-party skills as untrusted code *and* untrusted prompts. Recent evidence:
- arXiv 2608.12273 (Convergent Detour Hijacking, Aug 2026): a malicious skill whose description wins selection is chosen in 80.02% of tasks on one backend. It quietly inflates tokens and latency while still completing the task.
- arXiv 2610.25064 (SkillClash, Oct 2026): two same-job skills loaded together drop rule-following from 93-99% to 61-62%, because "one skill takes over." Ending each skill with one example that follows *both* skills cut takeover to 1-15%.
- arXiv 2609.28693 (Sep 2026, "skilder"): delivering tools only *inside* learned skills makes the skill boundary an enforceable access-control layer. ADK's `adk_additional_tools` follows the same idea.

**Variation.**
- `discovery_mode=SkillDiscoveryMode.EAGER` drops `list_skills` and injects the catalog into the system instruction.
- Load skills from GCS with `load_skill_from_gcs_dir(...)` (`skills/__init__.py`).
- Set `metadata: {adk_inject_state: true}` to interpolate `{user:tier}` from session state into the SKILL.md body (models.py docstring).
- Enable `ADK_ENABLE_SKILL_LIFECYCLE=1` for `unload_skill` and for pruning released skills from the request (CHANGELOG 2.10.0). The cap itself is `SkillToolset(lifecycle_config=SkillLifecycleConfig(default_mode=SkillLifecycleMode.BOUNDED, max_active_skills=3))`; its bookkeeping runs without the flag, but evicted skill text is only removed from the prompt when the flag is on (`skill_toolset.py` L2246, L2794-2795; verifier).

---

## Lab 6: Plugins as global guardrails (refund limit, PII redaction, self-healing retries)

> **VERIFIED against google-adk 2.13.0 source (tag v2.13.0, commit d68ca857), re-checked by the verifier on 2026-10-23: every import path, class/function name and parameter in the code.** Expected-output blocks stay illustrative (nothing was executed).

**Goal.** Enforce one rule across every agent and tool in the app without editing them: no tool may move more than $500, and card numbers are masked in tool results. Then add ADK's built-in `ReflectAndRetryToolPlugin` so tool exceptions become structured retry guidance.

**Prerequisites.** `pip install "google-adk==2.13.0"` and `.env`. Source: `plugins/base_plugin.py` and `apps/app.py`. Docs: https://adk.dev/plugins/. Prior research (`research-adk-platform/05-adk2-yaml-plugins.md`) verified that `Runner(plugins=...)` is deprecated in favor of `App(plugins=...)`.

**Code: `guarded_app.py`**
```python
import asyncio
import re
from typing import Any, Optional

from google.adk.agents import LlmAgent
from google.adk.apps import App
from google.adk.plugins import ReflectAndRetryToolPlugin
from google.adk.plugins.base_plugin import BasePlugin
from google.adk.runners import InMemoryRunner
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext

CARD = re.compile(r"\b(?:\d[ -]?){12}(\d{4})\b")


class RefundGuardPlugin(BasePlugin):
    def __init__(self, max_amount: float = 500.0):
        super().__init__(name="refund_guard")
        self.max_amount = max_amount

    async def before_tool_callback(
        self, *, tool: BaseTool, tool_args: dict[str, Any], tool_context: ToolContext
    ) -> Optional[dict]:
        amount = float(tool_args.get("amount", 0) or 0)
        if amount > self.max_amount:
            # returning a dict skips the tool and becomes its result
            return {"status": "blocked", "reason": f"{amount} exceeds limit {self.max_amount}"}
        return None

    async def after_tool_callback(
        self, *, tool: BaseTool, tool_args: dict[str, Any],
        tool_context: ToolContext, result: dict,
    ) -> Optional[dict]:
        masked = CARD.sub(r"**** \1", str(result))
        return {"result": masked} if masked != str(result) else None


def issue_refund(order_id: str, amount: float) -> dict:
    """Refund amount (USD) to the card on file for order_id."""
    if order_id.startswith("X"):
        raise ValueError("order ids must start with A-")
    return {"status": "ok", "refunded": amount, "card": "4111 1111 1111 1234"}


agent = LlmAgent(name="refunds", model="gemini-3.5-flash",
                 instruction="Issue refunds the user asks for.", tools=[issue_refund])
app = App(name="refund_app", root_agent=agent,
          plugins=[RefundGuardPlugin(), ReflectAndRetryToolPlugin(max_retries=2)])


async def main():
    async with InMemoryRunner(app=app) as runner:
        await runner.run_debug(["Refund $80 on A-100", "Refund $900 on A-200"], verbose=True)

asyncio.run(main())
```

**Run.** `python guarded_app.py`. With the dev UI on an agents folder instead: `adk web --extra_plugins=google.adk.plugins.LoggingPlugin .` (`cli/cli_tools_click.py` `--extra_plugins` at L2141).

**Expected output (illustrative).**
```text
User > Refund $80 on A-100
  [tool] issue_refund {"order_id": "A-100", "amount": 80}
  [tool result] {"result": "{'status': 'ok', 'refunded': 80, 'card': '**** 1234'}"}
refunds > Done: $80 refunded to the card ending 1234.
User > Refund $900 on A-200
  [tool] issue_refund {"order_id": "A-200", "amount": 900}
  [tool result] {"status": "blocked", "reason": "900.0 exceeds limit 500.0"}
refunds > I can't refund $900: refunds over $500 need a supervisor.
```

**Key lines.**
1. `super().__init__(name="refund_guard")`: `BasePlugin.__init__(self, name: str)` (L105). The name must be unique within the app.
2. `before_tool_callback(self, *, tool, tool_args, tool_context) -> Optional[dict]` (L297-303). A non-None return **short-circuits** the tool. Plugin callbacks run before object-level callbacks and take precedence (adk.dev/plugins).
3. `after_tool_callback(..., result) -> Optional[dict]` (L321-327). A non-None return replaces the result the model sees.
4. `App(name=..., root_agent=..., plugins=[...])`. `App` is a pydantic model with `extra="forbid"` (`apps/app.py` L65-80). The name must match `validate_app_name`: "must start with a letter and can only consist of letters, digits, underscores, and hyphens."
5. `ReflectAndRetryToolPlugin(name="reflect_retry_tool_plugin", max_retries=3, throw_exception_if_retry_exceeded=True, tracking_scope=TrackingScope.INVOCATION)` (`plugins/reflect_retry_tool_plugin.py` L103-109). It "intercepts tool failures, provides structured guidance to the LLM".
6. `InMemoryRunner(app=app)` and `run_debug(...)`: `run_debug` is for experimentation only, per the docstring (`runners.py` L1852-1872). Use `run_async` in services.

**Common errors.**
- `ValueError: Invalid app name 'refund app': must start with a letter and can only consist of letters, digits, underscores, and hyphens.` (`apps/app.py` L42-48). Fix: no spaces.
- Passing both `app=` and `plugins=` to `Runner` raises a `ValueError`, and `plugins=` alone gives a `DeprecationWarning` (verified in prior research from `runners.py`). Fix: put plugins on `App`.
- `pydantic ValidationError ... Extra inputs are not permitted` for a typo such as `App(plugin=[...])`, because of `extra="forbid"`. Fix: the field is `plugins`. (Standard pydantic v2 wording.)
- The plugin never fires for a YAML-only agent. `AgentConfig` has no plugins key (prior research). Fix: `adk web --extra_plugins=module.ClassName`.

**Best practice.** Put **deterministic** policy (limits, redaction, allowlists) in plugins, and keep only judgment in prompts. Prompt rules "remain probabilistic advice rather than hard constraints" (arXiv 2609.28693).

Also bound what tool output does to cost. arXiv 2609.28585 (Denial-of-Wallet, Sep 2026) shows a malicious tool return can drive cumulative session input to **14,293x** the first call, and that raw history retention adds 21.2-35.9% to mean session cost. An `after_tool_callback` that truncates or summarizes huge results is a cheap defense.

**Variation.** Add `on_tool_error_callback(self, *, tool, tool_args, tool_context, error)` (L348-355) to map exceptions to a friendly `{"status": "error"}`. Or attach `BigQueryAgentAnalyticsPlugin` for org-wide tool analytics (needs the `bigquery-analytics` extra since 2.7.0, CHANGELOG L1176).

---

## Lab 7: Refund approvals, from an inline confirmation to a manager ticket (long-running)

> **VERIFIED against google-adk 2.13.0 source (tag v2.13.0, commit d68ca857), re-checked by the verifier on 2026-10-23: every import path, class/function name and parameter in the code.** Still [UNVERIFIED]: whether 2.13 lifted the docs' 'confirmation lost across restarts' limitation for Database/VertexAi session services. Expected-output blocks stay illustrative (nothing was executed).

**Goal.** Refunds of $100 or more pause for a yes/no. Account closure always needs a yes. Above $1,000 the agent files a manager ticket with a long-running tool and resumes when the ticket resolves. Approve programmatically, the way a Slack bot or email webhook would.

**Prerequisites.** `pip install "google-adk==2.13.0"` and `.env`. Adapted from ADK samples `contributing/samples/hitl/tool_confirmation/agent.py` (the `transfer_funds`/`close_account` pattern, with recorded fixture `tests/transfer_200_confirmed.json`) and `contributing/samples/tools/long_running_functions/agent.py`. Docs: https://adk.dev/tools-custom/confirmation/.

**Code: `approvals.py`**
```python
import asyncio

from google.adk.agents import LlmAgent
from google.adk.runners import InMemoryRunner
from google.adk.tools import FunctionTool, LongRunningFunctionTool, ToolContext
from google.genai import types


def refund(order_id: str, amount: float, tool_context: ToolContext) -> dict:
    """Refund amount (USD) for order_id."""
    if amount >= 100:
        if not tool_context.tool_confirmation:
            tool_context.request_confirmation(hint=f"Refund ${amount} on {order_id}?")
            return {"status": "pending_confirmation"}
        if not tool_context.tool_confirmation.confirmed:
            return {"status": "rejected_by_user"}
    return {"status": "ok", "refunded": amount}


def close_account(account_id: str) -> dict:
    """Close a customer account. Destructive."""
    return {"status": "closed", "account_id": account_id}


def request_manager_approval(order_id: str, amount: float) -> dict:
    """Open a manager approval ticket for refunds over $1000."""
    return {"status": "pending", "ticket_id": f"T-{order_id}"}


agent = LlmAgent(
    name="refund_desk", model="gemini-3.5-flash",
    instruction="Refunds over $1000: call request_manager_approval first, then refund once approved.",
    tools=[refund, FunctionTool(close_account, require_confirmation=True),
           LongRunningFunctionTool(func=request_manager_approval)],
)


async def ask(runner, sid, content):
    pending = []
    async for ev in runner.run_async(user_id="u1", session_id=sid, new_message=content):
        for fc in ev.get_function_calls():
            if fc.name == "adk_request_confirmation" or fc.id in (ev.long_running_tool_ids or set()):
                pending.append(fc)
        if ev.is_final_response() and ev.content and ev.content.parts:
            print("AGENT:", ev.content.parts[0].text)
    return pending


async def main():
    runner = InMemoryRunner(agent=agent, app_name="approvals")
    s = await runner.session_service.create_session(app_name="approvals", user_id="u1")
    msg = types.Content(role="user", parts=[types.Part(text="Refund $250 on A-100")])
    for fc in await ask(runner, s.id, msg):          # approver says yes
        reply = types.FunctionResponse(id=fc.id, name=fc.name, response={"confirmed": True})
        await ask(runner, s.id, types.Content(role="user", parts=[types.Part(function_response=reply)]))

asyncio.run(main())
```

**Run.** `python approvals.py`. Then change the prompt to `Refund $1500 on A-200`. When the pending call is `request_manager_approval`, answer it later with `FunctionResponse(id=fc.id, name="request_manager_approval", response={"status": "approved", "ticket_id": "T-A-200"})`.

**Expected events (illustrative; same shape as ADK fixture `hitl/tool_confirmation/tests/transfer_200_confirmed.json`).**
```text
model   -> functionCall refund {"order_id":"A-100","amount":250}            id=fc-1
model   -> functionCall adk_request_confirmation                            id=fc-2  longRunningToolIds=[fc-2]
           args={"originalFunctionCall":{"id":"fc-1","name":"refund",...},
                 "toolConfirmation":{"hint":"Refund $250.0 on A-100?","confirmed":false}}
tool    -> functionResponse refund {"status":"pending_confirmation"}  actions.requestedToolConfirmations={fc-1:...}
AGENT: I need your approval to refund $250 on A-100.
user    -> functionResponse adk_request_confirmation {"confirmed": true}    id=fc-2
tool    -> functionResponse refund {"status":"ok","refunded":250.0}         id=fc-1  (tool re-run, confirmed)
AGENT: Done - $250 refunded on A-100.
```

**Key lines.**
1. `tool_context.request_confirmation(hint=..., payload=None)` (`agents/context.py` L702-707). `ToolContext` is now just an alias: `ToolContext = Context` (`tools/tool_context.py`).
2. `FunctionTool(close_account, require_confirmation=True)`: the function only runs after a yes. In the sample's words: "this function is only called if the user approves."
3. The special call is named `adk_request_confirmation`, and the credential flow uses `adk_request_credential` (`utils/_function_call_names.py` L20-21). Reply with a `FunctionResponse` whose **id is the confirmation call's id** (fc-2), not the original tool call's id. The REST docs say the same: "The `id` in the `function_response` should match the `function_call_id` from the `adk_request_confirmation` `FunctionCall` event."
4. `ToolConfirmation(hint="", confirmed=False, payload=None)` is a pydantic model with camelCase aliases and `extra="forbid"` (`tools/tool_confirmation.py`). `from_response_dict` also accepts the `{"response": "<json>"}` wrapper that ADK web sends.
5. `LongRunningFunctionTool(func)` sets `is_long_running = True` and appends to the description: *"NOTE: This is a long-running operation. Do not call this tool again if it has already returned some intermediate or pending status."* (`tools/long_running_tool.py`). The pending call id appears in `event.long_running_tool_ids` (`events/event.py` L119).

**Common errors.**
- Your reply is ignored, or the agent asks again. Cause: you used the original tool's id (fc-1), or a different `name`. Fix: `id = <adk_request_confirmation call id>` and `name = "adk_request_confirmation"`.
- With an App that uses `ResumabilityConfig`, the confirmation starts a **new** invocation. The docs: "The Invocation ID you provide must be the same invocation that generated the confirmation request, otherwise the system starts a new invocation." Fix: pass `invocation_id=` to `run_async`.
- `pydantic ValidationError ... Extra inputs are not permitted` when the response carries unknown keys (for example `{"confirmed": true, "approved": 5}`), because of `extra="forbid"`. Fix: put custom data under `payload`.
- Confirmation is lost across restarts with `DatabaseSessionService` or `VertexAiSessionService`. Both are listed under "Known limitations" on adk.dev (2026-10-23). The registry marks the feature STABLE in 2.13, but the docs still list the limitation **[UNVERIFIED whether 2.13 lifted it]**. Fix: test resume on your session backend before production.

**Best practice.** Make the approval card **bind the exact effect**: amount, recipient and order id in the hint and payload. Re-check the arguments when the tool re-runs.

arXiv 2610.21063 ("Approve What, Exactly?", Oct 2026) audited ten agent runtimes. It found "no third-party verifiable approval record" and "post-approval argument changes in four of eight runtimes with measurable binding." Its 12 attacks include decoy recipients, amount cancellation and threshold splitting, so also cap the *sum* of sub-threshold refunds per session (threshold splitting).

**Variation.**
- Structured approval: `request_confirmation(hint=..., payload={"approved_amount": 0})`, then read `tool_context.tool_confirmation.payload["approved_amount"]` (docs `request_time_off` example).
- Over REST: POST the same `function_response` to `adk api_server`'s `/run_sse` (curl example in the docs).
- In Workflow graphs: the node-level `require_confirmation` (2.12) and `RequestInput` (see `hitl/request_input_tool`).

---

## Lab 8: Order-status REST API through `OpenAPIToolset`, with API-key auth (and the OAuth loop)

> **VERIFIED against google-adk 2.13.0 source (tag v2.13.0, commit d68ca857), re-checked by the verifier on 2026-10-23: every import path, class/function name and parameter in the code.** Still [UNVERIFIED]: the exact error when the spec has no `servers` entry. Expected-output blocks stay illustrative (nothing was executed).

**Goal.** Generate agent tools from a FastAPI service's OpenAPI spec and authenticate with an API key header. Hit and fix ADK's SSRF guard for localhost. Then see the client loop for OAuth (`adk_request_credential`).

**Prerequisites.** `pip install "google-adk==2.13.0"` (fastapi, httpx and uvicorn are already ADK dependencies) and `.env`. Docs: https://adk.dev/tools-custom/openapi-tools/ , https://adk.dev/tools-custom/authentication/.

**Code: `orders_api.py`** (the service)
```python
from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.security import APIKeyHeader

app = FastAPI(title="Orders API", servers=[{"url": "http://127.0.0.1:8081"}])
api_key = APIKeyHeader(name="X-API-Key")
ORDERS = {"A-100": {"status": "shipped", "carrier": "UPS", "eta": "2026-10-26"}}


def check_key(key: str = Security(api_key)) -> None:
    if key != "demo-key-123":
        raise HTTPException(status_code=401, detail="bad api key")


@app.get("/orders/{order_id}", operation_id="getOrderStatus", dependencies=[Depends(check_key)])
def get_order_status(order_id: str) -> dict:
    """Get shipping status, carrier and ETA for an order."""
    if order_id not in ORDERS:
        raise HTTPException(status_code=404, detail="order not found")
    return ORDERS[order_id]
```

**Code: `orders_agent/agent.py`**
```python
import os

import httpx
from google.adk.agents import LlmAgent
from google.adk.tools.openapi_tool.auth.auth_helpers import token_to_scheme_credential
from google.adk.tools.openapi_tool.openapi_spec_parser.openapi_toolset import OpenAPIToolset

spec = httpx.get("http://127.0.0.1:8081/openapi.json", timeout=5).json()

auth_scheme, auth_credential = token_to_scheme_credential(
    "apikey", "header", "X-API-Key", os.environ.get("ORDERS_API_KEY", "demo-key-123")
)

orders_tools = OpenAPIToolset(
    spec_dict=spec,
    auth_scheme=auth_scheme,
    auth_credential=auth_credential,
    tool_filter=["get_order_status"],      # snake_case of operationId getOrderStatus
    allow_private_network_access=True,     # needed ONLY because the API is on 127.0.0.1
)

root_agent = LlmAgent(
    name="order_tracker",
    model="gemini-3.5-flash",
    instruction="Answer shipping questions with get_order_status. Give carrier and ETA.",
    tools=[orders_tools],
)
```

**Run.**
```bash
uvicorn orders_api:app --port 8081     # terminal 1
adk web .                              # terminal 2 -> "Where is order A-100?"
```

**Expected output (illustrative).**
```text
[order_tracker]: function_call get_order_status {"order_id": "A-100"}
[order_tracker]: function_response {"status": "shipped", "carrier": "UPS", "eta": "2026-10-26"}
[order_tracker]: Order A-100 has shipped with UPS and should arrive on 2026-10-26.
```

**Key lines.**
1. `OpenAPIToolset(*, spec_dict=None, spec_str=None, spec_str_type="json", auth_scheme=None, auth_credential=None, credential_key=None, tool_filter=None, tool_name_prefix=None, ssl_verify=None, header_provider=None, httpx_client_factory=None, preserve_property_names=False, allow_private_network_access=False)` (`openapi_spec_parser/openapi_toolset.py` L68-86).
2. Tool name = `_to_snake_case(operationId)[:60]` (`operation_parser.py` L40, L288-291), so `getOrderStatus` becomes `get_order_status`. `tool_filter` matches the generated name. Without an `operation_id`, FastAPI generates a long id and the name changes.
3. `token_to_scheme_credential("apikey", "header", "X-API-Key", value)` returns `(APIKey scheme, AuthCredential(API_KEY))`. With `"oauth2Token"` it returns `HTTPBearer` + `HttpAuth(scheme="bearer")`, and "location" is ignored (`auth/auth_helpers.py` L77-157).
4. `allow_private_network_access=False` by default: "requests refuse loopback, private, link-local (including cloud metadata), and `*.internal` / `*.local` targets and return an error response" (`rest_api_tool.py` L259-263). Blocked names: `localhost`, `metadata`, `metadata.goog`, plus suffixes `.localhost .local .internal .metadata.goog` (`tools/_url_validator.py` L31-42). MCP connections do not go through this validator.
5. `preserve_property_names=True` keeps camelCase params for APIs that need them. Otherwise ADK snake_cases them.

**Common errors.**
- The tool returns `{"error": "Tool get_order_status execution failed. Analyze this execution error and your inputs. Retry with adjustments if applicable. But make sure don't retry more than 3 times. Execution Error: Blocked host: 127.0.0.1"}` (format from `_format_error_response`, L809-818; reason from `_validate_url`, L872-877). Cause: SSRF guard. Fix: `allow_private_network_access=True` for dev or internal APIs only. In prod, call a public or VPC-routed hostname.
- `... Execution Error: Status Code: 401, ...` comes back from the API. Cause: wrong header name or key. The scheme name must equal the API's header (`X-API-Key`).
- The model never calls the tool. Cause: `tool_filter` names the operationId (`getOrderStatus`) instead of the snake_case name. Fix: `tool_filter=["get_order_status"]`, or print `[t.name for t in await orders_tools.get_tools()]`.
- Every call fails with no host in the URL. Cause: the spec has no `servers` entry, so there is no base URL **[UNVERIFIED exact message]**. Fix: add `servers=[{"url": ...}]` in FastAPI, or patch `spec["servers"]` before building the toolset.

**OAuth variant: the client loop (adapted from ADK sample `mcp/mcp_toolset_auth/main.py` and adk.dev authentication).** With `auth_scheme=OAuth2(flows=OAuthFlows(authorizationCode=...))` and `auth_credential=AuthCredential(auth_type=AuthCredentialTypes.OAUTH2, oauth2=OAuth2Auth(client_id=..., client_secret=...))`, the first run yields a function call named `adk_request_credential`. Its `args["authConfig"]` parses with `AuthConfig.model_validate(...)`.
```python
from google.adk.auth.auth_tool import AuthConfig
# 1) from the event: fc.name == "adk_request_credential"
cfg = AuthConfig.model_validate(fc.args["authConfig"])
login_url = cfg.exchanged_auth_credential.oauth2.auth_uri + "&redirect_uri=" + REDIRECT_URI
# 2) user signs in; your web app captures the full callback URL
cfg.exchanged_auth_credential.oauth2.auth_response_uri = callback_url
cfg.exchanged_auth_credential.oauth2.redirect_uri = REDIRECT_URI
# 3) answer with the SAME id; ADK exchanges the code, stores the token, retries the tool
reply = types.FunctionResponse(id=fc.id, name="adk_request_credential", response=cfg.model_dump())
```
`AuthConfig` fields: `auth_scheme`, `raw_auth_credential`, `exchanged_auth_credential`, `credential_key` (`auth/auth_tool.py`). `OAuth2Auth` fields include `auth_uri`, `state`, `redirect_uri`, `auth_response_uri`, `access_token`, `refresh_token`, `expires_at` (`auth/auth_credential.py` L143-166).

When re-auth does not help, `RestApiTool` returns a distinct error so the model stops retrying: "...The user already re-authorized this connection and the API still rejected the credential, so retrying will not help..." (`rest_api_tool.py` L784-795).

**Best practice.** Use API keys only for service-to-service calls, read from Secret Manager or env (2.13 added Secret Manager/Parameter Manager samples, CHANGELOG). Never put them in instructions. Use OAuth so the agent acts as the user. Keep the SSRF guard on everywhere except explicit internal APIs.

Field data on why this matters: arXiv 2608.00150 (Jul 31, 2026) dynamically audited 414 internet-facing MCP servers. **91.8% lacked OAuth**, it found SSRF against cloud metadata among 68 vulnerabilities, and 41.6% of servers disappeared within three days.

**Variation.** Use `header_provider=lambda ctx: {"X-Request-ID": ctx.invocation_id}` for tracing headers. Or swap the toolset for `APIHubToolset` or `ApplicationIntegrationToolset` (folders `tools/apihub_tool`, `tools/application_integration_tool`) when the API is registered in Google Cloud.

---

## Lab 9: Competitor price research with `google_search` + code execution

> **VERIFIED against google-adk 2.13.0 source (tag v2.13.0, commit d68ca857), re-checked by the verifier on 2026-10-23: every import path, class/function name and parameter in the code.** Expected-output blocks stay illustrative (nothing was executed).

**Goal.** A pricing analyst agent searches the web for competitor prices and computes the average and spread with Gemini's sandboxed code execution. Combine built-in tools correctly on every model generation.

**Prerequisites.** `pip install "google-adk==2.13.0"` and `.env` (built-ins need Gemini). Samples: `contributing/samples/tools/built_in_multi_tools/`, `contributing/samples/code_execution/code_execution/agent.py`.

**Code: `pricing_agent/agent.py`**
```python
from google.adk.agents import LlmAgent
from google.adk.code_executors import BuiltInCodeExecutor
from google.adk.tools import AgentTool, google_search

search_agent = LlmAgent(
    name="price_search",
    model="gemini-3.5-flash",
    description="Finds current retail prices for a product on the public web.",
    instruction="Search the web. Return a list of {retailer, price_usd, url}. Cite every url.",
    tools=[google_search],
)

calc_agent = LlmAgent(
    name="price_math",
    model="gemini-3.5-flash",
    description="Runs Python to compute statistics over a list of prices.",
    instruction="Write and run Python. Print mean, min, max and spread. Never guess numbers.",
    code_executor=BuiltInCodeExecutor(),   # runs in Gemini's sandbox, not locally
)

root_agent = LlmAgent(
    name="pricing_analyst",
    model="gemini-3.5-flash",
    instruction=(
        "1) Use price_search to collect prices. 2) Pass the numbers to price_math. "
        "3) Report the table, the stats, and the source urls."
    ),
    tools=[AgentTool(agent=search_agent), AgentTool(agent=calc_agent)],
)
```

**Run.** `adk web .` and prompt: `What do the top US retailers charge for the Sony WH-1000XM6? Give the average.`

**Expected output (illustrative; prices are placeholders, not real data).**
```text
[pricing_analyst]: function_call price_search {"request": "Sony WH-1000XM6 price US retailers"}
[pricing_analyst]: function_response [{"retailer":"Retailer A","price_usd":449.99,"url":"https://..."}, ...]
[pricing_analyst]: function_call price_math {"request": "prices = [449.99, 429.00, 399.99]"}
[price_math]: executable_code: prices=[449.99,429.0,399.99]; print(sum(prices)/len(prices), ...)
[price_math]: code_execution_result: 426.33 399.99 449.99 50.0
[pricing_analyst]: Average $426.33 (range $399.99-$449.99, spread $50.00). Sources: ...
```

**Key lines.**
1. `google_search = GoogleSearchTool()` is a module-level singleton (`tools/google_search_tool.py` L88). It adds `types.Tool(google_search=types.GoogleSearch())` to the request and raises for non-Gemini models (L69-85).
2. `BuiltInCodeExecutor()` adds `types.Tool(code_execution=types.ToolCodeExecution())`. It executes nothing locally ("Execution is delegated to the model") (`code_executors/built_in_code_executor.py`).
3. `AgentTool(agent=...)` keeps each built-in alone in its own agent. Unlike `sub_agents`, control **returns** to the caller.
4. The model-generation rule is in `utils/model_name_utils.py` L199-214: "Gemini 3 and later accept built-in tools such as `google_search` in the same request as function declarations. Earlier Gemini models reject that combination with `400 INVALID_ARGUMENT: Tool use with function calling is unsupported`."
5. On older models, `GoogleSearchTool(bypass_multi_tools_limit=True)` makes ADK swap in a `GoogleSearchAgentTool` sub-agent automatically when the agent has other tools (`agents/llm_agent.py` L183-189).

**Common errors.**
- `400 INVALID_ARGUMENT: Tool use with function calling is unsupported`. Cause: `google_search` plus a function tool on a Gemini 2.x model. Fix: Gemini 3+, the `AgentTool` pattern, or `GoogleSearchTool(bypass_multi_tools_limit=True)`.
- At startup: `Agent 'pricing_analyst' has sub-agent transfer targets but is configured with GoogleSearchTool without bypass_multi_tools_limit=True. Gemini models before 3.0 do not allow built-in search tools to be combined with function calling (agent delegation)...` (`flows/llm_flows/extensions/_agent_transfer.py` L331-343). Fix: the same as above.
- `ValueError: Google search tool is not supported for model <name>` (or `Gemini code execution tool is not supported for model <name>`) on a non-Gemini model, such as via LiteLLM. Fix: keep built-ins on a Gemini sub-agent.

**Best practice.**
- Ground and cite. Google's terms require showing the search suggestions (`renderedContent` in grounding metadata) in production UIs (adk.dev integrations/google-search, from prior research).
- Since 2.13, `google_search` grounding is recorded on LLM spans (CHANGELOG: "record google_search grounding on LLM spans"), so you can audit which URLs backed an answer.
- Verify tool output before trusting it. arXiv 2609.37153 (Sep 2026, ToxicBench) shows that plausible but wrong tool evidence lowers data-agent task success by **26-39 points**, and agents sometimes adopt the wrong answer even *after* checking. Have `price_math` recompute from raw numbers and flag outliers rather than trusting a summarized price.

**Variation.**
- Swap `google_search` for `url_context` (from `google.adk.tools`) to read specific retailer pages.
- Swap `BuiltInCodeExecutor` for `AgentEngineSandboxCodeExecutor` or `GkeCodeExecutor` when you need files, packages or state the Gemini sandbox lacks (samples under `code_execution/`).

---

## Cross-lab gotcha sheet (all verified in v2.13.0 source unless marked)

| # | Gotcha | Where |
|---|---|---|
| 1 | `pip install google-adk` alone gives no MCP. Use `google-adk[mcp]`, and the import error is opaque. | `pyproject.toml`; `tools/mcp_tool/__init__.py` |
| 2 | mcp 2.x: `FastMCP` became `MCPServer`, and host/port go to `run()` | python-sdk v2.3.0 `server/fastmcp.py`, `mcpserver/server.py` |
| 3 | A toolset that fails to load is logged at ERROR and the agent runs **without** those tools | `agents/llm_agent.py` L211-229 |
| 4 | `tool_filter` matches pre-prefix names; the prefix is `f"{prefix}_{name}"` | `tools/base_toolset.py` |
| 5 | The tools/list cache ignores `list_changed` until TTL expiry | `mcp_toolset.py` docstring |
| 6 | `to_a2a` default port 8000 goes into the card URL | `agent_to_a2a.py` L222-226 |
| 7 | A2A `security_schemes` are card metadata only, not enforced | `agent_to_a2a.py` L127-137 |
| 8 | A2A state is not shared across the boundary | `_remote_a2a_agent.py` docstring |
| 9 | Skill dir name must equal frontmatter `name` (kebab-case, at most 64 chars) | `skills/_utils.py`, `skills/models.py` |
| 10 | `run_skill_script` needs an executor; `UnsafeLocalCodeExecutor` uses `exec()` in-process | `tools/skill_toolset.py` |
| 11 | Confirmation reply id is the `adk_request_confirmation` call id; extra keys are forbidden | fixture + `tool_confirmation.py` |
| 12 | `OpenAPIToolset` blocks localhost/private/metadata hosts unless `allow_private_network_access=True` | `_url_validator.py`, `rest_api_tool.py` |
| 13 | Built-in + function tools work only on Gemini 3+ | `utils/model_name_utils.py` |
| 14 | 2.13 telemetry default is GenAI semconv 1.44 (`call_llm` span removed). `ADK_TELEMETRY_SCHEMA_VERSION_OPT_IN=otel_semconv_1_36` restores it. | CHANGELOG 2.13.0 |
| 15 | Python >= 3.11 is required for google-adk 2.13.0 | PyPI JSON |

## Industry practice notes (for the "how teams do it" slide)
- **Gateway in front of MCP.** Enterprises aggregate MCP servers behind a gateway for auth, audit and tool shaping. arXiv 2610.23449 (GatewayBench) studies seven such gateways, and arXiv 2608.10760 (Aug 2026) proposes a gateway that unifies heterogeneous auth and identity delegation (title-level claim only; I did not read the paper body). arXiv 2609.22573 (Sep 2026) reports that the official MCP SDKs lack "fine-grained per-tool authorization" and dual-persona (SSO + service account) support. Plan to add these in middleware.
- **MCP for tools, A2A across teams.** Use MCP when you own the tool contract, and A2A when another team owns the agent's behavior and lifecycle. This matches the repo's rule of thumb (`research/05`). arXiv 2607.23884 (Jul 26, 2026), "A Comparative Study of MCP and A2A for Inter-Agent Coordination," is in the date window; I read the title only **[UNVERIFIED findings]**.
- **Skills as the unit of reuse.** Teams ship SKILL.md packages with references and scripts, and gate tools with `adk_additional_tools`. The research above (2610.25064, 2608.12273) says to curate and test skills together, not one at a time.
- **Human approval as a real control.** Bind approvals to effects and log them. The arXiv 2610.21063 audit found no runtime that produced a third-party-verifiable approval record.

## arXiv papers used (all first submitted 2026-07-23 .. 2026-10-23; abstracts read on arxiv.org/abs on 2026-10-23)
| arXiv | Date (v1) | Title | Used in |
|---|---|---|---|
| 2610.22301 | 2026-10-15 | My Credentials, Please: Detecting Filesystem Capability Laundering in MCP Servers at Scale | Lab 1 |
| 2610.14334 | 2026-10-09 | Which Metadata Matters for LLM Tool Selection in MCP? | Lab 2 |
| 2610.23449 | 2026-10-16 | GatewayBench: Unified Capability and Security Evaluation Platform for MCP Gateways | Lab 2, industry |
| 2609.10871 | 2026-09-09 (v2 10-13) | A2ABreak: Systematic Security Analysis of the A2A Protocol | Lab 4 |
| 2609.01693 | 2026-09-01 | Public-Sharing Labels and Verbatim Field Egress in an MCP-to-A2A Agent Configuration | Lab 4 |
| 2610.25064 | 2026-10-18 | One Skill Takes Over: Clashing Agent Skills and a One-File Fix | Lab 5 |
| 2608.12273 | 2026-08-12 | Convergent Detour Hijacking: Task-Preserving Resource Amplification in Skill-Based LLM Agents | Lab 5 |
| 2609.28693 | 2026-09-23 | Progressive Skill Discovery as Access Control for Tool-Using LLM Agents | Lab 5, Lab 6 |
| 2609.28585 | 2026-09-23 | Persistent Billable State: Denial-of-Wallet Attacks and Defenses in Tool-Calling LLM Agents | Lab 6 |
| 2610.21063 | 2026-10-15 | Approve What, Exactly? Effect Binding and Trusted Rendering for Agent Step-Up Authorization | Lab 7 |
| 2608.00150 | 2026-07-31 | Exposed by Design: A Dynamic Security Assessment of Internet-Facing MCP Servers at Scale | Lab 8 |
| 2609.37153 | 2026-09-29 | When Tools Silently Lie: Evaluating and Mitigating Blind Compliance in Tool-Augmented Data Agents | Lab 9 |
| 2609.22573 | 2026-09-18 | Zero-Trust Authorization and Discovery for Enterprise MCP | industry |
| 2609.34971 | 2026-09-28 | Action-Space Shaping for LLM Agents: Measuring and Mitigating Tool-Schema Bias (success "from complete failure to 97% depending solely on the schema") | design note for Labs 2/8 |

Title-only papers in the window (not read; cite only as "see also"): 2608.10760 (MCP auth gateway), 2607.23884 (MCP vs A2A comparative study), 2609.33924 (A2A-ForensicTrace), 2610.26624 (From TCP/IP to MCP).

## Primary sources
- google/adk-python v2.13.0 source (paths cited inline). Samples: `contributing/samples/{mcp,a2a,hitl,tools,plugins,environment_and_skills,code_execution}/`
- modelcontextprotocol/python-sdk v2.3.0: `src/mcp/server/mcpserver/server.py`, `src/mcp/server/fastmcp.py`
- a2aproject/a2a-python v1.2.3: `src/a2a/utils/constants.py`
- adk-docs: `docs/tools-custom/confirmation.md`, `docs/skills/index.md`, `docs/tools-custom/authentication.md`
- PyPI JSON: https://pypi.org/pypi/google-adk/json , /mcp/json , /a2a-sdk/json , /google-genai/json , /uvicorn/json
- MCP server-dev guide (stdout rule): https://modelcontextprotocol.io/docs/develop/build-server
- Codelab: "Getting Started with MCP, ADK and A2A", https://codelabs.developers.google.com/getting-started-mcp-a2a-adk
