# 04 — ADK 2.0 Workflows in Full Detail (graph engine, HITL, resume, release notes 2.0 → 2.13)

Research date: 2026-10-23. Sources were the primary repos and docs only: `github.com/google/adk-python` (source, CHANGELOG, `contributing/samples/workflows/*`, `docs/guides/workflow/*`) and `github.com/google/adk-docs`, which is the source of the docs site. The docs site moved: `google.github.io/adk-docs/` now returns **301 to `https://adk.dev/`**. All code below is copied from those files. Paths are given so a reader can open them.

> Method caveat: the shared WebSearch budget ran out during this run, so I could not search for codelab titles, Next '26 / I/O '26 session titles, or blog posts. The items that depend on search are marked **[UNVERIFIED]**. Everything else was read directly from source.

---

## 1. Headline facts (verified)

| Fact | Value | Source |
|---|---|---|
| ADK Python 2.0.0 GA | **2026-05-19**, from `v2.0.0b1` | adk-python `CHANGELOG.md` |
| ADK Go 2.0 GA | 2026-06-30 (`go get google.golang.org/adk/v2`) | adk.dev/2.0/ |
| ADK TypeScript 2.0 GA | 2026-08-21 | adk.dev/2.0/ |
| Latest Python release | **v2.13.0, 2026-10-22** (GitHub release page shows 23 Oct) | CHANGELOG / releases |
| Stay on 1.x | `pip install "google-adk~=1.0"`. The 1.x line still gets fixes (v1.39.1, 27 Aug 2026) | adk.dev/2.0/, releases |
| Core architectural change | ADK moved from a hierarchical agent executor to a **graph-based execution engine**. In Python, `BaseAgent` now subclasses `BaseNode` | adk.dev/2.0/ |
| Top-level exports | `from google.adk import Agent, Context, Event, Runner, Workflow`. `START` must come from `google.adk.workflow`, and `from google.adk import START` raises `ImportError` | docs/guides/workflow/workflow |
| `google.adk.workflow` exports | `BaseNode, DEFAULT_ROUTE, Edge, FunctionNode, JoinNode, Node, NodeTimeoutError, RetryConfig, START, Workflow, node` | `src/google/adk/workflow/__init__.py` |
| HITL primitive | `from google.adk.events import RequestInput` | adk.dev/graphs/human-input |

The CHANGELOG describes 2.0 as a "Multi-Agent Workflow Engine" with a "model-agnostic engine for orchestrating non-linear, conditional, and cyclical agent execution patterns", plus "Native Inter-Agent Routing" (CHANGELOG 2.0.0).

**Three workflow styles** (adk.dev/graphs/):
1. **Graph-based workflows**: a declarative graph of nodes and edges (`Workflow(edges=[...])`).
2. **Dynamic workflows**: ordinary code (`@node` plus `await ctx.run_node(...)`, loops, `asyncio.gather`) with automatic checkpointing.
3. **Prebuilt workflow agents**: `SequentialAgent`, `ParallelAgent`, `LoopAgent`, now documented as "template workflows". The TypeScript migration notes call them **deprecated but still working**, with graph workflows as the suggested replacement. In Python, 2.5.0 added a check that "no old orchestrators are used inside Workflow graphs" (CHANGELOG 2.5.0).

---

## 2. The graph API: nodes, edges, routes

### 2.1 What can be a node (`NodeLike`)
From `docs/guides/workflow/graph/index.md`:
1. **Python functions** (sync, async, or generators). These are auto-wrapped in `FunctionNode`. `@node` is needed only to set options.
2. **Agents**: `LlmAgent`, usually with `mode="single_turn"`.
3. **Tools**: `BaseTool` instances.
4. **Workflows**: a `Workflow` is itself a `BaseNode`, so workflows can be nested.
5. **`START`**: a sentinel `BaseNode` named `__START__`. It never executes. The string `"START"` is accepted as an alias in chain tuples but not in `Edge(...)`.

**Every node goes through the same steps** (base_node guide):
1. Validate `node_input` against `input_schema`. Dicts are coerced into the model.
2. Run the user logic.
3. Normalize each yielded item. `None` is dropped. An `Event` passes through, with its output validated. A `RequestInput` becomes an interrupt event. Any other value is wrapped as `Event(output=value)`. This is why `return "done"` works.

### 2.2 First workflow (adk.dev/graphs/ "Get started")
```python
from google.adk import Agent
from google.adk import Workflow
from google.adk import Event
from pydantic import BaseModel

city_generator_agent = Agent(
    name="city_generator_agent",
    model="gemini-flash-latest",
    instruction="""Return the name of a random city.
      Return only the name, nothing else.""",
)

class CityTime(BaseModel):
    time_info: str  # time information
    city: str       # city name

def lookup_time_function(node_input: str):
    """Simulate returning the current time in the specified city."""
    return CityTime(time_info="10:10 AM", city=node_input)

city_report_agent = Agent(
    name="city_report_agent",
    model="gemini-flash-latest",
    input_schema=CityTime,
    instruction="""Output following line:
    It is {CityTime.time_info} in {CityTime.city} right now.""",
)

def completed_message_function(node_input: str):
    return Event(
        message=f"{node_input}\n WORKFLOW COMPLETED.",
    )

root_agent = Workflow(
    name="root_agent",
    edges=[
        ("START", city_generator_agent, lookup_time_function,
          city_report_agent, completed_message_function)
    ],
)
```
Key idea: **each node's return value becomes the next node's `node_input`**. You do not have to write to session state to pass data along.

