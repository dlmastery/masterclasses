# 02 — Managed Agents on Google Cloud (Oct 2026): Agent Runtime (formerly Vertex AI Agent Engine) on Gemini Enterprise Agent Platform

> Research date: 2026-10-23. Sources were fetched directly from primary URLs: docs.cloud.google.com, adk.dev (the new home of google.github.io/adk-docs), the github.com/google/adk-python source and CHANGELOG, the googleapis/python-aiplatform source, PyPI, the Google Cloud Blog and codelabs. The web-search quota ran out during this session, so this pass used direct fetches only. Anything I could not confirm against a primary page is marked **[UNVERIFIED]**.

---

## 1. Naming: what things are called now, and the rename history

The naming changes are the main source of confusion, so the deck should lead with them.

| Date | Event | Source |
|---|---|---|
| 2024 | Managed agent hosting first ships as **Reasoning Engine** ("LangChain on Vertex AI"). The REST resource is still `reasoningEngines` today. | Resource name verified in deploy docs; the 2024 date is **[UNVERIFIED]** |
| ~early 2025 | Renamed to **Vertex AI Agent Engine** (part of "Vertex AI Agent Builder"). | **[UNVERIFIED exact date]** |
| 2025-10-09 | **Gemini Enterprise** launched. Release note: "Google Agentspace is part of Gemini Enterprise". The "Google Agentspace experience" is "now referred to as Gemini Enterprise." | Gemini Enterprise release notes; blog "Introducing Gemini Enterprise" (Oct 9, 2025) |
| 2025-11-17 | Gemini Enterprise can register ADK agents "hosted on the Vertex AI Agent Engine". | Gemini Enterprise release notes |
| **2026-04-22** (Cloud Next 2026) | **Gemini Enterprise Agent Platform** launched as "an evolution of Vertex AI". Release note: "**Agent Engine is now Agent Runtime.**" Memory Bank becomes **Agent Platform Memory Bank**. Sessions becomes **Agent Platform Sessions**. Agent Identity reaches GA, Agent Registry enters Public Preview, Agent Gateway enters Private Preview. Long-running operations are supported for up to 7 days. | Agent Platform release notes; blog "Introducing Gemini Enterprise Agent Platform…" (Apr 22, 2026, Gerstenhaber and Bachman) |
| 2026-06-18 | Agent Gateway GA, Agent Registry GA (v1 API, A2A v1), and **Agent Observability GA** with tracing on by default for new ADK deployments. | Release notes |
| 2026-09-03 | In Gemini Enterprise, **Workflow Builder (formerly Agent Designer)** reaches GA and can import existing A2A and ADK agents. | Gemini Enterprise release notes |
| **2026-09-18** | **Agent Platform SDK for Python 2.0.1** ships as a breaking change. Generative AI modules move to the Google Gen AI SDK, and the agent surface splits out into **`google-cloud-agentplatform`**. `agent_engines` is renamed to `runtimes`. | Release notes; SDK migration page |

Official mapping excerpts, from https://docs.cloud.google.com/gemini-enterprise-agent-platform/vertex-ai-name-changes:
- Vertex AI Platform → **Gemini Enterprise Agent Platform** (short form "Agent Platform")
- Vertex AI Agent Engine → **Agent Runtime on Gemini Enterprise Agent Platform**
- Vertex AI Agent Engine Memory Bank / Sessions / Code Execution → **Gemini Enterprise Agent Platform Memory Bank / Sessions / Code Execution**
- Vertex AI Studio → **Agent Studio**; Vertex AI Search → **Agent Search**; Vector Search 2.0 → **Agent Retrieval**; Gen AI evaluation service → **Gemini Enterprise Agent Platform Evals**

Several old identifiers have not changed (all verified in the 2026 docs and source):
- The REST resource is still `projects/PROJECT_NUMBER/locations/LOCATION/reasoningEngines/RESOURCE_ID`.
- The endpoint is still `https://LOCATION-aiplatform.googleapis.com/v1/...`.
- IAM roles keep the `roles/aiplatform.*` prefix.
- The ADK CLI command is still `adk deploy agent_engine`, and there is no `agent_runtime` alias in `cli_tools_click.py`.
- The config file is still `.agent_engine_config.json`.
- Environment variables are still `GOOGLE_CLOUD_AGENT_ENGINE_*`.
- Doc URLs under `/vertex-ai/generative-ai/docs/agent-engine/*` now 301-redirect to docs.cloud.google.com, and adk.dev redirects `/deploy/agent-engine/` to `/deploy/agent-runtime/`.

**Platform pillars**, from https://docs.cloud.google.com/gemini-enterprise-agent-platform/overview:
- **Build:** ADK, Agent Studio, Agent Garden, CodeMender, Model Garden, RAG Engine, Vector Search, Managed Agents API
- **Scale:** Agent Runtime, Sessions, Memory Bank, Code Execution
- **Govern:** Agent Registry, Agent Identity, Agent Gateway, Governance Policies, AI threat scanning
- **Optimize:** Agent evaluation, Simulation, Observability, prompt optimization

**Gemini Enterprise and Agent Platform are different products.** Gemini Enterprise (formerly Agentspace) is the employee-facing app: chat, connectors, prebuilt agents and Workflow Builder. Gemini Enterprise Agent Platform (formerly Vertex AI) is the developer platform where agents are built, hosted and governed. Agents hosted on Agent Runtime are *published into* Gemini Enterprise, for example with `agents-cli publish gemini`.

---

## 2. Agent Runtime: what it is

