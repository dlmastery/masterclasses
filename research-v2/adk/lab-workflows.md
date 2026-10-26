# Hands-on labs: ADK 2.0 Workflow graphs (google-adk 2.13.0)

Research date: 2026-10-23. Subtopic: the Workflow graph API. That covers nodes, edges, conditional routing, fan-out/fan-in, loops, `@node` and `ctx.run_node` dynamic nodes, the task/chat/single_turn modes, `RequestInput` human-in-the-loop, `RetryConfig`, checkpoint/resume, and YAML config.

This file does not repeat the API survey in `research/02-workflows.md` or `research-adk-platform/04-adk2-workflows-graph.md`. It adds nine runnable labs. Each one has verified signatures, exact error strings and the exact resume protocol. It also adds new facts found in source (section 0) and arXiv papers from 2026-07-23 to 2026-10-23 (section 10).

## Method and verification status

- **Versions (PyPI JSON, fetched 2026-10-23).** `google-adk` **2.13.0** was uploaded 2026-10-23T18:26:31. It sets `requires_python >=3.11` and depends on `google-genai>=2.30,<3`. The latest `google-genai` is **2.33.0**.
- **Source.** All API claims were checked against a local clone of `google/adk-python` at tag **v2.13.0** (commit `d68ca857`). Citations use the form `src/google/adk/<path>:<line>`. Browse the same file at `https://github.com/google/adk-python/blob/v2.13.0/<path>`.
- **No code was run.** `pip install` is blocked on this machine. Every "Expected output" block is therefore **illustrative**. It is built from the source's print and format code (`cli/cli.py:365-415`) and from the sample goldens (`contributing/samples/workflows/*/tests/*.json`). Model text in those blocks is invented for the illustration. The event structure in them is not invented.
- **Base samples.** Each lab adapts an official sample from `contributing/samples/workflows/<name>/agent.py` at v2.13.0. Where a lab follows the official codelab it cites "ADK 2 Orchestration: Graph, Collaborative & Dynamic Workflows", https://codelabs.developers.google.com/adk2/instructions. That codelab is pinned to 2.3.0.
- **[UNVERIFIED]** marks anything I derived from source reading where no sample or test exercises it.

Common setup for every lab:

```bash
python -m venv .venv && source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install "google-adk==2.13.0"                          # pulls google-genai>=2.30,<3 (2.33.0 today)
# Gemini API (AI Studio) — put these in <agent_folder>/.env or export them:
export GOOGLE_GENAI_USE_ENTERPRISE=FALSE      # 2.x name; GOOGLE_GENAI_USE_VERTEXAI still works but raises DeprecationWarning (utils/env_utils.py:82-98)
export GOOGLE_API_KEY="<your key>"
# or Agent Platform (Vertex AI):
# export GOOGLE_GENAI_USE_ENTERPRISE=TRUE GOOGLE_CLOUD_PROJECT=<id> GOOGLE_CLOUD_LOCATION=us-central1
```

Folder convention: `adk run` and `adk web` load `root_agent` from `<folder>/agent.py`, from `<folder>/__init__.py`, or from `<folder>/root_agent.yaml` (`cli/utils/agent_loader.py:53,69-75`). The loader accepts both `BaseAgent` and `BaseNode`, so a `Workflow` works as `root_agent` (`agent_loader.py:139,191`). Every lab therefore uses `mkdir <lab>; touch <lab>/__init__.py`, puts `from . import agent` in `__init__.py` (the official samples do the same, e.g. `samples/workflows/sequence/__init__.py`), and runs commands from the **parent** folder.

The model is pinned to `"gemini-3.5-flash"`, which is also the built-in default: `LlmAgent.DEFAULT_MODEL = 'gemini-3.5-flash'` (`agents/llm_agent.py:289`). An `Agent` without `model=` uses that default, which is why the official samples leave `model` out. `adk run --default_llm_model` overrides it.

---

## 0. New facts from source (not in the earlier research)

| # | Fact | Evidence |
|---|---|---|
| N1 | `adk run <agent> "<query>" --session_id S` runs **one step** and persists the session to SQLite under `.adk/` by default (`default_use_local_storage=True`). If the last event has an open interrupt, the next `adk run … --session_id S "<text>"` **auto-resumes** it. The CLI sends `FunctionResponse(id=<interrupt_id>, name="adk_request_input", response={"result": <text>})` with the paused `invocation_id`, and exits with **code 2** while paused. This means you can test HITL from a shell across separate processes. | `cli/cli.py:571`, `:680-790`; `cli/cli_tools_click.py:1009-1160`; `cli/utils/local_storage.py:50` |
| N2 | A human reply sent as a string is **JSON-parsed when possible**. `"approve"` stays a `str`, `"42"` becomes `int 42`, `"true"` becomes `bool`, and `'{"approved": true}'` becomes a `dict`. This is how structured replies reach a `response_schema` node. It can also surprise you: a manager who types `100` hands you an `int`. | `workflow/utils/_rehydration_utils.py:105-122` (`_unwrap_response`) |
| N3 | Without `ResumabilityConfig`, the Runner **finds the paused invocation from the FunctionResponse id by itself** (`_resolve_invocation_id_from_fr`). With `is_resumable=True` you may pass `invocation_id=` and **no** message. Without it, that raises `ValueError: Running an agent requires a new_message or a resumable app.` | `runners.py:1269-1296`, `:661` |
| N4 | Node confirmation (`@node(require_confirmation=...)`) is a `RequestInput` with `interrupt_id = "wf_tool_confirmation:<node_path>"` and `response_schema=ToolConfirmation`. The reply must be a dict such as `{"confirmed": true}`. A non-dict reply raises `WorkflowDataError: A tool confirmation response must be a ToolConfirmation payload, but got str.` A rejection makes the node output `{"error": "This tool call is rejected."}`. | `workflow/utils/_workflow_hitl_utils.py:42-102`; `workflow/_function_node.py:768-790` |
| N5 | A `require_confirmation` predicate gets the node's bound args by name, plus `ctx`/`tool_context`, `node_input`, and any state key with a matching name. | `_function_node.py:715-757` |
| N6 | Python `max_parallel_workers` defaults to `None`, which means **unlimited**. This settles the earlier [UNVERIFIED] item (TypeScript defaults to 8). | `workflow/_parallel_worker.py:71-77`; `workflow/_node.py:199-202` |
| N7 | With jitter on, retry delay is `min(initial*factor**(n-1), max_delay/(1+jitter)) ± jitter*delay`, clamped to [0, max_delay]. With the defaults, attempt 2 waits between 0 and 2 s. Use `jitter=0.0` for exact delays. | `workflow/utils/_retry_utils.py` (`_get_retry_delay`) |
| N8 | `RetryConfig.exceptions` matches **class names along the MRO**. `NodeTimeoutError` is an `Exception` subclass, so a node with `timeout=` and `exceptions=[ConnectionError]` does **not** retry on timeout. Add `"NodeTimeoutError"` to the list. | `_retry_utils.py` (`_should_retry_node`); `workflow/_errors.py` (`NodeTimeoutError`) |
| N9 | The attempt counter is not persisted. After an interrupt or a restart, a re-run node gets its full retry budget back. | `docs/guides/workflow/retry_config/index.md` "Limitations" |
| N10 | An unmatched route only logs `Node '%s' has conditional/DEFAULT edges but none were matched by the emitted route(s): %s. The branch will end.` | `workflow/_graph.py:~181` |
| N11 | YAML: a nested list inside a chain means fan-out. A bare word is a reference to a node defined earlier, and forward references raise `Unknown node 'x'. A node has to be defined by an earlier edge…`. `agent_class:` shorthands resolve from `google.adk.agents` **and** `google.adk.workflow`, so `agent_class: JoinNode` is legal **[UNVERIFIED at runtime, source only]**. | `agents/config_agent_utils.py:255-300`, `:351-372`, `:786-813` |
| N12 | `LlmAgent.mode` is `None` by default and resolves to **single_turn as a workflow node** and **chat as a sub-agent**. A `mode='chat'` agent after any node other than START fails validation. | `agents/llm_agent.py:410-418`; `workflow/utils/_graph_validation.py:192-210` |
| N13 | Event **author**: an `LlmAgent` node signs its events with its own name, but a function node's events are stamped with the **enclosing Workflow's name** (`Context.event_author` docstring: "Workflow sets this to its own name so all child events appear under the workflow's author"). The golden `request_input/tests/phone_broke.json` shows `author: "request_input"` for `process_input` and `author: "draft_email"` for the agent. To find a function node, filter on `event.node_info.path` (e.g. `"/pay@"`), not on `author`. | `agents/context.py:400-410`; sample golden |

---

## Lab 1: Sequence and typed hand-off (refund eligibility pipeline)