### 2.3 Edge syntax: two forms (graph guide)
**Chain tuples**, the common form:
```python
edges=[(START, step_a, step_b, step_c)]                       # sequence
edges=[(START, step_a, (step_b, step_c))]                     # parallel fan-out
from google.adk.workflow import DEFAULT_ROUTE
edges=[(START, step_a, {"success": step_b,
                        "failure": step_c,
                        DEFAULT_ROUTE: fallback_step})]        # conditional routing map
edges=[(START, step_a, {"success": (step_b, step_c), "failure": fallback_step})]  # route fans out
```
**Explicit `Edge` objects**. Both ends must be `BaseNode`, so bare functions have to be wrapped first:
```python
from google.adk.workflow import Edge, START, node

@node()
def step_a(node_input: str): ...
@node()
def step_b(node_input: str): ...
@node()
def step_c(node_input: str): ...

edges=[
    Edge(from_node=START, to_node=step_a),
    Edge(from_node=step_a, to_node=step_b, route="success"),
    Edge(from_node=step_a, to_node=step_c, route="failure"),
]
```
- **Route values** can be `str`, `int`, or `bool`. A node emits one with `Event(route="x")`. It can also emit `Event(route=[...])`, which dispatches to every matching branch. This is the multi-label classifier example in adk.dev/graphs.
- **`DEFAULT_ROUTE`** is the literal `"__DEFAULT__"`. It fires when a route is emitted and nothing else matches. Since 2.10.0 it can fan out: `{DEFAULT_ROUTE: (step_b, step_c)}`.
- **No match and no default**: the branch ends silently, with only a log warning. Other branches carry on.

### 2.4 The ten construction-time validation rules
These are checked when `Workflow(...)` is constructed, and errors come wrapped in a Pydantic `ValidationError` (a subclass of `ValueError`). Source: graph guide.
1. Unique node names. Reusing the *same instance* is how you loop back to a node.
2. `START` is present and has no incoming edges.
3. Edges out of `START` carry no route ("Edges from START must not have routes").
4. Every node is reachable from `START`.
5. No duplicate edges and no overlapping routes between the same pair of nodes.
6. `DEFAULT_ROUTE` cannot share a route list with other routes.
7. **No unconditional cycles**. Loops must be conditional.
8. **Static schema matching**: `output_schema` of a node must equal `input_schema` of its successor. These schemas are often *inferred from type hints*.
9. An `LlmAgent(mode='chat')` may only follow `START`. Use `single_turn` for nodes in the middle of a chain.
10. Node-specific checks on outgoing edges. For example, nodes with fixed routes reject unknown routes and require all their routes to be handled.

Limitation: validation is **structural, not behavioral**. Nothing checks that a node actually emits the routes its edges name.

### 2.5 Routers / conditional edges (adk.dev/graphs/)
```python
process_message = Agent(
    name="process_message",
    model="gemini-flash-latest",
    instruction="""Classify user message into either "BUG", "CUSTOMER_SUPPORT",
      or "LOGISTICS". If you think a message applies to more than one category,
      reply with a comma separated list of categories.
   """,
)

def router(node_input: str):
    routes = node_input.split(",")
    routes = [route.strip() for route in routes]
    return Event(route=routes)

root_agent = Workflow(
   name="routing_workflow",
   edges=[
       ("START", process_message, router),
       ( router,
           {
               "BUG": response_1_bug,
               "CUSTOMER_SUPPORT": response_2_support,
               "LOGISTICS": response_3_logistics,
           }
       )
   ],
)
```

**New in 2.13.0: `ClassifierNode`** (`google.adk.labs.classifiers`, so it is a labs API). Sample: `contributing/samples/workflows/classifier_node/agent.py`:
```python
from google.adk.labs.classifiers import Binary, Choice, ClassifierNode, LlmClassifier
classifier = LlmClassifier(model="gemini-3.5-flash")
triage = ClassifierNode(
    name="triage", classifier=classifier,
    question=Choice(
        instructions="Which team should handle this support ticket?",
        criteria={"billing": "Invoices, refunds, or subscription charges",
                  "technical": "Bugs, errors, outages, or API problems",
                  "general": "Product questions and anything else"}),
    answer_key="triage_answer",
)
is_urgent = ClassifierNode(name="is_urgent", classifier=classifier,
    question=Binary(instructions="Is this an outage, or does it block the customer's production use?"),
    threshold=0.7, answer_key="urgency_answer")
root_agent = Workflow(name="root_agent", edges=[
    ("START", process_input, triage),
    (triage, {"billing": billing_agent, "technical": is_urgent, "general": faq_agent}),
    (is_urgent, {True: page_oncall, False: eng_queue}),   # boolean routes
])
```
The 2.13 highlights also list `TypesafeClassifier` (TypeSafe "Jev" models, which return calibrated probabilities in one forward pass, "much faster than an LLM") and `BaseClassifier`.