Agent Runtime is a managed, serverless runtime for agentic apps. It handles the API server, scaling, sessions, memory, identity, and tracing, logging and monitoring. (Sources: overview page; blog of Apr 22, 2026.)

- **Frameworks**
  - Full integration: ADK, through the `adk` CLI for Python and `adkgo` for Go.
  - Managed SDK templates: LangChain, LangGraph, AG2 and LlamaIndex.
  - Custom template: CrewAI or a custom framework.
  - Any container that follows the "runtime contract".
- **What the Apr 2026 release added**
  - "Re-engineered Agent Runtime with **sub-second cold starts**" and multi-day long-running agents. The release notes give "up to 7 days".
  - WebSocket bidirectional streaming.
  - Custom Session IDs.
  - Memory Profiles.
  - Agent Sandbox for code and browser automation.
- **A2A on Agent Runtime** is labeled "preview" on the runtime overview page.
- **Scale numbers** (blog): more than 6 trillion tokens a month on Gemini through ADK, and more than 200 models in Model Garden. Named customers include Comcast, PayPal, L'Oréal and Payhawk. Payhawk reports that Memory Bank cut submission time by more than 50%.
- **Security support:** VPC-SC, CMEK, data residency at rest, HIPAA, Access Transparency and Access Approval. These apply to Runtime, Sessions, Memory Bank and Code Execution. **Example Store has no listed security features and is still Preview.**

### Architecture flow (diagram in words)
1. A client (a web app, Gemini Enterprise, another agent over A2A) sends a call.
2. Agent Gateway (optional; handles policy, Model Armor and egress control) passes it to `POST …/reasoningEngines/ID:streamQuery?alt=sse` with `class_method: async_stream_query`.
3. The Agent Runtime container (`AdkApp` → ADK `Runner`) loads the session from **Sessions** (`VertexAiSessionService`, selected automatically because `GOOGLE_CLOUD_AGENT_ENGINE_ID` is set).
4. The agent runs its LLM and tool loop. It calls Gemini, MCP tools, and the **Code Execution** sandbox. Outbound calls authenticate with the agent's **Agent Identity** (an X.509 certificate valid 24 hours, with bound access tokens).
5. Events are appended to the session, then optionally ingested into **Memory Bank**, which extracts and consolidates memories per scope `{app_name, user_id}`.
6. OpenTelemetry spans, logs and metrics go to Cloud Trace, Logging and Monitoring, which feed the **Agent Observability** dashboards and online eval monitors.

---

## 3. Deploying ADK to Agent Runtime: CLI paths

### 3a. ADK CLI (Python): `adk deploy agent_engine`
Source: https://adk.dev/deploy/agent-runtime/deploy/ and `src/google/adk/cli/cli_tools_click.py`. The latest ADK is **2.13.0 (2026-10-22)**; ADK 2.0 went GA on **2026-05-19**.
```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project MY-PROJECT-ID

PROJECT_ID=my-project-id
LOCATION_ID=us-central1
adk deploy agent_engine \
        --project=$PROJECT_ID \
        --region=$LOCATION_ID \
        --display_name="My First Agent" \
        multi_tool_agent
```
**Live (non-deprecated) flags in 2.x:**
- `--api_key` (Express Mode), `--project`, `--region`, `--agent_engine_id` (update an existing instance), `--otel_to_cloud`
- `--display_name`, `--description`, `--temp_folder`, `--agent_engine_config_file`
- `--trigger_sources` (e.g. `pubsub,eventarc`; registers `/trigger/*` endpoints), `--trigger_oidc_audience`, `--trigger_oidc_service_accounts`
- `--adk_version`, `--extra_packages` (repeatable), `--worker_pool` (Cloud Build private pool), `--service_account`
- `--session_service_uri` (`agentengine://`, `memory://`, `sqlite://`), `--artifact_service_uri` (`gs://`…), `--memory_service_uri` (`rag://`, `agentengine://`, …)
- `--use_local_storage`

**Now deprecated:** `--staging_bucket` ("no longer required"), `--trace_to_cloud`, `--adk_app`, `--env_file`, `--requirements_file`, `--absolutize_imports`.

**What the command does internally** (from `cli_deploy.py`, current main):
1. Copies the agent to `<temp>/agents/<app_name>`. It honours `.gitignore`, `.gcloudignore` and `.ae_ignore`, and skips `.adk`.
2. Reads `.agent_engine_config.json` for keys such as `display_name`, `description`, `worker_pool`, `build_config`, `extra_packages`, `service_account` and `env_vars`.
3. Writes `requirements.txt` with version floors: `google-cloud-aiplatform[adk,agent_engines]>=2.2,<3` **or** `google-cloud-agentplatform>=2.2`.
4. Reads `.env`. `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION`, `GOOGLE_CLOUD_SERVICE_ACCOUNT` and `GOOGLE_API_KEY` are consumed by the CLI; every other variable becomes an `env_var`.
5. Creates an **`agentplatform.Client`** and calls `client.runtimes.create()` followed by `client.runtimes.update(...)`. It passes `source_packages`, an empty `image_spec` (meaning: build from a Dockerfile), `class_methods` and `agent_framework='google-adk'`. If the update fails on a fresh create, it deletes the new runtime.
6. The generated Dockerfile runs the ADK `api_server` on port 8080 with `--a2a`.

**Agent Identity through ADK:** put this in the agent folder before you deploy:
```json
{ "identity_type": "AGENT_IDENTITY" }
```
(file: `.agent_engine_config.json`; source: the Agent Identity with Agent Runtime docs)

