# 01 — ADK 2.0 vs ADK 1.x: What's New, What Broke, How to Migrate

Research date: 2026-10-23. Primary sources: adk.dev (official docs; raw Markdown at `https://adk.dev/<page>/index.md`), `github.com/google/adk-python` CHANGELOG/README/CLI source, PyPI `google-adk` release history, GitHub Releases API for every ADK repo, Google Developers Blog.
Note: ADK docs moved to **adk.dev** (formerly google.github.io/adk-docs).

---

## 1. TL;DR (one slide)

- **ADK 2.0 = new Workflow Runtime.** Per the docs, 2.0 is the move "from a hierarchical agent executor to a graph-based execution engine". "Agents, Tools, and Functions are evaluated as individual *nodes* within a workflow graph." (https://adk.dev/2.0/)
- **Three new workflow styles:** graph-based workflows, dynamic (code-driven) workflows, and collaborative workflows (a coordinator agent plus subagents that run in `chat` / `task` / `single_turn` modes).
- **GA dates:** Python 2.0.0 on **May 19, 2026**, Go 2.0.0 on **June 30, 2026**, TypeScript 2.0.0 on **August 21, 2026**. Java and Kotlin are still on 1.x. (https://adk.dev/2.0/)
- **Current version (today):** `google-adk` **2.13.0**, released on PyPI **Oct 23, 2026** (CHANGELOG date 2026-10-22). The 1.x line is still maintained: the latest is **1.39.1** (Aug 27, 2026).
- **The 1.x features carry over.** `App`, plugins, resumability, tool confirmation (HITL), context caching and event compaction all shipped in 1.7–1.18. In 2.0 they become the base the graph engine is built on.
- **Upgrading is not drop-in.** The Event schema, the BaseAgent→BaseNode contract, event appending and exception handling all changed (see §5).

---

## 2. Version timeline (exact, verified)

### PyPI `google-adk` (source: https://pypi.org/project/google-adk/#history and the CHANGELOG)

| Version | Date | Significance |
|---|---|---|
| 0.0.1 | 2025-03-17 | First PyPI upload (the public launch came at Cloud NEXT '25, April 2025) |
| 1.0.0 | 2025-05-20 | 1.x GA (Google I/O 2025) |
| 1.7.0 | 2025-07-16 | **Plugins** introduced ("a class that packages these individual callback functions together") |
| 1.12.0 | 2025-08-21 | **Agent Config** (YAML-authored agents) |
| 1.14.0 | 2025-09-10 | **`App` class** ("Upgrade ADK runner to use App in addition to root_agent"), **tool confirmation flow** (HITL), `GkeCodeExecutor` |
| 1.15.0 | 2025-09-24 | **Context caching** (`App(..., context_cache_config=...)`), `static_instruction`, `ContextFilterPlugin`, `--otel_to_cloud` |
| 1.16.0 | 2025-10-08 | **Event compaction** ("LLM context compaction"), **pause/resume an invocation** (resumability), `ReflectRetryToolPlugin` |
| 1.18.0 | 2025-11-05 | **ADK Visual Agent Builder** in `adk web`, `run_debug()` helper |
| 1.25–1.27 | Feb–Mar 2026 | Token-threshold compaction, `SkillToolset` (Agent Skills) |
| 2.0.0a1 / a2 / a3 | 2026-03-18 / 03-27 / 04-09 | 2.0 alphas |
| 2.0.0b1 | 2026-04-21 | 2.0 beta |
| 1.34.0 | 2026-05-18 | Last 1.x release before 2.0 GA (Skill Registry, OAuth PKCE in McpToolset) |
| **2.0.0** | **2026-05-19** | **GA** |
| 2.1.0 | 2026-05-23 | Fixes, sandboxes from templates and snapshots |
| 2.2.0 | 2026-06-04 | `AutoTracingPlugin`, native OTel `gen_ai.client.*` metrics, "restore 1.x agent config wiring for backward compatibility" |
| 2.3.0 | 2026-06-17 | `GEPARootAgentOptimizer`, Gemma4, E2B sandbox environment |
| 2.4.0 | 2026-07-07 | **Workflow as Tool**, `ManagedAgent`, Daytona sandbox, OpenAI Responses API (labs) |
| 2.5.0 | 2026-07-16 | `to_mcp_server` (serve an ADK agent over MCP), HITL resumption for standalone nodes/`NodeTool`, "Validate that no old orchestrators are used inside Workflow graphs" |
| 2.6.0 | 2026-07-29 | BREAKING: file artifacts namespaced by app; `ReflectAndRetryModelPlugin` |
| 2.7.0 | 2026-08-13 | "A correctness release". Tools can return media, Jinja2 instruction templates. BREAKING: `pyarrow` moved to the `bigquery-analytics` extra (about 50 MB smaller `[gcp]` install) |
| 2.8.0 | 2026-08-25 | Model Armor guardrail plugin, `ADK_MAX_LLM_CALLS` |
| 2.9.0 | 2026-09-10 | Model failover, LiveKit runner, **graphs from declarative YAML**, MCP SDK 2.x. Behavior change: failed nodes re-run on resume |
| 2.10.0 | 2026-09-24 | Skill lifecycle (`ADK_ENABLE_SKILL_LIFECYCLE=1`), MongoDB toolset, eval efficiency metrics |
| 2.11.0 | 2026-10-01 | `abort_signal` on Runner/Workflow/nodes, tool nodes pause via `RequestInput`, `ModelConsultTool`, `sqlite://` memory |
| 2.12.0 | 2026-10-13 | 40% faster time-to-first-model-request in long sessions, `require_confirmation` for workflow nodes, Python 3.15 |
| **2.13.0** | **2026-10-22 (CHANGELOG) / 2026-10-23 (PyPI + GitHub release)** | `TypesafeClassifier` + `ClassifierNode`, 12 experimental features promoted to stable, `MongoDbSessionService`, "Up to 8x faster execution turns for string-model agents". BREAKING: telemetry now defaults to OTel GenAI v2 (the `call_llm` span is removed; opt out with `ADK_TELEMETRY_SCHEMA_VERSION_OPT_IN=otel_semconv_1_36`) |

1.x is still maintained in parallel: 1.37.0 (Jul 30), 1.38.0 (Aug 7), 1.39.0 (Aug 17) and **1.39.1 (Aug 27, 2026)** are on PyPI. Pin it with `pip install "google-adk~=1.0"`.

Requirements: the README says **Python 3.11+** for 2.x. The 1.x pin note says Python 3.10+.

### Other languages (GitHub Releases API, checked 2026-10-23)

| Repo | Latest | 2.0 status | Stars |
|---|---|---|---|
| google/adk-python | v2.13.0 (2026-10-23) | GA 2026-05-19 | ~21,982 |
| google/adk-go | v2.6.0 (2026-10-13); 1.x line at v1.9.0 (2026-10-15) | GA 2026-06-30; module `google.golang.org/adk/v2` | ~8,890 |
| google/adk-js (TypeScript, `@google/adk`) | adk-v2.3.0 (2026-10-13) | GA 2026-08-21 | ~1,448 |
| google/adk-java | v1.13.0 (2026-10-21) | **No 2.0.** Quickstart uses 1.12.0; Java 17+, Maven 3.9+ | ~1,755 |
| google/adk-kotlin | v1.4.0 (2026-10-14) | **No 2.0.** Announced at Google I/O 2026 for JVM and Android (developer.android.com/ai/adk) | ~294 |
| google/adk-web (Dev UI) | v1.0.7 (2026-10-01) | — | ~1,059 |
| google/adk-samples | — | — | ~10,523 |

Graph, dynamic and HITL pages are marked "Supported in ADK Python v2.0.0 / TypeScript v2.0.0 / Go v2.0.0". Collaborative teams are Python v2.0.0 and Go v2.0.0 only. Java and Kotlin are not listed for graph workflows.

---

## 3. Announcements and quotable lines

- **"Welcome to ADK 2.0"**, https://adk.dev/2.0/ — "ADK 2.0 introduces powerful tools for building sophisticated AI agents, and helps you structure agents to execute challenging tasks with more control, predictability, and reliability."
- **"Why we built ADK 2.0"**, Google Developers Blog, **July 1, 2026**, by Swapnil Agarwal (SWE, ADK), Alan Blount (TPM, Google Cloud AI) and Frank Guan (PMM). https://developers.googleblog.com/en/why-we-built-adk-20/
  - "For production-grade reliability, you need full deterministic control over your application flow."
  - "Developers shouldn't have to choose between flexibility and predictability."
  - "Workflows separate execution routing from language processing."
  - "LLMs are trained to express creativity and variety — it's a feature."
  - Benchmark (illustrative, `gemini-3.5-flash` with mock APIs, customer-refund example): **5,152 → 2,265 tokens per run (~50% lower)** and **7.2 s → 5.7 s latency (~20% lower)**, comparing a vanilla tool-calling agent with an ADK 2.0 workflow. The example's refund step calls the Stripe API. The post points to the risk of an agent that succeeds "95 out of 100 times" on a standard business process.
  - Argument: workflows reduce context bloat because tool outputs don't pile up in the model's context. They also reduce prompt-injection blast radius because the graph defines which actions are possible.
- **CHANGELOG 2.0.0** — "establishing production-grade foundations for multi-agent workflows and advanced dynamic agent collaboration … a model-agnostic engine for orchestrating non-linear, conditional, and cyclical agent execution patterns."
- **README key feature** — "Workflow Runtime: A graph-based execution engine … with support for routing, fan-out/fan-in, loops, retry, state management, dynamic nodes, human-in-the-loop, and nested workflows." "Task API: Structured agent-to-agent delegation with multi-turn task mode, single-turn controlled output …"
- README beginner note: "ADK applications are built using two main classes: `Agent` … and `Workflow`."

---

## 4. New primitives in 2.0 (with real code)

### 4.1 Graph workflow: `Workflow(edges=[...])`
Source: https://adk.dev/graphs/ (verbatim, trimmed)
```python
from google.adk import Agent, Workflow, Event
from pydantic import BaseModel

city_generator_agent = Agent(
    name="city_generator_agent", model="gemini-flash-latest",
    instruction="Return the name of a random city. Return only the name, nothing else.",
)

class CityTime(BaseModel):
    time_info: str
    city: str

def lookup_time_function(node_input: str):
    return CityTime(time_info="10:10 AM", city=node_input)

city_report_agent = Agent(
    name="city_report_agent", model="gemini-flash-latest", input_schema=CityTime,
    instruction="It is {CityTime.time_info} in {CityTime.city} right now.",
)

root_agent = Workflow(
    name="root_agent",
    edges=[("START", city_generator_agent, lookup_time_function, city_report_agent)],
)
```
How it works: `"START"` starts the run, and a tuple is a chain. Each node's return value becomes the next node's `node_input`, so you don't need session state for handoffs. A node can be an `Agent` (LLM), a plain Python function (deterministic) or another `Workflow` (nested).

### 4.2 Routing: `Event(route=...)` plus a dict edge
Source: https://adk.dev/graphs/
```python
def router(node_input: str):
    routes = [r.strip() for r in node_input.split(",")]
    return Event(route=routes)          # a list fans out to several branches

root_agent = Workflow(
   name="routing_workflow",
   edges=[
       ("START", process_message, router),
       (router, {"BUG": response_1_bug,
                 "CUSTOMER_SUPPORT": response_2_support,
                 "LOGISTICS": response_3_logistics}),
   ],
)
```
Added in 2.13.0: `TypesafeClassifier` / `ClassifierNode` for typed routing.

### 4.3 Dynamic workflows: `@node` plus `ctx.run_node()`
Source: https://adk.dev/graphs/dynamic/
```python
from google.adk import Context, Workflow
from google.adk.workflow import node

@node(name="hello_node")
def my_node(node_input):
    return "Hello World"

@node(rerun_on_resume=True)          # required for orchestrators that call run_node
async def my_workflow(ctx: Context, node_input: str) -> str:
    result = await ctx.run_node(my_node, node_input="hello")
    return result

root_agent = Workflow(name="root_agent", edges=[("START", my_workflow)])
```
Docs: "Automatic Checkpointing: … Successful sub-nodes are automatically skipped when resuming the workflow, making complex logic durable and resumable by default." There is also an explicit `FunctionNode(fn, name=..., rerun_on_resume=True)` wrapper. Go uses `workflow.NewFunctionNode`, `workflow.NewDynamicNode` and `workflow.RunNode`. TypeScript uses `node(fn, {rerunOnResume: true})` and `ctx.runNode()`, which returns a result whose value is in `.output`.

### 4.4 Human-in-the-loop node: `RequestInput`
Source: https://adk.dev/graphs/human-input/
```python
from google.adk.events import RequestInput
from google.adk import Workflow

def step1():                       # pauses the workflow
  yield RequestInput(message="Enter a number:")

def step2(node_input):             # receives the human reply
  return node_input * 2

root_agent = Workflow(name="root_agent", edges=[('START', step1, step2)])
```
Options are `message`, `payload` (structured context for the client UI) and `response_schema` (a Pydantic model). With `rerun_on_resume=False` (the leaf default), the reply goes to the successor. With `True`, the node body re-runs. Go uses `workflow.ResumeOrRequestInput` and returns `ErrNodeInterrupted` on the first pass. Related changes: tool nodes pause for approval via `RequestInput` (2.11), `require_confirmation` on workflow nodes (2.12), and 1.x `require_confirmation` on tools/MCP (1.14–1.17).

### 4.5 Collaborative agent teams: `mode=`
Source: https://adk.dev/workflows/collaboration/
```python
from google.adk import Agent
weather_agent = Agent(name="weather_checker", mode="single_turn",
                      tools=[get_weather, user_info, geocode_address])
flight_agent = Agent(name="flight_booker", mode="task",
                     input_schema=FlightInput, output_schema=FlightResult,
                     tools=[search_flights, book_flight])
root = Agent(name="travel_planner", sub_agents=[weather_agent, flight_agent])
# Auto-injects delegation tools named after each subagent
```
Modes: **chat** is the default (1.x behaviour, manual return to the parent). **task** allows clarifying questions and returns to the parent automatically. **single_turn** has no user interaction, returns automatically and can run in parallel. Caveat from the docs: "task behavior is disabled for use in graph-based workflows in ADK Python v2.0.0" [re-enable status after 2.0 UNVERIFIED].

### 4.6 Other 2.x primitives
- **Workflow as Tool** (2.4.0), `NodeTool`, `ManagedAgent` (2.4.0, backed by the Managed Agents API).
- **Declarative YAML graphs** (2.9.0) extend 1.12's Agent Config.
- **`RetryConfig(max_attempts=3)`**: automatic node retries when exceptions propagate.
- **`abort_signal`** (2.11.0): graceful cancellation. `/run_sse` cancels when the client disconnects.
- **Model failover** (2.9.0), `ReflectAndRetryModelPlugin` (2.6.0).
- Event fields added: `node_info` and `output` (Python). TypeScript adds `output`, `route`, `nodeInfo` and `isolationScope`. Go adds `IsolationScope`, `Routes`, `RequestedInput`, `Output` and `NodeInfo`.
- **Template agents** (`SequentialAgent`, `ParallelAgent`, `LoopAgent`) still work. In TypeScript 2.0 they log a deprecation warning once per class per process. Python 2.5.0 rejects them *inside* `Workflow` graphs ("Validate that no old orchestrators are used inside Workflow graphs").

---

## 5. Breaking changes and migration guide (Python 1.x → 2.0)

Source: https://adk.dev/2.0/ ("Breaking changes: ADK Python 1.x to 2.0 incompatibilities")

| # | Area | What changed | Migration action |
|---|---|---|---|
| 1 | **Event schema / custom session storage** | New `node_info` and `output` fields. "Inserting a 2.0 Event into a rigid 1.x database table causes insertion or ORM deserialization failures." Strict JSON validators (`additionalProperties: false`) reject 2.0 events. JSON-blob stores are fine. | Update DB schemas and validators. **Upgrade all readers before writing 2.0 sessions to a shared DB.** For DB sessions, `adk migrate session --source_db_url ... --dest_db_url ...` exists in the CLI source. |
| 2 | **BaseAgent → BaseNode** | `BaseAgent` now subclasses `BaseNode`. Overrides of `_run_async_impl()` or `generate_content()` "are silently ignored" by the graph engine. | Move custom logic into `BeforeAgentCallback` / `AfterAgentCallback`, or rewrite it as nodes. |
| 3 | **Direct event appending** | `context.session.events.append(custom_event)` "circumvents the graph engine and breaks determinism". | "Do not append events directly to the session, and do not use `enqueue_event` directly." **Yield** events from the node or agent. |
| 4 | **Error handling** | A broad `except Exception:` swallows errors, so automatic retries never fire. Catching `BaseException` traps `NodeInterruptedError` and breaks HITL pauses. | Let exceptions propagate and configure `RetryConfig(max_attempts=3)`. Never catch `BaseException` unless you re-raise. |
| 5 | Resume semantics (2.9.0) | "A node that failed now runs again when the workflow resumes." | Make node bodies **idempotent**. |
| 6 | `InMemorySessionService` (2.9.0) | Raises `SessionNotFoundError` for unknown sessions. | Create sessions explicitly. |
| 7 | Telemetry (2.13.0) | OTel GenAI v2 is the default and the `call_llm` span is removed. | Update dashboards, or opt out with the env var. |

TypeScript: `InvocationContext.agent` is now optional, so use `requireAgent(ctx)`. `description` defaults to `""`. Rename subclass fields that collide with inherited `rerunOnResume`, `waitForOutput`, `retryConfig`, `timeout`, `inputSchema`, `outputSchema` and `stateSchema`.
Go: module path changes to `google.golang.org/adk/v2`. `session.NewEvent(ctx, ctx.InvocationID())` now takes a `context.Context` first, and `NewEventWithContext` is removed.

Pins to stay on 1.x: `pip install "google-adk~=1.0"`, `npm install @google/adk@^1.6.0`, `go get google.golang.org/adk@v1`.

**Migration flow (diagram in words):** audit custom `BaseAgent` subclasses and session stores → upgrade readers and DB schemas → move overrides into callbacks/nodes → replace `events.append` with `yield` → remove broad `except` blocks and add `RetryConfig` → optionally replace Sequential/Parallel/Loop agents with `Workflow` edges → make nodes idempotent → test HITL pause/resume in `adk web`.

---

## 6. The 1.x foundations that 2.0 builds on (with code)

### `App` (1.14.0) — the top-level container
Source: https://adk.dev/apps/
```python
from google.adk.agents.llm_agent import Agent
from google.adk.apps import App

root_agent = Agent(model='gemini-flash-latest', name='greeter_agent',
                   instruction='Reply with Hello, World!')
app = App(
    name="agents",
    root_agent=root_agent,
    # Optional App-level features: plugins, context_cache_config,
    # events_compaction_config, resumability_config
)
# runner = InMemoryRunner(app=app); await runner.run_debug("Hello there!")  # run_debug: 1.18+
```

### Resumability (1.16.0)
Source: https://adk.dev/runtime/resume/
```python
app = App(name='my_resumable_agent', root_agent=root_agent,
          resumability_config=ResumabilityConfig(is_resumable=True))
async for event in runner.run_async(user_id='u_123', session_id='s_abc',
                                    invocation_id='invocation-123'):
  print(event)
```

### Event compaction (1.16.0; token-threshold mode added in 1.25/1.26)
Source: https://adk.dev/context/compaction/ (Python v1.16.0, Go v2.3.0, Java v0.2.0, TS v0.6.0, Kotlin v0.7.0)
```python
from google.adk.apps.app import App, EventsCompactionConfig
app = App(name="my_compacting_agent_app", root_agent=root_agent,
    events_compaction_config=EventsCompactionConfig(
        token_threshold=4000,      # compact when token count exceeds this
        event_retention_size=5,    # keep the last 5 raw events
        # or a sliding window: compaction_interval=3, overlap_size=1
    ))
```
Safety fixes: compaction no longer drops events with pending function calls (1.27.0) or HITL events (1.34.0). Summaries include thoughts and tool calls (2.2.0).

### Context caching (1.15.0)
Source: https://adk.dev/context/caching/
```python
from google.adk.agents.context_cache_config import ContextCacheConfig
app = App(name='my-caching-agent-app', root_agent=root_agent,
    context_cache_config=ContextCacheConfig(
        min_tokens=2048, ttl_seconds=600, cache_intervals=5))
```
This pairs with `LlmAgent(static_instruction=types.Content(...))`, which puts the stable prefix first so the cached prefix is longer (CHANGELOG 1.15.0).

### Plugins (1.7.0)
Source: https://adk.dev/plugins/ ("registered once … its callbacks apply globally to every agent, tool, and LLM call")
```python
from google.adk.plugins.base_plugin import BasePlugin

class CountInvocationPlugin(BasePlugin):
    def __init__(self) -> None:
        super().__init__(name="count_invocation")
        self.agent_count = 0
    async def before_agent_callback(self, *, agent, callback_context) -> None:
        self.agent_count += 1
    async def before_model_callback(self, *, callback_context, llm_request) -> None:
        print("[Plugin] LLM request")
# App(..., plugins=[CountInvocationPlugin()])
```
Prebuilt plugins: `ReflectAndRetryToolPlugin`, `BigQueryAgentAnalyticsPlugin`, `ContextFilterPlugin`, `SaveFilesAsArtifactsPlugin`, `DebugLoggingPlugin`, `AutoTracingPlugin` (2.2), Model Armor (2.8), plus third-party plugins for Temporal, DBOS, Restate, Dapr, Daytona, Datadog, Galileo, Cisco AI Defense and StackOne (adk.dev/integrations).

---

## 7. `adk` CLI and Dev UI

Commands verified in `src/google/adk/cli/cli_tools_click.py` (main):
`adk create`, `adk run`, `adk web`, `adk api_server`, `adk eval`, `adk eval_set {create, add_eval_case, generate_eval_cases}`, `adk test`, `adk optimize` (GEPA), `adk deploy {cloud_run, docker, agent_engine, gke}`, `adk migrate session`, `adk conformance {record, test}`, `adk telemetry {enable, disable, status}`.

```bash
pip install google-adk                         # 2.13.0, Python 3.11+
adk create my_agent                            # scaffold (--model, --api_key, --project, --region)
adk run my_agent                               # terminal chat
adk run --save_session --session_id s1 my_agent
adk run --resume my_agent/s1.session.json my_agent
adk run --session_service_uri "sqlite:///my_sessions.db" my_agent
adk web --port 8000                            # Dev UI, run from the PARENT dir of agents
adk api_server                                 # FastAPI server (/run, /run_sse)
adk eval <agent_dir> <file.evalset.json> --config_file_path eval_config.json
adk deploy cloud_run --with_ui <agent-folder>
adk deploy docker --with_ui <agent-folder>
adk deploy agent_engine ...                    # Vertex AI Agent Engine / "Agent Runtime"
adk deploy gke ...
```
Sources: README, https://adk.dev/runtime/command-line/, https://adk.dev/get-started/python/

**`adk web` defaults** (https://adk.dev/runtime/web-interface/): `--port 8000`, `--host 127.0.0.1`, and sessions persisted per agent in SQLite at `<agents_dir>/<agent>/.adk/session.db`. Artifacts go to `.adk/artifacts`. `--reload` is on by default, and `--no_use_local_storage` falls back to in-memory. TypeScript uses `npx adk web`. Go serves the UI at `/ui/` and the API at `/api` on port 8080. In Java the web UI and API server are bundled (Maven `exec` with `--adk.agents.source-dir`).
**Dev UI features:** chat, an event/trace inspector, state and artifacts panels, eval set creation and running, a **Visual Agent Builder** (1.18.0: a visual designer whose natural-language assistant "proposes and writes agent configuration yaml files for you"), and HITL request rendering. The UI lives in `google/adk-web` (v1.0.7). Demo video: "ADK Web Demo", https://youtu.be/TEjqk0eeNy8 (linked from the README).

**Agents CLI** (new, separate tool): `uvx google-agents-cli setup` (or `pip install google-agents-cli && agents-cli setup`, or skills only via `npx skills add google/agents-cli`). It installs ADK skills into coding agents such as Antigravity, Claude Code and Codex so they can build, evaluate and deploy ADK agents. Requires Python 3.11+, uv and Node.js. Docs: https://adk.dev/get-started/agents-cli/, https://google.github.io/agents-cli/

---

## 8. Real-world and ecosystem notes
- Google products and partners named in primary sources: Stripe (refund example in the blog), Google Cloud Workflows and Application Integration (named as earlier orchestration options), Vertex AI Agent Engine (`adk deploy agent_engine`), Gemini Enterprise env (`GOOGLE_GENAI_USE_ENTERPRISE=1`), Android (ADK Kotlin, I/O 2026), and MongoDB, LiveKit, E2B, Daytona, NVIDIA NIM integrations (CHANGELOG 2.3–2.13).
- Adoption: about 22k GitHub stars on adk-python and about 10.5k on adk-samples (GitHub API, 2026-10-23).
- Third-party commentary [secondary, not primary]: AlphaSignal "Google's ADK Hits 20K Stars as 2.0 Ships Multi-Agent Workflows"; byteiota "Google ADK 2.0 Graph Workflows Ship: LangGraph Has a Fight".

## 9. Sample repos (official)
- Python workflows: https://github.com/google/adk-python/tree/main/contributing/samples/workflows
- Python collaboration: https://github.com/google/adk-python/tree/main/contributing/samples/multi_agent
- TypeScript: https://github.com/google/adk-js/tree/main/samples/workflows
- Go: https://github.com/google/adk-go/tree/main/examples/workflow and …/examples/multiagent/collaboration
- Samples hub: https://github.com/google/adk-samples

## 10. Uncertain items
- [UNVERIFIED] Whether collaborative `task` mode inside graphs was re-enabled after 2.0.0.
- [UNVERIFIED] The full content of the 2.0.0a1–b1 changelogs. They are not in main's CHANGELOG.md, which jumps from 1.34.0 to 2.0.0.
- [UNVERIFIED] Plans for Java and Kotlin 2.0 (no 2.0 tags as of 2026-10-23).
- Model ids in code (`gemini-flash-latest`, `gemini-3.5-flash`) are copied from the docs and README as written.

---

## Slide ideas (8)

1. **"From Tree to Graph"**: a 1.x agent hierarchy (root → sub_agents, LLM-driven transfer) morphs into a 2.0 graph (START → agent node → function node → router → branches). Animate the tree edges re-wiring into directed graph edges.
2. **"The 2.0 Timeline"**: horizontal timeline from 0.0.1 (Mar 2025) through 1.0 (May 2025), 1.7 Plugins, 1.14 App/HITL, 1.15 Caching, 1.16 Resume/Compaction, 2.0 alphas (Mar 2026), Python GA (May 19), Go GA (Jun 30), TS GA (Aug 21), to 2.13 (Oct 23). Milestones pop in one at a time.
3. **"Three Ways to Orchestrate"**: three columns (Graph `edges=[...]`, Dynamic `@node` + `ctx.run_node`, Collaborative `mode=chat/task/single_turn`), each with a 6-line snippet and a "use when" line.
4. **"Why Deterministic Routing? The Numbers"**: bar chart of 5,152 vs 2,265 tokens and 7.2 s vs 5.7 s (Google blog, illustrative), with the quote "Workflows separate execution routing from language processing."
5. **"Pause, Ask a Human, Resume"**: sequence diagram of node yields `RequestInput` → workflow interrupted → checkpoint persisted → UI shows form from `response_schema` → reply → successor node (or rerun when `rerun_on_resume=True`). Animate a pause icon on the node.
6. **"The App Is the Production Envelope"**: concentric box with `App` outside and `root_agent`/`Workflow` inside, with plug-in slots for `plugins`, `context_cache_config`, `events_compaction_config`, `resumability_config`. Each slot lights up with its intro version.
7. **"Four Breaking Changes You Must Know"**: a 2×2 card grid (Event schema, BaseAgent→BaseNode, no `events.append`, don't catch `BaseException`), each flipping to its migration fix. End with a "upgrade readers first" warning banner.
8. **"Language Matrix"**: table of Python / Go / TS / Java / Kotlin × versions × 2.0 GA date × graph support, with green check vs grey 1.x badges.
9. **"The adk CLI Loop"**: circular flow `create → run → web → eval → deploy (cloud_run | agent_engine | gke | docker)` with a terminal-typing animation of each command, and the Dev UI screenshot fading in at `web`.
10. **"Compaction and Caching: Paying Less for Long Sessions"**: a context window filling with events, then a sliding-window summary collapsing old events (`compaction_interval`, `overlap_size`, `token_threshold`), and a cached static prefix shaded separately (`ContextCacheConfig`, `static_instruction`).