### 2.6 Fan-out / fan-in and `JoinNode`
```python
from google.adk.workflow import JoinNode
my_join_node = JoinNode(name="my_join_node")
edges=[
    ("START", parallel_task_A, my_join_node),
    ("START", parallel_task_B, my_join_node),
    ("START", parallel_task_C, my_join_node),
    (my_join_node, final_task_D),
]
```
The `JoinNode` source is short. It overrides `_requires_all_predecessors -> True` and yields `Event(output=node_input)`, where `node_input` is a **dict keyed by predecessor node name**. A more compact form, from the graph guide:
```python
workflow = Workflow(name="fan_out_workflow",
    edges=[(START, (word_count, shout), join, report)])
def report(node_input: dict[str, Any]) -> str:
    return f"{node_input['shout']} ({node_input['word_count']} words)"
```
**Terminal-output rule** (workflow guide): a workflow's output is the output of its terminal node. If several terminal nodes run and produce output, the run fails with `WorkflowConfigurationError` ("multiple terminal nodes produced output"). The fix is to put a `JoinNode` before the end.
Related fixes: 2.8.0 "honor START as a satisfied JoinNode predecessor". 2.13.0 "`JoinNode` in a loop waits for each iteration's predecessors".

**Multi-trigger without a join** (`samples/workflows/multi_triggers`): `("START", (make_uppercase, count_characters, reverse_string), send_message)`. Here `send_message` runs **once per predecessor**.

**`parallel_worker` (map over a list)**, from `samples/workflows/parallel_worker`:
```python
@node(parallel_worker=True)
def make_upper_case(node_input: str):
  yield node_input.upper()
explain_topic = Agent(name="explain_topic", ..., parallel_worker=True, output_schema=TopicExplanation)
# START -> process_input -> find_related_topics(list[str]) -> make_upper_case -> explain_topic -> aggregate(list[...])
```
`max_parallel_workers` caps the per-item concurrency. `Workflow(max_concurrency=2)` caps how many graph-scheduled nodes run at once. Nodes started with `ctx.run_node()` are exempt from that cap, because throttling them would deadlock.

### 2.7 Loops (back-edges)
Sample `samples/workflows/loop/agent.py` (generator–critic):
```python
def route_headline(node_input: Feedback):
  return Event(route=node_input.grade)

root_agent = Workflow(
    name="root_agent",
    edges=[
        ("START", process_input, generate_headline, evaluate_headline, route_headline),
        (route_headline, {"unrelated": generate_headline}),   # conditional back-edge
    ],
)
```
A self-loop is also allowed: `(guess_number, {'guessed_wrong': guess_number})` (`samples/workflows/loop_self`).
**Failure mode:** "A graph cycle is not bounded automatically" (adk.dev/graphs/routes). There is **no `max_iterations` on graph cycles**. Bound the loop with a counter in state, or move it into a dynamic-workflow `while` loop. (`LoopAgent.max_iterations` still exists for the template agent. 2.9.0 fixed "treat a max_iterations of zero as zero loop passes".)
Each pass re-activates the target node "with a fresh lifecycle". Event `node_info.path` values show the iteration counter, for example `request_input@1/request_human_review@2`.

### 2.8 Subgraphs (nested workflows)
```python
find_famous_person = Workflow(name="find_famous_person",
                              edges=[("START", find_name, generate_bio)])
join_for_aggregation = JoinNode(name="join_for_aggregation")
root_agent = Workflow(name="root_agent", edges=[(
    "START", process_input,
    (find_famous_person, find_historical_event),   # sub-workflow is one parallel branch
    join_for_aggregation, aggregate_results)])
```
(`samples/workflows/nested_workflow`.) Inner events **bubble up to the parent** so the run can be traced. The output of the inner terminal node becomes the subgraph's output. `Workflow.rerun_on_resume` defaults to **True**, so a nested workflow re-runs its graph on resume, and completed children are replayed, not executed again.
Related: "Workflow as Tool" (2.4.0) and `NodeTool` (wrap any node or workflow as a tool for an LLM agent). In 2.13.0, `NodeTool` infers `input_schema` from START successors.

---

## 3. Data, state, and typed state schema

Event fields (adk.dev/graphs/data-handling):
- `output`: data passed to the next node. **Only one `Event.output` per node execution.** A second one raises a runtime error.
- `message`: content shown to the user.
- `state`: a state delta persisted in the session.
- `route`: the routing decision.