### 3b. Go: `adkgo deploy agentengine`
```bash
adkgo deploy agentengine -e ./main.go -s "multi_tool_agent" -p $PROJECT_ID -r $LOCATION_ID -d .
```

### 3c. Agents CLI, the successor to Agent Starter Pack
- The GitHub repo `GoogleCloudPlatform/agent-starter-pack` says: "Agent Starter Pack is in **maintenance mode** — switch to `agents-cli`". It now gets critical fixes only. The README calls agents-cli "the next evolution of Agent Starter Pack".
- Old ASP commands: `uvx agent-starter-pack create` and `uvx agent-starter-pack enhance`. Templates were `adk`, `adk_a2a`, `agentic_rag`, `langgraph`, `adk_java` and `adk_live`.
- Install agents-cli with `uvx google-agents-cli setup`. It installs "CLI and skills for building agents on Google Cloud" and works with coding agents such as **Antigravity CLI**, Claude Code and Codex. Docs: https://google.github.io/agents-cli/

Commands, verified from https://google.github.io/agents-cli/cli/:
```bash
agents-cli create my-agent -d agent_runtime           # -d: agent_runtime | cloud_run | gke | none
agents-cli scaffold enhance --deployment-target agent_runtime   # add deploy/CI to existing ADK project
agents-cli playground                                  # local UI
agents-cli eval run --dataset evals.json --metrics ... # generate + grade
agents-cli eval compare BASELINE CANDIDATE
agents-cli infra single-project --apply                # Terraform + telemetry infra
agents-cli infra setup-cicd --cicd-runner github_actions --dev-project ... --staging-project ... --prod-project ...
agents-cli deploy --agent-identity                     # reads deployment_target from pyproject.toml
agents-cli publish gemini --agent-runtime-id ... --registration-type a2a   # surface in Gemini Enterprise
```
New projects default to `--agent-runtime-identity-default agent_identity`. `deploy` also accepts `--agent-gateway-egress` and `--agent-gateway-ingress`, `--min-instances` and `--max-instances`, `--concurrency`, and `--secrets`.

---

## 4. Deploying with the Python SDK: two surfaces coexist

### 4a. Current quickstart, `vertexai` namespace (still in the docs as of Oct 2026)
Source: https://docs.cloud.google.com/gemini-enterprise-agent-platform/build/runtime/quickstart-adk
```python
# pip install --upgrade --quiet google-cloud-aiplatform[agent_engines,adk]>=1.112
import vertexai
from vertexai import agent_engines, types
from google.adk.agents import Agent

client = vertexai.Client(project="PROJECT_ID", location="LOCATION")

agent = Agent(model="gemini-3.5-flash", name="currency_exchange_agent",
              tools=[get_exchange_rate])
app = agent_engines.AdkApp(agent=agent)

async for event in app.async_stream_query(user_id="USER_ID",
        message="What is the exchange rate from US dollars to SEK today?"):
    print(event)                      # local test, in-memory sessions

remote_agent = client.agent_engines.create(
    agent=app,
    config={
        "requirements": ["google-cloud-aiplatform[agent_engines,adk]"],
        "staging_bucket": "STAGING_BUCKET",          # gs://...
        "identity_type": types.IdentityType.AGENT_IDENTITY,
    },
)
async for event in remote_agent.async_stream_query(user_id="USER_ID", message="..."):
    print(event)
remote_agent.delete(force=True)       # force=True also deletes child sessions etc.
```

### 4b. New SDK, `agentplatform` (2.0.1+, Sep 18, 2026; latest on PyPI is **2.6.0, 2026-10-21**)
Source: https://docs.cloud.google.com/gemini-enterprise-agent-platform/build/runtime/sdk-migration
```python
# pip install google-cloud-agentplatform[adk,agent_engines]
import agentplatform
client = agentplatform.Client(project=PROJECT, location=LOCATION)
client.runtimes.create(
    agent=local_agent,
    config={"staging_bucket": STAGING_BUCKET,
            "requirements": REQUIREMENTS,
            "extra_packages": EXTRA_PACKAGES},
)
```

Method mapping, old → new:
| Old | New |
|---|---|
| `agent_engines.create/get/list/update/delete` | `client.runtimes.*` |
| `create_session` / `append_session_event` | `client.sessions.create` / `client.sessions.events.append` |
| `generate_memories` / `retrieve_memories` | `client.memory_banks.memories.generate` / `.retrieve` |

The legacy namespaces are "in the deprecation phase", and the new SDK claims "full feature parity". No removal date has been published.

### 4c. The five deployment methods
Source: https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/runtime/deploy-an-agent

1. **Agent object.** Best for Colab and notebooks. Config keys:
   - `requirements`, `extra_packages`, `gcs_dir_name`, `display_name`, `description`, `labels`, `env_vars`, `build_options`
   - `identity_type`, `service_account`
   - `min_instances`, `max_instances`, `resource_limits`, `container_concurrency`
   - `encryption_spec`, `agent_framework`
2. **Source files.** Needs no GCS bucket. Uses `source_packages`, `entrypoint_module` (e.g. `agent_dir.agent`), `entrypoint_object` (`root_agent`) and `class_methods`. **The source tree is limited to 8 MB.**
3. **Developer Connect** (from a Git repository). Uses `developer_connect_source` with `git_repository_link`, `revision` and `dir`.
4. **Container image.** Uses `container_spec: {image_uri: "us-central1-docker.pkg.dev/..."}` and needs `google-cloud-aiplatform>=1.144`.
5. **Dockerfile.** Set `"image_spec": {}` and include the `Dockerfile` in `source_packages`. Works with any language.

