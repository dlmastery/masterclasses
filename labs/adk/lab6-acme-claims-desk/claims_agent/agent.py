"""Acme claims desk agent: two MCP toolsets and one OpenAPI toolset.

google-adk 2.13.0, mcp 2.3.0. Start claims_api.py (terminal 1) and
handbook_server.py (terminal 2) before adk: this file fetches the
OpenAPI spec when it is imported.
"""
import os
import pathlib
import sys

import httpx
from google.adk.agents import LlmAgent
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.tools.mcp_tool import (
    McpToolset, StdioConnectionParams, StreamableHTTPConnectionParams)
from google.adk.tools.openapi_tool.auth.auth_helpers import token_to_scheme_credential
from google.adk.tools.openapi_tool.openapi_spec_parser.openapi_toolset import (
    OpenAPIToolset)
from mcp import StdioServerParameters

SERVER = pathlib.Path(__file__).parent / "claims_server.py"


# ---- step 2: stdio MCP server, least privilege ---------------------------
def payout_needs_human(**kwargs) -> bool:  # gets the call's args
    """Toolset-wide confirmation rule: only big payouts need a human."""
    return float(kwargs.get("approved_amount", 0)) > 1000


claims_tools = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command=sys.executable, args=[str(SERVER)]),  # same venv
        timeout=10.0),                                    # default 5.0 s
    tool_filter=["get_claim", "approve_claim", "login"],  # no purge_claim
    tool_name_prefix="claims",                            # claims_get_claim
    require_confirmation=payout_needs_human,
)


# ---- steps 3-4: streamable HTTP MCP server with tenant identity ----------
def tenant_headers(ctx: ReadonlyContext) -> dict[str, str]:
    # user: state is set at login, never by the model
    tenant = ctx.state.get("user:tenant")
    if not tenant:
        raise ValueError("no user:tenant in state")  # fail closed
    return {"X-Tenant-ID": tenant}


handbook_tools = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="http://127.0.0.1:3000/mcp",  # path defaults to /mcp
        timeout=5.0,                      # connect, default 5.0 s
        sse_read_timeout=300.0),          # streamed reads, 300 s
    tool_filter=["search_policy", "list_topics"],
    tool_name_prefix="handbook",          # handbook_search_policy
    header_provider=tenant_headers,  # one session per identity
    tool_list_cache_ttl_seconds=300,   # tools/list reused for 5 minutes
)


# ---- build: the claims-status REST API through OpenAPIToolset ------------
SPEC_URL = "http://127.0.0.1:8081/openapi.json"
spec = httpx.get(SPEC_URL, timeout=5).json()   # at import time
auth_scheme, auth_credential = token_to_scheme_credential(  # no default key
    "apikey", "header", "X-API-Key", os.environ["CLAIMS_API_KEY"])

claims_status = OpenAPIToolset(
    spec_dict=spec,
    auth_scheme=auth_scheme,
    auth_credential=auth_credential,
    tool_filter=["get_claim_status"],   # snake_case(operationId)
    allow_private_network_access=True,  # 127.0.0.1: dev only
)

root_agent = LlmAgent(
    name="claims_desk",
    model="gemini-3.5-flash",
    instruction=(
        "You help Acme claims adjusters. Look up a claim before approving it. "
        "Pay at most the claimed amount. "
        "Answer coverage only from handbook_search_policy."),
    tools=[claims_tools, handbook_tools, claims_status],
)

# Optional: for third-party MCP servers whose errors you cannot edit,
# register the error-rewriting plugin on an App (the loader prefers `app`):
# from google.adk.apps import App
# from .agent_errors import AgentErrorPlugin
# app = App(name="claims_agent", root_agent=root_agent,
#           plugins=[AgentErrorPlugin()])
