# 12 - AgentOps Tooling Landscape (as of 2026-10-23)

Scope: OpenTelemetry GenAI semantic conventions, ADK 2.x telemetry, third-party observability and eval vendors, registries and governance (Agent Registry, A2A Agent Cards, MCP Registry), agent identity, runtime guardrails (Model Armor), and cost/model routing.

Research method and caveats:
- Facts tagged **[V]** were confirmed by fetching the primary source on 2026-10-23. **[UNVERIFIED]** marks material from memory or secondary sources that I could not re-fetch.
- The session's WebSearch budget ran out early, so almost all research was direct WebFetch of known primary URLs. Vendor pricing, funding, and codelab URLs are therefore thin. Treat them as gaps to fill, not as settled facts.
- Google docs moved hosts. `google.github.io/adk-docs/*` now 301-redirects to **adk.dev**. The Vertex AI Agent Engine docs now sit under **"Gemini Enterprise Agent Platform"**, and the runtime is called **"Agent Runtime"** [V].

---

## 1. Key takeaways for the deck (one-liners)

1. **OTel GenAI semconv now has its own repo**: `github.com/open-telemetry/semantic-conventions-genai`. The old opentelemetry.io GenAI pages say they are "no longer maintained" [V]. Every GenAI spec page there is still marked **Development**, not Stable [V].
2. **Canonical span names**: `invoke_agent {gen_ai.agent.name}`, `execute_tool {gen_ai.tool.name}`, `create_agent {gen_ai.agent.name}`, `invoke_workflow ...`, and `{gen_ai.operation.name} {gen_ai.request.model}` for inference (for example `chat gpt-4` or `generate_content gemini-...`) [V].
3. **ADK v2.13.0 (released 2026-10-23, today)** switches telemetry by default to OTel GenAI "v2" (`otel_semconv_1_44`) and **removes the `call_llm` span**. Set `ADK_TELEMETRY_SCHEMA_VERSION_OPT_IN=otel_semconv_1_36` to keep the old schema [V]. This is a breaking change for dashboards.
4. **ADK to Google Cloud takes one flag.** `adk web --otel_to_cloud` or `adk deploy agent_engine --otel_to_cloud`. In code, `get_gcp_exporters(...)` plus `maybe_set_otel_providers(...)` [V].
5. **Most third-party tools reach ADK through OpenInference's `GoogleADKInstrumentor` or plain OTLP.** Phoenix, Arize AX, Langfuse, and Galileo use the instrumentor. Weave and Langfuse also take raw OTLP. LangSmith ships `configure_google_adk`. Datadog uses `ddtrace-run` and also ingests OTel GenAI 1.37+ [V].
6. **Governance stack on Google Cloud**: Agent Registry is the catalog of agents, MCP servers, tools, and skills. Agent Identity gives each agent a SPIFFE-based principal. Agent Gateway enforces IAM and Model Armor on agent traffic [V].
7. **Guardrails ship as an ADK plugin.** `ModelArmorPlugin` arrived in ADK Python v2.8.0 [V].
8. **Cost telemetry is landing in the framework itself.** ADK 2.13 measures model-consultation escalations, tokens, and cost. 2.8 added experimental per-invocation and per-workflow token spend [V].

---

## 2. OpenTelemetry GenAI semantic conventions (status Oct 2026)

**Location [V]:** https://github.com/open-telemetry/semantic-conventions-genai. The old pages https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-agent-spans/ and .../gen-ai-spans/ say: "GenAI semantic conventions have moved to the OpenTelemetry GenAI semantic conventions repository... no longer maintained."

**Repo layout [V]:** `docs/gen-ai/` holds `gen-ai-agent-spans.md`, `gen-ai-spans.md`, `client-inference.md`, `gen-ai-events.md`, `gen-ai-metrics.md`, `gen-ai-token-metrics.md`, `gen-ai-exceptions.md`, `mcp.md`, and the provider files `openai.md`, `anthropic.md`, `aws-bedrock.md`, `azure-ai-inference.md`. YAML lives in `model/`, managed by Weaver. A Python reference compliance matrix lives in `reference/`. The Releases section showed none, and the Schema URL reads "TODO" [V]. The repo appears not to have cut a tagged release yet.

**Stability [V]:** `gen-ai-agent-spans.md` and `gen-ai-spans.md` are both marked **Development**.

### 2.1 Operation names (`gen_ai.operation.name`) [V]
`chat`, `generate_content`, `text_completion`, `embeddings`, `execute_tool`, `invoke_agent`, `invoke_workflow`, `create_agent`, `retrieval`, `plan`, plus memory operations such as `create_memory` and `search_memory`.

### 2.2 Span table [V unless noted]