New `Event` fields in 2.0 (Python): `node_info`, `output`. Custom session stores with rigid schemas must migrate.

Four ways to read and write state (`samples/workflows/state`):
```python
def process_initial_input(ctx, node_input: str):
  ctx.state["original_text"] = node_input          # direct write
  return node_input
def update_state_via_event(node_input: str):
  yield Event(state={"uppercased_text": node_input.upper()})   # write via Event
def read_state_via_ctx(ctx):
  return ctx.state["original_text"]                # direct read
def read_state_via_param(appended_text: str):      # auto-injected from state by param name
  return f"Final Result: {appended_text}!"
```
`parameter_binding` defaults to `'state'`. Function parameters other than `ctx` and `node_input` are resolved from state.

**Typed state, `state_schema`** (base_node guide):
```python
class ResearchState(BaseModel):
    topic: str
    depth: int
def pick_topic(ctx) -> str:
    ctx.state["topic"] = "graph databases"   # allowed
    ctx.state["temp:scratch"] = [1, 2, 3]    # allowed, prefixed keys are exempt
    return "ok"
workflow = Workflow(name="research", edges=[(START, pick_topic)], state_schema=ResearchState)
```
- Writing an undeclared key, or a value of the wrong type, raises `StateSchemaError` (exported from `google.adk.sessions`; it subclasses **`TypeError`**).
- Keys containing `:` (`app:`, `user:`, `temp:`) bypass the schema, so **a typo in a prefix is not caught**.
- Child nodes inherit the schema. When a `Workflow` sets it, function-node parameters bound to state are checked at construction time.

**Typed I/O:** a function node's `input_schema` comes from its `node_input` hint and its `output_schema` from its return hint. Agents take `input_schema=` and `output_schema=`. Instruction templating uses `{CityTime.city}`, or the stricter `<CityTime.city from lookup_time_function>`, which qualifies the value by source node.

---

## 4. How 2.0 graphs differ from SequentialAgent / ParallelAgent / LoopAgent

| Dimension | 1.x template agents | 2.0 `Workflow` graph |
|---|---|---|
| Control flow | Fixed order across sub-agents | Explicit edges, routes, fan-out/fan-in, conditional cycles |
| Node types | Agents only | Functions, agents, tools, workflows, `JoinNode`, `ClassifierNode`, HITL |
| Data passing | Session state via `output_key` plus `{var}` templating | Typed `node_input` → `output` hand-off; state is optional |
| Routing | No `Event.route` dispatch. Encode the decision in state, or exit a `LoopAgent` with `escalate` | `Event(route=...)` plus routing maps and `DEFAULT_ROUTE` |
| Non-LLM steps | Needed a custom agent | Plain function = node; can "run chains of functions without AI" |
| Validation | Little | 10 rules at construction, including schema matching |
| Loop bound | `LoopAgent(max_iterations=...)` | None. Programmer bounds the cycle |
| Resume | Per-agent `current_sub_agent`, `times_looped` in agent state (Resume docs, Python ≥1.16) | Rebuilt from the session event log by replay; per-node status checkpoints |
| HITL | Custom tool / LongRunningFunctionTool / tool confirmation | `RequestInput` node, `require_confirmation`, `rerun_on_resume` |
| Status | Deprecated in TS 2.0; still shown in Visual Builder | Recommended |

Breaking change to remember: in Python 2.0, **overriding `_run_async_impl()` on a custom `BaseAgent` is silently ignored**. Use callbacks, or write a node. Also: do not catch broad `except Exception` in tools, because that disables retries and breaks HITL pauses (adk.dev/2.0).

---

## 5. Dynamic workflows (code-first graphs)

```python
from google.adk import Context, Workflow
from google.adk.workflow import node
from typing import Any

@node(name="hello_node")
def my_node(node_input: Any):
    return "Hello World"

@node(rerun_on_resume=True)
async def my_workflow(ctx: Context, node_input: str) -> str:
    result = await ctx.run_node(my_node, node_input="hello")
    return result

root_agent = Workflow(name="root_agent", edges=[("START", my_workflow)])
```
Loop with a verifier (adk.dev/graphs/dynamic, "Loop route"):
```python
@node
async def code_workflow(ctx: Context, user_request: str):
  code = await ctx.run_node(coder_agent, user_request)
  check_resp = await ctx.run_node(compile_lint_check, code)
  while check_resp.findings:
    yield Event(state={"code": code, "findings": check_resp.findings})
    code = await ctx.run_node(fixer_agent, {"code": code, "findings": check_resp.findings})
    check_resp = await ctx.run_node(compile_lint_check, code)
  yield Event(output=code)
```
Parallel execution: `tasks.append(ctx.run_node(real_node, item))` and then `await asyncio.gather(*tasks)`. On resume, **only failed or interrupted workers re-run**.
- **Deterministic execution IDs**: each child run gets parent id plus a counter (`"1"`, `"2"`, …). These ids are the checkpoint keys. A custom `ctx.run_node(..., run_id=f"order-{id}")` must contain a non-numeric character. The docs warn against custom ids.
- **Rule:** a parent that calls `ctx.run_node` **must set `rerun_on_resume=True`**.