The SDK source (`vertexai/_genai/agent_engines.py`) accepts more config keys: `psc_interface_config`, `agent_gateway_config`, `keep_alive_probe`, `python_version`, `agent_server_mode`, `agent_config_source`, `context_spec.memory_bank_config`, and `build_config` (worker pool). It also has batch `run_query_job` and `check_query_job` methods, and sub-clients `memories`, `sessions`, `sandboxes`, `runtimes` and `a2a_tasks`.

### 4d. AdkApp reference
Source: python-aiplatform `vertexai/agent_engines/templates/adk.py`

**Constructor**, keyword-only:
```
AdkApp(*, agent=None | app=None, app_name=None, plugins=None, enable_tracing=None,
       session_service_builder=None, artifact_service_builder=None,
       memory_service_builder=None, instrumentor_builder=None)
```
- Pass either `agent` or `app` (an ADK `App`). `app` cannot be combined with `plugins` or `app_name`.
- It raises an error if `google-adk` is older than 1.5.0.

**Methods**
- `async_stream_query(message, user_id, session_id=None, run_config=None)`
- `async_create_session`, `async_get_session`, `async_list_sessions`, `async_delete_session`
- `async_add_session_to_memory`, `async_search_memory`
- `streaming_agent_run_with_events` (used by Gemini Enterprise/AgentSpace)
- The sync wrappers `stream_query` and `create_session` are **deprecated**.

**Default services when deployed** (that is, when `GOOGLE_CLOUD_AGENT_ENGINE_ID` is set):
- Sessions: `VertexAiSessionService`
- Memory: `VertexAiMemoryBankService`
- Artifacts: in-memory unless you pass a builder. **This is a failure mode: artifacts are lost unless you supply `artifact_service_builder`, for example backed by GCS.**

### 4e. Calling a deployed agent over REST
Source: https://adk.dev/deploy/agent-runtime/test/
```bash
curl -H "Authorization: Bearer $(gcloud auth print-access-token)" \
 https://$LOCATION-aiplatform.googleapis.com/v1/projects/$PROJECT/locations/$LOCATION/reasoningEngines/$ID:query \
 -d '{"class_method":"async_create_session","input":{"user_id":"u_456"}}'
curl ... "$BASE:streamQuery?alt=sse" \
 -d '{"class_method":"async_stream_query","input":{"user_id":"u_456","session_id":"SID","message":"hi"}}'
```
In Express mode, use the `x-goog-api-key` header instead of the bearer token.

---

## 5. Agent Platform Sessions

Source: https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/sessions

**Concepts**
- **Session:** the chronological sequence of messages and actions in one interaction.
- **Event:** a record with a flexible schema; function calls are events too.
- **State:** temporary data for the current conversation.
- **Memory:** information that persists across sessions.

**Operations:** create, resume (get), append events, list per user and app, delete. "Once the agent is deployed, session management is handled automatically" for ADK.

**ADK usage**
- Use `--session_service_uri=agentengine://<id>` with `adk web` or `adk api_server`.
- `VertexAiSessionService` works from Cloud Run or GKE too, so you can use managed sessions without hosting on Agent Runtime.

**Timeline**
- Custom Session IDs: Apr 2026
- Multi-regional and global endpoints: Preview May 19, 2026; GA Jun 17, 2026. **CMEK is not available on the global endpoint.**
- Compute metering started on Sep 1, 2026.

**ADK 2.x changelog:** 2.12.0 "update session last_update_time on Vertex AI append_event"; 2.10.0 "auto-configure session and memory services on Agent Runtime". ADK also has session backends for Database, Redis, Firestore, BigQuery and MongoDB (2.13.0) when you are not on Agent Runtime.

---

## 6. Agent Platform Memory Bank

Sources: https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/memory-bank (and its /setup and /api-quickstart pages), and the SDK `memories.py`.

### Mechanics
- **Extraction:** an LLM pulls "only the most meaningful information" from events or multimodal content into self-contained memories.
- **Consolidation:** new facts are merged into existing memories, so memories evolve over time.
- **Scope isolation:** each scope gets an isolated collection. ADK uses `{"app_name", "user_id"}`.
- **Topics:**
  - Managed topics: `USER_PERSONAL_INFO`, `USER_PREFERENCES`, `KEY_CONVERSATION_DETAILS`, `EXPLICIT_INSTRUCTIONS`.
  - Custom topics: `custom_memory_topic {label, description}`, plus few-shot examples.
- **Revisions:** memories keep a revision history; `rollback` restores an earlier revision.
- **TTL:** `default_ttl`, or `granular_ttl` with `create_ttl`, `generate_created_ttl` and `generate_updated_ttl`.
- **Memory Profiles:** GA Jul 15, 2026.
- **Streaming ingestion:** the `IngestEvents` API (GA Jul 8, 2026) streams events and triggers generation according to batching rules.
- **Models:** Gemini 3.5 Flash has been the default generation model since Jun 29, 2026. Gemini Embedding 2 is supported but needs a global, us or eu endpoint.

### Config shape
Path: `config.context_spec.memory_bank_config`.
- `generation_config.model`
- `similarity_search_config.embedding_model`
- `customization_configs[].memory_topics[]`
- `ttl_config`
- `structured_memory_configs`
- `disable_memory_revisions`