| Span | Name format | Kind | Required / key attributes |
|---|---|---|---|
| Inference | `{gen_ai.operation.name} {gen_ai.request.model}`, e.g. `chat gpt-4` | CLIENT (INTERNAL allowed for in-process models) | Required: `gen_ai.operation.name`, `gen_ai.provider.name`. Conditionally required: `gen_ai.request.model`, `error.type`, `gen_ai.conversation.id` (never a fallback UUID) |
| Create agent | `create_agent {gen_ai.agent.name}` | CLIENT | `gen_ai.provider.name` (required), `gen_ai.agent.id`, `gen_ai.agent.name`, `gen_ai.agent.description`, `gen_ai.agent.version`, `gen_ai.system_instructions` (opt-in) |
| Invoke agent | `invoke_agent {gen_ai.agent.name}` | Spec has separate "Invoke agent **client** span" (remote agent) and "Invoke agent **internal** span" (in-process) sections | `gen_ai.agent.*`, `gen_ai.conversation.id` |
| Invoke workflow | `invoke_workflow {workflow name}` (ADK form; spec section exists) | - | `gen_ai.workflow.name` (per ADK docs) |
| Execute tool | `execute_tool {gen_ai.tool.name}` | INTERNAL | Required `gen_ai.tool.name`. Conditionally required `gen_ai.tool.call.id` (only if the model supplied one), `gen_ai.conversation.id`, `gen_ai.agent.name`. Recommended `gen_ai.tool.type` (`function`, `extension`, `datastore`). Opt-in `gen_ai.tool.call.arguments`, `gen_ai.tool.call.result` |
| Embeddings | `embeddings {model}` | CLIENT | `gen_ai.usage.input_tokens` |
| Retrieval | `retrieval {gen_ai.data_source.id}` | - | query text is sensitive |

- Execute-tool spans "should be associated with `gen_ai.main_agent`" [V]. ADK v2.10 stamps the **Agent Registry URN as `gen_ai.main_agent.id`** [V], which links traces to the registry.
- For hosted agents, `gen_ai.agent.id` should be the provider's stable ID, not a transient in-memory ID [V].
- Set `gen_ai.agent.name`, `gen_ai.operation.name`, `gen_ai.provider.name`, `gen_ai.request.model`, and `gen_ai.tool.name`/`type` **at span start**, because samplers use them [V].
- Well-known providers include `openai`, `anthropic`, `aws.bedrock`, and `gcp.gemini` [V].

### 2.3 Tokens and content [V]
- `gen_ai.usage.input_tokens` **includes cached tokens**. `gen_ai.usage.output_tokens` **includes reasoning tokens**. `gen_ai.usage.cache_read.input_tokens` and `gen_ai.usage.cache_write.input_tokens` are subsets of input. `gen_ai.usage.reasoning.output_tokens` is a subset of output. If a provider reports both billed and consumed counts, prefer billed.
- Content attributes are **opt-in and off by default**: `gen_ai.input.messages`, `gen_ai.output.messages`, `gen_ai.system_instructions`, `gen_ai.tool.definitions`. Events must carry them in structured form. On spans they may be JSON strings. A third option is to store content externally and reference it from the span.
- Common gate: `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT`. Opting into the newest experimental conventions in instrumentations uses `OTEL_SEMCONV_STABILITY_OPT_IN=gen_ai_latest_experimental`. Both Agent Runtime and Datadog docs use it [V].

---

## 3. ADK telemetry (ADK Python 2.x)

### 3.1 Release timeline (from https://github.com/google/adk-python/releases) [V]

| Version | Date (2026) | Telemetry/ops change |
|---|---|---|
| v2.7.1 | Aug 17 | Restored the OpenTelemetry 1.42.1 dependency ceiling |
| v2.8.0 | Aug 26 | `ADK_EXPERIMENTAL_TELEMETRY=true` adds per-invocation and per-workflow token spend and inference/tool counts. MCP HTTP exchanges become OTel log records. Model Armor guardrail plugin. `RunConfig.telemetry` honored |
| v2.9.0 | Sep 10 | Logs exported over OTLP to `telemetry.googleapis.com`. Script-execution and skill-load instrumentation |
| v2.9.2 | Sep 18 | OTel event name now dropped only on Agent Engine |
| v2.10.0 | Sep 25 | Per-feature experimental telemetry. **Agent Registry URN stamped as `gen_ai.main_agent.id`** |
| v2.11.0 | Oct 2 | Spans whose response came from a callback are marked. Skill telemetry attributes are no longer experimental. `ToolCallIntegrityPlugin` |
| v2.12.0 | Oct 13 | `on_schema_error` and `on_schema_ready` hooks on `BigQueryLoggerConfig`. Skill tool spans named after the skill |
| **v2.13.0** | **Oct 23** | **BREAKING: default schema is OTel GenAI v2 (`otel_semconv_1_44`), `call_llm` span removed.** Opt back with `ADK_TELEMETRY_SCHEMA_VERSION_OPT_IN=otel_semconv_1_36`. Tool call content goes into semconv attributes. google_search grounding recorded on LLM spans. Compaction counts. Eval session/turn trace views. `ForceEscalationPlugin`. Escalation, token, and cost metrics for model consultation |

### 3.2 ADK span tree (from https://adk.dev/observability/traces/) [V]