---

## 6. Human-in-the-loop interrupts

### 6.1 `RequestInput` node (pause → resume into the next node)
```python
from google.adk.events import RequestInput
from google.adk import Workflow
def step1():
  yield RequestInput(message="Enter a number:")
def step2(node_input):
  return node_input * 2
root_agent = Workflow(name="root_agent", edges=[('START', step1, step2)])
```
`RequestInput` fields (`src/google/adk/events/request_input.py`):
- `interrupt_id`: defaults to a new uuid.
- `payload`: any data to send with the request.
- `message`: text shown to the user.
- `response_schema`: a Python type, a generic alias, or a JSON-schema dict.

The schema **does not reformat** a human reply. Put an agent after the pause to normalize free text.

**On the wire** (`samples/workflows/request_input/tests/phone_broke.json`):
1. The workflow emits an event with `longRunningToolIds: ["fc-1"]` and a `functionCall` whose args include `interruptId: "fc-1"` and `message`.
2. The client resumes by sending a user event containing `functionResponse {id: "fc-1", name: "adk_request_input", response: {result: "shorter"}}`.
3. The next node receives `"shorter"`, routes `revise`, and loops back to `draft_email`. The second interrupt is `fc-2` at path `.../request_human_review@2`.

So HITL is built on the long-running function-call protocol, and any client that can return a FunctionResponse can resume a workflow.

Full approve/reject/revise loop (`samples/workflows/request_input/agent.py`):
```python
def handle_human_review(node_input: str):
  if node_input == "reject":
    yield Event(route="rejected")
  elif node_input == "approve":
    yield Event(route="approved")
  else:
    yield Event(state={"feedback": node_input}, route="revise")
root_agent = Workflow(name="request_input", edges=[
    ("START", process_input, draft_email, request_human_review, handle_human_review),
    (handle_human_review, {"revise": draft_email, "approved": send_email, "rejected": reject_email})])
```

### 6.2 Rerun pattern (one node asks the question and handles the answer)
From `samples/workflows/request_input_rerun/README.md`:
```python
@node(rerun_on_resume=True)
def human_review(draft: str, ctx: Context):
    interrupt_id = f"human_review_{ctx.invocation_id}_{ctx.run_id}"
    resume_input = ctx.resume_inputs.get(interrupt_id)
    if not resume_input:
        yield RequestInput(interrupt_id=interrupt_id, message="Please review the draft...")
        return
    ...
```
`rerun_on_resume` defaults to False for functions and True for `LlmAgent` and `Workflow`. With False, the node *completes using the resume input as its output*.

### 6.3 Confirmation gates
- 2.12.0: `@node(require_confirmation=True | predicate)` and `FunctionNode(require_confirmation=...)`. This automatically enables `rerun_on_resume`.
- 2.11.0: tool nodes pause for approval through `RequestInput`.
- Tool confirmation inside `LlmAgent` is separate (adk.dev `tools-custom/confirmation`).
- Auth works the same way: `@node(auth_config=...)`, which requires `rerun_on_resume=True`.

---

## 7. Checkpointing, resume, durability (how it really works)

From the in-repo architecture note `.agents/skills/adk-architecture/references/architecture-workflow-resumability.md`:
- **Resume is always on within an invocation.** On every run the `Workflow` scans the invocation's session events (`ReplayManager.scan_workflow_events`) and rebuilds which nodes completed, their outputs, and which interrupts are still pending. Completed nodes are **fast-forwarded**, and the interrupted node re-runs with the responses.
- **`ResumabilityConfig(is_resumable=True)` adds durability.** It enables resume across separate runner calls without a new message, adds `agent_state` / `end_of_agent` checkpoint events to the log, and routes function responses back to their originating invocation.
- `Workflow._emit_node_checkpoint` writes `{"nodes": {name: {status, interrupts}}}` (resume inputs are deliberately left out). However, **nothing reads that checkpoint yet** (`TODO: resume from checkpoint event`), so resume cost still grows with history length. The stated direction is a LangGraph-style "load latest snapshot". The note compares ADK with LangGraph `StateSnapshot`, pydantic-graph `NodeSnapshot`, and OpenAI Agents SDK `RunState`.
- Node statuses (`_node_status.py`, persisted as ints): `INACTIVE 0, PENDING 1, RUNNING 2, COMPLETED 3, WAITING 4, FAILED 5, CANCELLED 6`.

Enable durability and resume (adk.dev/runtime/resume):
```python
app = App(name='my_resumable_agent', root_agent=root_agent,
          resumability_config=ResumabilityConfig(is_resumable=True))
```
```console
adk api_server my_resumable_agent/
curl -X POST http://localhost:8000/run_sse -H "Content-Type: application/json" \
 -d '{"app_name": "my_resumable_agent","user_id": "u_123","session_id": "s_abc","invocation_id": "invocation-123"}'
```
In Python: `runner.run_async(user_id=..., session_id=..., invocation_id='invocation-123')`. The docs say resuming from the ADK Web UI or the CLI is **not supported**.

