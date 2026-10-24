# 05 — ADK Tools, MCP, A2A and Deployment (ADK 2.x, as of 2026-10-23)

Research for the 60-slide ADK 2.0 deck. Every fact links to a source. Items marked **[UNVERIFIED]** could not be confirmed in a primary source during this pass.

---

## 0. Version and naming baseline (read this first)

| Item | Fact | Source |
|---|---|---|
| ADK Python 2.0 GA | **May 19, 2026**. Introduces a Workflow Runtime where agents, tools and functions run as nodes in a graph. | https://adk.dev/2.0/ |
| Latest ADK Python | **v2.13.0 (Oct 23, 2026)**. Promotes 12 experimental features to stable and adds `TypesafeClassifier`/`ClassifierNode` and `ForceEscalationPlugin`. Telemetry now defaults to a newer GenAI schema, which is a breaking change. | https://github.com/google/adk-python/releases |
| 1.x maintenance | v1.39.1 (Aug 27, 2026), a backport line of security fixes | same |
| Session compatibility | Sessions written by ADK 2.0 can be read by 1.28+ (extra fields are ignored) but not by older 1.x | adk-python README |
| Install | `pip install google-adk` (Python 3.10+). Extras: `google-adk[a2a]`, `google-adk[toolbox]` | adk.dev |
| Docs domain | `google.github.io/adk-docs` now 301-redirects to **https://adk.dev** | observed |
| **Vertex AI rename** | Since **Apr 22, 2026** (Cloud Next '26) Vertex AI is **Gemini Enterprise Agent Platform** ("Agent Platform (formerly Vertex AI)"). **Agent Engine became Agent Runtime.** The APIs stay backward compatible: the SDK module is still `vertexai.agent_engines`, resources are still `reasoningEngines/…`, and the CLI command is still `adk deploy agent_engine`. | https://docs.cloud.google.com/gemini-enterprise-agent-platform/release-notes |
| Agent Starter Pack | **In maintenance mode**: "Agent Starter Pack is in maintenance mode — switch to `agents-cli`." | https://github.com/GoogleCloudPlatform/agent-starter-pack |
| MCP spec | Current version **2026-07-28**. Secondary reports say it removes the initialize handshake and `Mcp-Session-Id` header, making requests stateless (SEP-2575 [UNVERIFIED in primary spec text]). | https://modelcontextprotocol.io/docs/learn/versioning |
| A2A | Released Apr 2025. Donated to the Linux Foundation **Jun 23, 2025**. **v1.0 in Mar 2026** (signed Agent Cards, multi-tenancy, JSON-RPC / gRPC / HTTP+JSON bindings). **150+ organizations** at the one-year mark (Apr 2026). Joined the Agentic AI Foundation in Aug 2026 (banner on a2a-protocol.org). | https://www.linuxfoundation.org/press/a2a-protocol-surpasses-150-organizations-lands-in-major-cloud-platforms-and-sees-enterprise-production-use-in-first-year , https://opensource.googleblog.com/2026/04/a-year-of-open-collaboration-celebrating-the-anniversary-of-a2a.html |

Teaching tip: in the slides, say "Agent Runtime (formerly Vertex AI Agent Engine)" every time. Students will find both names online.

---

## 1. The tool taxonomy in ADK

A tool is a capability the LLM can choose to call. The model sees each tool's **name, docstring and typed signature**, then emits a `FunctionCall`. ADK executes the call and returns a `FunctionResponse` to the model.

Diagram in words: `User msg → LlmAgent → model returns FunctionCall(name,args) → ADK runs tool (with ToolContext) → FunctionResponse → model → final text`. Callbacks `before_tool_callback` and `after_tool_callback` wrap the tool step. v2.12 added `after_tool_callback` filtering of tool output before it reaches the model.

Families:
1. **Function tools**: `FunctionTool`, `LongRunningFunctionTool`, `AgentTool`
2. **Built-in (Gemini) tools**: `google_search`, code execution (`BuiltInCodeExecutor`), `VertexAiSearchTool` (Agent Search), computer use
3. **Google Cloud toolsets**: `BigQueryToolset`, Spanner, Bigtable, Pub/Sub, Application Integration, API Hub and others
4. **Toolsets from specs and protocols**: `OpenAPIToolset`, `McpToolset`, `ToolboxToolset` (MCP Toolbox for Databases)
5. **Third-party integrations catalog**: 100+ entries at https://adk.dev/integrations/ (GitHub, Linear, Stripe, Notion, MongoDB, Pinecone, Qdrant, and more)

### 1.1 FunctionTool and ToolContext
Source: https://adk.dev/tools-custom/function-tools/ , https://adk.dev/tools-custom/
```python
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool, ToolContext

def get_weather_report(city: str) -> dict:
    """Retrieves the current weather report for a specified city.
    Args:
        city: The name of the city.
    Returns:
        dict with 'status' and 'report'.
    """
    return {"status": "success", "report": f"Sunny in {city}, 25C"}

def update_user_preference(preference: str, value: str, tool_context: ToolContext):
    """Updates a user preference."""          # do NOT document tool_context
    tool_context.state[f"user:{preference}"] = value
    return {"status": "ok"}

agent = LlmAgent(
    name="weather_agent", model="gemini-flash-latest",
    tools=[FunctionTool(func=get_weather_report), update_user_preference],
)
```
Key facts:
- Plain functions passed in `tools=[...]` are wrapped as `FunctionTool` automatically.
- ADK injects `tool_context` itself. The docs say not to mention it in the docstring.
- `tool_context.actions.transfer_to_agent = "support_agent"` (flow control). `tool_context.state` holds session state (`user:` / `app:` / `temp:` prefixes).
- Return a `dict` with a `status` key. The docs recommend it because the model reads it.

### 1.2 AgentTool (agent-as-a-tool)
```python
from google.adk.tools.agent_tool import AgentTool
root = LlmAgent(name="root", model="gemini-flash-latest",
                tools=[AgentTool(agent=search_agent), AgentTool(agent=coding_agent)])
```
- Unlike `sub_agents` (transfer), control **returns** to the caller.
- `skip_summarization=True` "instructs the framework to bypass the LLM-based summarization" of the tool agent's reply.
Source: https://adk.dev/tools-custom/function-tools/ , https://adk.dev/tools/limitations/

### 1.3 LongRunningFunctionTool (human approval / async jobs)
Source: https://adk.dev/tools-custom/function-tools/
Docs flow, quoted:
1. "When the LLM calls the tool, your function starts the long-running operation."
2. "Your function should optionally return an initial result (e.g. the long-running operation id)." Then "the agent run is ended / paused."
3. "Agent client should send the intermediate or final response back to the agent for the next run."
```python
from typing import Any
from google.adk.tools import LongRunningFunctionTool

def ask_for_approval(purpose: str, amount: float) -> dict[str, Any]:
    """Ask for approval for the reimbursement."""
    # create a ticket in your approval system here
    return {'status': 'pending', 'approver': 'Sean Zhou',
            'purpose': purpose, 'amount': amount, 'ticket-id': 'approval-ticket-1'}

long_running_tool = LongRunningFunctionTool(func=ask_for_approval)

# --- later, client side, when the human approves ---
updated_response = long_running_function_response.model_copy(deep=True)
updated_response.response = {'status': 'approved'}
# send back as types.Content(parts=[types.Part(function_response=updated_response)], role='user')
```
With Resume, "The Invocation ID you provide must be the same invocation that generated the long running function request."

### 1.4 Tool confirmation (Human-in-the-Loop, "action confirmations")
Source: https://adk.dev/tools-custom/confirmation/ . Experimental. Supported in Python v1.14.0+, TS v0.2.0, Go v0.3.0, Kotlin v0.1.0.

Boolean or callable gate:
```python
from google.adk.tools import FunctionTool, ToolContext

async def confirmation_threshold(amount: int, tool_context: ToolContext) -> bool:
    """Returns true if the amount is greater than 1000."""
    return amount > 1000

tools = [
    FunctionTool(reimburse, require_confirmation=True),                   # always ask
    FunctionTool(reimburse_big, require_confirmation=confirmation_threshold),  # ask only if > 1000
]
```
Advanced: structured confirmation with a payload (adapted from the `request_time_off` docs example):
```python
def request_time_off(days: int, tool_context: ToolContext):
    """Request day off for the employee."""
    tool_confirmation = tool_context.tool_confirmation
    if not tool_confirmation:
        tool_context.request_confirmation(
            hint=("Please approve or reject the tool call request_time_off() by "
                  "responding with a FunctionResponse with an expected ToolConfirmation payload."),
            payload={'approved_days': 0},
        )
        return {'status': 'Manager approval is required.'}
    approved_days = min(tool_confirmation.payload['approved_days'], days)
    if approved_days == 0:
        return {'status': 'The time off request is rejected.', 'approved_days': 0}
    return {'status': 'ok', 'approved_days': approved_days}
```
- Over REST, the client answers with a `FunctionResponse` named **`adk_request_confirmation`** whose response includes `"confirmed": true` (plus a payload).
- Documented limitation: `DatabaseSessionService` and `VertexAiSessionService` are not supported [may be lifted in 2.x, UNVERIFIED].
- ADK 2.x adds the same idea to workflow graphs: v2.11 made tool nodes pause for confirmation via `RequestInput`, and v2.12 added `require_confirmation` for workflow nodes.

---

## 2. Built-in tools (Gemini-native)

| Tool | Import | Notes |
|---|---|---|
| Google Search grounding | `from google.adk.tools import google_search` | Docs say "only compatible with Gemini 2 models" (examples use `gemini-flash-latest`). You must display search suggestions (`renderedContent`) in production. https://adk.dev/integrations/google-search/ |
| Code execution | `from google.adk.code_executors import BuiltInCodeExecutor` → `LlmAgent(code_executor=BuiltInCodeExecutor())` | Code runs in Gemini's sandbox. Other executors appear in the catalog: GKE Code Executor and "Code Execution Tool with Agent Runtime". https://adk.dev/integrations/code-execution/ |
| Vertex AI Search / "Agent Search" | `from google.adk.tools import VertexAiSearchTool` → `VertexAiSearchTool(data_store_id=PATH)` | PATH = `projects/<P>/locations/<us-central1\|global>/collections/default_collection/dataStores/<ID>`. https://adk.dev/integrations/agent-search/ |
| Computer Use | catalog entry `computer-use` | v2.13 adds Gemini 3.x computer-use browser action schemas |

```python
from google.adk.agents import LlmAgent
from google.adk.tools import google_search
search_agent = LlmAgent(name="search_agent", model="gemini-flash-latest",
    instruction="Answer using Google Search. Cite sources.", tools=[google_search])
```

**Limitations** (https://adk.dev/tools/limitations/):
- The one-built-in-per-agent rule: "use of specific tools within an agent excludes the use of any other tools in that agent" (Search, Agent Search, Code Execution).
- "Built-in tools cannot be used within a sub-agent," except `GoogleSearchTool` and `VertexAiSearchTool` in Python.
- Workaround 1: wrap each specialist in `AgentTool`.
- Workaround 2 (Python ≥ v1.16.0): `GoogleSearchTool(bypass_multi_tools_limit=True)` / `VertexAiSearchTool(..., bypass_multi_tools_limit=True)`. See the `built_in_multi_tools` sample.

### 2.1 BigQuery toolset (first-party Google Cloud)
Source: https://adk.dev/integrations/bigquery/
```python
import google.auth
from google.adk.integrations.bigquery import BigQueryToolset, BigQueryCredentialsConfig
from google.adk.integrations.bigquery.config import BigQueryToolConfig, WriteMode

creds, _ = google.auth.default()
credentials_config = BigQueryCredentialsConfig(credentials=creds)
tool_config = BigQueryToolConfig(write_mode=WriteMode.BLOCKED)   # block any write ops
bigquery_toolset = BigQueryToolset(credentials_config=credentials_config,
                                   bigquery_tool_config=tool_config)
```
- Tools: `list_dataset_ids`, `get_dataset_info`, `list_table_ids`, `get_table_info`, `get_job_info`, `execute_sql`, `forecast`, `analyze_contribution`, `detect_anomalies`, `ask_data_insights`, `search_catalog`.
- Path note: the current docs use `google.adk.integrations.bigquery`. 1.x tutorials use `google.adk.tools.bigquery`. Whether the old path still works as an alias is [UNVERIFIED].
- v2.8 added a BigQuery SQL-injection guard (release notes).

---

## 3. OpenAPIToolset (any REST API from a spec)
Source: https://adk.dev/tools-custom/openapi-tools/
```python
from google.adk.tools.openapi_tool.openapi_spec_parser.openapi_toolset import OpenAPIToolset
from google.adk.tools.openapi_tool.auth.auth_helpers import token_to_scheme_credential

auth_scheme, auth_credential = token_to_scheme_credential(
    "apikey", "query", "apikey", "YOUR_API_KEY")
toolset = OpenAPIToolset(spec_str=openapi_spec_json, spec_str_type="json",
                         auth_scheme=auth_scheme, auth_credential=auth_credential)
agent = LlmAgent(name="petstore_agent", model="gemini-flash-latest", tools=[toolset])
```
- The spec can be passed as `spec_dict`, a JSON string or a YAML string.
- ADK creates one `RestApiTool` per operation. The tool name is the `operationId` in snake_case, capped at **60 chars**. Without an `operationId`, the name comes from the method and path.

## 4. Tool authentication
Source: https://adk.dev/tools-custom/authentication/
- **AuthScheme** describes how the API expects credentials. It follows OpenAPI 3.0: `APIKey`, `HTTPBearer`, `OAuth2`, `OpenIdConnectWithConfig`.
- **AuthCredential** holds the starting secrets. `auth_type` is one of `API_KEY | HTTP | OAUTH2 | OPEN_ID_CONNECT | SERVICE_ACCOUNT`.
- Imports: `from google.adk.auth import AuthCredential, AuthCredentialTypes, OAuth2Auth, AuthConfig`; `from google.adk.auth.auth_schemes import OpenIdConnectWithConfig`; helpers `token_to_scheme_credential`, `service_account_dict_to_scheme_credential`, `service_account_scheme_credential` in `google.adk.tools.openapi_tool.auth.auth_helpers`.

**Interactive OAuth flow (7 steps, good animated slide):**
1. Run `runner.run_async`. An event arrives with a function call named **`adk_request_credential`**.
2. Read the `AuthConfig`. `auth_uri` is the base authorization URL.
3. Append `redirect_uri` and send the user to the provider.
4. The user consents. Capture the full callback URL.
5. Set `auth_response_uri` and `redirect_uri` on `exchanged_auth_credential.oauth2`.
6. Send a `FunctionResponse` named `adk_request_credential` with the same call id, then call `run_async` again.
7. ADK exchanges the code for tokens, stores them in session state and **retries the original tool call**.
- Platform-level complements in the integrations catalog: **Google Cloud Agent Identity**, **Secret Manager** and **Parameter Manager**.

---

## 5. MCP in ADK

### 5.1 Consuming MCP servers: `McpToolset`
Source: https://adk.dev/tools-custom/mcp-tools/
```python
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import (
    StdioConnectionParams, StreamableHTTPConnectionParams)
from mcp import StdioServerParameters

fs_tools = McpToolset(                                   # local subprocess (stdio)
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", TARGET_FOLDER]),
        timeout=5),
    tool_filter=["list_directory", "read_file"],         # least privilege
)
maps_tools = McpToolset(                                 # remote (streamable HTTP)
    connection_params=StreamableHTTPConnectionParams(
        url="https://mapstools.googleapis.com/mcp",
        headers={"X-Goog-Api-Key": API_KEY,
                 "Accept": "application/json, text/event-stream"},
        timeout=5, sse_read_timeout=300))
root_agent = LlmAgent(name="fs_maps", model="gemini-flash-latest",
                      tools=[fs_tools, maps_tools])
```
- Class name: the current docs spell it **`McpToolset`**. Older tutorials use `MCPToolset`. Both names appear in the wild, and whether the old one is still an alias is [UNVERIFIED].
- The docs advise: "Always supply `tool_filter=[...]`".
- Lifecycle: the toolset opens the MCP session, calls `list_tools`, turns each MCP tool into an ADK tool (`MCPTool`), and proxies each `call_tool`.
- Timeline: v2.9.0 added **MCP SDK 2.x** support next to 1.x. v2.10 sends an ADK client identity in the MCP handshake. v2.11 adds an opt-in "modern-protocol" connection path. v2.8 reports MCP HTTP exchanges as OpenTelemetry logs.
- Deployment patterns for MCP with ADK: https://adk.dev/tools-custom/mcp-tools/deployment/ . Sub-agent delegation: `/tools-custom/mcp-tools/agent-managed/`.

### 5.2 Exposing ADK as an MCP server
Source: https://adk.dev/tools-custom/mcp-tools/agent-as-server/
**(a) Whole agent → MCP server (one line):**
```python
from google.adk.agents import LlmAgent
from google.adk.tools.load_web_page import load_web_page
from google.adk.tools.mcp_tool import to_mcp_server

agent = LlmAgent(name="web_reader", model="gemini-flash-latest",
                 instruction="Summarize web pages.", tools=[load_web_page])
app = to_mcp_server(agent)          # returns a FastMCP server
if __name__ == "__main__":
    app.run()                       # stdio by default
```
(Adapted from the docs description. The docs cover stdio only, so HTTP transport via FastMCP is [UNVERIFIED].)

**(b) Individual ADK tools → a hand-built MCP server:** run `pip install mcp`, wrap the tool in `FunctionTool`, implement `@app.list_tools()` returning `adk_to_mcp_tool_type(tool)` (from `google.adk.tools.mcp_tool.conversion_utils`), and implement `@app.call_tool()` → `await tool.run_async(args=..., tool_context=None)` → `mcp_types.TextContent`.

### 5.3 MCP Toolbox for Databases
Sources: https://adk.dev/integrations/mcp-toolbox-for-databases/ , https://github.com/googleapis/mcp-toolbox
- Renamed from "Gen AI Toolbox for Databases". The repo moved from `googleapis/genai-toolbox` to **`googleapis/mcp-toolbox`**. Install docs use **v1.15.0**.
- Architecture: Agent → (Toolbox SDK or MCP) → **Toolbox server** (Go binary: connection pooling, auth, OTel) → database. You declare SQL tools in YAML, and the agent never writes raw credentials.
- 40+ sources: BigQuery, AlloyDB, Spanner, Cloud SQL (PG/MySQL/SQL Server), Firestore, Bigtable, Looker, PostgreSQL, MySQL, SQLite, Oracle, Snowflake, Trino, MongoDB, Redis, Neo4j, Elasticsearch, Cassandra, ClickHouse and more.
```bash
export VERSION=1.15.0
curl -L -o toolbox https://storage.googleapis.com/mcp-toolbox-for-databases/v$VERSION/linux/amd64/toolbox
chmod +x toolbox && ./toolbox --config "tools.yaml"      # or: brew install mcp-toolbox
./toolbox --prebuilt=postgres --stdio                    # prebuilt tool set as MCP stdio server
```
```yaml
kind: source
name: my-pg-source
type: postgres
host: 127.0.0.1
port: 5432
database: toolbox_db
user: toolbox_user
password: my-password
---
kind: tool
name: search-hotels-by-name
type: postgres-sql
source: my-pg-source
description: Search for hotels based on name.
parameters:
  - name: name
    type: string
    description: The name of the hotel.
statement: SELECT * FROM hotels WHERE name ILIKE '%' || $1 || '%';
---
kind: toolset
name: my-toolset
tools: [search-hotels-by-name]
```
(The source block is verbatim. The tool and toolset blocks are reassembled from README fragments, and the exact field order is [UNVERIFIED].)
```python
# pip install google-adk[toolbox]
from google.adk.tools.toolbox_toolset import ToolboxToolset
toolset = ToolboxToolset(server_url="http://127.0.0.1:5000")
agent = LlmAgent(name="hotel_agent", model="gemini-flash-latest", tools=[toolset])
```
Framework-agnostic SDK: `pip install toolbox-core` → `async with ToolboxClient("http://127.0.0.1:5000") as c: tools = await c.load_toolset("toolset_name")`.

---

## 6. A2A protocol in ADK

### 6.1 Concepts (https://a2a-protocol.org/latest/topics/key-concepts/)
- **Actors:** User → A2A Client (client agent) → A2A Server (remote agent, opaque).
- **Agent Card:** a JSON discovery document with identity, endpoint URL, capabilities, auth requirements and **skills**. It is served at `/.well-known/agent-card.json`. v1.0 supports **signed** cards.
- **Task:** a stateful unit with an id and a lifecycle, for long-running and multi-turn work. **Message:** one turn (`role` user/agent, `messageId`, Parts). **Part:** `text` | `raw` | `url` | `data`. **Artifact:** a deliverable made of Parts that can be streamed. `contextId` groups related tasks.
- **Transport:** HTTP(S) + JSON-RPC 2.0. v1.0 adds gRPC and HTTP+JSON bindings. Interaction modes: polling, **SSE streaming** and **push notifications** (webhooks).
- Quotable lines: "An open protocol enabling communication and interoperability between opaque agentic applications." / "MCP standardizes how an agent connects to tools… A2A standardizes how independent agents discover each other, delegate tasks, and share results." (a2a-protocol.org)
- ADK's A2A support is marked **Experimental** in Python, Go and Java (consuming also works in Kotlin). https://adk.dev/a2a/

### 6.2 Exposing: `to_a2a`
Source: https://adk.dev/a2a/quickstart-exposing/
```python
# pip install google-adk[a2a]
from google.adk.agents import LlmAgent
from google.adk.a2a.utils.agent_to_a2a import to_a2a

root_agent = LlmAgent(name="check_prime_agent", model="gemini-flash-latest",
                      instruction="Check whether numbers are prime.", tools=[check_prime])
a2a_app = to_a2a(root_agent, port=8001)   # ASGI app; agent card auto-generated
```
```bash
uvicorn my_pkg.remote_agent.agent:a2a_app --host localhost --port 8001
curl http://localhost:8001/.well-known/agent-card.json
# alternative: adk api_server --a2a <agents_dir>   (requires a hand-written agent.json card)
```
- The `port` value is written into the card URL, so it must match the port you serve on. You can pass your own `AgentCard` object or a JSON file path instead.

### 6.3 Consuming: `RemoteA2aAgent`
Source: https://adk.dev/a2a/quickstart-consuming/
```python
from google.adk.agents import LlmAgent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent, AGENT_CARD_WELL_KNOWN_PATH

prime_agent = RemoteA2aAgent(
    name="prime_agent",
    description="Agent that handles checking if numbers are prime.",
    agent_card=f"http://localhost:8001/a2a/check_prime_agent{AGENT_CARD_WELL_KNOWN_PATH}",
)
root_agent = LlmAgent(name="root_agent", model="gemini-flash-latest",
    instruction="Roll dice locally; delegate prime checks to prime_agent.",
    sub_agents=[roll_agent, prime_agent])
```
- `name` and `agent_card` are required. `agent_card` can be an `AgentCard` object, a URL or a local file path.
- The remote agent behaves like any local sub-agent: the root's LLM transfers to it, and ADK translates events ⇄ A2A messages and tasks.
- 2.x additions: native **task mode** (v2.8), optional `context_builder` (v2.10), tool_call/tool_response handling and a namespaced `context_id` mode (v2.12), and delegation fixes plus `transfer_reason` (v2.9). An "A2A Extension (V2)" guide covers Python: https://adk.dev/a2a/a2a-extension/

Diagram in words: `root_agent (LLM) --transfer--> RemoteA2aAgent --GET /.well-known/agent-card.json--> remote server; --message/send (JSON-RPC)--> Task{submitted→working→completed} --Artifacts--> back into root session as events`.

---

## 7. Deployment

| Target | Command | Source |
|---|---|---|
| **Agent Runtime** (formerly Vertex AI Agent Engine) | `adk deploy agent_engine --project=$PROJECT_ID --region=$LOCATION_ID --display_name="My First Agent" multi_tool_agent` | https://adk.dev/deploy/agent-runtime/deploy/ |
| **Cloud Run** | `adk deploy cloud_run --project=$GOOGLE_CLOUD_PROJECT --region=$GOOGLE_CLOUD_LOCATION --service_name=$SERVICE_NAME --app_name=$APP_NAME --with_ui $AGENT_PATH` | https://adk.dev/deploy/cloud-run/ |
| Cloud Run (raw) | `gcloud run deploy capital-agent-service --source . --region $GOOGLE_CLOUD_LOCATION --project $GOOGLE_CLOUD_PROJECT --allow-unauthenticated --set-env-vars="GOOGLE_CLOUD_PROJECT=...,GOOGLE_CLOUD_LOCATION=...,GOOGLE_GENAI_USE_ENTERPRISE=True"` | same |
| **GKE** | `adk deploy gke --project myproject --cluster_name test --region us-central1 --with_ui --log_level info AGENT_PATH` (`--service_type ClusterIP\|LoadBalancer`) | https://adk.dev/deploy/gke/ |

- Agent Runtime: "Agent Runtime is a set of modular services that help developers scale and govern agents in production." The Python upload leaves out the ADK API server and web UI libraries. Output resource: `projects/…/locations/us-central1/reasoningEngines/<id>`, fetched with `vertexai.agent_engines.get(...)`. v2.12 added a custom service account option for Agent Engine deploys. Go CLI spelling: `agentengine`.
- GKE: grant `roles/aiplatform.user` to the K8s `default` service account via **Workload Identity**, otherwise model calls return 403. Create an Artifact Registry repo first (`gcloud artifacts repositories create adk-repo ...`). Check with `kubectl get pods` and `kubectl port-forward svc/adk-default-service-name 8080:80`.
- A custom FastAPI server works on any container host:
```python
from fastapi import FastAPI
from google.adk.cli.fast_api import get_fast_api_app
app: FastAPI = get_fast_api_app(agents_dir=AGENT_DIR,
    session_service_uri=SESSION_SERVICE_URI, allow_origins=ALLOWED_ORIGINS,
    web=SERVE_WEB_INTERFACE)
```

### 7.1 Agent Starter Pack → agents-cli
- **Agent Starter Pack** (https://github.com/GoogleCloudPlatform/agent-starter-pack): `uvx agent-starter-pack create` / `enhance`. Templates: `adk`, `adk_a2a`, `agentic_rag`, `langgraph`, `adk_java`, `adk_live`. Ships Terraform, CI/CD and observability for Cloud Run and Agent Engine. **Now in maintenance mode**: "no new features, no new templates, no new deployment targets." Migration guide: https://google.github.io/agents-cli/reference/from-agent-starter-pack/
- **agents-cli** (https://google.github.io/agents-cli/): "CLI and skills for building agents on Google Cloud." Set up with `uvx google-agents-cli setup`, which installs the CLI and **skills into coding agents**.
  - Commands (https://google.github.io/agents-cli/cli/): `scaffold create|enhance|upgrade`, `create`, `playground`, `run`, `deploy`, `eval generate|grade|run|compare|optimize (GEPA)`, `infra single-project|setup-cicd`, `publish gemini`, `lint`, `login`.
  - Deployment targets: `agent_runtime | cloud_run | gke` (plus `none` for scaffolding).
```bash
uvx google-agents-cli setup
agents-cli scaffold create my-agent
agents-cli scaffold enhance --deployment-target agent_runtime
agents-cli deploy                       # builds a container, deploys to the target in pyproject.toml
agents-cli infra setup-cicd             # multi-env Terraform + CI/CD
agents-cli publish gemini               # register the deployed agent with Gemini (Enterprise)
```

---

## 8. Codelabs, repos and talks to cite

- Codelab: **"Getting Started with MCP, ADK and A2A"** (currency agent, Jack Wotherspoon; last updated Jun 25, 2025, so check for API drift). Builds a FastMCP server, deploys it to Cloud Run, connects an ADK agent via MCP and exposes it with A2A. https://codelabs.developers.google.com/codelabs/currency-agent . Sample repo: https://github.com/jackwotherspoon/currency-agent
- Repos: https://github.com/google/adk-python (releases), https://github.com/google/adk-samples [samples repo name per common usage; UNVERIFIED this pass], https://github.com/googleapis/mcp-toolbox , https://github.com/GoogleCloudPlatform/agent-starter-pack , https://github.com/a2aproject/A2A [UNVERIFIED org path this pass]
- Docs: https://adk.dev/tools-custom/ , https://adk.dev/tools-custom/mcp-tools/ , https://adk.dev/a2a/ , https://adk.dev/deploy/
- Blog: "A year of open collaboration: Celebrating the anniversary of A2A" (Google Open Source Blog, Apr 2026) https://opensource.googleblog.com/2026/04/a-year-of-open-collaboration-celebrating-the-anniversary-of-a2a.html
- Linux Foundation press: "A2A Protocol Surpasses 150 Organizations, Lands in Major Cloud Platforms…" https://www.linuxfoundation.org/press/a2a-protocol-surpasses-150-organizations-lands-in-major-cloud-platforms-and-sees-enterprise-production-use-in-first-year
- MCP versioning: https://modelcontextprotocol.io/docs/learn/versioning
- YouTube talks: none verified in this pass [UNVERIFIED]. Look for Cloud Next '26 ADK, Agent Platform and A2A sessions.

## 9. Real-world examples
- A2A launch partners (more than 50, 2025): Atlassian, Box, Cohere, Elastic, LangChain, MongoDB, PayPal, Salesforce, SAP, ServiceNow, UiPath, Accenture, Deloitte. The TSC (2026) includes AWS, Cisco, Google, IBM Research, Microsoft, Salesforce, SAP and ServiceNow. The LF press release cites "deep integration across Google, Microsoft and AWS platforms."
- Google's own remote MCP servers: the Maps tools endpoint `https://mapstools.googleapis.com/mcp` appears in the ADK docs. The Google Developer Knowledge MCP is in the integrations catalog.
- The ADK integrations catalog lists vendor-maintained toolsets from GitHub, GitLab, Linear, Atlassian, Asana, Notion, Stripe, PayPal, Postman, MongoDB, Pinecone, Qdrant, Redis, Couchbase, Hugging Face and others: https://adk.dev/integrations/

## 10. Quotable lines
- "use of specific tools within an agent excludes the use of any other tools in that agent." (ADK limitations)
- "Always supply `tool_filter=[...]`" (ADK MCP docs, on least privilege)
- "A2A is for agent-to-agent communication… a machine-to-machine protocol for autonomous agents." (a2a-protocol.org)
- "Agent Runtime is a set of modular services that help developers scale and govern agents in production." (adk.dev/deploy/agent-runtime)
- "Agent Starter Pack is in maintenance mode — switch to `agents-cli`." (ASP README)
- Rule of thumb for the deck (ours, not quoted): **MCP = agent ↔ tools/data (vertical); A2A = agent ↔ agent (horizontal); ADK = the runtime that speaks both.**

---

## Slide ideas (8)

1. **"Anatomy of a tool call"**: animated sequence diagram User → LlmAgent → Gemini → `FunctionCall` → FunctionTool(+ToolContext) → `FunctionResponse` → answer. Callback hooks light up as the call passes them.
2. **"The tool zoo"**: a 5-ring map (Function / Built-in / Cloud toolsets / Spec+Protocol toolsets / Integrations catalog) with one import line per ring. Clicking a ring reveals its snippet.
3. **"The one-built-in rule and how to escape it"**: a red "X" over an agent holding `google_search` + a function tool, then morph to a root agent holding two `AgentTool`s, with a footnote on `bypass_multi_tools_limit=True`.
4. **"Pause, approve, resume"**: a swimlane (Agent / Tool / Human / Client) for `require_confirmation` and `LongRunningFunctionTool`, showing the `adk_request_confirmation` FunctionResponse returning. The run is frozen in a grey band during the pause.
5. **"OAuth in 7 steps"**: a numbered loop between ADK, client app, browser and identity provider, ending with "ADK retries the original tool call".
6. **"MCP both ways"**: split screen. Left: `McpToolset` (stdio subprocess icon vs. HTTP cloud icon). Right: `to_mcp_server(agent)` turns an ADK agent into a tool for Claude Desktop, IDEs and others. Animated arrows reverse direction.
7. **"Databases without secrets in prompts"**: Agent → ToolboxToolset → Toolbox server (pooling, auth, OTel) → 40+ DB logos, with tools.yaml on the side and the SQL template highlighted.
8. **"A2A handshake"**: discovery (`GET /.well-known/agent-card.json`) → `message/send` → Task state machine (submitted→working→input-required→completed) → Artifacts streamed via SSE. Code panes for `to_a2a` and `RemoteA2aAgent` side by side.
9. **"MCP vs A2A"**: a 2x2 table (who talks, unit of work, discovery, state), with the vertical vs. horizontal axes metaphor.
10. **"From laptop to production"**: a three-lane highway (Agent Runtime / Cloud Run / GKE), each lane with its one-liner `adk deploy ...` and an `agents-cli deploy --deployment-target` overlay. A banner reads "Vertex AI → Agent Platform (Apr 2026); Agent Engine → Agent Runtime; ASP → agents-cli".