| Span | Key attributes |
|---|---|
| `invoke_agent {agent.name}` | `gen_ai.agent.name`, `gen_ai.agent.description`, `gen_ai.conversation.id` |
| `invoke_workflow {workflow.name}` | `gen_ai.workflow.name`, `gen_ai.workflow.nested` |
| `execute_tool {tool.name}` | `gen_ai.tool.name`, `.description`, `.type`, `gen_ai.tool.call.id`, `error.type` |
| `generate_content {model.name}` | `gen_ai.system`, `gen_ai.request.model`, `gen_ai.response.finish_reasons`, `gen_ai.usage.input_tokens`/`output_tokens` |

Note: the Cloud Trace integration page still lists `call_llm` among ADK spans [V]. As of v2.13 that is stale.

**Diagram flow (in words):** User request, then Runner, then `invoke_agent root_agent` (root span). Under it come `invoke_workflow pipeline` (for ADK 2.0 graph workflows), then child `invoke_agent sub_agent`, then `generate_content gemini-x`. A model function call produces `execute_tool get_weather`, then another `generate_content`, then the final response. Sibling OTel log records hold MCP HTTP exchanges and events. The BigQuery plugin writes a parallel `agent_events` row stream that is joinable on `trace_id`/`span_id`.

### 3.3 Wiring ADK to OTel and Cloud Trace (real code, source: https://adk.dev/observability/traces/ and https://adk.dev/integrations/cloud-trace/) [V]

Generic OTLP collector:
```python
from google.adk.telemetry.setup import maybe_set_otel_providers
import os

os.environ["OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"] = "http://your-collector:4318/v1/traces"
os.environ["OTEL_SERVICE_NAME"] = "your-adk-agent"
os.environ["OTEL_RESOURCE_ATTRIBUTES"] = "key1=value1,key2=value2"
maybe_set_otel_providers()
```

Google Cloud Trace:
```python
from google.adk.telemetry.google_cloud import get_gcp_exporters
from google.adk.telemetry.setup import maybe_set_otel_providers
import os

gcp_exporters = get_gcp_exporters(
  enable_cloud_tracing = True,
)
os.environ["OTEL_SERVICE_NAME"] = "your-adk-agent"
os.environ["OTEL_RESOURCE_ATTRIBUTES"] = "key1=value1,key2=value2"
maybe_set_otel_providers([gcp_exporters])
```

CLI:
```bash
adk web --otel_to_cloud path/to/your/agents_dir
adk deploy agent_engine --otel_to_cloud $AGENT_PATH
adkgo web -otel_to_cloud            # Go launcher
```

TypeScript: `import { getGcpExporters, maybeSetOtelProviders } from '@google/adk';`. Go: `telemetry.New(ctx, telemetry.WithOtelToCloud(true))`, then `SetGlobalOtelProviders()` from `google.golang.org/adk/v2/telemetry` [V].

Content capture env vars [V]: `ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS='true'|'false'` and `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT='true'`.