**Semantics to teach:**
- Resume is **at-least-once**, so tools with side effects must be idempotent (resume docs). 2.9.0 changelog: "Node bodies with external side effects must be idempotent".
- A failed node **re-runs** on resume. Before 2.9.0 it was replayed as completed.
- Do not change the graph while a run is paused. A long-lived paused run can outlive a code change, and the architecture note lists checkpoint versioning as an open consideration.

**Retry and timeout:**
```python
@node(retry_config=RetryConfig(max_attempts=5, initial_delay=1))
def get_weather(ctx: Context) -> str:
  yield Event(message=f"Getting weather... attempt {ctx.attempt_count}")
  ...
```
`RetryConfig` defaults (`_retry_config.py`): `max_attempts` 5, `initial_delay` 1.0 s, `max_delay` 60 s, `backoff_factor` 2.0, `jitter` 1.0, `exceptions=None` (retry on all). `@node(timeout=30.0)` raises `NodeTimeoutError`, and a timeout counts as a retryable failure.

**Cancellation:** `abort_signal` on `Runner`, `Workflow`, and nodes (2.11.0). `/run_sse` cancels when the client disconnects.

---

## 8. Long-running operations and streaming intermediate events
- **Long-running = interrupt.** A `RequestInput`, a confirmation, an auth request, or a `LongRunningFunctionTool` all surface as a function call listed in `longRunningToolIds`. The invocation pauses until a matching `FunctionResponse` arrives, possibly across calls if `is_resumable`.
- **Streaming:** every node yields `Event`s as it goes, and the runner streams them, for example over `/run_sse`. Each event carries `node_info.path` (`workflow@1/node@n`) so a UI can attribute it to a node and an iteration. `Event(message=...)` is user-visible progress, separate from `output`. Nested workflows bubble child events up to the parent.
- **Live (voice):** under `run_live()` a whole `Workflow` runs inside **one live connection**, and agent nodes use `mode='task'` (adk.dev/live/workflows, Python v2.0.0). Note: the collaboration docs still say *"task mode is disabled in graph-based workflows in ADK Python v2.0.0"*. Later changelogs add task-mode workflow resume (2.5.0, 2.12.0), so treat that warning as stale for 2.12+ **[UNVERIFIED which statement is current]**.

---

## 9. Declarative YAML graphs (2.9.0+)
2.9.0 highlight: "load ADK 2.0 graph workflows from YAML configuration". Sample `contributing/samples/workflows/loop_config/root_agent.yaml`:
```yaml
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
# evaluate_headline.yaml
agent_class: LlmAgent
name: evaluate_headline
instruction: |
  Grade whether the headline is related to technology or software engineering.
output_schema:
  name: loop_config.agent.Feedback
output_key: feedback
```
Resolution rules (sample README):
- A string ending in `.yaml` is an agent file.
- `.agent.fn` is a function relative to the agent package, auto-wrapped as `FunctionNode`.
- `name:` holds a fully qualified Python object.
- Resolved nodes are **cached by string**, so loops reuse the same instance.

Run it from `contributing/samples/workflows`.
Visual Builder (`adk web`, experimental since v1.18.0) writes Agent Config YAML. Its listed components are still LLM, Sequential, Loop, and Parallel agents. Whether it can author `Workflow` graphs is **[UNVERIFIED]**. For security, the builder endpoints exist only under `adk web`, accept only `.yaml`/`.yml`, and reject `..`, absolute paths, and blocked keys such as `args`.

---

## 10. Visualising graphs in `adk web`
From `src/google/adk/cli/dev_server.py` and `cli/utils/graph_visualization.py`:
- `GET /dev/apps/{app_name}/graph` returns the base graph as DOT (`dot_src`).
- `GET /dev/apps/{app_name}/build_graph_image?dark_mode=&node=` returns DOT for every sub-workflow. `node=` drills into a nested workflow.
- `GET /dev/apps/{app_name}/users/{u}/sessions/{s}/events/{event_id}/graph` returns the graph highlighted for one event.
- `plot_workflow_graph()` renders with **graphviz** and colours nodes by `NodeStatus`. Dark theme: COMPLETED `#16A34A` green, RUNNING `#D97706` amber, FAILED `#EF4444` red, WAITING `#9333EA` purple, CANCELLED `#475569` slate. START is green and END is red. For a non-workflow agent it falls back to a sub-agent tree.
- These are dev-only endpoints, added by `DevServer`. `AdkWebServer` is deprecated in favour of `ApiServer` and `DevServer`.

---

