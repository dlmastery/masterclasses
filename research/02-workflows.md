# 02 — Workflow Orchestration in ADK 2.0

Research date: 2026-10-23. Most facts come from the docs at adk.dev, which absorbed google.github.io/adk-docs; the old URLs return a 301 to adk.dev. The rest come from `google/adk-python` source on `main`, the official samples, and the official ADK 2 codelab. Anything I could not confirm is marked [UNVERIFIED].

---

## 1. Version and timeline facts (verified)

| Item | Value | Source |
|---|---|---|
| ADK Python v2.0.0 GA | **May 19, 2026** | https://adk.dev/2.0/ |
| ADK Go v2.0.0 GA | **June 30, 2026** (new module path `google.golang.org/adk/v2`) | https://adk.dev/2.0/ |
| ADK TypeScript v2.0.0 GA | **August 21, 2026** | https://adk.dev/2.0/ |
| Latest adk-python release | **v2.13.0, published 2026-10-23** (v2.12.0 on 10-13, v2.11.0 on 10-02, v2.9.0 on 09-10). The 1.x line is still patched: v1.39.1 on 08-27 | GitHub releases API, google/adk-python |
| Staying on 1.x | `pip install "google-adk~=1.0"` | https://adk.dev/2.0/ |
| Codelab pin | `google-adk==2.3.0`, verified on 2.3.0 and 2.0.0b1 | codelab below |

Key quote, from https://adk.dev/2.0/:
> "The ADK 2.0 release introduces the Workflow Runtime, transitioning ADK from a hierarchical agent executor to a graph-based execution engine. In this new architecture, your Agents, Tools, and Functions are evaluated as individual *nodes* within a workflow graph."