### API, new SDK
```python
import agentplatform
client = agentplatform.Client(project="PROJECT_ID", location="LOCATION")
memory_bank = client.memory_banks.create()
session = client.sessions.create(name="SESSIONS_NAME", user_id="USER_ID")
client.sessions.events.append(name=session.response.name, author="user", invocation_id="1", ...)
client.memory_banks.memories.generate(name=memory_bank.name,
    vertex_session_source={"session": session.response.name})
mems = client.memory_banks.memories.retrieve(name=memory_bank.name, scope={"user_id": "123"}).page
client.memory_banks.delete(name=memory_bank.name, force=True)
```
The Memories methods in the SDK source are `create`, `generate` (one source among `vertex_session_source`, `direct_contents_source` and `direct_memories_source`), `retrieve` (`similarity_search_params` or `simple_retrieval_params`), `retrieve_profiles`, `rollback`, `purge` (staged unless `force=True`), `ingest_events` and `revisions`.

### ADK integration
Source: https://adk.dev/sessions/memory/ and `vertex_ai_memory_bank_service.py`.
```python
from google.adk.memory import VertexAiMemoryBankService
from google.adk.tools import preload_memory      # auto-retrieve every turn
# or the load_memory tool: model decides when to recall
memory_service = VertexAiMemoryBankService(project=P, location=L, agent_engine_id=ID)
# after_agent_callback=auto_save_session_to_memory_callback -> add_session_to_memory
```
```bash
adk web path/to/agents_dir --memory_service_uri="agentengine://1234567890"
```
- `add_session_to_memory` calls `memories.ingest_events` by default.
- `search_memory` calls `memories.retrieve(similarity_search_params={'search_query': query})`.
- Using `enable_consolidation` for direct memories switches to `generate` in batches of 5 or fewer.

---

## 7. Code Execution sandbox (Agent Sandbox)

Source: https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/sandbox/code-execution-overview

**Properties**
- Isolated and managed. Works with any framework or model, and the agent does not have to be hosted on Agent Runtime.
- **Sandbox creation and execution take under a second.**
- Stateful: later calls build on earlier ones. Snapshots are not supported.
- **State TTL is up to 14 days**, configurable.
- **Input and output are limited to 100 MB per request or response.**
- **No network access.** The library set is preinstalled (Python data science and ML), and you cannot install your own libraries.

**SDK** (`client.agent_engines.sandboxes` / `sandboxes.py`): `create(name=<reasoningEngine>, spec=..., config={ttl, sandbox_environment_template, ...})`, `execute_code(name=..., input_data={"code": "...", "files": [...]})`, `get`, `list`, `delete`. Outputs come back in `response.outputs`.

**ADK:** `google.adk.code_executors.AgentEngineSandboxCodeExecutor(sandbox_resource_name=None, agent_engine_resource_name=None)`.
- If you pass neither argument, it reads `GOOGLE_CLOUD_PROJECT` and `GOOGLE_CLOUD_LOCATION` (default `us-central1`) and lazily creates an engine.
- It creates **one sandbox per session**, stores the sandbox name in session state, and gives it a 1-year TTL with display name `default_sandbox`.
- **Failure mode:** a static `sandbox_resource_name` on a shared agent triggers a `UserWarning`, because state can leak across user sessions.
- Other executors in the package: `BuiltInCodeExecutor`, `VertexAiCodeExecutor`, `GkeCodeExecutor`, `ContainerCodeExecutor` and `UnsafeLocalCodeExecutor`. ADK 2.13 fixed `UnsafeLocalCodeExecutor` "waiting forever".

---

## 8. Example Store

Source: https://docs.cloud.google.com/gemini-enterprise-agent-platform/optimize/example-store/overview

- Status: **still Preview** under the Pre-GA terms.
- Stores few-shot input/output examples and retrieves them by **cosine similarity** of search keys, optionally filtered by function name.
- An ADK agent linked to a store automatically injects retrieved examples into its LLM requests.
- **Limit: 50 Example Store instances per region per project.**
- It now sits under the *Optimize* pillar, no longer under Scale.

---

## 9. Agent Identity and IAM for agents

Sources: https://docs.cloud.google.com/gemini-enterprise-agent-platform/govern/agent-identity-overview and `/scale/runtime/agent-identity`.

**Basics**
- **GA on Apr 22, 2026.**
- **SPIFFE-based**: `spiffe://TRUST_DOMAIN/resources/SERVICE/RESOURCE_PATH`.
- IAM principal: `principal://agents.global.org-ORG_ID.system.id.goog/resources/aiplatform/projects/PROJECT_NUMBER/locations/LOCATION/reasoningEngines/ID`. Projects without an organization use `agents.global.proj-PROJECT_NUMBER.system.id.goog`.

**Why it beats service accounts:** agent identities are "not shared by multiple workloads by default, can't be impersonated, and don't allow developers to generate long-lived service account keys."

**Credentials**
- Auto-rotated X.509 certificates, **valid for 24 hours**.
- Access tokens bound to the certificate through mTLS, plus DPoP across Agent Gateway ("double-bound").
- OIDC ID tokens for federation to external services.
- A default Context-Aware Access policy prevents token replay outside the runtime.

**Auth manager:** a vault and broker for API keys, 2-legged OAuth (the recommended machine-to-machine option), 3-legged user-delegated OAuth, and basic auth (not recommended).

**Roles**
- Grant the agent:
  - `roles/aiplatform.expressUser` (inference, sessions, memory)
  - `roles/serviceusage.serviceUsageConsumer`
  - `roles/browser`
- Granted by default: `roles/aiplatform.agentContextEditor` and `roles/aiplatform.agentDefaultAccess`.
- For agent-to-agent calls, the caller needs `roles/agentregistry.viewer` plus `roles/aiplatform.user` on the callee's reasoning engine.
- Use `principalSet://` to grant a role to all agents in a project at once.