## 11. Release notes, 2.x → Oct 2026 (Python, CHANGELOG)
| Ver | Date | Workflow-relevant items |
|---|---|---|
| 2.0.0 | 2026-05-19 | GA. Graph engine, dynamic workflows, collaborative modes (chat/task/single_turn) |
| 2.1.0 | 05-23 | Fixes (sandboxes, telemetry) |
| 2.2.0 | 06-04 | Restored 1.x agent-config wiring; abort runs when the client drops; standardized `request_input` tool for LLM clarification |
| 2.3.0 | 06-17 | Labs: experimental **Antigravity SDK agent wrapper**; per-request OTel |
| 2.4.0 | 07-07 | **Workflow as Tool**; `ManagedAgent` (Managed Agents API) |
| 2.5.0 | 07-16 | Strict input-schema validation for LlmAgent nodes; **HITL resume for standalone nodes and NodeTool**; check that no old orchestrators are used in graphs; task-mode node state resume |
| 2.6.x | 07-29 → 08-07 | ManagedAgent `instruction`; misc |
| 2.7.0/2.7.1 | 08-13/08-17 | Eval state collected from workflow nodes |
| 2.8.0 | 08-25 | START counts as satisfied JoinNode predecessor; `BaseNode` is `abc.ABC`; native A2A task mode; `ADK_MAX_LLM_CALLS` |
| 2.9.0 | 09-10 | **YAML graph workflows**; failed node re-runs on resume (behaviour change); nested multi-turn HITL; `max_iterations=0` fix; FallbackModel |
| 2.10.0 | 09-24 | `DEFAULT_ROUTE` fan-out; abort-signal primitives; rewind filtering on rehydration |
| 2.11.0 | 10-01 | `abort_signal` on Runner/Workflow/nodes; `ToolNode` approval via `RequestInput`; plugin callbacks around ToolNode |
| 2.12.0 | 10-13 | `require_confirmation` on nodes; `retry_config` for dynamic nodes; centralized resume routing; parallel isolation by `node_path` |
| 2.13.0 | 10-22 | **`ClassifierNode`** (LLM/TypeSafe); JoinNode-in-loop fix; unique `interrupt_id` per loop iteration; `ReplaySequenceBarrier`; 12 experimental features promoted to stable; **breaking:** OTel GenAI v2 semconv default (`ADK_TELEMETRY_SCHEMA_VERSION_OPT_IN=otel_semconv_1_36` keeps v1) |

---

## 12. Failure modes cheat-sheet
1. **Two terminal nodes both produce output** → `WorkflowConfigurationError`. Add a `JoinNode`.
2. **Unbounded conditional loop.** The engine has no cap. Use a state counter, or a dynamic `while` with a bound.
3. **A route matches no edge** → the branch silently stops, with only a log warning. Add `DEFAULT_ROUTE`.
4. **`wait_for_output=True` and the node is never re-triggered** → the workflow finishes with no output and the downstream nodes are skipped, with nothing logged.
5. **Schema mismatch from type hints** → rejected at construction (rule 8).
6. **`mode='chat'` agent in the middle of a chain** → rejected (rule 9).
7. **`from google.adk import START`** → `ImportError`.
8. **Side effects on resume** → at-least-once execution. Make tools idempotent.
9. **Broad `except Exception` in tools** swallows retry and HITL signals.
10. **Parent dynamic node without `rerun_on_resume=True`** → its interrupts do not resume correctly.
11. **More than one `Event.output` per node** → runtime error.
12. **Large blobs in `state`** → use artifacts instead.
13. **Prefixed state keys skip `state_schema`.** A typo in `temp:` is not caught.

---

## 13. Interview questions (crisp answers)
1. **What changed architecturally in ADK 2.0?** ADK moved from a hierarchical agent executor to a graph execution engine. Agents, tools, and functions are all `BaseNode`s. `BaseAgent` subclasses `BaseNode`.
2. **How do you branch?** A node yields `Event(route=v)` with a str, int, or bool value (or a list of them). A routing map `{v: node}` dispatches. `DEFAULT_ROUTE` (`"__DEFAULT__"`) catches the rest.
3. **How do you join parallel branches?** Use `JoinNode`. It waits for all predecessors and emits a dict keyed by node name.
4. **Why can't a graph loop forever by accident?** Unconditional cycles are rejected at construction. Conditional ones are allowed but *not bounded*, and the developer owns the exit.
5. **How does resume work?** By replaying the session event log for the invocation. Completed nodes fast-forward and the interrupted node re-runs. `is_resumable` adds durability and cross-call resume. It does not switch resume on.
6. **How does HITL work on the wire?** `RequestInput` becomes a long-running `functionCall` with an `interruptId`. The client replies with `functionResponse(name="adk_request_input", id=...)`.
7. **`rerun_on_resume` true vs false?** False: the node completes with the human reply as its output. True: the node runs again from the top and reads `ctx.resume_inputs`.
8. **Graph vs dynamic workflow?** Graphs are declarative, validated, and visualisable. Dynamic workflows are code (`ctx.run_node`, `while`, `gather`) with automatic per-node checkpointing through deterministic run ids.
9. **How do you type state?** Set `state_schema=PydanticModel` on the Workflow or a node. A bad write raises `StateSchemaError` (a `TypeError`).
10. **What is a verifier per step in ADK 2.0?** Several things: a typed `output_schema` on the producing node, a function or `ClassifierNode` node that routes pass or fail, `RetryConfig` for transient errors, and `require_confirmation` for human gating.
11. **What happens with two outputs at the end?** The run fails with `WorkflowConfigurationError` because it cannot choose which output becomes the workflow's output.
12. **How do you see the graph?** Run `adk web`. The DevServer serves DOT from `/dev/apps/{app}/graph`, coloured by node status.