ADK 2.0 has three ways to compose work (https://adk.dev/graphs/):
1. **Graph-based workflows.** A declarative graph of nodes and edges with explicit routing.
2. **Dynamic workflows.** Orchestration written in your own code with `ctx.run_node()`: loops, conditionals, recursion.
3. **Collaborative workflows.** A coordinator `Agent` with `sub_agents` that each run in a `mode` (`chat`, `task` or `single_turn`).

The 1.x template workflows (`SequentialAgent`, `ParallelAgent`, `LoopAgent`) and custom `BaseAgent` still exist, but they are deprecated (see §3).

---

## 2. Public Python API surface (verified from source)

`google/adk/__init__.py` exports exactly `Agent, Context, Event, Runner, Workflow`, loaded lazily.

`google/adk/workflow/__init__.py` exports:
`BaseNode, DEFAULT_ROUTE, Edge, FunctionNode, JoinNode, Node, NodeTimeoutError, RetryConfig, START, Workflow, node`.

Human input: `from google.adk.events import RequestInput`. Its fields are `interrupt_id`, `payload`, `message` and `response_schema`.

**`Workflow(BaseNode)`.** Fields are `name`, `edges: list[EdgeItem]`, `rerun_on_resume=True` and `max_concurrency: int | None`. The `max_concurrency` docstring reads: "Maximum parallel graph-scheduled nodes. None or <= 0 means unlimited. Only applies to nodes triggered by graph edges. Dynamic nodes (via ctx.run_node()) are excluded — they are awaited inline by their parent and throttling them would cause deadlock." The class docstring reads: "`_run_impl()` IS the graph orchestration loop: SETUP: build graph, seed triggers / LOOP: schedule ready nodes via NodeRunner, handle completions / FINALIZE: collect terminal outputs." Source: `src/google/adk/workflow/_workflow.py`.

**`@node(...)` keyword arguments** (from `_node.py`): `name`, `rerun_on_resume`, `retry_config`, `timeout`, `parallel_worker=False`, `max_parallel_workers`, `auth_config`, `require_confirmation` (a bool or a predicate), and `parameter_binding: Literal['state','node_input'] = 'state'`.
- `parameter_binding='state'` is the default. It binds function parameters **from `ctx.state` by name**. In the samples, `def guess_number(target_number: int)` and `def send_email(draft: str)` read state keys this way.
- `require_confirmation` turns on `rerun_on_resume=True` automatically.

**`RetryConfig` fields and defaults** (`_retry_config.py`):

| Field | Default |
|---|---|
| `max_attempts` | 5, counting the first attempt |
| `initial_delay` | 1.0 s |
| `max_delay` | 60.0 s |
| `backoff_factor` | 2.0 |
| `jitter` | 1.0 |
| `exceptions` | `None`, meaning retry on all exceptions |

**`Context.run_node`** (`agents/context.py`):
```python
async def run_node(self, node: NodeLike, node_input: Any = None, *,
    use_as_output: bool = False, run_id: str | None = None,
    use_sub_branch: bool = False, override_branch: str | None = None,
    override_isolation_scope: str | None = None, raise_on_wait: bool = False) -> Any
```
The docstring warns: "Always `await` this method directly. Wrapping it in `asyncio.create_task()` means the task runs unsupervised — errors are silently swallowed and the task is not cancelled if the parent node is interrupted (e.g. via HITL)."

Other `Context` properties: `state`, `node_path`, `run_id`, `attempt_count`, `resume_inputs`.

**Event schema (Python).** 2.0 adds the `node_info` and `output` fields. Nodes emit `Event(output=..., message=..., state=..., route=...)`.

---

## 3. Template workflow agents (1.x model, still shipping, deprecated)

### Deprecation status (verified in source on `main`)
Each class carries `@deprecated(...)`:
> "SequentialAgent is deprecated in favor of Workflow and will be removed in a future version. Workflow cannot yet be used as an LlmAgent sub-agent."

`ParallelAgent` and `LoopAgent` carry the same text. The docs add: "Starting in ADK 2.0 for Python and Go, templated workflows have been superseded by more flexible workflow structures." In TypeScript 2.0, constructing one "logs a deprecation warning once per class, per process."

Teaching point: the caveat "Workflow cannot yet be used as an LlmAgent sub-agent" is the main reason a team might still pick the template agents.

### Execution semantics (from https://adk.dev/agents/custom-agents/ and the workflow-agent pages)

**SequentialAgent**
- Runs `sub_agents` in list order.
- Passes the **same `InvocationContext`** to each one, so they share session state, including `temp:`.

**ParallelAgent**
- Starts every child's `run_async()` concurrently. In current source the children are merged with `asyncio.TaskGroup` on Python 3.11+.
- Gives each child its own branch, `ParentName.ChildName`, built by `_BranchPath.create_sub_branch(...)` in `parallel_agent.py`.
- Children see no conversation history from each other: "no automatic sharing of conversation history or state between these branches."
- They still share one `session.state`, so each child should write to a distinct `output_key`.
- Events can arrive interleaved.

**LoopAgent**
- Runs `sub_agents` in order and repeats.
- Stops when `max_iterations` is reached or when any event has `actions.escalate == True`.
- Source loop (`loop_agent.py`): `while (max_iterations is None or times_looped < max_iterations) and not (should_exit or pause_invocation)`. A pause (HITL or long-running tool) also ends the loop without emitting end-of-agent. The docstring says "A value of zero or less runs the sub-agents no times at all."

### State passing: `output_key` plus `{state}` templating
```python
# https://adk.dev/agents/custom-agents/ (conceptual example)
from google.adk.agents import SequentialAgent, LlmAgent
step1 = LlmAgent(name="Step1_Fetch", output_key="data")  # Saves output to state['data']
step2 = LlmAgent(name="Step2_Process", instruction="Process data from {data}.")
pipeline = SequentialAgent(name="MyPipeline", sub_agents=[step1, step2])
```
- `{key?}` is the optional form: it gives an empty value instead of an error when the key is missing. Used in the 2.0 `loop` sample: `The feedback: {feedback?}`.
- State prefixes: `app:` is app-wide, `user:` is per user, `temp:` is discarded at the end of the invocation, and no prefix means session lifetime.

### escalate / exit_loop
Built-in tool, `google/adk/tools/exit_loop_tool.py`:
```python
def exit_loop(tool_context: ToolContext) -> None:
  """Exits the loop.
  Call this function only when you are instructed to do so.
  """
  tool_context.actions.escalate = True
  tool_context.actions.skip_summarization = True
```
The doc pattern is a writer, then `LoopAgent([critic, refiner], max_iterations=5)` inside a `SequentialAgent`. The refiner gets `tools=[exit_loop]` and is told to call it only when the critique equals exactly `"No major issues found."`. Source: https://adk.dev/agents/workflow-agents/loop-agents/

A custom checker agent can escalate instead of using the tool:
```python
# https://adk.dev/agents/custom-agents/
class CheckCondition(BaseAgent):
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        status = ctx.session.state.get("status", "pending")
        is_done = (status == "completed")
        yield Event(author=self.name, actions=EventActions(escalate=is_done))

poller = LoopAgent(name="StatusPoller", max_iterations=10,
                   sub_agents=[process_step, CheckCondition(name="Checker")])
```

### Custom `BaseAgent` with `_run_async_impl`
- Signature: `async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]`.
- The body calls children with `async for event in self.child.run_async(ctx): yield event`.
- It reads and writes `ctx.session.state`.
- The canonical example is StoryFlowAgent: a generator, then a critic/reviser loop, then post-processing, then a conditional regeneration when `tone_check_result == "negative"`. Source: https://adk.dev/agents/custom-agents/

**Conflicting 2.0 guidance (flag this on a slide).**
- The migration page (https://adk.dev/2.0/) says `BaseAgent` now subclasses `BaseNode` and that custom overrides of `_run_async_impl()` "are no longer the correct way to drive execution. The Workflow Graph engine completely bypasses these legacy overrides … silently ignored." It tells you to use `BeforeAgentCallback` and `AfterAgentCallback`.
- Current `base_agent.py` on `main` contradicts this. `class BaseAgent(BaseNode, abc.ABC)` still runs `run_async()`, then `_run_with_lifecycle(parent_context, self._run_async_impl)`, and the node entry `_run_impl()` delegates to `run_async()`. `LoopAgent` itself is written with `_run_async_impl`.
- So "bypassed" holds only in specific engine paths. [UNVERIFIED which paths; test before you rely on it.]
- Safe advice: write new orchestration as a `Workflow` or a dynamic `@node`, not as a `BaseAgent` subclass.

---

## 4. The 2.0 graph workflow model

### Concepts
- **Node.** One of: an `Agent` (LlmAgent), a plain function (wrapped automatically as a `FunctionNode`), a Tool, a human-input step, or another `Workflow`, since a Workflow is itself a `BaseNode`.
- **Edge.** A row in `edges`.
  - A tuple starting with `"START"` (or the `START` constant) is a chain: each node runs once, in order.
  - A `(source, {route_value: target, ...})` row is a conditional edge.
- **Data flow.** A node's return value, or its `Event(output=...)`, becomes the next node's `node_input`. **No session-state writes are needed.**
- **Constraint.** An `LlmAgent` used as a graph node must run in `single_turn` mode (the default) or `task` mode. Per the collaboration page, `task` mode is "disabled for use in graph-based workflows in ADK Python v2.0.0."

### Sequence (the docs' get-started example)
```python
# https://adk.dev/graphs/
from google.adk import Agent, Workflow, Event
from pydantic import BaseModel

city_generator_agent = Agent(name="city_generator_agent", model="gemini-flash-latest",
    instruction="Return the name of a random city. Return only the name, nothing else.")

class CityTime(BaseModel):
    time_info: str
    city: str

def lookup_time_function(node_input: str):
    return CityTime(time_info="10:10 AM", city=node_input)

city_report_agent = Agent(name="city_report_agent", model="gemini-flash-latest",
    input_schema=CityTime,
    instruction="It is {CityTime.time_info} in {CityTime.city} right now.")

root_agent = Workflow(name="root_agent",
    edges=[("START", city_generator_agent, lookup_time_function, city_report_agent)])
```
Inside an agent instruction there are three placeholder forms:
- `{Class.field}` reads a field from this node's input.
- `<Class.field from source_node>` reads a field from the output of a named predecessor.
- `{state_key}` reads session state.

The docs say "The `Class.` prefix is documentation only; resolution uses the field name after the dot." Source: https://adk.dev/graphs/data-handling/

### Conditional routing
```python
# https://adk.dev/graphs/
def router(node_input: str):
    routes = [r.strip() for r in node_input.split(",")]
    return Event(route=routes)          # list => dispatch to EVERY matching branch

root_agent = Workflow(name="routing_workflow", edges=[
    ("START", process_message, router),
    (router, {"BUG": response_1_bug,
              "CUSTOMER_SUPPORT": response_2_support,
              "LOGISTICS": response_3_logistics}),
])
```
- Route values can be strings, numbers or booleans.
- `DEFAULT_ROUTE` matches when no other route on that source matches.
- `route` is independent of `output`, so one event can choose a branch and carry a payload, e.g. `Event(output=node_input, route="HOT")`, as in the codelab.

### Fan-out / fan-in with JoinNode
```python
# contributing/samples/workflows/fan_out_fan_in/agent.py
from google.adk import Event, Workflow
from google.adk.workflow import JoinNode

def make_uppercase(node_input: str): return node_input.upper()
def count_characters(node_input: str): return len(node_input)
def reverse_string(node_input: str): return node_input[::-1]

join_node = JoinNode(name="join_for_results")

async def aggregate(node_input: dict):
    yield Event(message=f"Upper: {node_input['make_uppercase']} | "
                        f"Len: {node_input['count_characters']} | Rev: {node_input['reverse_string']}")

root_agent = Workflow(name="root_agent", edges=[(
    "START", (make_uppercase, count_characters, reverse_string), join_node, aggregate)])
```
- A tuple of nodes inside a chain means fan-out.
- The docs' other form uses several `("START", task_X, join)` rows.
- `JoinNode` is a barrier: it waits for every predecessor, then passes on a **dict keyed by predecessor node name**.
- Docs caution: "every node that feeds a join has an output of its own", and add a retry config to any node that can fail. Otherwise "the resulting failure appears downstream, away from the node that caused it."

### Parallel worker (map over a list, sized at runtime)
```python
# contributing/samples/workflows/parallel_worker/agent.py
@node(parallel_worker=True)
def make_upper_case(node_input: str):
  yield node_input.upper()

explain_topic = Agent(name="explain_topic", parallel_worker=True,
    instruction='Explain how the following topic relates to "{topic}".',
    output_schema=TopicExplanation)

root_agent = Workflow(name="root_agent", edges=[("START",
    process_input, find_related_topics, make_upper_case, explain_topic, aggregate)])
```
- `find_related_topics` returns `list[str]`. Each worker runs once per item, and `aggregate` receives a list.
- The TypeScript docs say default worker concurrency is 8 (`maxParallelWorkers`). [UNVERIFIED for Python's `max_parallel_workers` default.]

### Loops as back-edges
```python
# contributing/samples/workflows/loop/agent.py  (generator-critic)
def route_headline(node_input: Feedback):
  return Event(route=node_input.grade)

root_agent = Workflow(name="root_agent", edges=[
    ("START", process_input, generate_headline, evaluate_headline, route_headline),
    (route_headline, {"unrelated": generate_headline}),   # back-edge
])
```
- A self-loop works too: `(guess_number, {'guessed_wrong': guess_number})` in the `loop_self` sample.
- The engine "re-activates that node with a fresh lifecycle on each iteration."
- Docs caution: "A graph cycle is not bounded automatically." There is no `max_iterations` on a graph cycle. Bound it in the router, or use a dynamic workflow.
- Graph equivalent of `escalate`: route to a terminal node, or emit no route at all.

### Nested workflows
A `Workflow` can be a branch target, e.g. `(router, {"RUN_WORKFLOW_B": workflow_B, ...})`. While it runs, each inner node's events bubble up to the parent for traceability. When it finishes, the output of its terminal node becomes the output of the nested node.

### Execution flow in words (for a diagram)
1. `Runner.run_async(user_id, session_id, new_message)` starts an **invocation** (`invocation_id`).
2. **SETUP.** `Workflow._run_impl` compiles `edges` into a `Graph` and seeds triggers from `START`.
3. **LOOP.** Ready nodes are scheduled through `NodeRunner`, concurrently, up to `max_concurrency`. Each node yields events:
   - `output` goes to its successors;
   - `message`/`content` is shown to the user and not passed on;
   - `state` deltas are committed with that node's events;
   - `route` picks the conditional edges.
4. **Fan-in.** `JoinNode` keeps track of which predecessors have arrived (`join_arrivals`) and fires once all are in.
5. **Checkpoint.** The engine emits a node checkpoint after each node (`_emit_node_checkpoint`).
6. **Pause.** On interrupt (`RequestInput`, confirmation, auth), the invocation ends and leaves pending interrupt ids.
7. **FINALIZE.** Outputs of terminal nodes are collected and the end-of-agent event is emitted.

Method names in steps 2–7 come from `_workflow.py`.

---

## 5. Dynamic workflows: `ctx.run_node()`

```python
# https://adk.dev/graphs/dynamic/  (generate -> lint -> fix loop)
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
Parallel version:
```python
@node(rerun_on_resume=True)
async def parallel_supervisor(ctx: Context, node_input: list, real_node: BaseNode):
    tasks = [ctx.run_node(real_node, item) for item in node_input]  # don't await yet
    return await asyncio.gather(*tasks)
```
Rules:
- An orchestrator that calls `ctx.run_node` **must** set `rerun_on_resume=True`.
- **Automatic checkpointing.** "Successful sub-nodes are automatically skipped when resuming the workflow." Only failed or interrupted parallel workers run again.
- **Execution IDs** are deterministic: parent ID plus a counter, as sequential strings `"1"`, `"2"`, ….
- A custom `run_id` (e.g. `f"order-{order.order_id}"`) must contain at least one non-numeric character. The docs warn against using custom IDs.
- `use_as_output=True` makes the child's output the parent's output. See the `use_as_output` sample.
- The codelab's L4b level shows **recursive** spawning with a depth guard (`@node(parallel_worker=True, rerun_on_resume=True)`).

---

## 6. Human-in-the-loop, checkpoints and resume

### RequestInput (handoff mode, the default `rerun_on_resume=False`)
```python
# https://adk.dev/graphs/human-input/
from google.adk.events import RequestInput
from google.adk import Workflow

def step1():
  yield RequestInput(message="Enter a number:")   # pauses the workflow
def step2(node_input):
  return node_input * 2                            # receives the human reply

root_agent = Workflow(name="root_agent", edges=[('START', step1, step2)])
```
- With `rerun_on_resume=False`, the reply goes to the successor and the interrupted node does not run again.
- `response_schema` does **not** reshape the reply. Docs: "The reply must already be in that format."

### Re-entry mode: approve / reject / revise loop
```python
# contributing/samples/workflows/request_input_rerun/agent.py
@node(rerun_on_resume=True)
def human_review(draft: str, ctx: Context):
  interrupt_id = f"human_review_{ctx.invocation_id}_{ctx.run_id}"
  resume_input = ctx.resume_inputs.get(interrupt_id)
  if not resume_input:
    yield RequestInput(interrupt_id=interrupt_id,
        message=f"Review draft: 'approve', 'reject', or feedback.\n---\n{draft}")
    return
  if resume_input == "reject":    yield Event(route="rejected")
  elif resume_input == "approve": yield Event(route="approved")
  else: yield Event(state={"feedback": resume_input}, route="revise")
# edges: (human_review, {"revise": draft_email, "approved": send_email, "rejected": reject_email})
```

### Tool confirmation, at the LlmAgent level (marked Experimental, since Python v1.14.0)
- `FunctionTool(reimburse, require_confirmation=True)` asks for a plain yes/no.
- `require_confirmation=` also accepts a predicate, e.g. `async def confirmation_threshold(amount, tool_context) -> bool: return amount > 1000`.
- `tool_context.request_confirmation(hint=..., payload=...)` handles structured answers.
- Source: https://adk.dev/tools-custom/confirmation/

### Long-running tools
```python
# https://adk.dev/tools-custom/function-tools/
from google.adk.tools import LongRunningFunctionTool
def ask_for_approval(purpose: str, amount: float) -> dict: ...
long_running_tool = LongRunningFunctionTool(func=ask_for_approval)
```
Flow:
1. The LLM calls the tool.
2. The tool returns an initial result, such as a ticket id. The run **pauses**, and the event lists the call in `event.long_running_tool_ids`.
3. The client polls the external system.
4. The client sends a `types.Part(function_response=...)` back through `runner.run_async(..., new_message=...)`.

Docs warn: the tool should *manage* the long job, "not perform" it. If resume is enabled, the response must include the original `invocation_id`.

### Resume (1.x, Python v1.16.0+)
```python
app = App(name='my_resumable_agent', root_agent=root_agent,
          resumability_config=ResumabilityConfig(is_resumable=True))
# resume:
async for event in runner.run_async(user_id='u_123', session_id='s_abc',
                                    invocation_id='invocation-123'): ...
```
- `POST /run_sse` with `invocation_id` also resumes. Resuming from ADK Web or the CLI is not supported.
- Per-agent behaviour:
  - Sequential resumes at `current_sub_agent`.
  - Loop uses `current_sub_agent` plus `times_looped`.
  - Parallel reruns only the children that had not finished.
- **Tools run at least once**, so make side effects idempotent (purchases!).
- Do not change the workflow between the stop and the resume.
- Custom agents need `BaseAgentState`, `ctx.set_agent_state(...)`, `self._create_agent_state_event(ctx)` and `end_of_agent=True`.
- Source: https://adk.dev/runtime/resume/

In 2.0 Workflows, checkpoint and resume are built in: `Workflow.rerun_on_resume=True`, node checkpoints, and replay of finished children. [UNVERIFIED: whether `ResumabilityConfig` is still required on the `App` for 2.0 Workflows.]

### Retries and error handling (2.0)
```python
# contributing/samples/workflows/retry/agent.py
@node(retry_config=RetryConfig(max_attempts=5, initial_delay=1))
def get_weather(ctx: Context) -> str:
  yield Event(message=f"Getting weather... attempt {ctx.attempt_count}")
  if random.random() < 0.7:
    raise HTTPError(url="http://mock-api.example.com", code=500, msg="ISE", hdrs={}, fp=None)
  yield "sunny"
```
Migration rules (https://adk.dev/2.0/):
- Don't wrap tools in `except Exception:`. That hides the failure from retries.
- Never catch `BaseException`, because it traps `NodeInterruptedError` and breaks HITL pauses.
- Don't call `session.events.append(...)` or `enqueue_event`. Yield events instead.

---

## 7. Events, invocation and branch (semantics)

- `invocation_id` is the ID of one user-request-to-final-response cycle. Every event in that cycle shares it.
- `branch` is a hierarchy path such as `Parent.Child`. ParallelAgent children and `task`/`single_turn` collaborators run on isolated branches, so "each agent only sees events from its own branch when building context for AI model calls."
- Control signals: `event.actions.escalate` (end a loop), `event.actions.transfer_to_agent`, `event.actions.state_delta`, `event.actions.artifact_delta`.
- `event.is_final_response()` filters out tool calls and partial chunks.
- New in 2.0: `node_info` (scheduler metadata such as the path) and `output`.
  - The TypeScript event also has `route` and `isolationScope`.
  - The Go event also has `IsolationScope`, `Routes`, `RequestedInput`, `Output` and `NodeInfo`. Before Go v2.2.0 these were serialized under Go field names, so validators must accept both forms.
- One output per node execution. The two doc pages disagree on what happens with two outputs: the Python caution says two `Event.output` yields cause "a runtime error", while the generic caution says each one "overwrites the previous one". Emit a single output either way. [UNVERIFIED which behaviour current Python has.]

---

## 8. Collaborative mode table (2.0)

| | `chat` (default) | `task` | `single_turn` |
|---|---|---|---|
| HITL | full | clarification only | none |
| Return to parent | manual (`transfer_to_agent`) | automatic (`finish_task`) | automatic, with the result |
| Parallel | no | no | yes |

- The coordinator auto-injects delegation tools named after each sub-agent.
- Task-mode agents must be leaf agents.
- Do not set `mode` on the root agent.
- Source: https://adk.dev/workflows/collaboration/

---

## 9. Choosing a mechanism

| Need | 1.x way | 2.0 way |
|---|---|---|
| Fixed order | `SequentialAgent` + `output_key` | `Workflow(edges=[("START", a, b, c)])` |
| Concurrent independent tasks | `ParallelAgent` (separate branches, shared state) | tuple fan-out + `JoinNode`, or `parallel_worker=True` |
| Iterate until good | `LoopAgent(max_iterations=…)` + `exit_loop`/escalate | back-edge route, or a `while` loop in a dynamic `@node` |
| If/else | custom `BaseAgent._run_async_impl` | `Event(route=…)` + dict edge + `DEFAULT_ROUTE` |
| Human approval | `LongRunningFunctionTool` / `require_confirmation` | `RequestInput` node (`rerun_on_resume` handoff or re-entry) |
| Crash recovery | `ResumabilityConfig(is_resumable=True)` | built-in node checkpoints + `RetryConfig` |

Third-party claim, [UNVERIFIED, not official]: ecorpit.com reports that an ADK 2.0 workflow "cut a benchmark run from 5,152 to 2,265 tokens" compared with an LLM loop (https://ecorpit.com/adk-2-0-workflows-vs-autonomous-agents-guide-2026/). Cite only as anecdote.

Real-world example (official): the codelab's **Marathon Race Day Coach** begins with a mega-prompt that "invents its own weather data". It then replaces each step with real functions, a JoinNode fan-out over weather, course and fitness data, a temperature router (HOT ≥70°F, COLD ≤40°F), specialist sub-agents, and recursive research. I found no named production customer case studies for 2.0 workflows. [UNVERIFIED]

---

## 10. Sources

**Docs (adk.dev; `/index.md` serves raw markdown)**
- ADK 2.0 overview and migration — https://adk.dev/2.0/
- Graph-based agent workflows — https://adk.dev/graphs/
- Build graph routes for agent workflows — https://adk.dev/graphs/routes/
- Data handling for agent workflows — https://adk.dev/graphs/data-handling/
- Human input for agent workflows — https://adk.dev/graphs/human-input/
- Dynamic agent workflows — https://adk.dev/graphs/dynamic/
- Build collaborative agent teams — https://adk.dev/workflows/collaboration/
- Multi-agent workflow patterns — https://adk.dev/workflows/patterns/
- Sequential / Loop / Parallel template workflow agent — https://adk.dev/agents/workflow-agents/sequential-agents/ , …/loop-agents/ , …/parallel-agents/
- Custom agents — https://adk.dev/agents/custom-agents/
- Resume stopped agents — https://adk.dev/runtime/resume/
- Function tools (long-running) — https://adk.dev/tools-custom/function-tools/
- Get action confirmation for ADK Tools — https://adk.dev/tools-custom/confirmation/
- Events — https://adk.dev/events/

**Codelab**
- "ADK 2 Orchestration: Graph, Collaborative & Dynamic Workflows" (~50 min) — https://codelabs.developers.google.com/adk2/instructions

**Repos and samples**
- google/adk-python — https://github.com/google/adk-python
- Workflow samples, https://github.com/google/adk-python/tree/main/contributing/samples/workflows. The folder holds: agent_in_workflow, auth_api_key, auth_oauth, classifier_node, dynamic_fan_out_fan_in, dynamic_nodes, fan_out_fan_in, loop, loop_config, loop_self, message, multi_triggers, nested_workflow, node_as_tool, node_output, parallel_worker, request_input, request_input_advanced, request_input_rerun, retry, route, sequence, state, use_as_output.
- Go workflow examples — https://github.com/google/adk-go/tree/main/examples/workflow
- TypeScript workflow samples — https://github.com/google/adk-js/tree/main/samples/workflows
- Go 2.0 announcement — https://developers.googleblog.com/en/announcing-adk-go-20/

---

## 11. Slide ideas (8)

1. **"From tree to graph: the 2.0 Workflow Runtime."** Morph animation: the 1.x agent tree (root, then Sequential/Parallel/Loop) collapses into a node-and-edge graph. Agents, Tools and Functions turn into uniform node boxes. Quote the adk.dev/2.0 line and show the GA dates as a timeline: May 19, Jun 30, Aug 21.
2. **"Three ways to orchestrate."** A three-column card: Graph (declarative), Dynamic (`ctx.run_node` code), Collaborative (`mode`). Each column has a code thumbnail and a "use when" line. Template agents appear as a greyed, deprecated fourth column.
3. **"Sequential then and now."** Split screen. Left: `SequentialAgent` + `output_key` + `{data}`, with a state-dict panel filling in. Right: `("START", a, b, c)`, with `node_input` arrows carrying values and no state. Animate data packets moving along the edges.
4. **"Routing with Event(route=…)."** Animated classifier: one packet hits the router and splits along matching dict keys. Show the list-route case (multi-dispatch) and `DEFAULT_ROUTE` as a catch-all lane.
5. **"Fan-out / fan-in."** Three parallel lanes run at different speeds and wait at a `JoinNode` gate, which turns green when all arrive. Show the output dict `{make_uppercase:…, count_characters:…, reverse_string:…}`. Contrast with ParallelAgent's branch labels `Parent.Child` over a shared state store.
6. **"Loops: escalate vs back-edge vs while."** Three mini-diagrams: LoopAgent with `exit_loop` setting `escalate=True` (counter to `max_iterations`), a graph back-edge (`unrelated` goes to `generate_headline`) with the warning "cycles are not bounded automatically", and a dynamic `while check_resp.findings`.
7. **"Pause, approve, resume."** Timeline: the workflow runs, `RequestInput` raises a pause banner and the invocation ends, the human replies (`resume_inputs[interrupt_id]`), then the node re-runs (`rerun_on_resume=True`) and routes to approve, reject or revise. A side panel shows handoff vs re-entry, with `LongRunningFunctionTool` and `require_confirmation` as the LLM-level options.
8. **"Durability: checkpoints, retries, at-least-once."** A crash animation mid-graph. On resume, completed nodes show as ghosted and replayed from checkpoint, and only failed nodes re-run. Overlay the `RetryConfig` backoff curve (1s, 2s, 4s… capped at 60s) and a warning card: make tools idempotent, and never catch `BaseException`.
9. **"Migration gotchas."** Checklist slide: Event schema adds `node_info`/`output`, don't append events by hand, don't swallow exceptions, the `_run_async_impl` caveat, and "Workflow cannot yet be used as an LlmAgent sub-agent."