**Governance controls:** Principal Access Boundary on outbound calls, VPC-SC ingress and egress rules that use agent principals, and dual-attribution audit logs (agent SPIFFE ID plus human user; filter with `is_agentic=true`).

**Enable it in code:**
```python
client = agentplatform.Client(project=PROJECT_ID, location=LOCATION,
                              http_options=dict(api_version="v1beta1"))
remote_app = client.runtimes.create(config={
    "display_name": "identity-for-agent",
    "identity_type": types.IdentityType.AGENT_IDENTITY,
})
```

**Failure modes**
1. Redeploying by *replacing* the agent creates a **new principal**, so you must re-grant its roles.
2. Deleting an agent leaves **orphaned IAM bindings**.
3. Agent identities cannot hold legacy GCS bucket roles (`storage.legacyBucketReader` and the like).
4. If you omit `identity_type`, the agent falls back to a service account.

Since ADK 2.12, you can deploy with a dedicated custom service account (`--service_account`).

**Agent Gateway and Registry**
- Gateway is the "central policy enforcement point to govern all agent tool calls" (GA Jun 18, 2026). Since Sep 2026 it supports VPC egress templates (`ALL_TRAFFIC` / `PRIVATE_RANGES_ONLY`) and enforces VPC-SC for deployments created after Sep 8, 2026. Cloud Trace integration has been in Preview since Sep 30, 2026.
- Registry catalogs agents, tools and MCP servers (GA Jun 18, 2026). It is visible inside Gemini Enterprise since Jun 25, 2026.

---

## 10. Observability

Source: https://docs.cloud.google.com/gemini-enterprise-agent-platform/optimize/observability/overview

**Data:** OpenTelemetry traces, logs and metrics, following the OTel GenAI semantic conventions.

**Agent Observability tabs**
- *Overview*: sessions, turns per session, tokens, p50/p95/p99 latency, errors.
- *Evaluation*: online monitors for quality, safety, hallucination and tool use.
- *Models*, *Tools* (includes "no tool called" rate), *Usage* (CPU, memory, tokens), *Logs*, *Traces* (a DAG of spans), and *Topology* (inbound and outbound dependencies).

**Timeline**
- Tracing on by default for new ADK deployments: Jun 18, 2026.
- User IDs in prompt and response logs from ADK 2.1 or later: May 27, 2026. Requires redeploying and opting in.
- ADK telemetry metrics exported to Cloud Monitoring from **ADK 2.6.0**: Aug 13, 2026.

**Switches**
- `adk deploy ... --otel_to_cloud` (`--trace_to_cloud` is deprecated).
- The environment variable `GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true`.
- `AdkApp(enable_tracing=...)`. Passing `False` is deprecated. Message-content capture is controlled by `ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS`.

**On Cloud Run:** `get_fast_api_app(..., trace_to_cloud=True)`. In Trace Explorer, filter on the span `agent_run [weather_agent]` (from the codelab).

---

## 11. Pricing model

What is verified:
- Agent Runtime bills compute: vCPU-hours and GiB-hours of memory for the running instances.
- From **Sep 1, 2026**: "Session and memory bank compute metering is in effect for the Agent Platform compute SKU".
- Memory Bank embedding SKUs changed on the same date (6E46-5623-C0B6, C15D-A68F-5C1E, 2D07-D52C-A93B).
- Model tokens are billed separately. Standard PayGo tiers go up to Tier 4 (more than $50k per 30 days, Sep 10, 2026). Priority PayGo is GA (May 14, 2026). A **Deferred tier (Preview, Sep 2, 2026) gives a 50% token discount** for scheduled autonomous agents.
- Pricing page: https://cloud.google.com/products/gemini-enterprise-agent-platform/pricing. It was too large to fetch, so I could not extract the rates.

What is **not** verified. These are 2025-era list prices from memory:
- Runtime at about $0.0864 per vCPU-hour and $0.0090 per GiB-hour, with a monthly free tier of about 50 vCPU-hours and 100 GiB-hours.
- Sessions at about $0.25 per 1,000 events stored.
- Memory Bank at about $0.25 per 1,000 memories stored per month and $0.50 per 1,000 memories retrieved.

All of these are **[UNVERIFIED]**. Check them on the pricing page before you put them on a slide.

**Cost levers:** `min_instances=0` (scale to zero, but cold starts), `container_concurrency`, `resource_limits`, Memory Bank TTLs, and choosing preload_memory (retrieves every turn) versus load_memory (on demand).

---

## 12. Alternatives: Cloud Run and GKE