Agent Runtime (formerly Agent Engine) deploy env (https://docs.cloud.google.com/agent-builder/agent-engine/manage/tracing) [V]:
```python
env_vars = {
  "GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY": "true",
  "OTEL_SEMCONV_STABILITY_OPT_IN": "gen_ai_latest_experimental",
  "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT": "EVENT_ONLY",
}
```
Google now recommends these env vars over the older `AdkApp(enable_tracing=True)`. The console Deployments page has a Traces tab with **Session view and Span view**. Cloud Trace quotas can truncate attribute values, and Cloud Trace has a free tier [V].

### 3.4 AutoTracingPlugin [V]
Source: https://github.com/google/adk-python/blob/main/src/google/adk/plugins/auto_tracing_plugin.py (copyright 2026). The docstring reads "Auto-instruments in-scope Python functions with OpenTelemetry spans." The plugin monkey-patches public functions, static methods, and class methods in modules that match scope prefixes, plus packages reachable from the invocation's agent. It runs once per run. Constructor (keyword-only): `name="AutoTracingPlugin"`, `extra_scope_prefixes: tuple[str,...]=()`, `tracer=None`, `max_repr_len`, `max_recorded_yields`, `max_walk_depth`. It was **not** in `google.adk.plugins.__all__` when fetched. Import it from its module:
```python
from google.adk.apps import App
from google.adk.plugins.auto_tracing_plugin import AutoTracingPlugin  # module path per source file
app = App(name="my_app", root_agent=root_agent,
          plugins=[AutoTracingPlugin(extra_scope_prefixes=("my_company.tools",))])
```
(Usage composed from the signature; there is no official snippet [UNVERIFIED usage].)

Plugin registration rule [V]: in Python, `Runner(plugins=...)` is deprecated. Use `App(plugins=[...])` with `InMemoryRunner(app=app)`. You can also load a plugin without code changes: `adk web --extra_plugins=google.adk.plugins.LoggingPlugin /path/to/agents`.

Other ops plugins [V] (https://adk.dev/plugins/): `LoggingPlugin`, `DebugLoggingPlugin` (YAML per invocation), `ReflectAndRetryToolPlugin`, `ReflectAndRetryModelPlugin`, `ContextFilterPlugin`, `GlobalInstructionPlugin`, `SaveFilesAsArtifactsPlugin`, `ToolCallIntegrityPlugin` (signs stored function calls and runs a tool only if the signature verifies), `ForceEscalationPlugin`, and `ModelConsultObservabilityPlugin`.

### 3.5 BigQuery Agent Analytics plugin [V] (https://adk.dev/integrations/bigquery-agent-analytics/)
```python
from google.adk.plugins.bigquery_agent_analytics_plugin import BigQueryAgentAnalyticsPlugin
plugin = BigQueryAgentAnalyticsPlugin(
    project_id="your-gcp-project-id",
    dataset_id="your-big-query-dataset-id",
)
```
- The default table is `agent_events`, partitioned by `DATE(timestamp)` and clustered by `event_type`, `agent`, and `user_id`. Columns include `trace_id`, `span_id`, `parent_span_id`, `content` (JSON), `latency_ms`, `status`, and `is_truncated`.
- Events: `INVOCATION_*`, `AGENT_*`, `LLM_REQUEST/RESPONSE/ERROR`, `TOOL_STARTING/COMPLETED/ERROR/PAUSED`, `STATE_DELTA`, `A2A_INTERACTION`, HITL events, and the ADK 2.0 workflow events `AGENT_TRANSFER`, `AGENT_STATE_CHECKPOINT`, `EVENT_COMPACTION`, `NODE_OUTPUT`, `NODE_ERROR`.
- Supported since Python v1.21.0, Java v1.5.0, and Kotlin v0.8.0.

---

## 4. Third-party tool landscape

Source for the integration list: https://adk.dev/integrations/?topic=observability [V]. It lists AgentOps, Arize AX, BigQuery Agent Analytics, Datadog, Freeplay, Future AGI, Galileo, Google Cloud Trace, Grafana Cloud, Langfuse, LangWatch, Latitude, Monocle, MLflow Tracing, Phoenix, Respan, W&B Weave, and Zespan. Braintrust and Helicone are not on that list.

### 4.1 Comparison table

| Tool | ADK hookup (verified) | Transport | Strengths | Notes |
|---|---|---|---|---|
| **Cloud Trace / Cloud Observability** | `--otel_to_cloud`, `get_gcp_exporters` | OTLP to `telemetry.googleapis.com` | Native GCP, Session/Span views in Agent Runtime, IAM | Quota truncation of attributes [V] |
| **BigQuery Agent Analytics** | ADK plugin | BigQuery Storage Write | SQL over agent events, joins with business data | Not a trace UI; pair with Looker [V] |
| **Langfuse** | `GoogleADKInstrumentor().instrument()` + `langfuse.get_client()`; `pip install langfuse "google-adk>=2" openinference-instrumentation-google-adk` | OTLP HTTP at `/api/public/otel` (no gRPC) | Open source, self-hostable, prompt management, cost via `gen_ai.usage.cost` | Header `x-langfuse-ingestion-version=4`; regions EU/US/JP/HIPAA [V] |
| **Arize Phoenix** | `phoenix.otel.register(auto_instrument=True)` | OTLP | OSS, local-first, evals | `PHOENIX_API_KEY`, `PHOENIX_COLLECTOR_ENDPOINT` [V] |
| **Arize AX** | `arize.otel.register(space_id, api_key, project_name)` + `GoogleADKInstrumentor` | OTLP | Enterprise version of Phoenix, online evals | [V] |
| **LangSmith** | `pip install langsmith[google-adk]`; `configure_google_adk(project_name=...)` | LangSmith SDK/OTel | Datasets, evals, annotation queues | env `LANGSMITH_TRACING=true` [V] |
| **W&B Weave** | Raw OTLP exporter to `https://trace.wandb.ai/otel/v1/traces`, Basic auth `api:<key>`, `project_id` header | OTLP HTTP | Experiment tracking lineage, evals | The global tracer provider must be set **before** ADK components exist [V] |
| **Datadog LLM Observability** | `ddtrace-run adk run my_agent` with `DD_LLMOBS_ENABLED=true`, `DD_LLMOBS_ML_APP`, `DD_LLMOBS_AGENTLESS_ENABLED=true` | ddtrace, or OTLP with header `dd-otlp-source=llmobs` | Joins APM, infra, and security | Ingests OTel GenAI **1.37+** and OpenInference [V] |
| **Galileo** | `otel.GalileoSpanProcessor()` + `GoogleADKInstrumentor` | OTLP | Eval-centric (Luna evaluators [UNVERIFIED]), guardrails | env `GALILEO_PROJECT`, `GALILEO_LOG_STREAM` [V] |
| **AgentOps.ai** | `agentops.init()` | Own SDK (OTel-based) | Session replays; spans `adk.agent.<Name>`, `adk.llm.<model>`, `adk.tool.<tool>` | **Replaces ADK's native tracer with a no-op** [V], which conflicts with Cloud Trace |
| **MLflow 3 Tracing** | ADK listed on the MLflow Tracing integration page; `@mlflow.trace`, `mlflow.<lib>.autolog()` | "Fully OpenTelemetry-compatible," supports GenAI semconv export and ingest [V] | OSS, ties into model registry and eval | Version/date not shown on the fetched page |
| **Braintrust** | [UNVERIFIED] `braintrust-adk` / OTel. The doc URL I tried returned 404 | OTLP | Eval-first, CI scorers | Verify before the slide |
| **Helicone** | Gateway: OpenAI-compatible `base_url="https://ai-gateway.helicone.ai"` [V]; for ADK use `LiteLlm` pointed at the gateway [UNVERIFIED pattern] | HTTP proxy | 100+ models, provider fallbacks, unified billing, "0% markup" [V] | A gateway, not a tracer: captures LLM calls only, not tool or agent spans |

**Architectural takeaway:** the market split into (a) **OTel-native backends** that ingest `gen_ai.*` (Cloud Trace, Datadog, Langfuse, MLflow, Weave), (b) **OpenInference-instrumentor shops** (Arize, Phoenix, Galileo, Langfuse), (c) **proprietary-SDK** tools (AgentOps, LangSmith helper), and (d) **gateways** (Helicone, LiteLLM proxy) that see only model traffic. Teach students to export once and fan out from an OTel Collector.

### 4.2 Third-party code: ADK + Langfuse via OpenInference (source: https://adk.dev/integrations/langfuse/) [V]
```bash
pip install langfuse "google-adk>=2" openinference-instrumentation-google-adk
export LANGFUSE_PUBLIC_KEY=pk-lf-...
export LANGFUSE_SECRET_KEY=sk-lf-...
export LANGFUSE_BASE_URL=https://cloud.langfuse.com   # or us./jp./hipaa. or self-host
export GOOGLE_API_KEY=...
```
```python
from langfuse import get_client
from openinference.instrumentation.google_adk import GoogleADKInstrumentor

langfuse = get_client()
assert langfuse.auth_check()
GoogleADKInstrumentor().instrument()
# ...define LlmAgent / App and run as usual; spans flow to Langfuse
```
(The env var names are as I recall them. The page confirms that public key, secret key, base URL, and Gemini key are required, but quote limits kept me from capturing exact names [UNVERIFIED names].)

Alternative with no vendor SDK, using raw OTLP to Langfuse [V endpoint/header]:
```bash
AUTH=$(echo -n "pk-lf-...:sk-lf-..." | base64 -w 0)
export OTEL_EXPORTER_OTLP_ENDPOINT="https://cloud.langfuse.com/api/public/otel"
export OTEL_EXPORTER_OTLP_HEADERS="Authorization=Basic ${AUTH},x-langfuse-ingestion-version=4"
adk web path/to/agents   # ADK's maybe_set_otel_providers picks up OTEL_* env
```

### 4.3 Third-party code: Arize AX [V] (https://adk.dev/integrations/arize-ax/)
```python
import os
from arize.otel import register
from openinference.instrumentation.google_adk import GoogleADKInstrumentor

tracer_provider = register(
    space_id=os.environ["ARIZE_SPACE_ID"],
    api_key=os.environ["ARIZE_API_KEY"],
    project_name="my-adk-project",
)
GoogleADKInstrumentor().instrument(tracer_provider=tracer_provider)
```

### 4.4 Datadog [V] (https://adk.dev/integrations/datadog/ and https://docs.datadoghq.com/llm_observability/instrumentation/otel_instrumentation/)
```bash
pip install ddtrace
export DD_API_KEY=... DD_SITE=... DD_LLMOBS_ENABLED=true DD_LLMOBS_ML_APP=my-app DD_LLMOBS_AGENTLESS_ENABLED=true
ddtrace-run adk run my_agent
# OTel route instead:
export OTEL_EXPORTER_OTLP_TRACES_PROTOCOL=http/protobuf
export OTEL_EXPORTER_OTLP_TRACES_HEADERS="dd-api-key=<key>,dd-otlp-source=llmobs"
```
The variables must be exported in the shell, not set in the agent `.env`, because `ddtrace-run` reads them at launch [V].

---

## 5. Registries and governance

### 5.1 Google Cloud Agent Registry [V] (https://docs.cloud.google.com/agent-registry/overview, updated 2026-10-22)
- Catalogs **agents, MCP servers and tools, endpoints, and standalone skills** for discovery, reuse, and governance.
- It is one of three parts. **Agent Registry** is the authoritative catalog. **Agent Identity** provides agent principals. **Agent Gateway** queries the registry and enforces IAM and content-security policies (Model Armor) on agent traffic.
- Deployment models: single-project, or a **central governance project** in which components from other projects are registered as "remote" `Service` resources.
- Telemetry tie-in: ADK v2.10+ writes the registry URN to `gen_ai.main_agent.id` [V].
- The page states no release stage. "Gemini Enterprise agent registry" in the Gemini Enterprise app (agent gallery for employees) is a related but distinct surface [UNVERIFIED how they're linked].

### 5.2 A2A Agent Cards [V] (https://a2a-protocol.org/latest/specification/)
- The latest spec is **1.0.0** (earlier: 0.3.0, 0.2.6, 0.1.0). A blog banner dated **2026-08-27** announces A2A **joining the Agentic AI Foundation** [V headline only].
- Discovery: `https://{server_domain}/.well-known/agent-card.json`.
- Required AgentCard fields: `name`, `description`, `supportedInterfaces`, `version`, `capabilities` (`streaming`, `pushNotifications`, `extendedAgentCard`), `defaultInputModes`, `defaultOutputModes`, `skills`. Also `securitySchemes`/`security`, `provider`, `extensions`, and **`signatures`** (signed cards: canonicalization §8.4.1, format §8.4.2, verification §8.4.3).
- Governance angle: a signed card is the agent's "passport." The registry stores cards, and the gateway checks them.

### 5.3 MCP Registry
- Official registry at **registry.modelcontextprotocol.io**, launched in **preview on 2025-09-08** [V] (https://blog.modelcontextprotocol.io/posts/2025-09-08-mcp-registry-preview/). Open OpenAPI spec. Public sub-registries (marketplaces) and private sub-registries (enterprise). The launch post makes no durability guarantees. Moderation is by community flagging plus maintainer denylist.
- Status in 2026: still preview, with the API frozen at `v0.1` (`GET /v0.1/servers`) [UNVERIFIED, from a secondary source]. Reported size is roughly 17k servers as of 2026-07-16 per Towards AI, while other guides say about 2k [UNVERIFIED, conflicting].
- Key caveat: namespace auth proves who published a server, not that the code is safe. **A listing is not a security review.**

---

## 6. Identity for agents [V] (https://docs.cloud.google.com/agent-builder/agent-engine/agent-identity, updated 2026-10-22)
- Each agent gets a **SPIFFE ID**: `spiffe://TRUST_DOMAIN/resources/SERVICE/RESOURCE_PATH`. The IAM principal is `principal://TRUST_DOMAIN/resources/...`.
- Example: `principal://agents.global.org-123456789012.system.id.goog/resources/aiplatform/projects/9876543210/locations/us-central1/reasoningEngines/my-test-agent`.
- The trust domain is `agents.global.org-ORG_ID.system.id.goog`, or `agents.global.proj-PROJECT_NUMBER.system.id.goog` for projects without an organization.
- Compared with service accounts: not shared by default, **can't be impersonated, no long-lived keys**. Access tokens are **bound to the agent's X.509 certificate**. Certificates are valid for 24 hours and auto-renew.
- The agent can act as itself or on behalf of a user (OAuth delegation).
- Failure modes: deleting an agent leaves stale IAM bindings. Redeploying creates a new resource ID and principal, so you must re-grant roles. Legacy GCS bucket roles can't be granted to agents.
- Slide framing: workload identity (SPIFFE) gives the agent a principal, the registry gives it an entry, the gateway gives it policy, and traces give it accountability, all joined on the same ID.

## 7. Runtime guardrails: Model Armor [V]
Service (https://docs.cloud.google.com/model-armor/overview, updated 2026-10-22):
- **Filters:**
  - Responsible AI (hate, harassment, sexual, dangerous; CSAM always on).
  - Prompt injection and jailbreak (inputs under 3 words return `NO_MATCH_FOUND`).
  - Sensitive Data Protection (basic, or advanced with de-identification).
  - Malicious URL (first 256 URLs).
- **Templates** set filters and thresholds (High, Medium-and-above, Low-and-above). **Floor settings** set a project-wide minimum. Modes are **Inspect only** (start here) and **Inspect and block**.
- Documents up to 4 MB. Image screening is in Preview (us/eu only).
- **Limits:** single-turn only, no Base64 decoding, no audio or video.
- Integrations: Agent Gateway, Apigee, Gemini Enterprise, Google MCP servers, networking, Agent Platform, LangChain. Billed per token.

ADK plugin (https://adk.dev/integrations/model-armor/, ADK Python ≥ 2.8.0, `pip install 'google-adk[gcp]'`):
```python
from google.adk.agents import LlmAgent
from google.adk.apps import App
from google.adk.integrations.model_armor import ModelArmorConfig, ModelArmorPlugin

agent = LlmAgent(model="gemini-flash-latest", name="screened_agent",
                 instruction="You are a helpful assistant.")
app = App(
    name="model_armor_demo",
    root_agent=agent,
    plugins=[ModelArmorPlugin(config=ModelArmorConfig(
        prompt_template_name="projects/my-project/locations/us-central1/templates/my-prompt-template",
        response_template_name="projects/my-project/locations/us-central1/templates/my-response-template",
    ))],
)
```
Config: `input_blocked_message`, `output_blocked_message`, and `block_on_screening_failure=True` (fail closed). Both templates must be in the **same region**, or construction raises `ValueError` [V].

**Diagram flow (guardrail lifecycle):** user prompt, then the Model Armor prompt template (via the plugin's before-model callback). Block returns the canned message and the span records the block. Allow passes the prompt to the LLM, then the response goes through the response template, then the user. Tool output from untrusted sources (web, MCP) is the indirect-injection risk. Model Armor screens model I/O, so add tool-level controls (`ToolCallIntegrityPlugin`, Agent Gateway egress policy).

---

## 8. Cost management and model routing
- **Token accounting standard:** OTel `gen_ai.usage.*` with cache and reasoning subsets (section 2.3). Langfuse reads `gen_ai.usage.cost` [V].
- **ADK native:** `ADK_EXPERIMENTAL_TELEMETRY=true` (v2.8) gives per-invocation and per-workflow token spend and inference/tool counts. v2.13 adds `ForceEscalationPlugin` ("deterministic model consultation") and metrics for consultation escalations, tokens, and cost. `ModelConsultObservabilityPlugin` is exported [V]. This is the "cheap model first, escalate to the strong model" pattern, now measurable.
- **Context-cost levers in ADK:** `ContextFilterPlugin` shrinks context. EVENT_COMPACTION events and compaction counts per workflow appear in v2.13 [V].
- **Gateways:** Helicone AI Gateway (OpenAI-compatible, 100+ models, fallbacks, unified billing) [V]. LiteLLM proxy through ADK's `LiteLlm` model wrapper [UNVERIFIED in this pass, well known].
- **Vertex/Agent Platform routing:** Google offered a "Model Optimizer" router in 2025 that picked a Gemini model by a cost/quality setting [UNVERIFIED; the doc URL 404'd today]. Do not put it on a slide without re-checking.
- **Recipe:** tag every span with `user.id`, `tenant`, `gen_ai.agent.name`. Export to BigQuery. Build a cost-per-successful-task metric (not cost per call). Alert on tokens per invocation p95.

---

## 9. Failure modes (teach these)
1. **Schema drift:** ADK 2.13 removed `call_llm`, so dashboards and alerts keyed on it go silent. Pin `ADK_TELEMETRY_SCHEMA_VERSION_OPT_IN` during migration [V].
2. **Tracer-provider ordering:** if the global provider is set after ADK components exist, spans are lost (Weave doc warning) [V].
3. **Double or zero instrumentation:** AgentOps no-ops ADK's tracer [V]. Combining it with Cloud Trace silently drops the GCP side. Running an OpenInference instrumentor plus native ADK spans can duplicate them.
4. **Over-capturing content:** prompt, response, and `user.id` capture needs consent and a retention policy. The semconv default is off [V].
5. **Fake conversation IDs:** filling `gen_ai.conversation.id` with a trace ID breaks session grouping. The spec forbids it [V].
6. **Attribute truncation** at Cloud Trace quotas. Use `EVENT_ONLY` or BigQuery for large payloads [V].
7. **Identity churn:** redeploying gives a new principal, so IAM grants are missing [V].
8. **Guardrail gaps:** single-turn screening, Base64 bypass, no audio [V]. Region-mismatched templates crash at startup [V].
9. **Registry trust:** an MCP registry listing does not verify code [secondary].
10. **Sampling:** if span-start attributes are missing, samplers can't keep the expensive or failed agent runs [V].

---

## 10. Interview questions (crisp answers)
1. **What are the core OTel GenAI agent span names?** `invoke_agent {agent}`, `execute_tool {tool}`, `create_agent {agent}`, `invoke_workflow`, and inference `{op} {model}`, e.g. `chat gpt-4`. Status is still Development.
2. **CLIENT or INTERNAL for invoke_agent?** CLIENT for a remote agent (for example, over A2A). INTERNAL for an in-process sub-agent. `execute_tool` is INTERNAL.
3. **Does `input_tokens` include cached tokens?** Yes. `cache_read`/`cache_write` are subsets. Output includes reasoning tokens.
4. **How do you send ADK traces to Cloud Trace with no code?** `adk web --otel_to_cloud`, or `adk deploy agent_engine --otel_to_cloud`.
5. **What broke in ADK 2.13 telemetry?** It defaults to semconv 1.44 and removes `call_llm`. Opt back with `ADK_TELEMETRY_SCHEMA_VERSION_OPT_IN=otel_semconv_1_36`.
6. **Why prefer OTel over a vendor SDK?** One instrumentation, many backends through a Collector. No lock-in. Correlates with app and infra traces.
7. **How is an agent principal different from a service account?** It is SPIFFE-based and per-agent, can't be impersonated, has no long-lived keys, and its tokens are bound to a 24-hour X.509 certificate.
8. **What does Agent Gateway add over Agent Registry?** The registry is the catalog. The gateway is the policy enforcement point: IAM plus Model Armor on agent traffic.
9. **Where does Model Armor sit in ADK?** As `ModelArmorPlugin` on the `App`, screening prompts and responses in model callbacks. It fails closed by default.
10. **What are Model Armor's limits?** Single-turn, no Base64 decoding, no audio or video, 4 MB documents.
11. **What is in an A2A Agent Card and where is it?** `/.well-known/agent-card.json`, with name, description, supportedInterfaces, version, capabilities, input/output modes, skills, security schemes, and optional signatures.
12. **Is the MCP Registry a security vetting service?** No. It handles discovery and namespace ownership. Vet servers yourself or through a private sub-registry.
13. **How do you attribute cost per tenant?** Resource or span attributes, then token usage per span, then BigQuery Agent Analytics or the backend, aggregated per successful task.
14. **Name a pitfall of combining AgentOps and Cloud Trace.** AgentOps replaces ADK's tracer with a no-op, so native exports disappear.

---

## 11. Codelabs and hands-on resources
- Verified docs to use as labs [V]:
  - ADK Traces: https://adk.dev/observability/traces/
  - Cloud Trace integration: https://adk.dev/integrations/cloud-trace/
  - BigQuery Agent Analytics: https://adk.dev/integrations/bigquery-agent-analytics/
  - Model Armor plugin: https://adk.dev/integrations/model-armor/
  - Agent Runtime tracing: https://docs.cloud.google.com/agent-builder/agent-engine/manage/tracing
  - Plugins catalog: https://adk.dev/plugins/
- Codelabs: **[UNVERIFIED]**. I could not confirm any Google Codelab URL for ADK observability today. Two guessed URLs returned 404, and the codelabs index is dynamic. Search codelabs.developers.google.com for "ADK", "Agent Engine", and "Cloud Trace" before citing one.

---

## 12. Slide ideas (8-10, with animation)
1. **"The trace is the agent's flight recorder."** A span waterfall `invoke_agent > invoke_workflow > generate_content > execute_tool`. *Animation:* the bars grow left to right in time order and the tool bar flashes red on error.
2. **"Semconv moved house."** The opentelemetry.io page dissolves into the `semantic-conventions-genai` repo, with a "Development" badge. *Animation:* a moving-truck wipe.
3. **"One flag to the cloud."** A terminal types `adk web --otel_to_cloud` and the Cloud Trace UI lights up. *Animation:* the typewriter finishes, then a cross-fade to the trace screenshot.
4. **"ADK 2.13 breaking change."** `call_llm` crossed out and replaced by `generate_content {model}`. *Animation:* strike-through, then the new span slides in and a dashboard tile goes grey, then recovers after the opt-in flag appears.
5. **"Export once, fan out."** ADK feeds an OTel Collector, which feeds Cloud Trace, Langfuse, Datadog, and BigQuery. *Animation:* particles flow along the fan-out edges.
6. **"Four families of AgentOps tools."** A 2x2 of OTel-native, OpenInference, proprietary SDK, and gateway, with logos placed. *Animation:* logos drop into quadrants one by one.
7. **"Passport, registry, border control."** Agent Identity (SPIFFE certificate), Agent Registry (catalog), Agent Gateway (policy). *Animation:* an agent icon gets a passport stamp, a registry entry, then passes a gate.
8. **"Guardrail sandwich."** Prompt, Model Armor, LLM, Model Armor, user, with a blocked branch. *Animation:* a red prompt-injection packet bounces off the first layer.
9. **"Tokens are COGS."** A stacked bar of input (with cached slice), output (with reasoning slice), and cost per successful task. *Animation:* the cached slice shrinks as caching turns on.
10. **"Ten ways your observability lies."** The failure-mode checklist. *Animation:* each item ticks off with a short one-line fix.

---

## 13. Sources (fetched 2026-10-23 unless noted)
- OTel GenAI semconv repo: https://github.com/open-telemetry/semantic-conventions-genai (agent spans: /blob/main/docs/gen-ai/gen-ai-agent-spans.md; spans: /gen-ai-spans.md; inference: /client-inference.md)
- Deprecated pages: https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-agent-spans/
- ADK releases: https://github.com/google/adk-python/releases (v2.7.1-v2.13.0, Aug-Oct 2026)
- ADK traces: https://adk.dev/observability/traces/ ; Cloud Trace: https://adk.dev/integrations/cloud-trace/ ; Plugins: https://adk.dev/plugins/
- AutoTracingPlugin source: https://github.com/google/adk-python/blob/main/src/google/adk/plugins/auto_tracing_plugin.py
- BigQuery plugin: https://adk.dev/integrations/bigquery-agent-analytics/ ; Model Armor plugin: https://adk.dev/integrations/model-armor/
- Integrations: https://adk.dev/integrations/{langfuse,phoenix,arize-ax,weave,agentops,galileo,datadog}/
- LangSmith: https://docs.langchain.com/langsmith/trace-with-google-adk
- Langfuse OTel: https://langfuse.com/docs/opentelemetry/get-started
- Datadog OTel: https://docs.datadoghq.com/llm_observability/instrumentation/otel_instrumentation/
- MLflow Tracing: https://mlflow.org/docs/latest/genai/tracing/
- Helicone: https://docs.helicone.ai/
- Agent Runtime tracing: https://docs.cloud.google.com/agent-builder/agent-engine/manage/tracing
- Agent Platform overview: https://docs.cloud.google.com/agent-builder/agent-engine/overview
- Agent Identity: https://docs.cloud.google.com/agent-builder/agent-engine/agent-identity
- Agent Registry: https://docs.cloud.google.com/agent-registry/overview
- Model Armor: https://docs.cloud.google.com/model-armor/overview
- A2A spec: https://a2a-protocol.org/latest/specification/
- MCP Registry preview (2025-09-08): https://blog.modelcontextprotocol.io/posts/2025-09-08-mcp-registry-preview/ ; secondary: https://pub.towardsai.net/mcp-registries-in-mid-2026-one-upstream-won-2ce541b92036