---

## 14. Slide ideas (with animations)
1. **"From tree to graph"**: a 1.x agent tree morphs into a 2.0 node graph. *Animation:* the tree edges straighten into directed edges and agent boxes shrink into `BaseNode` circles, with function and tool nodes popping in between them.
2. **Chain-tuple decoder**: show `(START, a, (b, c), join, d)`. *Animation:* each tuple element highlights in turn while the matching edge draws itself, and the inner tuple splits into two parallel arrows.
3. **Routing map**: a router node emits a coloured `route` token. *Animation:* the token travels and only the matching edge lights up. An unmatched token fades out, which teaches the silent-stop failure, until a `DEFAULT_ROUTE` edge appears to catch it.
4. **JoinNode barrier**: three branches finish at different times. *Animation:* outputs pile up at a gate labelled with predecessor names. The gate opens only when all three have arrived and emits one dict.
5. **Generator–critic loop**: headline loop. *Animation:* the critic's "unrelated" route draws a back-edge, the iteration counter `@1 → @2 → @3` ticks on the `node_info.path` label, and the loop exits on "tech-related".
6. **HITL on the wire**: a sequence diagram of workflow, client, and human. *Animation:* a `functionCall{interruptId: fc-1}` appears, the timeline freezes with a pause icon, the human types "shorter", and a `functionResponse adk_request_input` resumes the flow at the next node.
7. **Resume by replay**: an event log scrolls past. *Animation:* completed nodes flash green and skip ("fast-forward"), the interrupted node turns purple (WAITING) and then amber (RUNNING). The `is_resumable` switch toggles a "checkpoint" stamp onto the log.
8. **Typed state guardrail**: `state_schema` as a bouncer. *Animation:* writes of `topic` and `depth` pass, `budget` is rejected with `StateSchemaError`, and `temp:scratch` slips through a side door labelled "prefix bypass".
9. **adk web live colours**: the graphviz DOT render. *Animation:* nodes change colour in step with the event stream (green, amber, red, purple), and clicking an event re-highlights the graph through the `/events/{id}/graph` endpoint.
10. **Release timeline 2.0 → 2.13**: a horizontal timeline from May 19 to Oct 22, 2026. *Animation:* milestones drop in one by one: GA, Workflow-as-Tool, HITL for NodeTool, YAML graphs, abort_signal, require_confirmation, ClassifierNode.

---

## 15. Codelabs / sessions
I could not verify these because web search was exhausted. Treat all of them as **[UNVERIFIED]** and check them before putting them on a slide. To find them, search codelabs.developers.google.com for "ADK 2.0 workflow" and "graph". Do not cite invented titles. The verified hands-on material is the runnable samples under `github.com/google/adk-python/tree/main/contributing/samples/workflows/`: `sequence`, `route`, `loop`, `loop_self`, `loop_config` (YAML), `fan_out_fan_in`, `dynamic_fan_out_fan_in`, `nested_workflow`, `parallel_worker`, `request_input`, `request_input_rerun`, `request_input_advanced`, `retry`, `state`, `node_as_tool`, `classifier_node`, `dynamic_nodes`, `auth_oauth`, `auth_api_key`, `message`, `multi_triggers`, `use_as_output`, `agent_in_workflow`. Each one has `tests/*.json` event goldens.

## Source URLs
- https://adk.dev/2.0/ · https://adk.dev/graphs/ · https://adk.dev/graphs/routes/ · https://adk.dev/graphs/data-handling/ · https://adk.dev/graphs/human-input/ · https://adk.dev/graphs/dynamic/ · https://adk.dev/runtime/resume/ · https://adk.dev/visual-builder/ · https://adk.dev/live/workflows/ · https://adk.dev/workflows/collaboration/
- https://github.com/google/adk-python/blob/main/CHANGELOG.md · https://github.com/google/adk-python/releases
- https://github.com/google/adk-python/tree/main/src/google/adk/workflow
- https://github.com/google/adk-python/tree/main/docs/guides/workflow (graph, workflow, base_node, node, join_node, retry_config, parallel_worker, dynamic_nodes)
- https://github.com/google/adk-python/blob/main/.agents/skills/adk-architecture/references/architecture-workflow-resumability.md
- https://github.com/google/adk-python/blob/main/src/google/adk/cli/dev_server.py · .../cli/utils/graph_visualization.py
- https://github.com/google/adk-python/tree/main/contributing/samples/workflows