**Cloud Run** (https://adk.dev/deploy/cloud-run/):
```bash
adk deploy cloud_run --project=$GOOGLE_CLOUD_PROJECT --region=$GOOGLE_CLOUD_LOCATION \
  --service_name=$SERVICE_NAME --app_name=$APP_NAME --with_ui $AGENT_PATH
```
- Other flags: `--a2a`, `--otel_to_cloud`, `--session_service_uri`, `--artifact_service_uri`, `--memory_service_uri`, `--with_cloud_run_sandbox` (beta), `--trigger_sources`, `--allow_origins`, `--port` (default 8000).
- **Failure mode:** if the URIs are unset, the container "falls back to the in-memory session and artifact services". State is then lost whenever an instance recycles.
- Custom server: `main.py` with `get_fast_api_app(agents_dir=..., session_service_uri=..., allow_origins=..., web=...)`, and a Dockerfile with `CMD uvicorn main:app --host 0.0.0.0 --port $PORT`.
- Agent Identity also supports Cloud Run.

**GKE** (https://adk.dev/deploy/gke/):
```bash
gcloud container clusters create-auto adk-cluster --location=$GOOGLE_CLOUD_LOCATION --project=$GOOGLE_CLOUD_PROJECT
adk deploy gke --project $P --cluster_name adk-cluster --region $R --service_type LoadBalancer --with_ui AGENT_PATH
```
- Internally: `gcloud builds submit --tag gcr.io/...`, then `get-credentials`, then `kubectl apply -f deployment.yaml`.
- Workload Identity: grant `roles/aiplatform.user` to `principal://.../subject/ns/default/sa/default`. **Without it, model calls fail with 403 PERMISSION_DENIED.**
- ADK 2.12 added `extra_packages` staging for cloud_run and gke, and a GKE code executor.

**When to choose which**
| Need | Choose |
|---|---|
| Managed sessions, memory and identity, A2A, publishing to Gemini Enterprise, least operations work | **Agent Runtime** |
| A custom FastAPI app, traffic splitting (`--no-traffic` canaries), your own database, broad HTTP control | **Cloud Run** |
| GPUs or self-hosted models, an existing Kubernetes platform, sidecars, custom networking | **GKE** |

Cloud Run and GKE can still use Agent Platform Sessions and Memory Bank over `agentengine://` URIs.

---

## 13. Codelabs and samples

**Verified titles and URLs**
- **"Deploy, Manage, and Observe ADK Agent on Cloud Run"** — https://codelabs.developers.google.com/deploy-manage-observe-adk-cloud-run
  - Steps: Cloud SQL Postgres 17 sessions, `uv run adk web`, `gcloud run deploy weather-agent --min 1 --concurrency 10`, a Locust load test (60 users), a `--no-traffic` canary, and Cloud Trace.
- **"Google's Agent Stack in Action: ADK, A2A, MCP on Google Cloud"** (InstaVibe) — https://codelabs.developers.google.com/instavibe-adk-multi-agents/instructions
  - The orchestrator runs on Agent Engine; the MCP server and A2A agents run on Cloud Run.

**Docs-hosted guides**
- Agent Platform "Quickstart: Develop with Agent Development Kit on Agent Runtime" — https://docs.cloud.google.com/gemini-enterprise-agent-platform/build/runtime/quickstart-adk
- Memory Bank ADK quickstart — https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/memory-bank/adk-quickstart
- Memory Bank API quickstart — .../memory-bank/api-quickstart

**Samples:** https://github.com/google/adk-samples. Agents CLI migration guide: "From Agent Starter Pack" on https://google.github.io/agents-cli/

I could not confirm a codelab specific to Memory Bank or Agent Runtime: guessed URLs returned 404, and search was unavailable. **[UNVERIFIED]**

---

## 14. Failure modes cheat-sheet

1. **Lost state on Cloud Run or GKE** because the session and artifact URIs are unset. The service falls back to in-memory storage.
2. **Artifacts lost on Agent Runtime.** AdkApp defaults to `InMemoryArtifactService`; supply `artifact_service_builder`.
3. **Mixing the SDK surfaces.** Mixing `vertexai.agent_engines` (deprecated) with `agentplatform` (`client.runtimes`) causes confusion. The ADK CLI now uses `agentplatform` and requires `>=2.2`.
4. **Source deploys over 8 MB fail.** Use `.ae_ignore` or `.gcloudignore`, or switch to a container image.
5. **Agent Identity re-grants.** A replaced agent gets a new principal, so re-grant its roles. Deleting an agent leaves orphaned bindings.
6. **CMEK on the global endpoint.** CMEK is unavailable on the global Sessions and Memory Bank endpoint.
7. **Shared static sandbox** in `AgentEngineSandboxCodeExecutor` leaks state across users.
8. **No network in Code Execution.** Code that calls `pip install` or fetches URLs fails.
9. **GKE without the Workload Identity binding** returns 403 PERMISSION_DENIED.
10. **Logging regressions.** Prompt and response logs with user IDs require redeploying and opting in again (ADK 2.1+).
11. **Memory pollution.** Always scope memories by `user_id`. Use TTLs and `purge` (staged unless `force=True`).
12. **Cold starts** with `min_instances=0`. Agent Runtime claims sub-second cold starts, but heavy dependencies still add latency.

---

## 15. Interview questions with crisp answers

1. **What is Agent Runtime, and what was it called before?** The managed runtime for agents on Gemini Enterprise Agent Platform. It was Vertex AI Agent Engine until Apr 22, 2026, and Reasoning Engine before that. The REST resource is still `reasoningEngines`.
2. **Gemini Enterprise versus Gemini Enterprise Agent Platform?** Gemini Enterprise (formerly Agentspace, renamed Oct 9, 2025) is the employee app. Agent Platform (formerly Vertex AI) is where developers build, host and govern agents. You publish from Agent Platform into Gemini Enterprise.
3. **Name three ways to deploy an ADK agent to Agent Runtime.** `adk deploy agent_engine`, `agents-cli deploy -d agent_runtime`, and the SDK `client.runtimes.create(agent=AdkApp(...))`. The SDK path also covers source files, Developer Connect, a container image and a Dockerfile.
4. **How does a deployed AdkApp get persistent sessions?** When `GOOGLE_CLOUD_AGENT_ENGINE_ID` is set, it automatically uses `VertexAiSessionService` and `VertexAiMemoryBankService`.
5. **Sessions versus Memory Bank?** Sessions hold the event log and state for one conversation. Memory Bank holds LLM-extracted, consolidated, scoped long-term facts across sessions, with topics, TTL and revisions.
6. **preload_memory versus load_memory?** Preload retrieves memories every turn: deterministic, but costs more tokens and latency. load_memory is a tool the model calls only when it decides it needs past context.
7. **Why use Agent Identity instead of a service account?** It is per agent and SPIFFE-attested, uses 24-hour bound certificates, cannot be impersonated and has no long-lived keys. It also enables dual-attribution audit logs and Principal Access Boundary.
8. **What are the Code Execution limits?** No network, preinstalled libraries only, 100 MB I/O, state for up to 14 days, and sub-second startup.
9. **When would you pick Cloud Run over Agent Runtime?** When you need a custom FastAPI surface, revision traffic splitting or your own database. GKE fits when you need GPUs or self-hosted models. Both can still call managed Sessions and Memory Bank.
10. **What replaced Agent Starter Pack?** agents-cli (`uvx google-agents-cli setup`), which scaffolds, evaluates (`eval run/compare`), runs Terraform (`infra`), sets up CI/CD, deploys and publishes to Gemini Enterprise.
11. **How do you observe a deployed agent?** OTel traces, logs and metrics feed the Agent Observability tabs (Overview, Evaluation, Models, Tools, Traces, Topology). Tracing has been on by default since Jun 2026; use `--otel_to_cloud`.
12. **How does pricing work?** Runtime compute in vCPU-hours and GiB-hours, plus model tokens. Sessions and Memory Bank compute metering began Sep 1, 2026. A Deferred tier gives 50% off tokens for scheduled agents.

---

## 16. Slide ideas (with the animation that explains each)

1. **"Name changes"** — a horizontal timeline: Reasoning Engine → Agent Engine → **Agent Runtime** (Apr 22, 2026), with a parallel track Agentspace → Gemini Enterprise (Oct 9, 2025). *Animation:* each old label morphs into the new one, while a fixed tag stays visible underneath: `reasoningEngines` / `aiplatform.googleapis.com`.
2. **"Four pillars"** — Build, Scale, Govern, Optimize as columns. *Animation:* the product icons drop into their columns one at a time. Example Store slides from Scale to Optimize.
3. **"One request, end to end"** — the flow from §2. *Animation:* a token travels Client → Gateway → Runtime → Sessions → Gemini/Tools/Sandbox → Memory Bank → Trace. Each hop lights up and leaves a span bar on a trace waterfall at the bottom.
4. **"Five ways to deploy"** — five lanes (object, source, Git, image, Dockerfile) that merge into one `reasoningEngines/ID`. *Animation:* the lanes converge, and the "8 MB" badge pulses on the source lane.
5. **"What `adk deploy agent_engine` actually does"** — *Animation:* a folder is copied, filtered by ignore files, `requirements.txt` gets its floors, a Dockerfile appears, then `runtimes.create()` followed by `update()`, with a rollback arrow if the update fails.
6. **"SDK migration"** — a split screen comparing `vertexai.agent_engines.create(...)` with `agentplatform.Client().runtimes.create(config={...})`. *Animation:* keyword arguments fly into the `config` dict.
7. **"Sessions versus Memory"** — a conversation transcript on the left, a memory card stack on the right. *Animation:* events stream in, the extractor pulls facts out, a consolidation step merges a duplicate ("likes window seats" + "prefers aisle" → a revision), and a TTL clock fades one card.
8. **"Agent Identity"** — a passport metaphor showing the SPIFFE ID. *Animation:* a certificate is issued (24-hour countdown), a token is bound to it with mTLS and DPoP, a stolen token is replayed from outside and bounces off the Context-Aware Access wall, and the audit log shows both agent and human.
9. **"Sandbox boundaries"** — a glass box. *Animation:* code runs inside, a network call hits the wall, a file over 100 MB is rejected, and state persists across two calls before a 14-day timer expires it.
10. **"Where to host"** — a decision tree (Agent Runtime / Cloud Run / GKE). *Animation:* three persona cards (enterprise, startup canary deploys, ML platform team) each travel down the tree to their answer, and all of them reach the shared Sessions and Memory Bank at the bottom.

---

### Key source URLs
- https://docs.cloud.google.com/gemini-enterprise-agent-platform/vertex-ai-name-changes
- https://docs.cloud.google.com/gemini-enterprise-agent-platform/release-notes
- https://cloud.google.com/blog/products/ai-machine-learning/introducing-gemini-enterprise-agent-platform (Apr 22, 2026)
- https://docs.cloud.google.com/gemini-enterprise-agent-platform/build/runtime/quickstart-adk
- https://docs.cloud.google.com/gemini-enterprise-agent-platform/build/runtime/sdk-migration
- https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/runtime/deploy-an-agent
- https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/runtime/agent-identity
- https://docs.cloud.google.com/gemini-enterprise-agent-platform/govern/agent-identity-overview
- https://adk.dev/deploy/agent-runtime/ (plus /deploy/, /agents-cli/, /test/), https://adk.dev/deploy/cloud-run/, https://adk.dev/deploy/gke/
- https://github.com/google/adk-python (CHANGELOG: 2.13.0 on 2026-10-22; v2.0.0 GA on 2026-05-19)
- https://github.com/googleapis/python-aiplatform (`vertexai/agent_engines/templates/adk.py`, `vertexai/_genai/*.py`)
- https://pypi.org/project/google-cloud-agentplatform/ (2.6.0, 2026-10-21)
- https://google.github.io/agents-cli/cli/
- https://github.com/GoogleCloudPlatform/agent-starter-pack (maintenance mode)
- https://docs.cloud.google.com/gemini/enterprise/docs/release-notes (Agentspace → Gemini Enterprise, 2025-10-09)