> **VERIFIED against google-adk 2.13.0 source (tag v2.13.0, commit d68ca857), re-checked by the verifier on 2026-10-23: every import path, class/function name and parameter in the code.** Expected-output blocks stay illustrative (nothing was executed).

**Goal.** Build a 4-node chain: function, function, LLM agent, function. Watch data move by `node_input`, by `Event(state=…)` and by state-bound parameters. Adapted from `samples/workflows/sequence` and `samples/workflows/state`, and from the adk.dev "Get started" graph (https://adk.dev/graphs/).

**Prereqs.** Common setup. Folder `refund_flow/`.

```python
# refund_flow/agent.py
from google.adk import Agent, Context, Event, Workflow
from pydantic import BaseModel

ORDERS = {"A-1001": {"amount": 89.00, "days_since_delivery": 12, "category": "electronics"},
          "A-1002": {"amount": 1450.00, "days_since_delivery": 41, "category": "furniture"}}

class RefundCase(BaseModel):
  order_id: str
  amount: float
  days_since_delivery: int
  eligible: bool

def parse_request(node_input: str) -> str:
  """'refund A-1001 arrived broken' -> 'A-1001'."""
  order_id = next(t for t in node_input.split() if t.upper().startswith("A-")).upper()
  return order_id

def check_policy(ctx: Context, node_input: str) -> RefundCase:
  order = ORDERS[node_input]
  eligible = order["days_since_delivery"] <= 30          # 30-day policy
  ctx.state["refund_case"] = {"order_id": node_input, **order, "eligible": eligible}
  return RefundCase(order_id=node_input, amount=order["amount"],
                    days_since_delivery=order["days_since_delivery"], eligible=eligible)

write_reply = Agent(
    name="write_reply",
    model="gemini-3.5-flash",
    instruction=("You are a refunds agent. Case: {refund_case}. "
                 "If eligible is true, confirm the refund amount. Otherwise explain "
                 "the 30-day policy politely and offer store credit. Max 3 sentences."),
    output_key="reply_text",
)

def audit_log(reply_text: str):                          # bound from ctx.state["reply_text"]
  yield Event(message=f"[audit] reply length={len(reply_text)} chars. WORKFLOW COMPLETED.")

root_agent = Workflow(
    name="refund_flow",
    edges=[("START", parse_request, check_policy, write_reply, audit_log)],
)
```

**Run.**
```bash
adk run refund_flow "refund A-1001 arrived broken"
adk run refund_flow "refund A-1002 wobbly legs" --jsonl     # one JSON event per line, with node_path
adk web                                                     # pick refund_flow; the graph tab draws the chain
```

**Expected output (illustrative; model text is invented):**
```
Session ID: 3f0c…
[write_reply]: Thanks for reaching out about order A-1001. Your refund of $89.00 has been approved and will reach your card in 3–5 business days.
[refund_flow]: [audit] reply length=142 chars. WORKFLOW COMPLETED.
```
With `--jsonl`, each event carries `"node_path": "refund_flow@1/check_policy@1"` and so on (`cli/cli.py:382-383`).

**Walk-through.**
1. `edges=[("START", a, b, c, d)]`: a chain tuple. Each element runs once, in order (`docs/guides/workflow/graph/index.md`). `"START"` is accepted as an alias for the `START` sentinel only in chain tuples.
2. `def parse_request(node_input: str) -> str`: a plain function becomes a `FunctionNode` automatically. Its `input_schema`/`output_schema` are **inferred from the type hints** (`workflow/_base_node.py:116-138`). The return value becomes the next node's `node_input`.
3. `ctx.state["refund_case"] = …`: a direct state write. It becomes the event's `state_delta`, and the agent reads it through `{refund_case}` templating.
4. `output_key="reply_text"`: the agent's final text is stored in state.
5. `def audit_log(reply_text: str)`: with `parameter_binding='state'` (the default, `workflow/_node.py:61`), any parameter not named `node_input`/`ctx` is looked up in `ctx.state` by name.
6. `yield Event(message=…)`: `message` is user-facing content. A plain `return "x"` only sets `output`, and `adk run` prints nothing for output-only events (`cli/cli.py:404-415`).

**Common errors.**
- `WorkflowDataError: Missing value for parameter "reply_txt" of function "audit_log". It was not found in … and has no default value.` (`workflow/_function_node.py:553`). Cause: a typo, or the state key is not written yet. Fix: match the `output_key`, or give the parameter a default.
- `GraphValidationError: Graph validation failed. Schema mismatch on edge check_policy -> write_reply2. Output schema <class 'RefundCase'> does not match input schema <class 'dict'>.` (`utils/_graph_validation.py:184-189`). Cause: the producer and consumer hints disagree. Fix: use the same Pydantic class on both sides, or drop one hint.
- `ImportError` on `from google.adk import START`. The top-level `__all__` is only `Agent, Context, Event, Runner, Workflow` (`src/google/adk/__init__.py`). Fix: `from google.adk.workflow import START`.
- "My workflow printed nothing." The terminal node returned a value. Fix: `yield Event(message=...)`, or read `event.output` in code.

**Best practice.** Pass data along edges (`node_input`) and keep state for things many nodes or prompts need. Hint every function with Pydantic types, because the graph validates producer/consumer schemas **at construction time**, before you spend a token.

**Variation.** Replace the `{refund_case}` templating with `input_schema=RefundCase` on `write_reply` and the instruction `"Order {RefundCase.order_id}, eligible={RefundCase.eligible}"`. That is the docs' `{Class.field}` form, where "The `Class.` prefix is documentation only" (https://adk.dev/graphs/data-handling/).

---

## Lab 2: Conditional routing and DEFAULT_ROUTE (support-ticket triage)

> **VERIFIED against google-adk 2.13.0 source (tag v2.13.0, commit d68ca857), re-checked by the verifier on 2026-10-23: every import path, class/function name and parameter in the code.** `google.adk.labs.classifiers` exports `Choice`, `ClassifierNode`, `LlmClassifier`; `ClassifierNode.threshold` verified. Expected-output blocks stay illustrative (nothing was executed).

**Goal.** An LLM classifies the ticket into a `Literal` schema and a deterministic function emits `Event(route=…)`. Branches are a dict edge with a `DEFAULT_ROUTE` fallback. Multi-label tickets fan out with a list route. Adapted from `samples/workflows/route` and from the router in https://adk.dev/graphs/.

```python
# ticket_triage/agent.py
from typing import Literal
from google.adk import Agent, Event, Workflow
from google.adk.workflow import DEFAULT_ROUTE
from pydantic import BaseModel, Field

class Triage(BaseModel):
  labels: list[Literal["billing", "outage", "how_to", "other"]] = Field(
      description="All labels that apply to the ticket.")
  priority: Literal["p1", "p2", "p3"]

def intake(node_input: str):
  yield Event(state={"ticket": node_input})

classify = Agent(
    name="classify", model="gemini-3.5-flash",
    instruction="Classify this support ticket. Ticket: {ticket}",
    output_schema=Triage, output_key="triage",
)

def route_ticket(node_input: Triage):
  routes = list(node_input.labels)
  if node_input.priority == "p1" and "outage" not in routes:
    routes.append("outage")                     # p1 always pages on-call
  yield Event(output=node_input.model_dump(), route=routes)   # list => every match runs

billing = Agent(name="billing", model="gemini-3.5-flash",
                instruction="Draft a billing reply for: {ticket}. Mention invoice lookup.")
def page_oncall(node_input: dict):
  yield Event(message=f"PAGED on-call (priority={node_input['priority']}).")
how_to = Agent(name="how_to", model="gemini-3.5-flash",
               instruction="Answer the product question in 4 steps: {ticket}")
def human_queue():
  yield Event(message="Routed to the human L1 queue.")

root_agent = Workflow(
    name="ticket_triage",
    edges=[
        ("START", intake, classify, route_ticket),
        (route_ticket, {"billing": billing, "outage": page_oncall,
                        "how_to": how_to, DEFAULT_ROUTE: human_queue}),
    ],
)
```

**Run.**
```bash
adk run ticket_triage "Checkout API returns 500 since 09:00 and we were double charged"
adk run ticket_triage "I want to say thanks for the swag"
```

**Expected output (illustrative):**
```
[billing]: Hi — sorry about the duplicate charge. I've pulled invoice INV-… and …
[ticket_triage]: PAGED on-call (priority=p1).
---
[ticket_triage]: Routed to the human L1 queue.
```

**Walk-through.**
1. `output_schema=Triage`: the agent's reply is validated JSON. The next node's hint `node_input: Triage` is the **same class**, so validation rule 8 passes (`utils/_graph_validation.py:178-189`).
2. `Event(output=…, route=routes)`: `route` and `output` are independent, so one event selects branches **and** carries a payload. A `list` route dispatches to every matching edge.
3. `(route_ticket, {...})`: a routing map, which becomes conditional `Edge`s. Route values may be `str`, `int` or `bool`.
4. `DEFAULT_ROUTE` is the literal `"__DEFAULT__"` (`workflow/_graph.py:91`). It fires when the emitted route matches nothing else. "other" has no edge of its own, so it lands here.
5. `page_oncall(node_input: dict)` receives the `output` payload. `billing`/`how_to` are agents and read `{ticket}` from state instead.

**Common errors.**
- No branch runs and there is no error. Only a log warning appears: `Node 'route_ticket' has conditional/DEFAULT edges but none were matched by the emitted route(s): ['Billing']. The branch will end.` (`workflow/_graph.py:~181`). Cause: a casing or typo mismatch between the LLM label and the dict key. Fix: use a `Literal` schema (as above) and always add `DEFAULT_ROUTE`.
- `GraphValidationError: Graph validation failed. DEFAULT_ROUTE cannot be combined with other routes in a list (edge from=…` (`_graph_validation.py:169`). Fix: give DEFAULT_ROUTE its own key.
- `WorkflowConfigurationError: Workflow ticket_triage: multiple terminal nodes produced output (2). A workflow must have at most one terminal output.` (`workflow/_workflow.py:930-935`). Cause: two branches both ended with an `output`. Fix: have terminal nodes emit only `message`, or add a `JoinNode` before one final node.

**Best practice.** Use the LLM for *classification into a closed set* and a function for *the routing decision*. That keeps business rules ("p1 always pages") deterministic and unit-testable. This also matches the 2026 evidence that bounded decisions should not go through a generative model (Jev-LiteMAS, §10).

**Variation.** In 2.13 you can replace `classify` + `route_ticket` with the labs `ClassifierNode` (`from google.adk.labs.classifiers import Choice, ClassifierNode, LlmClassifier`; see `samples/workflows/classifier_node/agent.py`). It emits the chosen label as the route, and a `Binary` question with `threshold=0.7` routes on `True`/`False`. Labs API: pin your version.

---

## Lab 3: Fan-out / fan-in with JoinNode (insurance claim checks, no LLM, runs offline)

> **VERIFIED against google-adk 2.13.0 source (tag v2.13.0, commit d68ca857), re-checked by the verifier on 2026-10-23: every import path, class/function name and parameter in the code.** Expected-output blocks stay illustrative (nothing was executed).

**Goal.** Run three independent checks in parallel, join them with a barrier, then make one decision. No model calls, so **no API key is needed**. Adapted from `samples/workflows/fan_out_fan_in` and from codelab level L2a "Parallel fan-out + JoinNode".

```python
# claim_checks/agent.py
import asyncio
from google.adk import Event, Workflow
from google.adk.workflow import JoinNode

POLICIES = {"POL-77": {"active": True, "deductible": 500, "limit": 20000}}

def parse_claim(node_input: str) -> dict:
  # "POL-77 rear-end collision 4200"
  policy_id, *desc, amount = node_input.split()
  return {"policy_id": policy_id, "description": " ".join(desc), "amount": float(amount)}

async def policy_check(node_input: dict) -> dict:
  await asyncio.sleep(0.3)                              # simulated policy-DB call
  p = POLICIES.get(node_input["policy_id"], {"active": False})
  return {"active": p["active"], "deductible": p.get("deductible", 0), "limit": p.get("limit", 0)}

async def fraud_score(node_input: dict) -> float:
  await asyncio.sleep(0.5)                              # simulated fraud model
  return 0.82 if "total loss" in node_input["description"] else 0.07

async def damage_estimate(node_input: dict) -> float:
  await asyncio.sleep(0.2)                              # simulated estimator
  return round(node_input["amount"] * 0.95, 2)

join_checks = JoinNode(name="join_checks")

def decide(node_input: dict):
  pol, fraud, est = node_input["policy_check"], node_input["fraud_score"], node_input["damage_estimate"]
  if not pol["active"]:
    verdict = "DENY: policy inactive"
  elif fraud > 0.6:
    verdict = f"REFER to SIU (fraud score {fraud:.2f})"
  else:
    payout = min(est, pol["limit"]) - pol["deductible"]
    verdict = f"APPROVE payout ${payout:,.2f}"
  yield Event(output=verdict, message=verdict)

root_agent = Workflow(
    name="claim_checks",
    max_concurrency=3,
    edges=[("START", parse_claim, (policy_check, fraud_score, damage_estimate), join_checks, decide)],
)
```

**Run.**
```bash
adk run claim_checks "POL-77 rear-end collision 4200"
adk run claim_checks "POL-77 total loss fire 18000"
adk run claim_checks "POL-99 hail 3000"
```

**Expected output (illustrative):**
```
[claim_checks]: APPROVE payout $3,490.00
[claim_checks]: REFER to SIU (fraud score 0.82)
[claim_checks]: DENY: policy inactive
```
Wall time is about 0.5 s (the slowest branch), not 1.0 s, because the three checks run concurrently.

**Walk-through.**
1. `(policy_check, fraud_score, damage_estimate)`: a tuple **inside** a chain means fan-out. Each branch gets the same `node_input` dict.
2. `JoinNode(name="join_checks")`: overrides `_requires_all_predecessors -> True` (`workflow/_join_node.py:32-40`). It fires once, after all three arrive.
3. `node_input["policy_check"]`: the join emits a **dict keyed by predecessor node name**. A function node's name is its function name.
4. `max_concurrency=3`: caps graph-scheduled nodes. "None or <= 0 means unlimited". Dynamic nodes are excluded (`workflow/_workflow.py:160-166`).
5. `async def`: sync, async and generator functions are all valid nodes. Use async for I/O so branches really overlap.

**Common errors.**
- `KeyError: 'fraud'` inside `decide`. Cause: you used a key other than the predecessor's node name. Fix: print `node_input.keys()` once, or name the nodes with `@node(name=...)`.
- `WorkflowConfigurationError: … multiple terminal nodes produced output (3)…`. Cause: you dropped the JoinNode and the three branches became terminal. Fix: join before the end.
- `send_message` runs 3 times. Cause: without a JoinNode a successor of a fan-out is triggered **once per predecessor** (`samples/workflows/multi_triggers`). Fix: add the JoinNode if you want a barrier.

**Best practice.** "every node that feeds a join has an output of its own", and add retry config to any branch that can fail. Otherwise "the resulting failure appears downstream, away from the node that caused it" (adk.dev/graphs/routes, quoted in prior research). For a map over a runtime-sized list, use `@node(parallel_worker=True, max_parallel_workers=4)` instead of a static tuple. Remember that the Python default is **unlimited** (N6).

**Variation.** Turn `damage_estimate` into an `Agent(..., output_schema=Estimate)` that reads photos. Agents and functions mix freely as fan-out branches.

---

## Lab 4: Bounded loop with a back-edge (marketing-copy compliance reviewer)

> **VERIFIED against google-adk 2.13.0 source (tag v2.13.0, commit d68ca857), re-checked by the verifier on 2026-10-23: every import path, class/function name and parameter in the code.** Expected-output blocks stay illustrative (nothing was executed).

**Goal.** A generator–critic loop. The critic grades the draft and the router either exits or routes back to the generator. A state counter bounds the loop, because "A graph cycle is not bounded automatically" (adk.dev/graphs/routes). Adapted from `samples/workflows/loop`.

```python
# copy_review/agent.py
from typing import Literal
from google.adk import Agent, Context, Event, Workflow
from pydantic import BaseModel, Field

MAX_ROUNDS = 3

class Review(BaseModel):
  grade: Literal["compliant", "needs_fix"]
  feedback: str = Field(description="What to change to meet the policy.")

def brief(node_input: str):
  yield Event(state={"brief": node_input, "feedback": "", "round": 0})

write_copy = Agent(
    name="write_copy", model="gemini-3.5-flash",
    instruction=("Write a 2-sentence ad for: {brief}. "
                 "Reviewer feedback to apply (may be empty): {feedback?}"),
    output_key="draft",
)

review_copy = Agent(
    name="review_copy", model="gemini-3.5-flash",
    instruction=("Policy: no guarantees of returns, no 'risk-free', must say 'Capital at risk.' "
                 "Grade this ad: {draft}"),
    output_schema=Review, output_key="review",
)

def gate(ctx: Context, node_input: Review):
  ctx.state["round"] = ctx.state["round"] + 1
  if node_input.grade == "compliant":
    yield Event(route="done")
  elif ctx.state["round"] >= MAX_ROUNDS:
    yield Event(route="escalate")
  else:
    yield Event(state={"feedback": node_input.feedback}, route="retry")

def publish(draft: str):
  yield Event(message=f"PUBLISHED:\n{draft}")

def escalate(draft: str, round: int):
  yield Event(message=f"Escalated to Legal after {round} rounds. Last draft:\n{draft}")

root_agent = Workflow(
    name="copy_review",
    edges=[
        ("START", brief, write_copy, review_copy, gate),
        (gate, {"retry": write_copy, "done": publish, "escalate": escalate}),
    ],
)
```

**Run.**
```bash
adk run copy_review "a high-yield savings ETF for first-time investors" --jsonl | grep node_path
```

**Expected output (illustrative, trimmed to `node_path`):**
```
"node_path": "copy_review@1/brief@1"
"node_path": "copy_review@1/write_copy@1"
"node_path": "copy_review@1/review_copy@1"
"node_path": "copy_review@1/gate@1"
"node_path": "copy_review@1/write_copy@2"      <- back-edge: fresh lifecycle, counter @2
"node_path": "copy_review@1/review_copy@2"
"node_path": "copy_review@1/gate@2"
"node_path": "copy_review@1/publish@1"
```

**Walk-through.**
1. `(gate, {"retry": write_copy, ...})` reuses the **same `write_copy` instance**. Reusing the instance is how you express a cycle (graph guide, rule 1: unique names).
2. The cycle is **conditional** (routed), so validation accepts it. An unconditional cycle is rejected.
3. `ctx.state["round"]` is the loop bound. Graph cycles have no `max_iterations`.
4. `{feedback?}`: the `?` makes the placeholder optional, so it renders empty instead of raising when the key is missing (prior research, `loop` sample).
5. `node_info.path` shows `write_copy@2`: each pass is a new run with its own run id. That is useful for tracing per-iteration cost.

**Common errors.**
- `GraphValidationError: Graph validation failed. Unconditional cycle detected: write_copy -> review_copy -> write_copy. Cycles must include at least one conditional (routed) edge to avoid infinite loops.` (`utils/_graph_validation.py:49-54`). Fix: route the back-edge.
- `GraphValidationError: Graph validation failed. Duplicate node names found: ['write_copy']…` (`_graph_validation.py:74`). Cause: you built a *second* `Agent(name="write_copy")` for the back-edge. Fix: reuse the object.
- A runaway bill. Cause: no counter, and the critic never says "compliant". Fix: a hard `MAX_ROUNDS` plus an escalation path. Prefer a dynamic `while` with a bound (Lab 5) when the loop logic is complex.

**Best practice.** Every loop needs **two** exits: success and budget exhaustion with escalation to a human. Log the round count in state so evals can measure "rounds to compliant".

**Variation.** Replace the LLM critic with a deterministic regex check (`"Capital at risk." in draft`), and use the LLM only for `feedback`. In 2.13.0 a `JoinNode` inside a loop waits for each iteration's predecessors (CHANGELOG 2.13.0, prior research), so you can fan out two critics per round (tone and legal) and join them.

---

## Lab 5: Dynamic nodes with `@node` + `ctx.run_node` (invoice line-item audit)

> **VERIFIED against google-adk 2.13.0 source (tag v2.13.0, commit d68ca857), re-checked by the verifier on 2026-10-23: every import path, class/function name and parameter in the code.** Expected-output blocks stay illustrative (nothing was executed).

**Goal.** The number of line items is known only at runtime. A parent orchestrator fans out one auditor run per line with `asyncio.gather`, then runs a bounded fix loop on the flagged items. Adapted from `samples/workflows/dynamic_fan_out_fan_in` and `samples/workflows/dynamic_nodes`, and from https://adk.dev/graphs/dynamic/.

```python
# invoice_audit/agent.py
import asyncio
from typing import Literal
from google.adk import Agent, Context, Event, Workflow
from google.adk.workflow import node
from pydantic import BaseModel

class LineVerdict(BaseModel):
  line: str
  status: Literal["ok", "flag"]
  reason: str

auditor = Agent(
    name="auditor", model="gemini-3.5-flash",
    instruction=("You audit one invoice line from the user message against policy: "
                 "meals <= $75/person, no alcohol, hotels <= $250/night. Return a verdict."),
    output_schema=LineVerdict,
)

@node(parameter_binding="node_input")
def policy_math(line: str, limit: float) -> bool:          # deterministic second opinion
  amount = float(line.rsplit("$", 1)[1])
  return amount <= limit

@node(rerun_on_resume=True)                                 # REQUIRED for any ctx.run_node caller
async def orchestrate(ctx: Context, node_input: str):
  lines = [l.strip() for l in node_input.split(";") if l.strip()]
  yield Event(message=f"Auditing {len(lines)} lines in parallel.")
  raw = await asyncio.gather(*[
      ctx.run_node(auditor, node_input=l, use_sub_branch=True) for l in lines])
  verdicts = [LineVerdict.model_validate(v) for v in raw]
  for v in verdicts:
    if v.status == "flag" and "hotel" in v.line.lower():
      ok = await ctx.run_node(policy_math, node_input={"line": v.line, "limit": 250.0})
      if ok:
        v.status, v.reason = "ok", "Within hotel cap per deterministic check."
  flagged = [v for v in verdicts if v.status == "flag"]
  yield Event(state={"flagged": [v.model_dump() for v in flagged]})
  yield Event(output=[v.model_dump() for v in verdicts],
              message="\n".join(f"{v.status.upper():4} {v.line} — {v.reason}" for v in verdicts))

root_agent = Workflow(name="invoice_audit", edges=[("START", orchestrate)])
```

**Run.**
```bash
adk run invoice_audit "Team dinner 4 people \$260; Hotel Berlin 1 night \$240; Wine for client \$90"
```

**Expected output (illustrative):**
```
[invoice_audit]: Auditing 3 lines in parallel.
[invoice_audit]: OK   Team dinner 4 people $260 — $65/person, under the $75 cap.
OK   Hotel Berlin 1 night $240 — Within hotel cap per deterministic check.
FLAG Wine for client $90 — Alcohol is not reimbursable.
```

**Walk-through.**
1. `@node(rerun_on_resume=True)`: mandatory. Without it the call raises (see errors). On resume the parent re-runs from the top, and finished `ctx.run_node` calls "are replayed from history and return their cached outputs" (`docs/guides/workflow/dynamic_nodes/index.md`).
2. `ctx.run_node(auditor, node_input=l, use_sub_branch=True)`: the signature is `run_node(node, node_input=None, *, use_as_output=False, run_id=None, use_sub_branch=False, override_branch=None, override_isolation_scope=None, raise_on_wait=False)` (`agents/context.py:434-445`). `use_sub_branch=True` is "Critical for parallel isolation", so that the parallel agent runs do not see each other's events.
3. `asyncio.gather(*[...])`: always await directly or through gather. Never use `asyncio.create_task`, because "errors are silently swallowed" (`context.py:453-456`).
4. `@node(parameter_binding="node_input")` + `node_input={"line":…, "limit":…}`: dict keys bind to parameters (`workflow/_node.py:61`; dynamic_nodes guide, "Bind dictionary keys").
5. `yield Event(output=...)`: in a generator, `return value` is a `SyntaxError` (async) or **silently discarded** (sync). Always yield the output.
6. For an agent child, `node_input` is turned into a **user message**. That is why the auditor's instruction says "from the user message" and has no `{placeholder}`.

**Common errors.**
- `ValueError: A node must have rerun_on_resume=True. Reason is that dynamically scheduled nodes might be interrupted, and the workflow wakes-up/re-runs the parent node, so it can get the child node response.` (`workflow/_dynamic_node_scheduler.py:769-774`). Fix: decorate the parent with `@node(rerun_on_resume=True)`. Nested parents need it too.
- `KeyError` / missing state key from an instruction like `"Audit {node_input}"`. Agent placeholders read **session state**, not `node_input` (dynamic_nodes guide comment). Fix: rely on the user message, or write state first.
- Interleaved, garbled events across children. Cause: `use_sub_branch` was left False for parallel runs. Fix: set it to True for every gathered call.
- A custom `run_id="1"` collides with auto ids. It must contain a non-numeric character, e.g. `f"line-{i}"` (dynamic_nodes guide).

**Best practice.** Keep the orchestrator thin, because it **re-runs from the top on every resume**. Push side effects (DB writes, emails) into child nodes run through `ctx.run_node`, which are cached and replayed instead of executed again.

**Variation.** Replace the gather with `auditor_pw = Agent(..., parallel_worker=True)` in a static graph `("START", split_lines, auditor_pw, summarize)`. The worker runs once per list item and `summarize` receives a list (`samples/workflows/parallel_worker`).

---

## Lab 6: Agent modes in a graph (HR onboarding: task-mode intake, then single_turn, then a tool with confirmation)

> **VERIFIED against google-adk 2.13.0 source (tag v2.13.0, commit d68ca857), re-checked by the verifier on 2026-10-23: every import path, class/function name and parameter in the code.** Note: the adk.dev banner about task mode is out of date (source + sample win). Expected-output blocks stay illustrative (nothing was executed).

**Goal.** A `mode="task"` agent chats with the user until it has a typed result, then the graph advances. A check routes back to it on failure. A `single_turn` agent writes the plan and calls a tool that needs human confirmation. Adapted from `samples/workflows/agent_in_workflow` (medical-lab intake), plus codelab levels L3a/L3b ("chat vs single_turn", "Task mode (pause/resume, finish_task)").

```python
# hr_onboarding/agent.py
from google.adk import Agent, Event, Workflow
from google.adk.tools.function_tool import FunctionTool
from google.adk.workflow import DEFAULT_ROUTE
from pydantic import BaseModel, Field

EMPLOYEES = {"maria lopez": {"id": "E-2231", "team": "Payments", "laptop": "MacBook Pro 14"}}

class NewHire(BaseModel):
  full_name: str = Field(description="The new hire's full name.")
  start_date: str = Field(description="Start date, YYYY-MM-DD.")

intake = Agent(
    name="intake", model="gemini-3.5-flash", mode="task",
    output_schema=NewHire,
    instruction=("You are HR onboarding. Ask the user for the new hire's full name and "
                 "start date. Do not invent values. When you have both, finish your task. "
                 "If the HR record check failed, ask for the name again."),
)

def check_hris(node_input: NewHire):
  rec = EMPLOYEES.get(node_input.full_name.lower())
  if rec is None:
    yield Event(message=f"No HRIS record for {node_input.full_name}.", route="retry")
  else:
    yield Event(state={"hire": {**rec, **node_input.model_dump()}},
                message=f"Found {rec['id']} on team {rec['team']}.")

def order_laptop(employee_id: str, model: str) -> dict:
  """Places a laptop order with IT procurement."""
  return {"po": f"PO-{employee_id}-01", "model": model, "eta_days": 3}

plan_writer = Agent(
    name="plan_writer", model="gemini-3.5-flash",      # mode=None -> single_turn as a node
    tools=[FunctionTool(order_laptop, require_confirmation=True)],
    instruction=("Hire record: {hire}. Order the laptop with order_laptop, then write a "
                 "5-item day-one checklist that includes the PO number."),
)

root_agent = Workflow(
    name="hr_onboarding",
    edges=[("START", intake, check_hris),
           (check_hris, {"retry": intake, DEFAULT_ROUTE: plan_writer})],
)
```

**Run (interactive, because task mode chats).**
```bash
adk run hr_onboarding          # interactive REPL
[user]: onboard someone new
[user]: Maria Lopez, starts 2026-11-02
[user]: yes                    # confirms the order_laptop tool call
```

**Expected output (illustrative):**
```
[intake]: Sure — what is the new hire's full name and start date (YYYY-MM-DD)?
[hr_onboarding]: Found E-2231 on team Payments.
[plan_writer]: (Paused for input...)
[plan_writer]: Laptop ordered (PO-E-2231-01, ETA 3 days). Day-one checklist: 1) Badge pickup …
```

**Walk-through.**
1. `mode="task"`: the agent may ask clarifying questions and returns automatically through the injected `finish_task` tool (`agents/llm_agent.py:1347-1350`). As a graph node, "control automatically advances to the next node" (adk.dev/workflows/collaboration).
2. `output_schema=NewHire` on the task agent: the `finish_task` result is the typed output that reaches `check_hris(node_input: NewHire)`.
3. `{"retry": intake, DEFAULT_ROUTE: plan_writer}`: a back-edge into a task agent. In the sample, the agent re-opens the conversation.
4. `plan_writer` sets no `mode`. As a workflow node it **defaults to single_turn** (`llm_agent.py:410-418`).
5. `FunctionTool(order_laptop, require_confirmation=True)`: tool-level HITL inside an LLM node. The `adk run` REPL maps "yes" to `{"confirmed": true}` for `adk_request_confirmation` calls (`cli/cli.py:720-735`).

**Common errors.**
- `GraphValidationError: The agent 'intake' has been added to the workflow with mode='chat' following node 'check_hris'. This is not supported because chat-mode agents rely on conversational history … Please change the agent's mode to 'single_turn'` (`utils/_graph_validation.py:200-210`). Fix: use `task` or `single_turn` for any agent reached by a non-START edge.
- Task agent with `sub_agents=`: rejected. "Task mode agents must be leaf agents and cannot have subagents" (collaboration docs, Known limitations).
- Docs/behaviour conflict: the adk.dev banner still says task mode is "disabled for use in graph-based workflows in ADK Python v2.0.0". The official sample `agent_in_workflow` uses `mode="task"` as a node, and CHANGELOG 2.5.0/2.12.0 add task-node resume. **Teach: works in ≥2.5. The banner is out of date** (see `research/09-critic-corrections.md` C2).

**Best practice.** Use **task** mode for slot-filling conversations with a typed exit, **single_turn** for one-shot workers (they can run in parallel and see only their own branch), and **chat** only at the root or as a free-form transfer target. Never put deterministic checks (HRIS lookup) inside the LLM. Make them a function node with a route.

**Variation (coordinator style, no graph).** `root = Agent(name="hr_coordinator", sub_agents=[intake, it_helper])`, where `it_helper = Agent(name="it_helper", mode="single_turn", tools=[order_laptop])`. The coordinator gets auto-injected delegation tools named `intake` and `it_helper` (`llm_agent.py:1352-1371`; adk.dev/workflows/collaboration "Get started").

---

## Lab 7: Human-in-the-loop with `RequestInput`, across separate processes (refund approval over $500)

> **VERIFIED against google-adk 2.13.0 source (tag v2.13.0, commit d68ca857), re-checked by the verifier on 2026-10-23: every import path, class/function name and parameter in the code.** Expected-output blocks stay illustrative (nothing was executed).

**Goal.** Refunds under $500 auto-approve. Larger ones pause for a manager, who answers from a **later, separate** `adk run` call. The answer can be free text (approve, reject or revise) or structured JSON. Adapted from `samples/workflows/request_input_rerun` (re-entry pattern) and `samples/workflows/request_input_advanced` (`response_schema`, time-off approval).

```python
# refund_approval/agent.py
from typing import Optional
from google.adk import Agent, Context, Event, Workflow
from google.adk.events import RequestInput
from google.adk.workflow import node
from pydantic import BaseModel

AUTO_APPROVE_LIMIT = 500.0

class ManagerDecision(BaseModel):
  approved: bool
  amount: Optional[float] = None          # partial refund allowed
  note: str = ""

def intake(node_input: str):
  order_id, amount = node_input.split()[:2]
  yield Event(state={"order_id": order_id, "amount": float(amount), "note": ""})

draft_reply = Agent(
    name="draft_reply", model="gemini-3.5-flash",
    instruction=("Draft a 2-sentence customer email for a refund of ${amount} on order "
                 "{order_id}. Manager note to apply (may be empty): {note?}"),
    output_key="draft",
)

@node(rerun_on_resume=True)
def manager_gate(ctx: Context, amount: float, draft: str):
  if amount <= AUTO_APPROVE_LIMIT:
    yield Event(route="approved", state={"final_amount": amount})
    return
  iid = f"refund_approval_{ctx.invocation_id}_{ctx.run_id}"   # unique per loop pass
  answer = ctx.resume_inputs.get(iid)
  if answer is None:
    yield RequestInput(interrupt_id=iid, response_schema=ManagerDecision,
                       payload={"amount": amount, "draft": draft},
                       message=(f"Refund ${amount:.2f} needs approval. Reply JSON "
                                '{"approved": true|false, "amount": <opt>, "note": "<opt>"}'
                                f"\n---\n{draft}"))
    return
  d = ManagerDecision.model_validate(answer)
  if not d.approved:
    yield Event(route="rejected")
  elif d.note:
    yield Event(state={"note": d.note}, route="revise")
  else:
    yield Event(state={"final_amount": d.amount or amount}, route="approved")

def issue_refund(order_id: str, final_amount: float, draft: str):
  yield Event(message=f"REFUNDED ${final_amount:.2f} on {order_id} (idempotency key refund-{order_id}).\n{draft}")

def notify_rejected(order_id: str):
  yield Event(message=f"Refund for {order_id} rejected by manager.")

root_agent = Workflow(name="refund_approval", edges=[
    ("START", intake, draft_reply, manager_gate),
    (manager_gate, {"approved": issue_refund, "rejected": notify_rejected, "revise": draft_reply}),
])
```

**Run (three separate processes; the session persists in `refund_approval/.adk/`).**
```bash
adk run refund_approval "A-2040 820" --session_id case-2040 ; echo "exit=$?"
adk run refund_approval '{"approved": true, "note": "Offer 10% coupon too"}' --session_id case-2040
adk run refund_approval '{"approved": true, "amount": 700}' --session_id case-2040
```

**Expected output (illustrative):**
```
Session ID: case-2040
[draft_reply]: Dear customer, we are processing your refund of $820.0 for order A-2040 …
[refund_approval]: (Paused for input...)
============================================================
🚨 [PAUSED] Workflow is waiting for human input! 🚨
To resume, run the command again with:
  --session_id case-2040
And provide your input as the query.
============================================================
exit=2
Auto-resuming interrupt refund_approval_e7…_1 with input: {"approved": true, "note": "Offer 10% coupon too"}
[draft_reply]: Dear customer, your refund of $820.0 for A-2040 is on its way, plus a 10% coupon …
[refund_approval]: (Paused for input...)
...
Auto-resuming interrupt refund_approval_e7…_2 with input: {"approved": true, "amount": 700}
[refund_approval]: REFUNDED $700.00 on A-2040 (idempotency key refund-A-2040).
```
The banner text and exit code 2 come from `cli/cli.py:776-790`, and the "Auto-resuming" line from `:703`.

**Walk-through.**
1. `yield RequestInput(...)`: the fields are `interrupt_id` (default: a new uuid), `payload`, `message` and `response_schema` (`events/request_input.py:28-70`). On the wire it becomes a `FunctionCall(name="adk_request_input", id=interrupt_id)` that is listed in `event.long_running_tool_ids` (`events/_interrupts.py`; `utils/_workflow_hitl_utils.py:105-125`).
2. `@node(rerun_on_resume=True)` + `ctx.resume_inputs.get(iid)`: the **re-entry** pattern. The same node asks the question and handles the answer. With the default `rerun_on_resume=False` (the **hand-off** pattern), the node "completes immediately using the user's resuming input as the node's output" (`workflow/_base_node.py:69-78`).
3. `f"…{ctx.invocation_id}_{ctx.run_id}"`: a unique id per loop pass. The docstring says reuse "is supported … Using unique IDs per iteration is still recommended" (`request_input.py:44-50`).
4. JSON replies: the CLI sends `{"result": "<text>"}`, and the engine JSON-parses string results (`_rehydration_utils.py:105-122`). That gives a `dict`, which `ManagerDecision.model_validate` accepts.
5. `"revise": draft_reply`: a revise back-edge. The manager's note goes into state and the draft is re-generated before the gate asks again.

**Common errors.**
- `pydantic_core.ValidationError: 1 validation error for ManagerDecision`. Cause: the manager typed `approve` (a plain string). `response_schema` "does **not** reshape the reply. The reply must already be in that format" (adk.dev/graphs/human-input). Fix: put a small LLM normalizer node after the pause, or accept `str` and parse it yourself.
- The node asks again forever after an answer. Cause: you used `interrupt_id=str(uuid4())` inside a `rerun_on_resume=True` node. The id changes on every rerun, so `resume_inputs.get` never matches. Fix: derive the id deterministically from `invocation_id` + `run_id`.
- `ValueError: Running an agent requires a new_message or a resumable app.` (`runners.py:1279-1284`). Cause: programmatic resume with only `invocation_id=` on a non-resumable app. Fix: send the FunctionResponse as `new_message` (see Lab 8), or enable `ResumabilityConfig`.
- Resuming from `adk web`/CLI after a crash mid-node: "resuming from the ADK Web UI or the CLI is not supported" for `ResumabilityConfig` resume (adk.dev/runtime/resume). Interrupt answers through `adk run --session_id` (N1) are a different path, and they do work.

**Best practice.** Make the gate **policy-driven** (the threshold lives in code) and **auditable**: put the draft and amount in `payload` so the approval UI shows exactly what is being approved. Long-lived approvals are an attack surface, so scope an approval to one `interrupt_id` and never cache "manager said yes" in `user:` state. This is the residual-authority replay attack in arXiv 2609.33910 (§10).

**Variation (node confirmation, 2.12+).** Replace the hand-written gate with `@node(require_confirmation=lambda amount: amount > 500)` on a function `def issue_refund(order_id: str, amount: float)`. The predicate receives bound args by name (N5). The pause uses `interrupt_id="wf_tool_confirmation:<node_path>"`, and the reply must be `'{"confirmed": true}'` (N4). Rejection yields `{"error": "This tool call is rejected."}`.

---

## Lab 8: RetryConfig, timeout and durable resume with SQLite (payments API, crash-safe)

> **VERIFIED against google-adk 2.13.0 source (tag v2.13.0, commit d68ca857), re-checked by the verifier on 2026-10-23: every import path, class/function name and parameter in the code.** Correction applied to the common setup: `GOOGLE_GENAI_USE_ENTERPRISE` replaces the deprecated `GOOGLE_GENAI_USE_VERTEXAI`. Expected-output blocks stay illustrative (nothing was executed).

**Goal.** A flaky payment-gateway node retries with deterministic backoff and a timeout. The workflow pauses for a fraud analyst, the process exits, and a **new process** resumes from SQLite. A side-effect log proves that completed nodes are **replayed, not re-executed**. The pattern follows `samples/workflows/retry` and adk.dev/runtime/resume. The driver code mirrors the CLI's own resume code (`cli/cli.py:680-770`).

```python
# payouts/app.py   (run with: python -m payouts.app start|resume ...)
import asyncio, json, sys
from google.adk import Context, Event, Runner, Workflow
from google.adk.apps import App, ResumabilityConfig
from google.adk.events import RequestInput
from google.adk.sessions.sqlite_session_service import SqliteSessionService
from google.adk.workflow import RetryConfig, node
from google.genai import types

def kyc_lookup(node_input: str) -> dict:
  open("side_effects.log", "a").write(f"kyc_lookup {node_input}\n")   # proves replay
  return {"payee": node_input, "risk": "medium"}

def analyst_review(node_input: dict):
  yield RequestInput(message=f"Approve payout to {node_input['payee']} (risk {node_input['risk']})? yes/no")

@node(retry_config=RetryConfig(max_attempts=4, initial_delay=0.5, backoff_factor=2.0, jitter=0.0,
                               exceptions=[ConnectionError, "NodeTimeoutError"]), timeout=2.0)
async def pay(ctx: Context, node_input: str):
  yield Event(message=f"gateway attempt {ctx.attempt_count}")
  if node_input.strip().lower() != "yes":
    yield Event(output="CANCELLED"); return
  if ctx.attempt_count < 3:
    raise ConnectionError("gateway 503")            # attempts 1-2 fail, 3 succeeds
  yield Event(output="PAID idempotency_key=payout-" + ctx.invocation_id)

root = Workflow(name="payouts", edges=[("START", kyc_lookup, analyst_review, pay)])
app = App(name="payouts", root_agent=root, resumability_config=ResumabilityConfig(is_resumable=True))
runner = Runner(app=app, session_service=SqliteSessionService("payouts.db"))

async def main(cmd: str, arg: str):
  if cmd == "start":
    await runner.session_service.create_session(app_name="payouts", user_id="ops", session_id="s1")
    msg, inv = types.Content(role="user", parts=[types.Part(text=arg)]), None
  else:
    pending = json.load(open("pending.json"))
    inv = pending["invocation_id"]
    msg = types.Content(role="user", parts=[types.Part(function_response=types.FunctionResponse(
        id=pending["interrupt_id"], name="adk_request_input", response={"result": arg}))])
  async for ev in runner.run_async(user_id="ops", session_id="s1", invocation_id=inv, new_message=msg):
    if ev.content and ev.content.parts and ev.content.parts[0].text:
      print(f"[{ev.author}] {ev.content.parts[0].text}")
    if ev.long_running_tool_ids:
      json.dump({"invocation_id": ev.invocation_id,
                 "interrupt_id": next(iter(ev.long_running_tool_ids))}, open("pending.json", "w"))
      print("PAUSED -> pending.json")
    if ev.output is not None and ev.node_info and "/pay@" in (ev.node_info.path or ""):
      print("OUTPUT:", ev.output)

if __name__ == "__main__":
  asyncio.run(main(sys.argv[1], sys.argv[2]))
```

**Run (no API key needed, since there is no LLM node).**
```bash
mkdir payouts && touch payouts/__init__.py   # then save app.py inside
python -m payouts.app start "ACME-GmbH"      # process 1: runs kyc_lookup, pauses, exits
python -m payouts.app resume yes             # process 2: new interpreter, reads payouts.db
cat side_effects.log                         # -> exactly ONE line
```

**Expected output (illustrative):**
```
PAUSED -> pending.json
[payouts] gateway attempt 1
[payouts] gateway attempt 2
[payouts] gateway attempt 3
OUTPUT: PAID idempotency_key=payout-e-9c1…
$ cat side_effects.log
kyc_lookup ACME-GmbH
```
With `jitter=0.0` the waits are exactly 0.5 s, then 1.0 s (`_retry_utils.py`: `initial_delay * backoff_factor**(attempt-1)`).

**Walk-through.**
1. `RetryConfig(max_attempts=4, …)`: every field defaults to `None` and resolves at run time to 5 / 1.0 s / 60 s / ×2.0 / jitter 1.0 (`workflow/_retry_config.py:31-60`; `_retry_utils.py`). `max_attempts` counts the first try.
2. `exceptions=[ConnectionError, "NodeTimeoutError"]`: matched by **class name along the MRO**. Without `"NodeTimeoutError"`, the `timeout=2.0` failure (`NodeTimeoutError: Node 'pay' timed out after 2.0 seconds.`, `workflow/_errors.py`) would **not** be retried (N8).
3. `ResumabilityConfig(is_resumable=True)`: per the in-repo architecture note, this flag does **not** switch resume on. Replay-resume always works inside an invocation. What the flag adds is **durability**: cross-call resume, `agent_state`/`end_of_agent` checkpoint events, and routing a FunctionResponse back to its invocation (`.agents/skills/adk-architecture/references/architecture-workflow-resumability.md`).
4. `FunctionResponse(id=interrupt_id, name="adk_request_input", response={"result": arg})`: exactly what `adk run` sends (`cli/cli.py:757-768`).
5. `side_effects.log` has one line. On resume the workflow scans the invocation's events (`ReplayManager.scan_workflow_events`) and **fast-forwards** completed nodes from their recorded output. Only the interrupted node and its successors run.

**Common errors.**
- The payment is charged twice after a crash between "charge" and "event persisted". Resume is **at-least-once**: "Tool call to resume needs to be idempotent" (`apps/_configs.py:37-41`). Fix: send an idempotency key to the gateway, derived from `invocation_id` or the order id, never from `uuid4()`.
- Retries never happen. Cause: the node body has `try: … except Exception: return "error"`. The migration guide says don't wrap in `except Exception:`, because that hides failures from retries (adk.dev/2.0). Never catch `BaseException`: `NodeInterruptedError` is a `BaseException` "so user code cannot accidentally catch it with except Exception" (`workflow/_errors.py`).
- `ValueError: Invalid app name 'payouts-v2!'…` / `App name cannot be 'user'` (`apps/app.py:42-50`). Fix: use letters, digits, `_` and `-`, starting with a letter.
- You changed the graph between pause and resume and the resume misbehaves. Docs: do not change the workflow between stop and resume. The architecture note lists checkpoint **versioning** as an open item. Fix: drain paused runs before you deploy a graph change, or version app names.

**Best practice.** Retry **narrowly**: list transient exception classes, use `jitter=0` in tests and the default jitter in prod (it avoids thundering herds), and put the retry on the failing node, not on a whole sub-workflow. Remember that the attempt counter resets after an interrupt or restart (N9). Cap total cost with `ADK_MAX_LLM_CALLS` (2.8.0) when LLM nodes retry.

**Variation.** Swap `SqliteSessionService("payouts.db")` for `DatabaseSessionService("postgresql+asyncpg://…")`. That needs `pip install "google-adk[db]==2.13.0"`, because `sessions/__init__.py:51-56` raises a missing-extra error for `sqlalchemy` otherwise. On Agent Runtime, use `VertexAiSessionService` and the same driver.

---

## Lab 9: Declarative YAML graph (support-ticket triage as config)

> **VERIFIED against google-adk 2.13.0 source (tag v2.13.0, commit d68ca857), re-checked by the verifier on 2026-10-23: every import path, class/function name and parameter in the code.** Still [UNVERIFIED at runtime]: the `__DEFAULT__:` YAML key and the inline `{agent_class: JoinNode}` fan-out (source-derived only). Expected-output blocks stay illustrative (nothing was executed).

**Goal.** Express the Lab 2 routing workflow (simplified) as `root_agent.yaml`. Functions and schemas stay in Python and agents live in YAML. Adapted from `samples/workflows/loop_config` (2.9.0+, "load ADK 2.0 graph workflows from YAML configuration").

```yaml
# triage_yaml/root_agent.yaml
agent_class: Workflow
name: root_agent
edges:
  - - START
    - .agent.intake
    - classify.yaml
    - .agent.route_ticket
  - - route_ticket                      # bare word = node defined by an earlier edge
    - billing: billing.yaml
      outage: .agent.page_oncall
      __DEFAULT__: .agent.human_queue   # literal value of DEFAULT_ROUTE
```
```yaml
# triage_yaml/classify.yaml
agent_class: LlmAgent
name: classify
model: gemini-3.5-flash
instruction: |
  Classify this support ticket into exactly one label. Ticket: {ticket}
output_schema:
  name: triage_yaml.agent.Triage
output_key: triage
```
```yaml
# triage_yaml/billing.yaml
agent_class: LlmAgent
name: billing
model: gemini-3.5-flash
instruction: |
  Draft a billing reply for: {ticket}. Mention that we will look up the invoice.
```
```python
# triage_yaml/agent.py   (no root_agent here; the loader falls through to root_agent.yaml)
from typing import Literal
from google.adk import Event
from pydantic import BaseModel

class Triage(BaseModel):
  label: Literal["billing", "outage", "other"]

def intake(node_input: str):
  return Event(state={"ticket": node_input})

def route_ticket(node_input: Triage):
  return Event(route=node_input.label)

def page_oncall():
  return Event(message="PAGED on-call.")

def human_queue():
  return Event(message="Routed to the human L1 queue.")
```

**Run (from the parent folder, which must be on `sys.path`; the CLI does this).**
```bash
ls triage_yaml        # root_agent.yaml classify.yaml billing.yaml agent.py  (no __init__.py needed, like loop_config)
adk run triage_yaml "We were charged twice for October"
adk web               # Visual graph of the YAML-defined workflow
```

**Expected output (illustrative):**
```
[billing]: Sorry about the duplicate October charge — I'm pulling up your invoice now …
```

**Walk-through.**
1. `agent_class: Workflow` + `edges:`: mapped onto the `Workflow.edges` field. A list in YAML is a chain tuple (`agents/config_agent_utils.py:255-262`).
2. `.agent.intake`: a leading dot resolves relative to the YAML folder's package (`triage_yaml.agent.intake`) and wraps it as a `FunctionNode` named `intake` (`config_agent_utils.py:363-372`).
3. `classify.yaml`: a separate agent file. Nodes are **cached by string and by name**, so a later reference reuses the same instance, which loops need (`:351-358`).
4. `- route_ticket` as a bare word: a reference to a node defined in an earlier edge. Forward references raise (N11).
5. `output_schema: {name: triage_yaml.agent.Triage}`: code references are fully qualified names resolved against `sys.path` (loop_config README).
6. `__DEFAULT__:`: works because `DEFAULT_ROUTE == "__DEFAULT__"` (`workflow/_graph.py:91`). **[UNVERIFIED at runtime]**: no official YAML sample uses it.

**Common errors.**
- `ValueError: Unknown node 'route_ticket'. A node has to be defined by an earlier edge before another edge can name it.` (`config_agent_utils.py:360-366`). Fix: reorder the edges, or use the full `.agent.route_ticket` reference.
- `ModuleNotFoundError: No module named 'triage_yaml'` when you run from inside the folder. Fix: run from the parent directory, "as the CLI does" (loop_config README).
- `ValueError: Invalid class 'Join'. It must be a subclass of BaseNode.` (`:811-813`). Fix: use the exact class names: `LlmAgent`, `Workflow`, `JoinNode`, `FunctionNode`.
- Builder security: the Visual Builder endpoints accept only `.yaml/.yml`, reject `..` and absolute paths, and block keys like `args` (prior research §9). Do not template YAML from user input.

**Best practice.** Keep **topology and prompts in YAML** (reviewable by PMs and legal, diffable) and **logic and schemas in Python** (typed and unit-tested). Generate YAML only from trusted sources, because `name:` references import arbitrary Python objects.

**Variation (fan-out in YAML, source-derived [UNVERIFIED at runtime]).** A nested list in a chain means fan-out, and an inline JoinNode is legal:
```yaml
  - - START
    - .agent.parse_claim
    - [.agent.policy_check, .agent.fraud_score, .agent.damage_estimate]
    - {agent_class: JoinNode, name: join_checks}
    - .agent.decide
```

---

## 9. Cross-lab gotchas checklist (for one slide)

1. A node that calls `ctx.run_node` must set `rerun_on_resume=True`, or you get a `ValueError`.
2. Two terminal outputs raise `WorkflowConfigurationError`. Join first, or emit only messages at the end.
3. An unmatched route stops the branch with a log warning only. Always add `DEFAULT_ROUTE`.
4. Graph cycles are unbounded. Add a state counter and an escalation route.
5. Schema hints are checked at construction, so producer and consumer must use the **same class**.
6. `mode='chat'` is allowed only right after START. Use `single_turn` or `task` everywhere else.
7. Human replies are JSON-parsed (`"100"` becomes an `int`). `response_schema` validates the reply but does not convert it.
8. A node's `require_confirmation` reply must be `{"confirmed": true}`, not `"yes"`, when you send it programmatically.
9. `exceptions=[...]` must include `"NodeTimeoutError"` if timeouts should retry.
10. Resume is at-least-once. Use idempotency keys and a thin orchestrator, and put side effects in child nodes.
11. Do not change the graph while runs are paused. Checkpoint versioning is still open.
12. Never use `except Exception`/`BaseException` around node bodies, because it disables retries and HITL.

---

## 10. arXiv, 2026-07-23 to 2026-10-23: insights that map onto these labs

Retrieved through the arXiv API (`export.arxiv.org/api/query`, sorted by submittedDate). Every claim below comes from the abstract only. Figures are as reported by the authors.

| Paper | Date | Finding (abstract) | Lab tie-in |
|---|---|---|---|
| **Jev-LiteMAS: Separating Decisions from Generation in Multi-Agent Workflows**, Wang et al., arXiv **2610.21411** | 2026-10-15 | Routing and review account for **31.7–43.5%** of generative-LLM tokens in three MAS frameworks. A lightweight decision model for routing and screening cuts generative tokens by **12.7–54.6%**, with accuracy within 1.34 pp. "Grounding routing in substantive expert outputs prevents up to 18.0 points in accuracy loss." | Lab 2 (function router, `ClassifierNode` / TypeSafe "Jev" classifier in ADK 2.13), Lab 4 (cheap critic first) |
| **When Faster Decisions Do Not Make Better Agents: An Empirical Study of Jev in Agent Workflows**, Ling et al., **2610.13092** | 2026-10-09 | Jev cuts decision cost and latency, but task success drops in two mobile agents. "Mean cost per successful outcome increases in one agent even as spending per attempt falls." Recommends preserving progress, supporting recovery and verifying completion. | Labs 2/8: measure cost **per delivered outcome**, and keep the retry/resume path |
| **CXBench: Process-Compliant LLM Agents in Regulated Customer-Experience Workflows**, Yu et al., **2610.25954** | 2026-10-19 | **55.5%** of 840 runs are *false-passes* (right outcome, non-compliant process). That is 80.1% of the outcome-passing runs, and only 13.8% pass both checks. | Labs 6/7: encode required steps (consent, disclosure, approval) as **graph nodes**, not prompt text, and evaluate the trace |
| **RITE: Resilience to Silent Tool Errors in E-Commerce Agentic Systems**, Zhang et al., **2610.27777** | 2026-10-20 | Silent tool errors "roughly halve task success" across 10 LLMs and are harder than explicit failures. A light **State Checker** is proposed. | Lab 3/8: validate tool outputs with typed `output_schema` and a check node. Raise exceptions so `RetryConfig` can see them, and never return silent defaults |
| **When Messages Go Wrong: Communication Faults in LLM-Based MAS**, Zhou et al., **2610.15459** | 2026-10-11 | Over 29,000 executions: 20.7% of failures carry no immediate failure signal (76.2% for partial-content faults). Flat topologies keep **53.0%** success under faults, versus **3.3%** (Sequential) and **3.2%** (Hierarchical), when an alternative information path preserves the evidence. | Lab 3: fan-out with each branch reading the **original** input (not a chain of rewrites) is the "alternative path" |
| **Upstream Influence, Downstream Re-Anchoring in LLM Agent Chains**, Hsu et al., **2610.17723** | 2026-10-13 | Injected stance shifts are halved by the third agent. Keeping untrusted content in front of every agent sustains them, and a stance relayed without its reasoning is mostly discounted. "Reasoning-trace audits miss the attack." | Lab 1/5: limit which nodes read untrusted text, and pass typed summaries along edges, not raw content |
| **Which Model for Which Role? Cost-Efficient Pareto Recommendation for LLM Agentic Workflows**, Xie et al., **2610.26676** | 2026-10-19 | CC-Gittins recovers much of the quality–cost Pareto frontier at about **10%** of exhaustive-evaluation cost, for workflows with 2–5 roles. | Per-node `model=` choice in every lab (flash for classify/critic, pro for drafting) |
| **Optimize Once, Execute Fast: Latency-Aware Multi-Agent Workflow Learning (LAWA)**, Zhang et al., **2610.14481** | 2026-10-10 | Reduces workflow makespan by graph edits on **critical-path bottlenecks** while keeping task performance, for recurring queries such as customer support. | Lab 3: parallelize off-critical-path checks, and use `max_concurrency` |
| **Truthful … Model Routing in Graph-Based Agentic Workflows (STAR)**, Liu et al., **2610.19316** | 2026-10-13 | Topology-aware routing benefit "grows with fan-out and transferred payload". Keeping dependent tasks on one provider reuses context. | Lab 3/5: keep fan-out branch payloads small |
| **AgentRewind: Recoverable Execution for Long-Horizon LLM Agents**, Zhuang et al., **2608.14380** | 2026-08-14 | Aligned checkpoints of agent context and environment let agents roll back and resume, and improve task success on MettleBench. | Lab 8: ADK checkpoints the *workflow*, not your external systems. Add compensations yourself |
| **Planarian: Managing Agent State with Statepoints**, Guo et al., **2609.35366** | 2026-09-28 | snapshot/rollback/fork across local and remote state, using compensating actions for remote changes. Up to **15×** task-quality gain, 3% overhead. | Lab 8 extension: pair each side-effecting node with a compensation node on the reject route |
| **When Consent Outlives Context: Residual Authority Replay in Long-Lived Agents**, Zhang et al., **2609.33910** | 2026-09-27 | Reusing earlier approvals raises attack success by up to **35.1 pp** (AgentDojo), and by 24.9 pp on average against production coding agents. | Lab 7: scope approval to one interrupt id, and never persist "approved" in `user:` state |
| **Local Allow, Global Deny: Why Per-Action Authorization Does Not Compose**, Pandey et al., **2610.27620** | 2026-10-20 | Per-action guards cannot detect relational policy violations. You need cross-execution monitoring. | Lab 7: confirmation per tool call is not enough. Add workflow-level policy nodes (e.g. daily refund total) |
| **Same Winners, Different Success Rates: Evaluating How LLM Agents Recover from Failures**, Xu et al., **2609.34215** | 2026-09-28 | Checkpoint-based recovery metrics based on set agreement hide near-zero recovery. Report pooled success as well. | Evals for Lab 8: measure resumed-run success, not only "same action chosen" |

Industry practice that complements this (already verified in earlier research, cited not repeated): the "Why we built ADK 2.0" blog (2026-07-01) argues that graphs constrain which actions are possible, and the codelab's "who decides the next step?" decision rule (codelab L5). Neither gives production customer numbers for 2.0 workflows. **[UNVERIFIED: none found]**

---

## Sources

- PyPI: https://pypi.org/pypi/google-adk/json (2.13.0, 2026-10-23T18:26:31, `>=3.11`); https://pypi.org/pypi/google-genai/json (2.33.0)
- Source at tag v2.13.0: https://github.com/google/adk-python/tree/v2.13.0. Files used: `src/google/adk/workflow/{__init__,_node,_base_node,_workflow,_join_node,_retry_config,_errors,_parallel_worker,_function_node,_graph,_dynamic_node_scheduler}.py`, `workflow/utils/{_graph_validation,_retry_utils,_rehydration_utils,_workflow_hitl_utils}.py`, `events/{request_input,_interrupts}.py`, `agents/{context,llm_agent,config_agent_utils}.py`, `runners.py`, `apps/{app,_configs}.py`, `sessions/{__init__,state,sqlite_session_service}.py`, `cli/{cli,cli_tools_click}.py`, `cli/utils/agent_loader.py`
- Guides at v2.13.0: `docs/guides/workflow/{graph,dynamic_nodes,retry_config,workflow,node,join_node,parallel_worker}/index.md`
- Architecture note: `.agents/skills/adk-architecture/references/architecture-workflow-resumability.md`
- Samples: `contributing/samples/workflows/{sequence,state,route,fan_out_fan_in,multi_triggers,loop,loop_config,dynamic_nodes,dynamic_fan_out_fan_in,parallel_worker,agent_in_workflow,request_input,request_input_rerun,request_input_advanced,retry,classifier_node}/`
- Docs: https://adk.dev/graphs/ · https://adk.dev/graphs/data-handling/ · https://adk.dev/graphs/human-input/ · https://adk.dev/graphs/dynamic/ · https://adk.dev/graphs/routes/ · https://adk.dev/workflows/collaboration/ · https://adk.dev/runtime/resume/ · https://adk.dev/2.0/
- Codelab: "ADK 2 Orchestration: Graph, Collaborative & Dynamic Workflows", https://codelabs.developers.google.com/adk2/instructions (repo `cuppibla/adk2-tutorial`)
- arXiv abstracts: 2610.21411, 2610.13092, 2610.25954, 2610.27777, 2610.15459, 2610.17723, 2610.26676, 2610.14481, 2610.19316, 2608.14380, 2609.35366, 2609.33910, 2610.27620, 2609.34215 (https://arxiv.org/abs/<id>)
