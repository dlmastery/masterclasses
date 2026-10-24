# 05 — ADK 2.0: Agent Config (YAML) and Plugins

Research date: 2026-10-23. Latest google-adk (Python) release: **v2.13.0 (23 Oct 2026)**. Docs moved from `google.github.io/adk-docs` to **https://adk.dev** (the old URLs now return a 301 redirect).
Items marked [UNVERIFIED] could not be confirmed against a primary source.

---

## 0. Names and dates to get right on the slides

| Old name | Current name (Oct 2026) | When / source |
|---|---|---|
| Google Agentspace | **Gemini Enterprise** | Rebranded 9 Oct 2025 (secondary sources agree: atlan.com, g-gen.co.jp; Google blog not re-fetched) |
| Vertex AI (agent stack) | part of **Gemini Enterprise Agent Platform** | 22 Apr 2026, Cloud Next '26: "Vertex AI is now part of Gemini Enterprise Agent Platform" — https://docs.cloud.google.com/gemini-enterprise-agent-platform/release-notes |
| Vertex AI Agent Engine | **Agent Runtime** | Same entry, 22 Apr 2026: "Agent Engine is now Agent Runtime." |
| Memory Bank / Agent Builder Sessions | Agent Platform Memory Bank / Agent Platform Sessions | Same release (per search summary of the notes) |
| `GOOGLE_GENAI_USE_VERTEXAI` | `GOOGLE_GENAI_USE_ENTERPRISE` (as used in current adk.dev samples) | adk.dev/agents/config, adk.dev BigQuery plugin page. Whether the old variable still works was not checked. [UNVERIFIED] |
| google.github.io/adk-docs | **adk.dev** | 301 redirect observed 2026-10-23 |

