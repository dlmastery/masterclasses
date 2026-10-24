# 04 — ADK Core Concepts: the exact current APIs (ADK Python 2.x, Oct 2026)

Research date: 2026-10-23. Target version: **google-adk 2.13.0** (GitHub release Oct 23 2026, changelog dated 2026-10-22). ADK 2.0.0 went GA on **2026-05-19** (CHANGELOG). Go 2.0 GA 2026-06-30, TypeScript 2.0 GA 2026-08-21 (https://adk.dev/2.0/).
Signatures marked "(source)" were read directly from `src/google/adk/*.py` on `main`. Anything not checked against a primary source is marked [UNVERIFIED].

---

## 0. Mental model in one paragraph

An **Agent** (= `LlmAgent`) is a config object: model, instruction, tools, and optional sub-agents. A **Runner** executes it. For each user message the Runner opens an **invocation**, runs the agent, and receives a stream of **Events**. It commits each event's `actions` (state_delta, artifact_delta) through the **SessionService**, **ArtifactService** and **MemoryService**, then forwards the event to the caller. Code receives a **Context** object at each hook point: `InvocationContext` in agent internals, `Context` (formerly `CallbackContext`) in callbacks, `ToolContext` in tools. **Callbacks** are per-agent hooks. **Plugins** are global hooks registered once on an **App**. In ADK 2.0 all of this runs on a graph-based **Workflow Runtime**, and `BaseAgent` is now a subclass of `BaseNode`.

Diagram in words: `User msg → Runner.run_async() → [append user event to Session] → Agent node runs → LLM call ⇄ tool calls → yield Event → Runner commits state/artifact deltas → Event forwarded to UI → agent resumes → … → final response event`.

---

## 1. Versions & breaking changes you must teach

| Fact | Value | Source |
|---|---|---|
| Latest release | v2.13.0 (Oct 23 2026) | https://github.com/google/adk-python/releases |
| 2.0 GA | 2026-05-19 | CHANGELOG.md `## [2.0.0] … (2026-05-19)` |
| Last 1.x before 2.0 | 1.34.0 (2026-05-18); 1.x line still patched (v1.39.1, Aug 27 2026) | releases page |
| Install | `pip install google-adk` (stay on 1.x: `pip install "google-adk~=1.0"`) | README; https://adk.dev/2.0/ |
| Python | README says **3.11+**, but the quickstart page still says 3.10+. These conflict, so teach 3.11+ | README vs https://adk.dev/get-started/python/ |
| Default model | `LlmAgent` falls back to `gemini-3.5-flash` when no model is set on the agent or any ancestor | `llm_agent.py` (source) |
| Docs home | https://adk.dev/ (LLM-friendly: https://adk.dev/llms.txt, /llms-full.txt) | README |

ADK 2.0 migration rules (https://adk.dev/2.0/):
- Events gain `node_info` and `output` fields. Session stores with rigid columns need a schema update. Compatibility is one-directional: ADK 1.28+ can read 2.0 sessions, but older 1.x versions cannot.
- "`BaseAgent` now subclasses `BaseNode`". Source confirms `class BaseAgent(BaseNode, abc.ABC)`. Overrides of `_run_async_impl()` are bypassed, so use before/after agent callbacks instead.
- Don't append events to the session yourself. Yield them from the node.
- Let exceptions propagate so `RetryConfig` applies. A broad `except BaseException` breaks HITL pausing.
- `SequentialAgent` / `ParallelAgent` / `LoopAgent` still work. The TypeScript SDK logs a deprecation warning for them. The Python docs call them "Template workflows". Graph `Workflow` is the recommended replacement.

Recent behaviour changes worth one bullet each (release notes):
- v2.9.0: `InMemorySessionService` raises `SessionNotFoundError` when you append to an unknown session. Failed workflow nodes rerun on resume.
- v2.10.0: `${var}` in instruction templates is no longer filled from state. `{var}` still is.
- v2.11.0: `abort_signal` added to `Runner`, `Workflow` and nodes. New `SqliteMemoryService` (`sqlite://` URI). New `ToolCallIntegrityPlugin`.
- v2.13.0: 12 experimental features promoted to stable. New `MongoDbSessionService` and `MongoDbMemoryService`. New `ClassifierNode`. Live barge-in for `CascadeLiveConnection`. Telemetry now defaults to the OTel GenAI v2 schema (`otel_semconv_1_44`), which removes the `call_llm` span.

---

## 2. `LlmAgent` / `Agent` — every parameter

`Agent` is a type alias: `Agent: TypeAlias = LlmAgent` (source: `src/google/adk/agents/llm_agent.py`).
Imports: `from google.adk import Agent`, `from google.adk.agents import LlmAgent`, `from google.adk.agents.llm_agent import Agent`.

**Inherited from `BaseAgent`** (source `base_agent.py`):
| Field | Type / default | Notes |
|---|---|---|
| `name` | `str`, required | Must be a Python identifier and cannot be `"user"`. The docstring says it must be unique in the tree, but duplicates only log a warning |
| `description` | `str = ''` | Other agents read this when deciding where to route, so it matters in multi-agent systems |
| `sub_agents` | `list[BaseAgent]` | Builds the hierarchy. `parent_agent` is set automatically (`init=False`) |
| `before_agent_callback` / `after_agent_callback` | callback or list | |

**Declared on `LlmAgent`** (source):
| Field | Type / default | What it does |
|---|---|---|
| `model` | `str \| BaseLlm = ''` | Empty means inherit from the nearest ancestor, then `set_default_model` (default `gemini-3.5-flash`) |
| `instruction` | `str \| InstructionProvider = ''` | Dynamic system prompt. Supports `{key}`, `{key?}` and `{artifact.name}` templating |
| `static_instruction` | `types.ContentUnion \| None` | Never-changing prefix, placed first to improve context/prefix caching (added in v1.15.0) |
| `global_instruction` | **DEPRECATED** | Use `GlobalInstructionPlugin` instead |
| `tools` | `list[ToolUnion]` | Python functions, `BaseTool`s, toolsets (MCP and others), `AgentTool` |
| `generate_content_config` | `types.GenerateContentConfig \| None` | temperature, max_output_tokens, safety, thinking_config… |
| `input_schema` | `type[BaseModel] \| None` | Expected input when the agent is used as a tool or task |
| `output_schema` | `SchemaType \| None` | Forces JSON output. With tools, only some models (e.g. Gemini 3) handle this natively. Otherwise ADK falls back to a `set_model_response` tool (https://adk.dev/agents/llm-agents/) |
| `output_key` | `str \| None` | Saves the final text response to `session.state[output_key]` |
| `include_contents` | `'default' \| 'none'` | `'none'` gives a stateless agent that sees no prior history |
| `planner` | `BasePlanner \| None` | `BuiltInPlanner(thinking_config=...)` or `PlanReActPlanner()` |
| `code_executor` | `BaseCodeExecutor \| None` | e.g. `BuiltInCodeExecutor()` |
| `mode` | `'chat' \| 'task' \| 'single_turn' \| None` | **New in 2.0**: the delegation mode (see §9). Defaults to chat when used as a sub-agent and single_turn when used as a workflow node |
| `disallow_transfer_to_parent` / `disallow_transfer_to_peers` | `bool = False` | Restricts LLM-driven transfer |
| `before_model_callback`, `after_model_callback`, `on_model_error_callback`, `before_tool_callback`, `after_tool_callback`, `on_tool_error_callback` | callback or list | See §7 |
| `parallel_worker` | `bool \| None` | Present in source. Semantics [UNVERIFIED] |

Planner and executor imports: `from google.adk.planners import BuiltInPlanner, PlanReActPlanner`; `from google.adk.code_executors import BuiltInCodeExecutor`. The docs say `PlanReActPlanner` is "particularly useful for models that don't have a built-in 'thinking' feature". It follows the ReAct paper: *ReAct: Synergizing Reasoning and Acting in Language Models*, Yao et al., arXiv:2210.03629 (2022; ICLR 2023).

**Snippet — a full-featured agent** (adapted from https://adk.dev/get-started/python/ and https://adk.dev/agents/llm-agents/):
```python
from google.adk import Agent
from google.adk.planners import BuiltInPlanner
from google.genai import types

def get_current_time(city: str) -> dict:
    """Returns the current time in a specified city."""
    return {"status": "success", "city": city, "time": "10:30 AM"}

root_agent = Agent(
    name="root_agent",
    model="gemini-flash-latest",
    description="Tells the current time in a specified city.",
    instruction="You help {user:name?} with time questions. Use get_current_time.",
    tools=[get_current_time],
    output_key="last_answer",
    generate_content_config=types.GenerateContentConfig(temperature=0.2),
    planner=BuiltInPlanner(
        thinking_config=types.ThinkingConfig(include_thoughts=True, thinking_budget=1024)
    ),
)
```
Teaching points:
- The function's docstring, type hints and defaults become the tool schema.
- A parameter with no default is required.
- Return a `dict` with a `"status"` key. Any other return type is wrapped under `"result"` (https://adk.dev/tools-custom/function-tools/).

Scaffold it with `adk create my_agent`, which creates `agent.py`, `__init__.py` and `.env`. Run with `adk run my_agent` or `adk web --port 8000`. Quote: ADK Web is "for development and debugging only, not production" (quickstart).

---

## 3. Runner, InMemoryRunner, App

**`Runner.__init__`** (source `src/google/adk/runners.py`, keyword-only):
```python
Runner(*, app=None, app_name=None, agent=None, node=None, plugins=None,
       artifact_service=None, session_service, memory_service=None,
       credential_service=None, plugin_close_timeout=5.0, auto_create_session=False)
```
- `session_service` is the only required argument.
- `node=` (2.0) lets you run any graph node or `Workflow` directly.
- Passing `plugins=` to `Runner` is **deprecated** in Python and raises a `DeprecationWarning`. Put plugins on `App` (https://adk.dev/plugins/).

**`run_async`** (source):
```python
async def run_async(self, *, user_id: str, session_id: str, invocation_id=None,
    new_message: types.Content | None = None, state_delta: dict | None = None,
    run_config: RunConfig | None = None, yield_user_message: bool = False,
    abort_signal: asyncio.Event | None = None) -> AsyncGenerator[Event, None]
```
Also available: `run(...)`, a synchronous generator with the same core arguments that is meant for local testing, and `run_live(*, user_id, session_id, live_request_queue, run_config, session)`.

**`InMemoryRunner(agent=None, *, node=None, app_name=None, plugins=None, app=None, plugin_close_timeout=5.0)`** (source). It bundles in-memory session, artifact and memory services. Its default `app_name` is `'InMemoryRunner'`.

**`App`** (`from google.adk.apps import App`, added in Python v1.14.0; https://adk.dev/apps/). Its fields are `name`, `root_agent`, `plugins`, `context_cache_config`, `events_compaction_config` and `resumability_config`. The docs describe it as "a top-level container for an entire Agent Development Kit (ADK) agent workflow". It also provides startup and shutdown hooks, scopes `app:` state, and is the deployable unit. Convention: assign it to a module variable named `app`.

**Snippet — the canonical programmatic loop** (signatures from source; pattern from https://adk.dev/events/ and https://adk.dev/apps/):
```python
import asyncio
from google.adk.apps import App
from google.adk.runners import InMemoryRunner
from google.genai import types

app = App(name="time_app", root_agent=root_agent)
runner = InMemoryRunner(app=app)

async def main():
    session = await runner.session_service.create_session(
        app_name="time_app", user_id="u1", state={"user:name": "Ada"})
    msg = types.Content(role="user", parts=[types.Part(text="Time in Paris?")])
    async for event in runner.run_async(user_id="u1", session_id=session.id, new_message=msg):
        for call in event.get_function_calls():
            print("TOOL CALL", call.name, call.args)
        if event.is_final_response() and event.content:
            print(event.author, ":", event.content.parts[0].text)

asyncio.run(main())
```
Note: `runner.session_service` is an attribute on Runner [UNVERIFIED in this pass; widely used in official samples].

**Event loop — 7 steps** (https://adk.dev/runtime/event-loop/):
1. Initiation
2. Kick-off
3. Yield
4. Process (the Runner commits the deltas)
5. Forward
6. Resume
7. Repeat

Quotable: a state change is "only **guaranteed to be persisted**" after the event carrying its `state_delta` has been yielded and processed. Code after a `yield` can "reliably assume" that those changes are committed. Local code can see uncommitted "dirty reads".

---

## 4. Sessions & SessionService types

A `Session` has `id`, `app_name`, `user_id`, `state`, `events` and `last_update_time` (https://adk.dev/sessions/session/). Service methods: `create_session`, `get_session`, `list_sessions`, `delete_session`, `append_event(session, event)`.

| Service | Import / construct | Use |
|---|---|---|
| `InMemorySessionService` | `from google.adk.sessions import InMemorySessionService` | Dev and tests. "All conversation data is lost if the application restarts." Not safe for multi-threaded use |
| `DatabaseSessionService` | `DatabaseSessionService(db_url="sqlite+aiosqlite:///./my_agent_data.db")`, needs `pip install google-adk[db]` | Postgres/MySQL/SQLite through an async SQLAlchemy driver. Uses a per-session lock |
| `VertexAiSessionService` | `VertexAiSessionService(project=PROJECT_ID, location=LOCATION)`, needs `google-adk[gcp]` | Managed **Agent Platform Sessions** on an Agent Runtime resource |
| `MongoDbSessionService` | new in v2.13.0. Import path [UNVERIFIED] | Shares sessions across runner replicas |

Branding note: on **2026-04-22** Google renamed Vertex AI to **Gemini Enterprise Agent Platform**. "Vertex AI Agent Engine" became **Agent Runtime**, and Memory Bank became **Agent Platform Memory Bank** (https://docs.cloud.google.com/gemini-enterprise-agent-platform/release-notes). The ADK class names still say `VertexAi…`.

---

## 5. State and its prefixes

Source for this section: https://adk.dev/sessions/state/.

| Prefix | Scope | Persistence |
|---|---|---|
| none | This session | Persists only with a Database or Vertex service |
| `user:` | All sessions of this `user_id` in this `app_name` | Persistent with Database or Vertex |
| `app:` | All users and sessions of the app | Persistent with Database or Vertex |
| `temp:` | This invocation only, including the sub-agents it calls | Never persisted. Discarded when the invocation ends |

Three legal ways to write state. Each one becomes an event's `state_delta`, which `append_event` applies:
1. `output_key="last_greeting"` on an agent.
2. `EventActions(state_delta={...})` on a manually appended `Event`.
3. `context.state["k"] = v` inside callbacks and tools.

**Anti-pattern:** never mutate `session.state` on a session you fetched from the service outside an invocation. The docs say such changes "will likely NOT be saved". They also skip the audit trail, are not thread-safe and don't update timestamps.

Templating rules:
- `{key}` raises an error if the key is missing. `{key?}` is optional.
- For literal braces (e.g. a JSON example in the prompt), pass an `InstructionProvider` function instead of a string. Inside it you can call `inject_session_state` selectively.

**Snippet — tool writing scoped state** (adapted from https://adk.dev/context/):
```python
from google.adk.tools import ToolContext

def add_to_cart(item: str, tool_context: ToolContext) -> dict:
    """Adds an item to the user's cart."""
    cart = tool_context.state.get("user:cart", [])
    cart.append(item)
    tool_context.state["user:cart"] = cart            # persists across sessions
    tool_context.state["temp:last_op"] = "add"        # gone after this invocation
    return {"status": "success", "cart_size": len(cart)}
```
ADK finds the `ToolContext` parameter by its type annotation and hides it from the LLM.

---

## 6. Memory, Memory Bank and Artifacts

**MemoryService** (https://adk.dev/sessions/memory/) is long-term, cross-session recall.

`BaseMemoryService` methods:
- `add_session_to_memory(session)`
- `add_events_to_memory` (optional; not every service implements it)
- `add_memory` (optional)
- `search_memory(...)`, which returns a `SearchMemoryResponse` of `MemoryEntry` objects
- `delete_memory` (added in v2.13.0)

| Implementation | Constructor |
|---|---|
| `InMemoryMemoryService` | `InMemoryMemoryService()`. Keyword matching only, for prototyping |
| `VertexAiMemoryBankService` | `VertexAiMemoryBankService(project=..., location=..., agent_engine_id=...)`. LLM-extracted memories plus semantic search |
| `VertexAiRagMemoryService` | `VertexAiRagMemoryService(rag_corpus="projects/.../ragCorpora/ID", similarity_top_k=5, vector_distance_threshold=0.6)` |
| `SqliteMemoryService` | v2.11.0, selected with a `sqlite://` URI |
| `MongoDbMemoryService` | v2.13.0, keyword recall with no embedding model needed |

- Memory tools: `from google.adk.tools import load_memory` lets the agent decide when to search. `preload_memory` retrieves memory "at the beginning of each turn".
- CLI: `adk web agents_dir --memory_service_uri="agentengine://<agent_engine_id>"`.
- The Runner does **not** write to memory automatically. Call `add_session_to_memory` yourself, typically from an `after_agent_callback`. `Context` and `ToolContext` have exposed `add_session_to_memory` since v1.21.0.

How Memory Bank works:
- Writing: session events go to Memory Bank, where `GenerateMemories` extracts the facts worth keeping.
- Reading: `RetrieveMemories` searches scoped to the current user and app.
- Direct `add_memory` calls `memories.create`. With `custom_metadata={"enable_consolidation": True}` it calls `memories.generate` instead, which merges new items with related existing memories.
- Platform news (release notes):
  - Gemini 3.5 Flash became the default Memory Bank generation model on 2026-06-29.
  - Memory profiles reached GA on 2026-07-15.
  - Memory Bank and Sessions got global and multi-regional endpoints on 2026-06-17.
- Risk to teach: **memory poisoning / prompt injection** persisting across sessions (Memory Bank overview, https://docs.cloud.google.com/agent-builder/agent-engine/memory-bank/overview).

**Artifacts** (https://adk.dev/artifacts/) are named, versioned binary blobs stored as `types.Part` with `inline_data` (a `Blob(data, mime_type)`).
- Services:
  - `InMemoryArtifactService`
  - `GcsArtifactService` (`google.adk.artifacts.gcs_artifact_service`)
  - Pass the service to the Runner as `artifact_service=`.
- API:
  - `await ctx.save_artifact(filename=..., artifact=part)` returns an int version, starting at 0.
  - `await ctx.load_artifact(filename=..., version=None)` loads the latest version unless you give one.
  - `await tool_context.list_artifacts()`.
- A filename prefixed `user:` (e.g. `user:settings.json`) is user-scoped. A plain filename is session-scoped.
```python
from google.genai import types
async def save_report(pdf_bytes: bytes, tool_context: ToolContext) -> dict:
    part = types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf")
    version = await tool_context.save_artifact(filename="report.pdf", artifact=part)
    return {"status": "success", "version": version}
```

---

## 7. Events, Contexts, Callbacks

**Event** (https://adk.dev/events/):
- Fields: `author` (`'user'` or an agent name), `invocation_id`, `id`, `timestamp`, `content`, `partial`, `turn_complete`, `actions`, `branch`.
- 2.0 adds `node_info` and `output`.

**EventActions** fields:
- `state_delta`, `artifact_delta`
- `transfer_to_agent`
- `escalate`, which ends a loop
- `skip_summarization`

**Helpers**:
- `is_final_response()`
- `get_function_calls()`, each with `.name` and `.args`
- `get_function_responses()`

**Contexts** (https://adk.dev/context/):
- `InvocationContext` (`google.adk.agents.invocation_context`) is the full picture: `session`, `agent`, `invocation_id`, `user_content`, the services, and `end_invocation`.
- `ReadonlyContext` is a read-only view, with state exposed as a `MappingProxyType`. Instruction providers receive it.
- **`Context`** (`from google.adk.agents.context import Context`) is the 2.0 unified type. Quote: "`CallbackContext` and `ToolContext` have been replaced by the `Context` type"; "you should use the `Context` class for all new development". `CallbackContext` remains as an alias.
- `ToolContext` adds `function_call_id`, `actions`, `request_credential()`, `get_auth_response()`, `list_artifacts()` and `search_memory()`.

**Callbacks** (https://adk.dev/callbacks/types-of-callbacks/). Python passes arguments by keyword, so parameter names must match exactly:

| Callback | Arguments | Return non-None to… |
|---|---|---|
| `before_agent_callback` | `callback_context` | Skip the agent (`types.Content`) |
| `after_agent_callback` | `callback_context` | Append content after the agent's events |
| `before_model_callback` | `callback_context, llm_request` | Skip the LLM (`LlmResponse`), e.g. for a cache or guardrail |
| `after_model_callback` | `callback_context, llm_response` | Replace the response |
| `on_model_error_callback` | `callback_context, llm_request, error` | Suppress the error |
| `before_tool_callback` | `tool, args, tool_context` | Skip the tool (`dict`) |
| `after_tool_callback` | `tool, args, tool_context, tool_response` | Replace the tool result |
| `on_tool_error_callback` | `tool, args, tool_context, error` | Suppress the error |

Each field also accepts a list of callbacks, which run in order and stop at the first truthy result.

```python
from typing import Optional
from google.adk.agents.context import Context
from google.adk.models import LlmRequest, LlmResponse
from google.genai import types

def block_secrets(callback_context: Context, llm_request: LlmRequest) -> Optional[LlmResponse]:
    last = llm_request.contents[-1].parts[0].text or ""
    if "password" in last.lower():
        return LlmResponse(content=types.Content(role="model",
               parts=[types.Part(text="I can't help with credentials.")]))
    return None   # proceed to the model

agent = Agent(name="safe", model="gemini-flash-latest", before_model_callback=block_secrets)
```
(The pattern is from the callbacks docs. The `google.adk.models` import of `LlmRequest`/`LlmResponse` follows official samples [UNVERIFIED path in this pass].)

---

## 8. Plugins (global, cross-cutting)

Source for this section: https://adk.dev/plugins/. Subclass `from google.adk.plugins.base_plugin import BasePlugin` and pass a unique `name`.

Hooks, in lifecycle order:
- `on_user_message_callback`
- `before_run_callback`
- agent: `before_agent_callback`, `after_agent_callback`, `on_agent_error_callback`
- model: `before_model_callback`, `after_model_callback`, `on_model_error_callback`
- tool: `before_tool_callback`, `after_tool_callback`, `on_tool_error_callback`
- `on_event_callback`
- `after_run_callback`, `on_run_error_callback`
- `close()`

Rules:
- Register on `App(plugins=[...])`. You can also inject one from the CLI with `adk web --extra_plugins=<import.path>`.
- Quote: "Plugin callback functions have precedence over callbacks implemented at the object level." When a plugin returns a value, the matching agent-level callback is skipped.

Prebuilt plugins:
- Reflect & Retry Tools
- Reflect & Retry Model
- BigQuery Agent Analytics
- Model Armor (v2.8.0)
- Context Filter
- Global Instruction
- Save Files as Artifacts
- Auto Tracing
- Multimodal Tool Results
- Logging / Debug Logging
- Tool Call Integrity (v2.11.0)
- `ForceEscalationPlugin` (v2.13.0)
```python
from google.adk.plugins.base_plugin import BasePlugin

class CountPlugin(BasePlugin):
    def __init__(self):
        super().__init__(name="count")
        self.llm_calls = 0
    async def before_model_callback(self, *, callback_context, llm_request):
        self.llm_calls += 1
        return None

app = App(name="agents", root_agent=root_agent, plugins=[CountPlugin()])
```
(The keyword-only signature follows the plugin docs pattern [UNVERIFIED exact signature].)

---

## 9. Delegation: sub_agents, transfer_to_agent, modes, AgentTool

There are three mechanisms:

1. **LLM-driven transfer (classic).**
   - A parent with `sub_agents=[...]` lets the LLM emit a `transfer_to_agent(agent_name=...)` function call.
   - ADK sets `EventActions.transfer_to_agent` and hands control to that agent.
   - You can restrict it with `disallow_transfer_to_parent` / `disallow_transfer_to_peers`.
   - The target is chosen from each sub-agent's `description`.

2. **2.0 delegation modes** (https://adk.dev/workflows/collaboration/). The coordinator "Auto-injects delegation tools named after each subagent".
   - `chat` (default): full conversation with the user. The sub-agent must call `transfer_to_agent` to return control.
   - `task`: can ask the user clarifying questions, and returns automatically when it calls `finish_task`. A task agent must be a **leaf**.
   - `single_turn`: no user interaction. Returns a result and can run in parallel.
   - Task and single-turn agents run in their own session **branch**, which isolates their context.
   - Warning from the docs: "Do not configure a root agent with the mode setting."
```python
from google.adk import Agent
weather_agent = Agent(name="weather_checker", mode="single_turn",
                      tools=[get_weather, geocode_address])
flight_agent  = Agent(name="flight_booker", mode="task",
                      input_schema=FlightInput, output_schema=FlightResult,
                      tools=[search_flights, book_flight])
root = Agent(name="travel_planner", sub_agents=[weather_agent, flight_agent])
```
(Verbatim structure from https://adk.dev/workflows/collaboration/. `FlightInput`/`FlightResult` are Pydantic models.)

3. **AgentTool**.
   - Import: `from google.adk.tools.agent_tool import AgentTool`, also re-exported from `google.adk.tools`.
   - Params: `agent`, `skip_summarization`, `propagate_grounding_metadata=False`, `include_plugins=True`.
   - Key contrast: with AgentTool the caller *keeps* control. Quote: "Agent A retains control and continues to handle future user input". A sub-agent transfer *hands over* the conversation instead.
   - Usage: `tools=[AgentTool(agent=summary_agent, skip_summarization=True)]` (https://adk.dev/tools-custom/function-tools/).

Graph alternative in 2.0: `Workflow(name="root_agent", edges=[("START", agent_a, agent_b)])` (README). The full graph topic belongs in the workflows research file.

---

## 10. Bidi streaming (Gemini Live API)

Sources: https://adk.dev/live/ and https://adk.dev/live/sessions/.
- Imports: `from google.adk.agents.live_request_queue import LiveRequestQueue`, `from google.adk.agents.run_config import RunConfig`.
- `LiveRequestQueue` methods:
  - `send_content(content)` sends a text turn.
  - `send_realtime(blob)` streams audio, image or video bytes.
  - `send_activity_start()` / `send_activity_end()` mark turns manually when VAD is off.
  - `close()`.
- `runner.run_live(user_id=..., session_id=..., live_request_queue=q, run_config=cfg)` is an async generator of Events.
- Interruption: when the user cuts in, events arrive with `interrupted: true`. v2.13.0 also added barge-in to the cascade (STT→LLM→TTS) path.
- Session resumption: `RunConfig(session_resumption=types.SessionResumptionConfig())` auto-reconnects up to 5 times. Quote: "The Live API closes each WebSocket connection after about 10 minutes." Context-window compression removes the session-duration cap.
- The docs example model is `gemini-live-2.5-flash-native-audio`. The platform release notes list "Gemini 3.8 Live is generally available" on 2026-09-24, but its model ID is [UNVERIFIED].
- Token streaming for text chat is `StreamingMode.SSE`, which the user cannot interrupt.
```python
q = LiveRequestQueue()
cfg = RunConfig(response_modalities=["AUDIO"],
                session_resumption=types.SessionResumptionConfig(),
                context_window_compression=types.ContextWindowCompressionConfig(
                    trigger_tokens=100000,
                    sliding_window=types.SlidingWindow(target_tokens=80000)))
q.send_realtime(types.Blob(mime_type="audio/pcm;rate=16000", data=pcm_chunk))
async for event in runner.run_live(user_id="u1", session_id=sid,
                                   live_request_queue=q, run_config=cfg):
    ...
```
Demo: LensMosaic, a visual shopping demo with camera and voice, listed on https://adk.dev/live/.

---

## 11. Models: Gemini 2.5/3.x and LiteLLM

ADK supports models in three ways (https://adk.dev/agents/models/):
1. A plain string resolved by the model registry (Gemini, Claude, Agent Platform-hosted models).
2. A connector class passed as `model=`: `LiteLlm`, `ApigeeLlm`, Ollama, vLLM, LiteRT-LM.
3. Model routing, or `FallbackModel` for automatic failover (v2.9.0).

**Gemini**
- `model="gemini-flash-latest"` (docs). The quote is that it selects the latest Flash, but "if you access Gemini from a regional endpoint, such as `us-central1`, this selection string may not work."
- Pinned IDs: `gemini-3.5-flash` (GA 2026-05-19, 1,048,576-token input context) and `gemini-2.5-flash`.
- Later GA releases per the platform release notes: 3.6 Flash (07-21), 3.7 Flash (08-13), 3.8 Flash (09-02). Their exact ID strings are [UNVERIFIED].
- Gemini 3 default thinking level is MEDIUM.
- Environment:
  - AI Studio: `GOOGLE_API_KEY`.
  - Google Cloud: `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION`, `GOOGLE_GENAI_USE_ENTERPRISE=True`. Current docs use this name. Older docs and codelabs used `GOOGLE_GENAI_USE_VERTEXAI=TRUE`.

**LiteLLM**
- Usage: `from google.adk.models.lite_llm import LiteLlm`, then `model=LiteLlm(model="openai/gpt-4o")` or `"anthropic/claude-3-haiku-20240307"` (https://adk.dev/agents/models/litellm/).
- Requires `litellm>=1.84`.
- **Security advisory to teach:** LiteLLM 1.82.7 and 1.82.8 on PyPI contained unauthorized code. The docs say: "If you installed or upgraded LiteLLM during this period, rotate all secrets and credentials."

---

## 12. Real-world anchors

- The ADK launch blog (Apr 9 2025, Cloud NEXT 2025) says "ADK is the same framework powering agents within Google products like Agentspace" and Google Customer Engagement Suite. Source: https://developers.googleblog.com/en/agent-development-kit-easy-to-build-multi-agent-applications/
- The ADK runtime and Memory Bank are now part of Gemini Enterprise Agent Platform (Next '26, Apr 22 2026).
- The ADK docs mention LensMosaic as a live demo.
- Named external production customers were **not verified** in this pass. A web search surfaced only third-party claims, so don't put customer logos on slides without a primary source.

## 13. Codelabs, repos, docs (exact titles + URLs)

- Codelab: **"Building Stateful and Personalized Agents with ADK"**. A travel agent that solves the "Goldfish Problem" over six levels covering session/state, multi-agent state and memory. https://codelabs.developers.google.com/codelabs/agent-memory/instructions
- Codelab: **"Quickstart with Agent Development Kit"** (Memory Bank). https://docs.cloud.google.com/agent-builder/agent-engine/memory-bank/quickstart-adk
- Repo: **google/adk-python** https://github.com/google/adk-python (CHANGELOG, `contributing/samples/`, `docs/guides/`)
- Web UI: https://github.com/google/adk-web
- Docs: Welcome to ADK 2.0 https://adk.dev/2.0/; Apps https://adk.dev/apps/; State https://adk.dev/sessions/state/; Memory https://adk.dev/sessions/memory/; Context https://adk.dev/context/; Plugins https://adk.dev/plugins/; Collaboration https://adk.dev/workflows/collaboration/; Live https://adk.dev/live/
- Paper: Yao et al., *ReAct: Synergizing Reasoning and Acting in Language Models*, arXiv:2210.03629 (2022). This is the basis of `PlanReActPlanner`.

## 14. Quotable lines

- "The App class is a top-level container for an entire Agent Development Kit (ADK) agent workflow." (adk.dev/apps)
- "`CallbackContext` and `ToolContext` have been replaced by the `Context` type." (adk.dev/context)
- "Plugin callback functions have precedence over callbacks implemented at the object level." (adk.dev/plugins)
- "Agent A retains control and continues to handle future user input." (AgentTool vs sub-agent, function-tools docs)
- "Do not configure a root agent with the mode setting." (adk.dev/workflows/collaboration)
- "The Live API closes each WebSocket connection after about 10 minutes." (adk.dev/live/sessions)
- "All conversation data is lost if the application restarts." (InMemorySessionService, adk.dev/sessions/session)

---

## Slide ideas (9)

1. **"Anatomy of an Agent"**: an exploded diagram of an `Agent(...)` call with each parameter as a labelled callout. Animate the callouts in three groups: identity (name/description), brain (model/instruction/planner), and hands (tools/code_executor/sub_agents).
2. **"The Runner Event Loop"**: a circular 7-step animation (Initiate → Kick-off → Yield → Process → Forward → Resume → Repeat). A token moves around the circle, and a "commit" flash on the Session DB marks step 4.
3. **"Four Shelves of State"**: four nested boxes, `temp:` ⊂ session ⊂ `user:` ⊂ `app:`. Fade out `temp:` when the invocation ends, then "restart the server" so the in-memory service wipes everything while Database/Vertex survive.
4. **"Session vs State vs Memory vs Artifacts"**: a 2×2 grid comparing short-term vs long-term and structured vs binary, with one code line per cell.
5. **"Who gets which Context?"**: a class ladder `ReadonlyContext → Context (ex-CallbackContext) → ToolContext`, plus a sidebar for `InvocationContext`. Highlight what each rung adds.
6. **"Hook Timeline"**: a horizontal swim-lane of one invocation. Plugin hooks sit on the top lane, agent callbacks below. Animate a `before_model_callback` returning an `LlmResponse` and short-circuiting the LLM box.
7. **"Transfer vs AgentTool vs Task mode"**: a three-column comparison showing who owns the conversation afterwards. Animate the control baton: it passes in a transfer, gets borrowed and returned with AgentTool, and comes back automatically via `finish_task` in task mode.
8. **"Talking to Your Agent in Real Time"**: a duplex pipe diagram, `LiveRequestQueue` → `run_live` → events back. Show an interruption with `interrupted: true` and a reconnect at about 10 minutes via session resumption.
9. **"Bring Any Model"**: a model plug-board with Gemini strings, `LiteLlm("openai/...")`, Ollama/vLLM and `FallbackModel`. Callout box: the LiteLLM 1.82.7/1.82.8 supply-chain warning.
10. **"1.x → 2.0: what broke"**: a before/after table covering `BaseAgent → BaseNode`, the new event fields, `Context` unification, plugins moving to `App`, and template agents → `Workflow`.