ADK 2.0 GA dates (https://adk.dev/2.0/): **Python 19 May 2026**, Go 30 Jun 2026, TypeScript 21 Aug 2026. A v1 maintenance line still gets backports (v1.39.1, 27 Aug 2026). To stay on 1.x: `pip install "google-adk~=1.0"`.

Related Agent Runtime notes: OTel tracing is on by default for newly deployed ADK agents (18 Jun 2026). User-ID logging needs ADK ≥ 2.1 (27 May 2026). `gen_ai` metrics need ADK ≥ 2.6.0 (13 Aug 2026).

---

## 1. Why both features exist: separate the "what" from the "how"

- **Agent Config (YAML)** says *what the agent is*: name, model, instruction, tools, sub-agents and, in 2.x, the graph edges. Prompt engineers and operators can change it without a Python release.
- **Plugins** say *how every run is governed*: logging, retries, guardrails, context trimming and analytics. They are registered once on the `App` and apply to every agent, model call and tool call.
- **Callbacks** are the per-agent version of plugin hooks. They are set on one agent object, or in YAML through `*_callbacks` keys.

Picture for the deck: an ADK app has three layers. **Declarative topology** (YAML) sits on top of **per-node behavior** (callbacks), and both run inside **cross-cutting policy** (plugins on the App/Runner).

---

## 2. Agent Config (YAML)

### 2.1 Status (be precise)
- The docs page https://adk.dev/agents/config/ still says: *"The Agent Config feature is experimental and has some known limitations."* It lists support from **Python v1.11.0** and **Java v0.3.0**.
- The `adk create` CLI help in `src/google/adk/cli/cli_tools_click.py` (main, Oct 2026) still reads:
  > `--type` … "EXPERIMENTAL Optional. Type of agent to create: 'config' or 'code'. 'config' is not ready for use so it defaults to 'code'." — `type=click.Choice(["CODE","CONFIG"], case_sensitive=False)`, `default="CODE"`.
- The published JSON schema `src/google/adk/agents/config_schemas/AgentConfig.json` now carries **`"deprecated": true`** at the top level. Its `oneOf` covers only the 1.x classes: `LlmAgentConfig`, `LoopAgentConfig`, `ParallelAgentConfig`, `SequentialAgentConfig` and `BaseAgentConfig`. It has **no** `Workflow` or `FunctionNode` entry. Treat the schema as legacy editor help, not the full 2.x grammar. (The `deprecated` flag was read directly from the file on 2026-10-23. Why it was set is not documented. [UNVERIFIED rationale])
- **2.x direction: YAML now describes graphs.** v2.9.0 (10 Sep 2026) added *"load ADK 2.0 graph workflows from YAML configuration"* (commit 2a9461b). It ships `agent_class: Workflow` + `edges:`. The in-repo guide `docs/guides/agents/config/index.md` describes YAML as a way to build "an agent, or a whole multi-agent graph".
- Related release notes: v2.8.0 *"block yaml and ruamel deserialization in agent-config code references"*. v2.11.0 *"skip `__init__.py` for config-based adk create"*. v1.39.1 backported code-reference and `config_path` validation to v1.

### 2.2 Scaffolding and running
```bash
adk --version
adk create --type=config my_agent      # -> my_agent/root_agent.yaml + my_agent/.env
adk run my_agent                       # terminal
adk web .                              # dev UI (parent dir of agent folders)
adk api_server .                       # HTTP server
```
`.env` (from adk.dev/agents/config):
```
GOOGLE_GENAI_USE_ENTERPRISE=0
GOOGLE_API_KEY=<your-Google-Gemini-API-key>
# or
GOOGLE_GENAI_USE_ENTERPRISE=1
GOOGLE_CLOUD_PROJECT=<your_gcp_project>
GOOGLE_CLOUD_LOCATION=us-central1
```
**Loader precedence** (in-repo guide plus `cli/utils/agent_loader.py`): `{agent}/__init__.py` exposing `root_agent` (or `app`), then `{agent}/agent.py`, then `{agent}/root_agent.yaml`. *"The Python definition has to go, or it keeps winning."* This is a common failure mode.

### 2.3 Minimal YAML (verbatim, adk.dev/agents/config)
```yaml
# yaml-language-server: $schema=https://raw.githubusercontent.com/google/adk-python/refs/heads/main/src/google/adk/agents/config_schemas/AgentConfig.json
name: assistant_agent
model: gemini-flash-latest
description: A helper agent that can answer users' questions.
instruction: You are an agent to help answer users' various questions.
```
Built-in tool:
```yaml
name: search_agent
model: gemini-flash-latest
description: 'an agent whose job it is to perform Google search queries and answer questions about the results.'
instruction: You are an agent whose job is to perform Google search queries and answer questions about the results.
tools:
  - name: google_search
```
Custom Python tool (fully-qualified name):
```yaml
agent_class: LlmAgent
model: gemini-flash-latest
name: prime_agent
description: Handles checking if numbers are prime.
instruction: |
  You are responsible for checking whether numbers are prime.
  When asked to check primes, you must call the check_prime tool with a list of integers.
  Never attempt to determine prime numbers manually.
  Return the prime number results to the root agent.
tools:
  - name: ma_llm.check_prime
```
Sub-agents by file:
```yaml
agent_class: LlmAgent
model: gemini-flash-latest
name: root_agent
description: Learning assistant that provides tutoring in code and math.
instruction: |
  You are a learning assistant ... delegate coding questions to the code_tutor_agent and math questions to the math_tutor_agent.
sub_agents:
  - config_path: code_tutor_agent.yaml
  - config_path: math_tutor_agent.yaml
```
Load it from Python:
```python
from google.adk.agents import config_agent_utils
agent = config_agent_utils.from_config("my_agent/root_agent.yaml")
```
Java: `BaseAgent agent = ConfigAgentUtils.fromConfig("my_agent/root_agent.yaml");`

### 2.4 Full key list (from AgentConfig.json, `LlmAgentConfig.properties`)
`agent_class, name, description, sub_agents, before_agent_callbacks, after_agent_callbacks, model, model_code, instruction, static_instruction, disallow_transfer_to_parent, disallow_transfer_to_peers, input_schema, output_schema, output_key, include_contents, tools, before_model_callbacks, after_model_callbacks, before_tool_callbacks, after_tool_callbacks, generate_content_config`

- `agent_class` enum for LlmAgent: `LlmAgent`, `Agent`, `google.adk.agents.LlmAgent`, …, or `""` (the default is LlmAgent). Other classes: `SequentialAgent`, `ParallelAgent`, `LoopAgent` (`max_iterations`). In 2.x the loader also takes `Workflow` and `FunctionNode`, plus any fully-qualified custom class.
- `sub_agents[]` entries are `AgentRefConfig {config_path | code}`.
- `tools[]` entries are `ToolConfig {name, args}`. `name` is a built-in name (e.g. `google_search`, `AgentTool`) or a fully-qualified user path.
- `model_code` is a `CodeConfig {name, args}` that instantiates a `BaseLlm` such as LiteLlm. It "Cannot be set together with `model`."
- Callbacks: a list of `{name: my_library.security_callbacks.before_agent_callback}`.

Supported tools listed on the docs: `google_search, google_maps_grounding, load_artifacts, url_context, exit_loop, preload_memory, get_user_choice, enterprise_web_search, load_web_page` (fully-qualified path), `AgentTool, LongRunningFunctionTool, McpToolset, ExampleTool`, plus `VertexAiSearchTool` (Python/Java). The page itself warns that "not all of these tools are fully supported".

**Known limitations** (docs): only Gemini models are supported. `LangGraphAgent` and `A2aAgent` are not supported. Code-dependent features need Python or Java. Deployment to Cloud Run and Agent Runtime works the same way as for code agents.

### 2.5 1.x-style multi-agent YAML (real sample, `contributing/samples/multi_agent/multi_agent_loop_config`)
```yaml
# root_agent.yaml
agent_class: SequentialAgent
name: IterativeWritingPipeline
description: Iterative writing pipeline agent.
sub_agents:
  - config_path: writer_agents/initial_writer_agent.yaml
  - config_path: loop_agent.yaml
```
```yaml
# loop_agent.yaml
agent_class: LoopAgent
name: RefinementLoop
description: Refinement loop agent.
max_iterations: 5
sub_agents:
  - config_path: writer_agents/critic_agent.yaml
  - config_path: writer_agents/refiner_agent.yaml
```
```yaml
# writer_agents/critic_agent.yaml (abridged)
agent_class: LlmAgent
name: CriticAgent
model: gemini-2.5-pro
instruction: |
  ... Document to Review: {{current_document}} ...
  Respond *exactly* with the phrase "No major issues found." ...
include_contents: none
output_key: criticism
```
This is the **generator → critic → refiner loop** (a verifier at each step) expressed in YAML. Note that ADK 2.0 TypeScript logs deprecation warnings for `SequentialAgent`/`ParallelAgent`/`LoopAgent` and recommends graph workflows (adk.dev/2.0). Python 2.x still loads them.

### 2.6 ADK 2.0 graph workflow in YAML (verbatim, `contributing/samples/workflows/loop_config`)
```yaml
# root_agent.yaml
agent_class: Workflow
name: root_agent
edges:
  - - START
    - .agent.process_input
    - generate_headline.yaml
    - evaluate_headline.yaml
    - .agent.route_headline
  - - .agent.route_headline
    - unrelated: generate_headline.yaml
```
```yaml
# generate_headline.yaml
agent_class: LlmAgent
name: generate_headline
instruction: |
  Write a headline about the topic "{topic}".
  If feedback is provided, take it into account.
  The feedback: {feedback?}
```
```yaml
# evaluate_headline.yaml  (the per-step verifier)
agent_class: LlmAgent
name: evaluate_headline
instruction: |
  Grade whether the headline is related to technology or software engineering.
output_schema:
  name: loop_config.agent.Feedback
output_key: feedback
```
```python
# agent.py
from typing import Literal
from google.adk import Event
from pydantic import BaseModel, Field

class Feedback(BaseModel):
  grade: Literal["tech-related", "unrelated"] = Field(description="...")
  feedback: str = Field(description="...")

def process_input(node_input: str):
  """Puts user input in the state."""
  return Event(state={"topic": node_input})

def route_headline(node_input: Feedback):
  return Event(route=node_input.grade)
```
**Edge grammar** (from `docs/guides/agents/config/index.md`):
- **Chain**: a block list `- - A\n  - B\n  - C` gives A→B and B→C. *"An inline list `[a, b]` always means a fan-out."*
- **Routing map**: `refund: refund_handler.yaml`, `question: faq_agent.yaml`, `other: [logger.yaml, escalation_agent.yaml]` (a list value is a fan-out).
- **Explicit edge**: `{from_node: classifier, to_node: refund_handler.yaml, route: refund}`.
- **Node forms**: `START`; a node name defined earlier in the file; `x.yaml` (a path relative to the current file); a dotted function ref (wrapped in a `FunctionNode` named after the function); a leading-dot ref `.agent.fn` (resolved relative to the agent package); or an inline mapping, e.g. `{name: preprocess, agent_class: FunctionNode, func_code: my_module.functions.process_data}`.
- Nodes are **cached by name/reference**, so repeating `generate_headline.yaml` reuses the same instance. That reuse is what makes loops work. *"A name an earlier edge has not introduced is rejected."*

**How the mapper works (2.x):** it reads the target class's field annotations and converts each YAML value to the type that field expects (tools, callbacks, schema, sub-agents, model, edges). *"A field added to a class is configurable immediately, with no parser to update."* Built-in configs forbid unknown keys. `Workflow`/`FunctionNode` declare no schema, so an unknown key only logs a warning: `"%s does not accept %s; ignoring."`

**Security model:**
- `yaml.safe_load` only.
- Every `*_code` and `*_callbacks` reference is checked against a module **denylist covering the entire stdlib**, plus `yaml` and `ruamel`, which offer unsafe deserialization paths to RCE.
- Absolute paths are rejected.
- A denylist for the `args` key exists but is **off by default** (`_ENFORCE_YAML_KEY_DENYLIST = False`). The guide says making it default-deny "is in progress".
- Guidance: *"Treat a config that can name arbitrary modules as trusted input."*

---

## 3. Plugins

### 3.1 Concept and registration
Docs: https://adk.dev/plugins/ (listed under "App management"). Support starts at Python v1.7.0, TypeScript v0.2.5, Go v0.4.0, Java v0.3.0 and Kotlin v0.7.0. A plugin subclasses `BasePlugin(name=...)` (source: `src/google/adk/plugins/base_plugin.py`). *"Plugin callback functions have precedence over callbacks implemented at the object level."*

```python
from google.adk.agents.base_agent import BaseAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.plugins.base_plugin import BasePlugin
from google.adk.apps import App
from google.adk.runners import InMemoryRunner

class CountInvocationPlugin(BasePlugin):
  def __init__(self) -> None:
    super().__init__(name="count_invocation")
    self.agent_count = 0
    self.llm_request_count = 0

  async def before_agent_callback(self, *, agent: BaseAgent,
                                  callback_context: CallbackContext) -> None:
    self.agent_count += 1
    print(f"[Plugin] Agent run count: {self.agent_count}")

  async def before_model_callback(self, *, callback_context: CallbackContext,
                                  llm_request: LlmRequest) -> None:
    self.llm_request_count += 1

app = App(name="test_app_with_plugin", root_agent=root_agent,
          plugins=[CountInvocationPlugin()])
runner = InMemoryRunner(app=app)
```
(The class name, `name=` and the `App`/`InMemoryRunner` lines are verbatim from adk.dev/plugins. The import lines and the body layout are reconstructed.)

- `Runner(plugins=...)` is **deprecated**. `runners.py` warns: *"The `plugins` argument is deprecated. Please use the `app` argument"* (DeprecationWarning). Passing both raises `ValueError`.
- `App` fields (`apps/app.py`): `name`, `root_agent` (any `BaseNode`), `plugins`, `events_compaction_config`, `context_cache_config`, `resumability_config`.
- CLI injection (Python only): `adk web --extra_plugins=google.adk.plugins.LoggingPlugin /path/to/agents` (repeatable; also on `adk api_server`). These are added **after** the App's own plugins. This is also the only way to attach plugins to a pure-YAML agent, because **AgentConfig has no `plugins` key** (none in the schema; the agent loader builds an agent, not an App, from `root_agent.yaml`).
- Other languages: TS `new InMemoryRunner({agent, appName, plugins:[...]})`. Java `new InMemoryRunner(rootAgent, "appName", List.of(...))`. Go `runner.Config{PluginConfig: runner.PluginConfig{Plugins: ...}}`.

### 3.2 Every hook (Python, keyword-only, all `async`), in lifecycle order
| Hook | Signature (kwargs) | Non-None return means |
|---|---|---|
| `on_user_message_callback` | `invocation_context, user_message: types.Content` | replaces the user message |
| `before_run_callback` | `invocation_context` | halts the runner, which ends with that content |
| `before_agent_callback` | `agent, callback_context` | skips the agent (and its callbacks) and returns the Content |
| `before_model_callback` | `callback_context, llm_request` | skips the LLM call (e.g. a cache hit) |
| `after_model_callback` | `callback_context, llm_response` | replaces the response |
| `on_model_error_callback` | `callback_context, llm_request, error` | an `LlmResponse` suppresses the exception |
| `before_tool_callback` | `tool, tool_args, tool_context` | a dict skips the tool and becomes its result |
| `after_tool_callback` | `tool, tool_args, tool_context, result` | a dict replaces the result |
| `on_tool_error_callback` | `tool, tool_args, tool_context, error` | a dict suppresses the error; `after_tool` then runs normally |
| `after_agent_callback` | `agent, callback_context` | Content is used as the agent response |
| `on_event_callback` | `invocation_context, event` | modifies the event before it is persisted and yielded (Python merges only the fields you set; `id`/`invocation_id`/`timestamp` are kept) |
| `on_agent_error_callback` | `agent, callback_context, error` | return is ignored (notification only) |
| `on_run_error_callback` | `invocation_context, error` | notification only |
| `after_run_callback` | `invocation_context` | `None` only; cleanup/flush |
| `close()` | — | runs when the runner closes; releases resources |

**PluginManager semantics** (`plugins/plugin_manager.py`):
- Plugins run in list order with an **early exit**: the first non-`None` return wins, and later plugins and the object-level callbacks are skipped (log line: *"Plugin '%s' returned a value for callback '%s', exiting early."*).
- Duplicate names raise `ValueError: Plugin with name '...' already registered.`
- An exception inside a plugin becomes `RuntimeError` with the original as `__cause__`.
- Error and notification hooks (`on_agent_error`, `on_run_error`) run on **every** plugin and log, rather than raise, their own exceptions.
- `close()` closes every plugin even if one fails, then raises `RuntimeError("Failed to close plugins: ...")`.

Three ways a hook can respond (docs): **Observe** (return None), **Intervene** (return a value, which short-circuits), **Amend** (mutate the context or request in place).

2.x graph note: v2.11.0 *"run plugin tool callbacks around ToolNode calls"*, so tool hooks now also fire for tools run as workflow nodes.

### 3.3 Built-in plugins (adk.dev list + `google/adk/plugins/` directory on main)
| Plugin | Import / ctor | What it does |
|---|---|---|
| **LoggingPlugin** | `from google.adk.plugins import LoggingPlugin`; `LoggingPlugin(name="logging_plugin", *, tool_result_classifier=None)` | Console trace of each hook. Logs `TOOL ERROR` on a raise **and** on a result that reports failure without raising (a ReflectAndRetry answer, an MCP `CallToolResult.isError`, or a classifier hit; v2.13.0) |
| **DebugLoggingPlugin** | `google.adk.plugins.DebugLoggingPlugin` | verbose debug dump |
| **ReflectAndRetryToolPlugin** | `ReflectAndRetryToolPlugin(max_retries=3, throw_exception_if_retry_exceeded=True, tracking_scope=TrackingScope.INVOCATION)`; `TrackingScope` from `google.adk.plugins.reflect_retry_tool_plugin` | On a tool error, gives the model structured reflection guidance and retries. `max_retries=3` means 4 attempts in total. Counts per tool, with locking for parallel calls. Override `extract_error_from_result(...)` to treat `{"status":"error"}` results as failures |
| **ReflectAndRetryModelPlugin** | `google.adk.plugins.ReflectAndRetryModelPlugin` | the same idea for model errors (params not verified [UNVERIFIED]) |
| **ContextFilterPlugin** | `google.adk.plugins.context_filter_plugin.ContextFilterPlugin(num_invocations_to_keep=None, custom_filter=None, name="context_filter_plugin", remove_amount=1)` | `before_model` trimming of history to the last N invocations, or a custom `list[Content]→list[Content]` function. `remove_amount<1` raises ValueError |
| **GlobalInstructionPlugin** | `google.adk.plugins.global_instruction_plugin.GlobalInstructionPlugin(global_instruction: str or InstructionProvider = "", name="global_instruction")` | *"replaces the deprecated global_instruction field on LlmAgent"*; injects app-wide identity/policy via `before_model` |
| **BigQueryAgentAnalyticsPlugin** | `google.adk.plugins.bigquery_agent_analytics_plugin` (`BigQueryAgentAnalyticsPlugin`, `BigQueryLoggerConfig`); `pip install "google-adk[bigquery-analytics]>=2.7.0"` | streams every lifecycle event to BigQuery (details below) |
| **SaveFilesAsArtifactsPlugin** | `save_files_as_artifacts_plugin.py` | saves uploaded files as artifacts |
| **MultimodalToolResultsPlugin** | `multimodal_tool_results_plugin.py` | lets tools return multimodal parts |
| **AutoTracing** | `auto_tracing_plugin.py` | automatic span wrapping |
| **Model Armor** | added v2.8.0 | prompt/response safety screening |
| **ToolCallIntegrityPlugin** | v2.11.0, optional; `ToolCallIntegrityError` | validates tool-call integrity. Docs note: tools run as workflow nodes are *not* checked |
| **ForceEscalationPlugin** | v2.13.0 (`tools/model_consult`) | forces escalation in model-consult flows (semantics [UNVERIFIED]) |

**BigQuery Agent Analytics** (adk.dev/integrations/bigquery-agent-analytics):
```python
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models.google_llm import Gemini
from google.adk.plugins.bigquery_agent_analytics_plugin import (
    BigQueryAgentAnalyticsPlugin, BigQueryLoggerConfig)

config = BigQueryLoggerConfig(max_content_length=500 * 1024, shutdown_timeout=10.0)
plugin = BigQueryAgentAnalyticsPlugin(project_id="your-gcp-project-id",
                                      dataset_id="your-big-query-dataset-id",
                                      config=config)
root_agent = Agent(model=Gemini(model="gemini-flash-latest"), name="my_agent",
                   instruction="You are a helpful assistant.")
app = App(name="my_agent", root_agent=root_agent, plugins=[plugin])
```
- Writes to table `agent_events` (default), **partitioned by `DATE(timestamp)`** and **clustered by `event_type, agent, user_id`**. It is created automatically.
- Columns: `timestamp, event_id, event_type, agent, session_id, invocation_id, user_id, trace_id, span_id, parent_span_id, content (JSON), content_parts, attributes, latency_ms (JSON: total_ms, time_to_first_token_ms), status, error_message, is_truncated`.
- Event types: `USER_MESSAGE_RECEIVED, INVOCATION_STARTING/COMPLETED/ERROR, AGENT_STARTING/COMPLETED/ERROR/RESPONSE/TRANSFER/STATE_CHECKPOINT, LLM_REQUEST/RESPONSE/ERROR, TOOL_STARTING/COMPLETED/ERROR/PAUSED, STATE_DELTA, EVENT_COMPACTION, NODE_OUTPUT, NODE_ERROR, HITL_* (+_COMPLETED), A2A_INTERACTION`.
- Config defaults: `batch_size=1`, `batch_flush_interval=1.0`, `queue_max_size=10000`, `max_content_length` 500 KB (`-1` means unlimited), `auto_schema_upgrade=True`, `create_views=True` (prefix `v`), `exactly_once_delivery=False`, `enable_otel_correlation=False`, optional `gcs_bucket_name` to offload multimodal content.
- IAM: `roles/bigquery.jobUser` (project) and `roles/bigquery.dataEditor` (table), plus storage objectCreator/objectViewer if GCS is used. It uses the **Storage Write API (paid)**.
- Recent releases: v2.12.0 added `on_schema_error`/`on_schema_ready` hooks. v2.13.0 classifies write-time 403/404 drops.

### 3.4 Callbacks vs plugins
| | Agent callbacks | Plugins |
|---|---|---|
| Scope | one agent object (`LlmAgent(before_model_callback=...)` or YAML `before_model_callbacks:`) | the whole App/Runner: every agent, model and tool |
| Form | a function (or a list of them) | a class with state, `name`, `close()` |
| Hooks | before/after agent, model, tool | the same, plus user_message, before/after_run, on_event, on_model_error, on_tool_error, on_agent_error, on_run_error |
| Order | after the plugins | **first**; a non-None return skips the object callbacks |
| Config | YAML-addressable | code (`App(plugins=[])`) or `--extra_plugins`; not in AgentConfig |
| Docs guidance | per-agent logic (state seeding, local guardrails) | *"When implementing security guardrails and policies, use ADK Plugins for better modularity and flexibility than Callbacks."* (adk.dev/callbacks) |

ADK 2.0 adds a reason to prefer hooks: overriding `_run_async_impl()` / `generate_content()` is **silently ignored** in 2.0. Use Before/AfterAgent callbacks (or plugins) instead (adk.dev/2.0).

---

## 4. Design patterns these features enable (2026 "loop / graph / verifier" engineering)

1. **Verifier per step (graph):** generator node → LLM judge with `output_schema` → `FunctionNode` that emits `Event(route=grade)` → a routing map that loops back on failure. This is the loop_config sample in §2.6. The verifier's output is typed (Pydantic), so routing is deterministic.
2. **Reflect-and-retry at the tool boundary:** `ReflectAndRetryToolPlugin` turns exceptions into model-readable feedback, a self-correction loop that needs no graph change. Combine it with `extract_error_from_result` for soft failures.
3. **Global policy as a plugin:** `GlobalInstructionPlugin` for persona, Model Armor for safety, `before_tool_callback` for an allow-list or arg validation. Each is written once and enforced on every node.
4. **Context engineering:** `ContextFilterPlugin(num_invocations_to_keep=N)` plus `App(events_compaction_config=..., context_cache_config=...)`.
5. **Eval / observability loop:** `BigQueryAgentAnalyticsPlugin` → SQL over `agent_events` (latency, tool error rates, HITL waits) → build eval sets → `adk eval` (note v2.10.0: `AgentEvaluator` raises ValueError when no eval cases run).
6. **Config-as-deployment:** YAML topology lets per-tenant graphs ship through CI without code. Pin the trust boundary, because YAML references can import code.

---

## 5. Failure modes and gotchas
- `agent.py` / `__init__.py` alongside `root_agent.yaml`: the **Python wins** and the YAML edits are silently ignored.
- `adk create` without `--type=config` produces a **code** agent (the default is `CODE`).
- Inline list `[a, b]` in `edges` is a **fan-out**, not a chain.
- Referencing a node name before an edge introduces it raises an error.
- Typos in `Workflow`/`FunctionNode` keys are only warnings, so a node can quietly lose a setting.
- The schema (`AgentConfig.json`) is marked deprecated and lacks `Workflow`, so the IDE flags valid 2.x graph YAML. Don't trust editor squiggles for graphs.
- Untrusted YAML can lead to RCE through `_code`/`args`. The stdlib, `yaml` and `ruamel` are denylisted, but the `args` denylist is off by default.
- Only Gemini models are supported in config (use `model_code` + LiteLlm at your own risk). `A2aAgent` and `LangGraphAgent` are unsupported.
- v2.9.0 workflow resume **re-runs failed nodes**, so make node side effects idempotent.
- Plugin bugs become `RuntimeError` and fail the whole run. Name collisions raise `ValueError`.
- An `after_agent` callback that returns content emits an **extra** event; return `None` unless you mean it.
- Broad `except Exception:` inside nodes or tools disables 2.0 automatic retries (`RetryConfig(max_attempts=3)`). Catching `BaseException` traps `NodeInterruptedError` and breaks HITL.
- v2.10.0: instruction templating leaves `${var}` and `\{var}` literal. Use `{var}` / `{var?}` (optional), as in the samples.
- v2.13.0: telemetry defaults to OTel GenAI semconv v2 (`call_llm` span removed), so dashboards keyed on `call_llm` break.
- The BigQuery plugin with `batch_size=1` causes one write per event. Raise it for throughput, and keep `flush_on_run_end=True`.

---

## 6. Codelabs and samples (exact titles)
- "Analyze ADK Agent execution with the BigQuery Agent Analytics Plugin": https://codelabs.developers.google.com/adk-bigquery-agent-analytics-plugin
- "Build Event-Driven AI Agents with Eventarc, Cloud Run and ADK" (Next '26; wraps the agent in an App with `LoggingPlugin`): https://codelabs.developers.google.com/next26/eventarc-ai-agents
- "Agentverse - The Summoner's Concord - Architecting Multi-Agent Systems" (has a callbacks-vs-plugins section): https://codelabs.developers.google.com/agentverse-architect/instructions
- "Create and deploy low code ADK (Agent Deployment Kit) agents using ADK Visual Builder": https://codelabs.developers.google.com/codelabs/create-low-code-agent-with-ADK-visual-builder (that the Visual Builder emits Agent Config YAML is [UNVERIFIED] here)
- "Build an Event-Driven Data Agent with BigQuery and ADK": https://codelabs.developers.google.com/bigquery-adk-event-driven-agents
- Repo samples: `contributing/samples/workflows/loop_config`, `contributing/samples/multi_agent/multi_agent_loop_config`, `plugin_reflect_tool_retry/basic`, `plugin_reflect_tool_retry/hallucinating_func_name` (github.com/google/adk-python).

Primary sources: https://adk.dev/agents/config/ · https://adk.dev/plugins/ · https://adk.dev/callbacks/ · https://adk.dev/2.0/ · https://adk.dev/integrations/reflect-and-retry/ · https://adk.dev/integrations/bigquery-agent-analytics/ · https://github.com/google/adk-python/releases (v2.8.0–v2.13.0) · commit 2a9461b · `src/google/adk/plugins/{base_plugin,plugin_manager,context_filter_plugin,global_instruction_plugin,logging_plugin}.py` · `src/google/adk/agents/config_agent_utils.py` · `src/google/adk/cli/cli_tools_click.py` · `docs/guides/agents/config/index.md` · https://docs.cloud.google.com/gemini-enterprise-agent-platform/release-notes

---

## 7. Interview questions (crisp answers)
1. **Plugin vs callback?** A callback attaches to one agent. A plugin is a named class registered on the App that hooks every agent, model and tool. Plugins run first and can short-circuit the callbacks.
2. **What does returning a non-None value from `before_model_callback` do?** It skips the LLM call and uses the returned `LlmResponse` (caching, guardrails). Later plugins and agent callbacks are skipped too.
3. **Where do you register plugins in ADK 2.x Python?** `App(name, root_agent, plugins=[...])` then `Runner/InMemoryRunner(app=app)`. `Runner(plugins=)` is deprecated, and passing both raises ValueError.
4. **How do you handle a flaky tool without changing the agent?** `ReflectAndRetryToolPlugin(max_retries=3)`: the error goes back to the model as reflection guidance, with up to 4 attempts. Override `extract_error_from_result` for soft errors.
5. **How do you attach a plugin to a YAML-only agent?** `adk web --extra_plugins=google.adk.plugins.LoggingPlugin agents/`. AgentConfig has no plugins key.
6. **What does `agent_class: Workflow` with `edges` give you?** An ADK 2.0 graph built from YAML (v2.9.0+). Chains, routing maps keyed by `Event(route=...)`, fan-out lists and `FunctionNode`s from dotted refs.
7. **Is Agent Config production-ready?** The docs still label it experimental, and `adk create --type` help says "config is not ready for use". It deploys to Cloud Run / Agent Runtime like code agents. Treat it as trusted input.
8. **Why is YAML a security risk and what does ADK do?** `_code`/`_callbacks`/`args` import Python. ADK uses `safe_load`, a stdlib + `yaml`/`ruamel` module denylist and rejects absolute paths. The `args` denylist is still off by default.
9. **Where does global persona go now?** `GlobalInstructionPlugin`; the `LlmAgent.global_instruction` field is deprecated.
10. **How do you measure agent quality in production?** `BigQueryAgentAnalyticsPlugin` → the `agent_events` table (partitioned by day, clustered by event_type/agent/user_id) → SQL for latency, tool errors and HITL waits → eval sets.
11. **Why can't you override `_run_async_impl` in 2.0?** Execution moved to the graph Workflow Runtime and the override is silently ignored. Use callbacks or plugins, or write a node.
12. **What does `on_tool_error_callback` returning a dict do?** It suppresses the exception, the dict becomes the tool result, and `after_tool` still runs.

---

## 8. Slide ideas (with explaining animation)
1. **"Three layers of an ADK 2.0 app"**: stack YAML topology / callbacks / plugins. *Animation:* layers slide in bottom-up. A request arrow then pierces all three, glowing at the plugin layer first.
2. **"Rename timeline"**: Agentspace → Gemini Enterprise (Oct 2025); Vertex AI → Gemini Enterprise Agent Platform and Agent Engine → Agent Runtime (22 Apr 2026); ADK 2.0 GA (19 May 2026); YAML graphs (v2.9.0, Sep 2026). *Animation:* old name labels flip like a split-flap board into the new names.
3. **"YAML to graph"**: left side shows the loop_config `root_agent.yaml`; right side shows the graph. *Animation:* each YAML edge line highlights and draws its arrow. The `unrelated:` line draws the loop-back in red.
4. **"Verifier per step"**: generate → evaluate (Pydantic `Feedback`) → route. *Animation:* a token travels the graph, the grade badge flips "unrelated" (red) and the token loops back, then "tech-related" (green) lets it exit.
5. **"Plugin lifecycle clock"**: all 14 hooks on a timeline from user message to after_run. *Animation:* a playhead sweeps and each hook lights as the run reaches it. Error hooks branch down in orange.
6. **"Early exit"**: three plugins in a row, then the agent callback, then the model. *Animation:* plugin 2 returns a cached LlmResponse, so everything to its right greys out and the response flies back.
7. **"Reflect and Retry"**: tool fails, then the model gets reflection guidance, then it retries. *Animation:* an attempt counter ticks 1→4 and a success checkmark lands on attempt 3.
8. **"Callbacks vs Plugins"** comparison table. *Animation:* a single agent spotlight (callback), then zooms out to the whole app spotlight (plugin).
9. **"From events to evals"**: the BigQuery plugin streams events into the `agent_events` partitioned table, SQL runs on it and an eval set comes out. *Animation:* event chips fall into date-partition buckets, a SQL query lens sweeps over them and outputs a chart.
10. **"YAML trust boundary"**: a YAML file with `_code:` refs passes a gate showing the denylist (stdlib, yaml, ruamel) and a "args denylist: OFF" warning light. *Animation:* `os.system` bounces off the gate while `my_pkg.tools.fn` passes through.
