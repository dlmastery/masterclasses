# Interview drills: Building agents with Google ADK 2.0 - outline

Deck key: `adk-interview`. 28 slides, 6 chapters (opening + 5). Facts as of 2026-10-23 (google-adk 2.13.0).
Rules: engine/AUTHORING.md section 9 (9.6 defines this deck). Every chapter = 1 opener + Q&A slides (3 pairs, each answer its own step) + 1 whiteboard + 1 debug-this.
Facts come only from research-v2/adk (00-VERIFIED.md overrides). Corrected v1 answer: `multi_run_config.num_runs` does not exist in 2.13.0; use `AgentEvaluator.evaluate(..., num_runs=3)` (default 2).

Mix: opening 1, chapter 5, qa 12, whiteboard 5, debug 5.

## Chapter 0: Opening  (tone: agent)

Scenario: How to use this drill deck: five topic areas, three drill types (Q&A, whiteboard, debug this).

Research files:
- C:/Users/evija/googleadk2.0/research-v2/adk/00-VERIFIED.md
- C:/Users/evija/googleadk2.0/research-v2/adk/industry.md
- C:/Users/evija/googleadk2.0/research-v2/adk/gotchas.md

### c00-01-hero.html - Answer ADK interview questions with mechanisms, numbers and code
- **id:** `adk-interview-c00-hero`
- **type:** opening
- **content:** .display line: 'Interview drills: Building agents with Google ADK 2.0'. Sub-line: 'Tested on google-adk 2.13.0 · October 2026'. Step 1: three drill-type cards (.grid.g3, .panel.tight): (a) Q&A - 3 questions per slide, answer before you click; (b) Whiteboard - a system-design prompt, then the reference architecture builds step by step; (c) Debug this - buggy code and a symptom, find the line before the answer step. Step 2: the five topic areas as a row of tone-coloured tags: 1 Architecture and graphs (agent), 2 Durable runs and HITL (human), 3 Context, state, memory, cost (state), 4 Tools, protocols, security (tool), 5 Evals and production (risk). Step 3: one .callout.tip: 'A strong answer names the mechanism, the failure mode, one number and the fix.' Three count-up stats (.stat): 13 minor releases in 5 months (2.0.0 on 2026-05-19 to 2.13.0 on 2026-10-23); 500 default LLM calls per run (ADK_MAX_LLM_CALLS); 0.95^20 = 36% end-to-end success. Notes: tell students to say the trade-off first, then the ADK API, then the evidence; interviewers at Google, Anthropic, OpenAI and Meta probe failure modes, not definitions.
- **visual:** Bespoke Deck.register hook (deterministic, gsap loop killed in leave): on the right half a small ADK 2.0 graph, START -> classify (n-model) -> route (n-tool, function) -> three branches (billing n-agent, page_oncall n-tool, human_queue n-human, DEFAULT). A token travels START->classify->route and then alternates branch by loop index (billing, page_oncall, human_queue). Each node it enters glows amber (running) then green (done); human_queue glows violet (waiting) for 1 s. Step 1 fades the three drill cards in with stagger; step 2 pops the five topic tags; step 3 counts the stats up.

## Chapter 1: Agent architecture and graph workflows  (tone: agent)

Scenario: Support-ticket triage and a marketing-copy compliance loop on ADK 2.0 Workflow graphs.

Research files:
- C:/Users/evija/googleadk2.0/research-v2/adk/00-VERIFIED.md
- C:/Users/evija/googleadk2.0/research-v2/adk/lab-workflows.md
- C:/Users/evija/googleadk2.0/research-v2/adk/arxiv-architectures.md
- C:/Users/evija/googleadk2.0/research-v2/adk/gotchas.md
- C:/Users/evija/googleadk2.0/research-v2/adk/industry.md

### c01-01-chapter.html - Code owns the flow, the model owns the judgment
- **id:** `adk-interview-c01-chapter`
- **type:** chapter
- **content:** class='slide chapter'. Chapter number 1. .display: 'Agent architecture and graph workflows'. .lede: 'Interviewers test where you put the boundary between deterministic code and the LLM.' Three small tags for what this chapter drills: workflow vs agent vs multi-agent; routes, joins and loops; agent modes in a graph.
- **visual:** Self-animating mini-diagram (data-wires, 3 steps): an n-agent 'LLM' node in the middle; step 1 a dashed g-tool group 'Workflow edges' draws around it; step 2 wires START>llm and llm>route:flow; step 3 route fans out to two n-tool nodes. A pulse loops along the flow wire.

### c01-02-qa-architecture.html - Pick workflow, agent or multi-agent by the evidence, not the trend
- **id:** `adk-interview-c01-qa-architecture`
- **type:** qa
- **content:** Kicker: 'Interview · architecture'. Three .qa pairs. Q1: 'A refund process: do you build a workflow or an agent?' A1: 'A workflow spine. The path is data-determined, the refund is irreversible and it needs an audit trail. Use an LLM node only to classify the free-text complaint. Google I/O 26 rule: move to a graph once you have more than two branching paths.' Tags: '> 2 branches = graph'. Q2: 'An agent is 95% reliable per step and runs 20 dependent steps. What is end-to-end success, and what do you change?' A2: 'About 36% (0.95^20). Success decays geometrically with step count: in arXiv 2609.01660 every model nears zero within 16 dependent steps. Hard-code the data-determined edges, add cheap verifiers after risky steps, and remove steps.' Tags: '0.95^20 = 36%', '16 steps'. Q3: 'When does a multi-agent design beat one agent with tools?' A3: 'Rarely, and only for parallel, read-heavy work with a strong verifier. On tau2-bench a centralized multi-agent system is worse than one agent in 12 of 13 cells (2610.27655). Policy facts get lost at each hand-off: 0% single loop, 56% pipeline, 85% orchestrator plus subagents (2608.16055). Keep writes in one thread.' Tags: '12 of 13 cells', '0 / 56 / 85%'. Notes: Shopify's advice 'Avoid multi-agent architectures early'; a flat topology keeps 53.0% success under faults vs 3.3% sequential (2610.15459) if you must split.
- **visual:** Standard .qa layout, three .qa blocks stacked in a .stack.lg. All three .q lines are visible at step 0; each .a reveals on its own data-step (1, 2, 3) with data-fx up. The current pair gets a left accent bar in the chapter tone; earlier pairs dim to 55%. A .tags row under each answer shows the 1-3 numbers to say out loud (tag t-<tone>). A thin bar at the bottom (.bar data-fx=bar) fills 33/66/100% per step.

### c01-03-qa-routing.html - An unmatched route ends the branch with only a log line
- **id:** `adk-interview-c01-qa-routing`
- **type:** qa
- **content:** Kicker: 'Interview · routes and joins'. Three .qa pairs. Q1: 'How do you branch in an ADK 2.0 Workflow, and what happens to a route with no matching edge?' A1: 'A function node yields Event(route=...) and a dict edge maps route values to nodes. An unmatched route ends the branch with only a log warning, no error. Constrain the LLM label with a Literal output_schema and always add DEFAULT_ROUTE ("__DEFAULT__").' Tags: 'DEFAULT_ROUTE', 'Literal[...]'. Q2: 'Why let the LLM classify but let code make the routing decision?' A2: 'Business rules such as "p1 always pages on-call" stay deterministic and unit-testable. Routing and review calls use 31.7-43.5% of multi-agent generative tokens; a lightweight decision model cut 12.7-54.6% within 1.34 pts accuracy (2610.21411).' Tags: '31.7-43.5% of tokens'. Q3: 'Two branches both end with an output. What happens?' A3: 'The run fails with WorkflowConfigurationError: multiple terminal nodes produced output. The engine cannot pick the workflow output. Put a JoinNode before one final node (it emits one dict keyed by predecessor name), or let terminal nodes emit only messages.' Tags: 'JoinNode'. Notes: a list route (route=["billing", "outage"]) runs every matching edge; DEFAULT_ROUTE cannot be combined with other routes in a list (GraphValidationError).
- **visual:** Standard .qa layout, three .qa blocks stacked in a .stack.lg. All three .q lines are visible at step 0; each .a reveals on its own data-step (1, 2, 3) with data-fx up. The current pair gets a left accent bar in the chapter tone; earlier pairs dim to 55%. A .tags row under each answer shows the 1-3 numbers to say out loud (tag t-<tone>). A thin bar at the bottom (.bar data-fx=bar) fills 33/66/100% per step. Optional mini diagram right of A1 (300x200): route node with three dict edges, one red dashed edge labelled 'Billing' (casing typo) going nowhere at step 1, then a DEFAULT edge appears in green.

### c01-04-qa-loops-modes.html - Graph cycles have no iteration cap: you write the bound
- **id:** `adk-interview-c01-qa-loops-modes`
- **type:** qa
- **content:** Kicker: 'Interview · loops and modes'. Three .qa pairs. Q1: 'Can a graph cycle run forever? How do you bound it?' A1: 'Yes. Validation rejects only unconditional cycles; a routed cycle has no max_iterations. Keep a round counter in ctx.state and give the gate two exits: done and escalate. The backstop is the default cap of 500 LLM calls per run (ADK_MAX_LLM_CALLS).' Tags: '500 LLM calls', 'two exits'. Q2: 'Static graph or dynamic workflow with ctx.run_node?' A2: 'Static graph for flows you can draw: construction-time validation checks schemas and adk web draws it. Dynamic @node for data-dependent fan-out and loops. A node that calls ctx.run_node must set rerun_on_resume=True. Python max_parallel_workers defaults to None, which means unlimited, so set a cap.' Tags: 'rerun_on_resume=True', 'workers: unlimited'. Q3: 'You port SequentialAgent to Workflow and the second agent forgets the user question. Why?' A3: 'Inside a Workflow an LlmAgent node defaults to mode single_turn with include_contents="none". Set include_contents="default" on nodes that need history. A mode="chat" agent never finishes a node, so it is legal only right after START; make it the root and put task agents under it.' Tags: 'single_turn', 'include_contents'. Notes: the back-edge reuses the same agent instance; a second Agent(name='write_copy') raises 'Duplicate node names found'.
- **visual:** Standard .qa layout, three .qa blocks stacked in a .stack.lg. All three .q lines are visible at step 0; each .a reveals on its own data-step (1, 2, 3) with data-fx up. The current pair gets a left accent bar in the chapter tone; earlier pairs dim to 55%. A .tags row under each answer shows the 1-3 numbers to say out loud (tag t-<tone>). A thin bar at the bottom (.bar data-fx=bar) fills 33/66/100% per step.

### c01-05-whiteboard-triage.html - Whiteboard: triage 10,000 support tickets a day without silent drops
- **id:** `adk-interview-c01-whiteboard-triage`
- **type:** whiteboard
- **content:** Kicker: 'Whiteboard · system design'. Left column (.panel.k-agent, step 0): the prompt - 'Design a triage system for a SaaS support desk: about 10,000 tickets a day; billing, outage and how-to tickets; p1 tickets must page on-call within a minute; nothing may be dropped; every decision must be auditable.' Under it, step 1: 'Clarify first' list (ul.clean, 3 items): label set closed or open? can one ticket have two labels? who owns the fallback queue? Right side: the reference architecture (below). Step 5: .callout.insight 'Say this: the LLM classifies into a closed set, code routes, DEFAULT_ROUTE catches the rest, and evals score the route, not only the reply.' Notes: walk the design in the order of the steps; mention a list route for multi-label tickets, Literal schema with a priority field, unit tests on route_ticket, per-node cost from node_info.path, and a trajectory eval that checks the route.
- **visual:** Large diagram (≈880x600, ≥40% of canvas) with data-wires: ticket (n-human pill) > intake (n-tool 'intake', ns 'function node') @1; intake > classify (n-model 'classify', ns 'output_schema=Triage') @1 [ticket text]; classify > route (n-tool 'route_ticket', ns 'code') @2 [Triage]; route > billing (n-agent) @3 [billing]; route > oncall (n-tool 'page_oncall') @3:flow{risk} [outage]; route > howto (n-agent 'how_to') @3; route > human (n-human 'L1 queue') @4:dash [DEFAULT]. ≤7 labelled wires, ≥80 px gaps, wires routed :lr. Step 4 also highlights a p1 ticket: a bespoke gsap token (Deck.register) leaves route and splits into two tokens that reach billing and page_oncall at the same time (list route). Step 5: a g-state dashed group 'trace + eval' fades in under the graph with two tags: 'route accuracy', 'p1 page < 60 s'. Deterministic animation, killed in leave.

### c01-06-debug-loop.html - Debug this: the compliance loop ran until the call cap stopped it
- **id:** `adk-interview-c01-debug-loop`
- **type:** debug
- **content:** Kicker: '<span class=pill>Debug this</span> loops'. Left: the buggy code (.code-wrap, head 'copy_review/agent.py', pre.code.xs, 28 lines). Right, step 1: symptom panel (.panel.k-risk): 'One ad brief ran 250 review rounds. The run then stopped at the 500-LLM-call cap. The critic never said compliant.' plus an output pane (.code-wrap.out, head 'output · illustrative') with node_path lines '.../write_copy@249', '.../review_copy@249', '.../gate@250' and a .dim comment '# 2 LLM calls per round x 250 = 500'. Step 2: hint line 'Which value does line 17 read in round 250?' with data-focus on line 9. Step 3 (answer): data-focus moves to line 17; a .gotcha card - Symptom: loop never escalates. Cause: gate reads ctx.state["round"] but nothing increments it, so it stays 0. Fix: increment the counter at the top of gate. Step 4: .code-wrap.good with the fix: 'ctx.state["round"] = ctx.state["round"] + 1' as the first line of gate, then the unchanged if/elif. Notes: graph cycles have no max_iterations; the 500-call cap is a cost backstop, not a design; log the round count so evals can measure rounds-to-compliant.
- **visual:** Code walk-through with data-focus="2:9, 3:17" synced to the hint and answer steps. Bespoke Deck.register counter beside the symptom: a round counter that counts up 1, 2, 3 ... 250 (gsap, deterministic) while a gauge 'LLM calls' fills to 500 and turns red at the cap; a second small counter labelled ctx.state["round"] stays at 0 the whole time (that is the clue). At step 4 the state counter starts to move 1, 2, 3 and the route arrow flips to 'escalate' at 3.
- **code (with the bug; numbered lines are the data-focus targets):**

```python
 1  from typing import Literal
 2  from google.adk import Agent, Context, Event, Workflow
 3  from pydantic import BaseModel
 4  MAX_ROUNDS = 3
 5  class Review(BaseModel):
 6    grade: Literal["compliant", "needs_fix"]
 7    feedback: str
 8  def brief(node_input: str):
 9    yield Event(state={"brief": node_input, "feedback": "", "round": 0})
10  write_copy = Agent(name="write_copy", model="gemini-3.5-flash", output_key="draft",
11      instruction="Write a 2-sentence ad for: {brief}. Apply this feedback: {feedback?}")
12  review_copy = Agent(name="review_copy", model="gemini-3.5-flash", output_schema=Review,
13      output_key="review", instruction="Must say 'Capital at risk.' Grade this ad: {draft}")
14  def gate(ctx: Context, node_input: Review):
15    if node_input.grade == "compliant":
16      yield Event(route="done")
17    elif ctx.state["round"] >= MAX_ROUNDS:
18      yield Event(route="escalate")
19    else:
20      yield Event(state={"feedback": node_input.feedback}, route="retry")
21  def publish(draft: str):
22    yield Event(message=f"PUBLISHED:\n{draft}")
23  def escalate(draft: str):
24    yield Event(message=f"Escalated to Legal. Last draft:\n{draft}")
25  root_agent = Workflow(name="copy_review", edges=[
26      ("START", brief, write_copy, review_copy, gate),
27      (gate, {"retry": write_copy, "done": publish, "escalate": escalate}),
28  ])
```

## Chapter 2: Durable execution and human-in-the-loop  (tone: human)

Scenario: Crash-safe payouts and a refund approval that a manager answers from a later process.

Research files:
- C:/Users/evija/googleadk2.0/research-v2/adk/00-VERIFIED.md
- C:/Users/evija/googleadk2.0/research-v2/adk/lab-workflows.md
- C:/Users/evija/googleadk2.0/research-v2/adk/lab-basics.md
- C:/Users/evija/googleadk2.0/research-v2/adk/gotchas.md
- C:/Users/evija/googleadk2.0/research-v2/adk/arxiv-reliability.md
- C:/Users/evija/googleadk2.0/research-v2/adk/lab-tools-protocols.md

### c02-01-chapter.html - Runs pause, crash and resume: side effects must happen once
- **id:** `adk-interview-c02-chapter`
- **type:** chapter
- **content:** class='slide chapter'. Chapter number 2. .display: 'Durable execution and human-in-the-loop'. .lede: 'Resume is at-least-once. Every answer in this chapter starts from that fact.' Tags: RetryConfig, RequestInput, require_confirmation, idempotency.
- **visual:** Self-animating mini timeline (Deck.register): a horizontal run bar with three node blocks; the middle block turns violet 'WAITING' and the bar breaks (process exits); a new bar starts below, the first block fast-forwards (replayed, grey), the rest runs green. A side-effect counter stays at 1.

### c02-02-qa-resume-retry.html - Retries and resume replay work, so design every write for twice
- **id:** `adk-interview-c02-qa-resume-retry`
- **type:** qa
- **content:** Kicker: 'Interview · retry and resume'. Three .qa pairs. Q1: 'After a crash, the resumed workflow charged the card twice. Why, and what is the fix?' A1: 'Resume is at-least-once: ADK says the tool call to resume needs to be idempotent. Send the gateway an idempotency key from the order id or invocation_id, never uuid4(). Also: retry_config on the parent workflow can re-run a finished sibling (#7524, open), so put it on the flaky node and test on your production session backend.' Tags: 'at-least-once', 'idempotency key'. Q2: 'Your RetryConfig never fires. What are the two usual causes?' A2: 'A broad except Exception in the node body swallows the failure, so the engine never sees it. And exceptions=[...] matches class names along the MRO: a timeout raises NodeTimeoutError, so add "NodeTimeoutError" to the list. Never catch BaseException: it traps NodeInterruptedError and breaks HITL pauses.' Tags: 'NodeTimeoutError'. Q3: 'A step fails. RetryConfig, a routed back-edge or ReflectAndRetryToolPlugin?' A3: 'RetryConfig for transient exceptions: defaults 5 attempts, 1.0 s initial, 60 s max, x2 backoff, jitter on; the model sees nothing. A back-edge for semantic failures: output is valid but wrong, the verifier reason goes back as feedback, with a round counter. ReflectAndRetryToolPlugin for tool errors the model can fix; override extract_error_from_result for soft errors returned as dicts.' Tags: '5 / 1 s / 60 s / x2'. Notes: the attempt counter is not persisted, so a node re-run after an interrupt or restart gets its full retry budget back; with jitter=0.0 delays are exact (0.5 s, 1.0 s).
- **visual:** Standard .qa layout, three .qa blocks stacked in a .stack.lg. All three .q lines are visible at step 0; each .a reveals on its own data-step (1, 2, 3) with data-fx up. The current pair gets a left accent bar in the chapter tone; earlier pairs dim to 55%. A .tags row under each answer shows the 1-3 numbers to say out loud (tag t-<tone>). A thin bar at the bottom (.bar data-fx=bar) fills 33/66/100% per step. Beside Q3 a small three-column decision strip (transient / semantic / model-fixable) whose column lights up with the answer step.

### c02-03-qa-hitl.html - Human approval is a protocol message, and it can be forged
- **id:** `adk-interview-c02-qa-hitl`
- **type:** qa
- **content:** Kicker: 'Interview · human-in-the-loop'. Three .qa pairs. Q1: 'How does a human-in-the-loop pause work on the wire in ADK 2.0?' A1: 'The node yields RequestInput. It becomes FunctionCall(name="adk_request_input", id=interrupt_id), listed in event.long_running_tool_ids. Any client resumes with a FunctionResponse with the same id. adk run exits with code 2 while paused and auto-resumes on the next call with the same --session_id.' Tags: 'exit code 2', 'long_running_tool_ids'. Q2: 'rerun_on_resume: True or False?' A2: 'False (hand-off): the node completes and the human reply becomes its output. True (re-entry): the node runs again from the top and reads ctx.resume_inputs. With True, derive the interrupt id from invocation_id and run_id; a uuid4 id changes on every rerun, so the node asks forever. Replies are JSON-parsed: a manager who types 100 gives you an int.' Tags: 're-entry vs hand-off'. Q3: 'Is a human approval a security boundary?' A3: 'Not by default. The ADK guard against a forged A2A confirmation was reverted on 2026-08-20 (#6461 open). Planted repo context got coding agents to request broad allow-rules in 58% of cases, then 81.0% silent malicious completion (2610.22987). Bind the approval to the exact effect, scope it to one interrupt id, put auth in front of api_server.' Tags: '58% -> 81.0%'. Notes: 2609.33910 - reusing earlier approvals raises attack success up to 35.1 pp; never cache 'manager said yes' in user: state.
- **visual:** Standard .qa layout, three .qa blocks stacked in a .stack.lg. All three .q lines are visible at step 0; each .a reveals on its own data-step (1, 2, 3) with data-fx up. The current pair gets a left accent bar in the chapter tone; earlier pairs dim to 55%. A .tags row under each answer shows the 1-3 numbers to say out loud (tag t-<tone>). A thin bar at the bottom (.bar data-fx=bar) fills 33/66/100% per step. Beside Q1 a mini sequence strip: node -> FunctionCall adk_request_input (violet) -> pause -> FunctionResponse same id (violet) -> node resumes; arrows draw at step 1.

### c02-04-whiteboard-refund-approval.html - Whiteboard: refunds over $500 wait for a manager, even overnight
- **id:** `adk-interview-c02-whiteboard-refund-approval`
- **type:** whiteboard
- **content:** Kicker: 'Whiteboard · system design'. Prompt panel (.panel.k-human): 'Design a refund flow: under $500 auto-approve; above it a manager approves, rejects or asks for a revised email, possibly the next day; the service redeploys and crashes; a refund must never be paid twice.' Step 1 'Clarify first': where do sessions live? can the manager change the amount? what is the audit record? Step 5 .callout.insight: 'Say this: durable session store, a re-entry gate with a deterministic interrupt id, the approval payload shows exactly what is approved, and the refund call carries an idempotency key.' Notes: mention ResumabilityConfig(is_resumable=True) for cross-call durability, drain paused runs before a graph change (checkpoint versioning is still open), and the Decline gate is enforced centrally since 2.10.0.
- **visual:** Large data-wires diagram (≈880x600): user (n-human pill) > intake (n-tool) @1; intake > draft (n-agent 'draft_reply') @1; draft > gate (n-human 'manager_gate', ns 'RequestInput') @2; gate > refund (n-tool 'issue_refund', ns 'key refund-<order>') @3 [approved]; gate > reject (n-tool 'notify_rejected') @3 [rejected]; gate > draft @4:bend-60 [revise]; store (n-state 'session store', ns 'SQLite / Agent Engine') -- gate @2:dash. Bespoke hook: at step 2 a token stops at the gate, the gate glows violet, and a 'process 1 exits' stamp appears; at step 3 a second token labelled 'process 2' starts at the store, intake and draft flash grey (replayed), and the token continues to issue_refund. A counter 'refunds paid: 1' stays at 1 through every step. Step 5 adds a small risk tag on the gate: 'scope approval to one interrupt'.

### c02-05-debug-interrupt-id.html - Debug this: the manager approves and the gate asks again
- **id:** `adk-interview-c02-debug-interrupt-id`
- **type:** debug
- **content:** Kicker: '<span class=pill>Debug this</span> human-in-the-loop'. Left: buggy code (head 'refund_approval/agent.py', pre.code.xs, 27 lines). Step 1 symptom (.panel.k-risk) plus output pane (head 'output · illustrative'): '$ adk run refund_approval "A-2040 820" --session_id case-2040' -> '(Paused for input...)' exit=2; '$ adk run refund_approval yes --session_id case-2040' -> 'Auto-resuming interrupt refund_approval_3f1...' then '(Paused for input...)' again. Step 2 hint: 'rerun_on_resume=True runs the node again from the top. What is iid on the second run?' (focus lines 9-10). Step 3 answer: focus lines 14-15; .gotcha - Symptom: every answer opens a new pause. Cause: uuid4() makes a new interrupt id on each rerun, so ctx.resume_inputs.get(iid) never matches the answered id. Fix: derive the id from the invocation and run. Step 4 .code-wrap.good: 'iid = f"refund_approval_{ctx.invocation_id}_{ctx.run_id}"'. Notes: the RequestInput docstring says reusing an id is supported but unique ids per loop pass are recommended - unique per pass, stable across reruns.
- **visual:** data-focus="2:9-10, 3:14-15". Bespoke Deck.register animation beside the code: two id tags side by side, 'answered: refund_approval_3f1...' (violet) and 'looked up: refund_approval_9c4...' (red); at step 3 they slide together and fail to match (red X). At step 4 both tags change to 'refund_approval_e7..._1' and lock together (green check); the route arrow goes to issue_refund.
- **code (with the bug; numbered lines are the data-focus targets):**

```python
 1  from uuid import uuid4
 2  from google.adk import Context, Event, Workflow
 3  from google.adk.events import RequestInput
 4  from google.adk.workflow import node
 5  AUTO_APPROVE_LIMIT = 500.0
 6  def intake(node_input: str):
 7    order_id, amount = node_input.split()[:2]
 8    yield Event(state={"order_id": order_id, "amount": float(amount)})
 9  @node(rerun_on_resume=True)
10  def manager_gate(ctx: Context, amount: float):
11    if amount <= AUTO_APPROVE_LIMIT:
12      yield Event(route="approved")
13      return
14    iid = f"refund_approval_{uuid4()}"
15    answer = ctx.resume_inputs.get(iid)
16    if answer is None:
17      yield RequestInput(interrupt_id=iid, message=f"Approve refund of ${amount:.2f}? yes/no")
18      return
19    yield Event(route="approved" if str(answer).lower() == "yes" else "rejected")
20  def issue_refund(order_id: str, amount: float):
21    yield Event(message=f"REFUNDED ${amount:.2f} on {order_id} (key refund-{order_id})")
22  def notify_rejected(order_id: str):
23    yield Event(message=f"Refund for {order_id} rejected.")
24  root_agent = Workflow(name="refund_approval", edges=[
25      ("START", intake, manager_gate),
26      (manager_gate, {"approved": issue_refund, "rejected": notify_rejected}),
27  ])
```

## Chapter 3: Context, state, memory and cost  (tone: state)

Scenario: An HR handbook assistant with state scopes, caching and compaction, and a 140-question account dossier.

Research files:
- C:/Users/evija/googleadk2.0/research-v2/adk/00-VERIFIED.md
- C:/Users/evija/googleadk2.0/research-v2/adk/lab-basics.md
- C:/Users/evija/googleadk2.0/research-v2/adk/lab-prod.md
- C:/Users/evija/googleadk2.0/research-v2/adk/arxiv-architectures.md
- C:/Users/evija/googleadk2.0/research-v2/adk/arxiv-tools-memory.md
- C:/Users/evija/googleadk2.0/research-v2/adk/industry.md
- C:/Users/evija/googleadk2.0/research-v2/adk/gotchas.md

### c03-01-chapter.html - What the model sees on each call decides quality and cost
- **id:** `adk-interview-c03-chapter`
- **type:** chapter
- **content:** class='slide chapter'. Chapter number 3. .display: 'Context, state, memory and cost'. .lede: 'Expect questions on state scopes, cache hits, compaction risks and the cost equation.' Tags: user: / app: / temp:, static_instruction, EventsCompactionConfig, Memory Bank, skills.
- **visual:** Self-animating mini-diagram: a request bar split into a long green 'cached prefix' block and a short coral 'new turn' block; on loop, the new-turn block grows turn by turn and a compaction bracket folds old turns into one small block. Deterministic gsap timeline.

### c03-02-qa-state-memory.html - State scope and memory deletion are where privacy bugs hide
- **id:** `adk-interview-c03-qa-state-memory`
- **type:** qa
- **content:** Kicker: 'Interview · state and memory'. Three .qa pairs. Q1: 'Which state prefix do you use for a user language, a tenant setting and scratch data? When is a write persisted?' A1: 'user:language follows the user across sessions; app: is global for the app; temp: lives for one invocation and is never persisted; no prefix is per session. A write commits when the Runner processes the event with its state_delta. get_session() returns a copy, so mutating it does nothing.' Tags: 'user: / app: / temp:'. Q2: 'preload_memory or load_memory?' A2: 'preload_memory searches memory on every turn: predictable, but it costs tokens and latency each turn. load_memory is a tool, so the model searches only when it needs past context. Neither one writes memory; you add the session to memory yourself, for example after the agent finishes.' Tags: 'per turn vs on demand'. Q3: 'A user asks you to erase their data. You call delete_session(). Are you done?' A3: 'No. Text copied into memory survives: search_memory() still returned a passport number after the session was deleted (#7109). ADK 2.13.0 adds BaseMemoryService.delete_memory; MemoryEntry.id is set for InMemory, Firestore and Memory Bank but not RAG. Memory also carries attacks: planted payloads re-fire across 5 rounds without decay (2610.28425).' Tags: 'delete_memory (2.13)', '5 rounds'. Notes: never store secrets in state; adk web prints it and GET /apps/.../sessions returns it.
- **visual:** Standard .qa layout, three .qa blocks stacked in a .stack.lg. All three .q lines are visible at step 0; each .a reveals on its own data-step (1, 2, 3) with data-fx up. The current pair gets a left accent bar in the chapter tone; earlier pairs dim to 55%. A .tags row under each answer shows the 1-3 numbers to say out loud (tag t-<tone>). A thin bar at the bottom (.bar data-fx=bar) fills 33/66/100% per step. Beside Q1 a small scope diagram: three nested rounded boxes app: > user: > session, with a dotted temp: chip that fades out at the end of the step.

### c03-03-qa-cache-cost.html - Turns drive agent cost: cache the prefix, compact without rewriting
- **id:** `adk-interview-c03-qa-cache-cost`
- **type:** qa
- **content:** Kicker: 'Interview · cache, compaction, cost'. Three .qa pairs. Q1: 'Why can the current time in the system prompt multiply your bill?' A1: 'It changes the prefix on every call, so the context cache never hits. Put long stable text in static_instruction and dynamic values in instruction. ADK creates no cache on turn 1, and the model minimum is 4096 tokens on Gemini 3 (2048 on 2.5). In one study 98.6% of input tokens came from the prefix cache, and turn count explained 84% of cost variance (2610.15093).' Tags: '4096 tokens', '98.6% cached'. Q2: 'What can go wrong with summarizing compaction?' A2: 'Summaries can invent facts: 83% of failed runs traced to an unsupported summary entry (2610.20927). Role flattening launders a forged "[User]:" approval in 87-100% of runs vs 0% when roles stay typed (2610.29869); ADK LlmEventSummarizer flattens to "author: text". Prefer truncate or drop; never compact a compaction. In ADK, set EventsCompactionConfig fields in pairs or you get a ValueError.' Tags: '83%', '87-100% vs 0%'. Q3: 'Agent spend doubled this month. How do you find out why?' A3: 'Decompose it: users x sessions/user x turns/session x requests/turn x tokens/request x price/token. Uber grew weekly agentic requests 9.4x while cost per session fell 52%: cheaper subagents, compaction at 400K tokens, cache TTL 5 min to 1 h. Report cost per successful outcome, not per call (2610.13092).' Tags: '9.4x', '-52%', '400K'. Notes: ContextCacheConfig defaults ttl_seconds=1800, cache_intervals=10 (1..100); extra='forbid', so a misspelled field raises.
- **visual:** Standard .qa layout, three .qa blocks stacked in a .stack.lg. All three .q lines are visible at step 0; each .a reveals on its own data-step (1, 2, 3) with data-fx up. The current pair gets a left accent bar in the chapter tone; earlier pairs dim to 55%. A .tags row under each answer shows the 1-3 numbers to say out loud (tag t-<tone>). A thin bar at the bottom (.bar data-fx=bar) fills 33/66/100% per step. Beside Q3 a bespoke six-term equation strip (Deck.register): the six factors appear as chips, and at the answer step three chips (turns, tokens, price) light up with Uber's levers.

### c03-04-qa-skills.html - Skills scale until routing collapses: preselect, do not pile up
- **id:** `adk-interview-c03-qa-skills`
- **type:** qa
- **content:** Kicker: 'Interview · skills and tools in context'. Three .qa pairs. Q1: 'Rule, skill, tool or sub-agent: what is the difference?' A1: 'A rule is always-on guidance. A skill is an on-demand folder of know-how, loaded by progressive disclosure (SkillToolset). A tool is one callable function. A sub-agent is a separate context with its own prompt, tools and model, and it returns a summary.' Tags: 'progressive disclosure'. Q2: 'You have 1,000 skills. What breaks?' A2: 'Implicit routing collapses: loaded-skill recall fell from 73.6% to 27.4% and the zero-load rate rose from 9.3% to 51.6% (2610.18522). Preselect a top-k set per request; preselection kept 73.9%. Two skills for the same job also clash: compliance fell from 93-99% to 61-62%, and one combined worked example cut takeover to 1-15% (2610.25064).' Tags: '73.6% -> 27.4%', '61-62%'. Q3: 'Should a skill run inline or as a sub-agent?' A3: 'Skills with clear input and output contracts work better as sub-agents; loose curated skills work as well or better inline, and sub-agents cost more tokens (2609.09233). In ADK, evicted skill text leaves the request only with ADK_ENABLE_SKILL_LIFECYCLE=1.' Tags: 'contract -> sub-agent'. Notes: skill directory name must equal the frontmatter name (kebab-case, at most 64 chars); since 2.10 run_skill_script is hidden when no skill has a script.
- **visual:** Standard .qa layout, three .qa blocks stacked in a .stack.lg. All three .q lines are visible at step 0; each .a reveals on its own data-step (1, 2, 3) with data-fx up. The current pair gets a left accent bar in the chapter tone; earlier pairs dim to 55%. A .tags row under each answer shows the 1-3 numbers to say out loud (tag t-<tone>). A thin bar at the bottom (.bar data-fx=bar) fills 33/66/100% per step. Beside Q2 a bespoke bar pair (Deck.register): recall bar shrinks 73.6 -> 27.4 as a distractor counter counts 0 -> 1,000; a third bar 'preselect top-k' snaps to 73.9.

### c03-05-whiteboard-dossier.html - Whiteboard: answer 140 questions per account without one giant context
- **id:** `adk-interview-c03-whiteboard-dossier`
- **type:** whiteboard
- **content:** Kicker: 'Whiteboard · system design'. Prompt panel (.panel.k-state): 'Pre-sales wants a 360-degree account document: 140+ standard questions per account, answered from CRM data and internal docs, with a confidence label per answer, written back to the CRM.' Step 1 'Clarify first': latency budget per document? which sources are trusted? who reads the confidence label? Step 5 .callout.insight: 'Say this: the document lives in my orchestrator, not in the agent context. One bounded agent call per question, five in flight, two answers scored for groundedness, asynchronous write-back.' Numbers (tags): '140+ questions', 'batches of 5', '2 agent endpoints', '3 confidence levels', 'about 2.5 h per document before optimization'. Notes: this is the Palo Alto Networks Document of Record design on ADK + Agent Engine (Google Cloud blog, 2026-01-14). One agent context for all 140 questions caused Out of Memory errors; orchestrator and agent in one GKE cluster caused pod crashes. Cite with .cite.doc.
- **visual:** Large data-wires diagram (≈900x600): crm (n-tool 'Salesforce trigger') > orch (n-agent 'Orchestrator', ns 'FastAPI on GKE') @1; orch > a1 (n-agent 'ADK agent A', ns 'Agent Engine') @2:flow [1 question]; orch > a2 (n-agent 'ADK agent B') @2:flow; a1 > rag (n-state 'RAG Engine') @2; a2 > rag @2; a1 > verify (n-risk 'groundedness score') @3; a2 > verify @3; verify > pubsub (n-tool 'Pub/Sub write-back') @4 [low/med/high]. Bespoke hook at step 2: 140 small dots queue at the orchestrator and leave in groups of exactly 5 (a counter 'in flight: 5' never exceeds 5; 'done: n/140' counts up deterministically). Step 1 also shows a ghost red bar 'one context for 140 questions -> OOM' (data-until=2).

### c03-06-debug-session-copy.html - Debug this: the language was set, and the agent raised KeyError
- **id:** `adk-interview-c03-debug-session-copy`
- **type:** debug
- **content:** Kicker: '<span class=pill>Debug this</span> session state'. Left: buggy code (head 'hr_state_debug.py', pre.code.sm, 22 lines). Step 1 symptom (.panel.k-risk) + output pane (head 'output'): '<span class=err>KeyError: "Context variable not found: `user:language` in agent \'hr_policy_agent\'."</span>' Step 2 hint: 'Line 17 sets the key. Which object did it change?' (focus line 8 then 16). Step 3 answer: focus lines 16-17; .gotcha - Symptom: KeyError on the template key. Cause: get_session() returns a deep copy; mutating s1.state never reaches the session service, so {user:language} is missing at render time. Fix: write state through an event. Step 4 .code-wrap.good: 'runner.run_async(user_id="emp-17", session_id=s1.id, new_message=msg, state_delta={"user:language": "German"})', and as an alternative seed it in create_session(state=...) or use {user:language?} to make it optional. Notes: tools write through tool_context.state and callbacks through callback_context.state; both go through events.
- **visual:** data-focus="2:8, 3:16-17". Bespoke Deck.register animation: two state boxes, 'session service' (green) and 's1 (copy)' (grey). At step 3 the key user:language drops into the copy box only; the service box stays without it and a red arrow from the template {user:language} hits the empty service box. At step 4 a state_delta event chip travels into the service box and the key appears there (green check).
- **code (with the bug; numbered lines are the data-focus targets):**

```python
 1  import asyncio
 2  from google.adk import Agent
 3  from google.adk.runners import InMemoryRunner
 4  from google.genai import types
 5  hr_agent = Agent(
 6      name="hr_policy_agent", model="gemini-3.5-flash",
 7      instruction=("You are the HR assistant for {app:company_name}. "
 8                   "Reply in {user:language}. Quote policy text exactly."),
 9      output_key="last_hr_answer",
10  )
11  async def main() -> None:
12      runner = InMemoryRunner(agent=hr_agent, app_name="hr_app")
13      svc = runner.session_service
14      s1 = await svc.create_session(app_name="hr_app", user_id="emp-17",
15                                    state={"app:company_name": "Acme Corp"})
16      s1 = await svc.get_session(app_name="hr_app", user_id="emp-17", session_id=s1.id)
17      s1.state["user:language"] = "German"
18      msg = types.UserContent(parts=[types.Part(text="How much parental leave do I get?")])
19      async for ev in runner.run_async(user_id="emp-17", session_id=s1.id, new_message=msg):
20          if ev.is_final_response():
21              print(ev.content.parts[0].text)
22  asyncio.run(main())
```

## Chapter 4: Tools, protocols and agent security  (tone: tool)

Scenario: A refund agent's tools, an MCP tool platform for many teams, and an A2A billing peer.

Research files:
- C:/Users/evija/googleadk2.0/research-v2/adk/00-VERIFIED.md
- C:/Users/evija/googleadk2.0/research-v2/adk/lab-tools-protocols.md
- C:/Users/evija/googleadk2.0/research-v2/adk/lab-basics.md
- C:/Users/evija/googleadk2.0/research-v2/adk/lab-prod.md
- C:/Users/evija/googleadk2.0/research-v2/adk/arxiv-reliability.md
- C:/Users/evija/googleadk2.0/research-v2/adk/arxiv-tools-memory.md
- C:/Users/evija/googleadk2.0/research-v2/adk/gotchas.md
- C:/Users/evija/googleadk2.0/research-v2/adk/industry.md

### c04-01-chapter.html - Every tool is an interface for a model and an attack surface
- **id:** `adk-interview-c04-chapter`
- **type:** chapter
- **content:** class='slide chapter'. Chapter number 4. .display: 'Tools, protocols and agent security'. .lede: 'Expect trade-off questions: MCP or A2A, prompt or code for policy, how many tools.' Tags: FunctionTool, McpToolset, to_a2a, before_tool_callback, Model Armor.
- **visual:** Self-animating mini-diagram: an n-agent node with four n-tool nodes around it; one tool node turns red (n-risk) on loop, a small shield chip (before_tool_callback) slides onto its wire and the pulse on that wire stops. Deterministic.

### c04-02-qa-tools-protocols.html - Fewer, honest tools beat many; protocols are trust boundaries
- **id:** `adk-interview-c04-qa-tools-protocols`
- **type:** qa
- **content:** Kicker: 'Interview · tools, MCP, A2A'. Three .qa pairs. Q1: 'How do you make the model pick the right tool?' A1: 'The docstring becomes the tool description verbatim; Args: is not parsed, so describe parameters with Annotated[..., Field(description=...)]. Keep parameters flat and few tools: Shopify sees boundaries blur at 20-50 tools; Vercel cut 17 tools to 2 and went from 274.8 s to 77.4 s on 5 queries. When only names differ, the first-listed tool wins 92-100% (2610.14334).' Tags: '0-20 / 20-50 / 50+', '274.8 s -> 77.4 s'. Q2: 'Another team owns billing. Do you connect with MCP or A2A?' A2: 'MCP if they expose typed tools and data: McpToolset with tool_filter. A2A if they expose an agent with its own model, memory and policy: RemoteA2aAgent on your side, to_a2a on theirs. Session state does not cross the A2A boundary, and card security_schemes are metadata, not enforcement, so pass data in the message and authenticate the transport.' Tags: 'state does not cross'. Q3: 'Your MCP server restarts. What does the agent see?' A3: 'Before 2.10 the toolset reused a dead session forever. With graceful error handling the agent gets a dict, "MCP tool execution failed: Session terminated", not an exception, so alert on that string. A toolset that fails to load is logged at ERROR and the agent runs without those tools. Write errors for agents: naming the recovery tool call lifted credential recovery 45% -> 84% (2609.35381).' Tags: '45% -> 84%'. Notes: 91.8% of 414 internet-facing MCP servers lacked OAuth (2608.00150); legacy MCP handshake 3 RTT / 230 ms vs A2A 1 RTT / 61 ms (2610.30151).
- **visual:** Standard .qa layout, three .qa blocks stacked in a .stack.lg. All three .q lines are visible at step 0; each .a reveals on its own data-step (1, 2, 3) with data-fx up. The current pair gets a left accent bar in the chapter tone; earlier pairs dim to 55%. A .tags row under each answer shows the 1-3 numbers to say out loud (tag t-<tone>). A thin bar at the bottom (.bar data-fx=bar) fills 33/66/100% per step. Beside Q2 a small two-lane comparison: MCP lane (agent -> typed tools, amber) vs A2A lane (agent -> remote agent with its own state box, blue), with a red dashed line 'state stops here' on the A2A lane.

### c04-03-qa-security.html - Policy belongs in deterministic code, not in the system prompt
- **id:** `adk-interview-c04-qa-security`
- **type:** qa
- **content:** Kicker: 'Interview · agent security'. Three .qa pairs. Q1: 'Where does the allow or deny decision for a refund live?' A1: 'In code: a before_tool_callback or plugin that checks the amount against a value set by trusted code, and returns a dict to skip the tool. System prompts are soft constraints. LLM guardrails fail open: six irrelevant log lines raised fail-open from 0% to 63% (2610.12292). Deterministic origin checks kept attack success at 1.6-2.6% (ROPE, 2608.27496).' Tags: '0% -> 63%', '1.6-2.6%'. Q2: 'Why must the user identity come from trusted state, not a tool argument?' A2: 'Injected text can change the arguments the model writes. Read the caller id from session state in the callback and block a mismatch, as the HrGuardPlugin does for get_salary_band. Note the names: plugin hooks receive tool_args, agent-level callbacks receive args.' Tags: 'tool_args vs args'. Q3: 'A web page tells your research sub-agent to call send_email. How do you contain it?' A3: 'Scope tools per agent: the reader has no send tool. In a 14-vector test, tool-output injection succeeded 43%, and privilege-scoped tools cut overall success from 31.2% to 4.2% (2609.22949). Screen tool outputs with Model Armor, and gate irreversible tools with confirmation. Detectors alone do not transfer: the best caught 2% of AgentDojo injections at 1% FPR (2610.03448).' Tags: '31.2% -> 4.2%', '2% caught'. Notes: low attack-success rates in small agents mostly mean attacks were ignored, not refused; the system prompt alone moved ASR 0.2% -> 43% (2610.23254).
- **visual:** Standard .qa layout, three .qa blocks stacked in a .stack.lg. All three .q lines are visible at step 0; each .a reveals on its own data-step (1, 2, 3) with data-fx up. The current pair gets a left accent bar in the chapter tone; earlier pairs dim to 55%. A .tags row under each answer shows the 1-3 numbers to say out loud (tag t-<tone>). A thin bar at the bottom (.bar data-fx=bar) fills 33/66/100% per step.

### c04-04-whiteboard-tool-platform.html - Whiteboard: give 40 teams' agents safe access to 300 MCP tools
- **id:** `adk-interview-c04-whiteboard-tool-platform`
- **type:** whiteboard
- **content:** Kicker: 'Whiteboard · system design'. Prompt panel (.panel.k-tool): 'Your company has 300+ internal MCP tools from 40 teams. Design how agents discover, authenticate to and call them, with per-user permissions, low token cost and an audit trail.' Step 1 'Clarify first': which calls act as the user and which as a service account? which tools write? who approves a new server? Step 5 .callout.insight: 'Say this: a gateway owns auth and per-tool authorization, agents see a preselected small tool set, tool outputs are screened, writes need confirmation, and every call is traced.' Numbers (tags): '50K-70K tokens for 100+ tool schemas (Uber)', '91.8% of exposed MCP servers lack OAuth', '16.4% expose filesystem capability under other labels', 'first-listed tool wins 92-100%'. Notes: official SDKs lack fine-grained per-tool authorization and dual-persona support (2609.22573); GatewayBench compared 7 gateways over 11,118 real tools (2610.23449); in ADK use McpToolset(tool_filter=[...], tool_name_prefix=...) and require_confirmation for write tools.
- **visual:** Large data-wires diagram (≈900x600): agent (n-agent 'team agent') > search (n-tool 'tool search', ns 'top-k per request') @1 [intent]; agent > gw (n-tool 'MCP gateway', ns 'auth + per-tool authz') @2:flow [tool call]; user (n-human 'user identity') > gw @2:dash [OAuth]; gw > s1 (n-tool 'HR MCP') @3; gw > s2 (n-tool 'Billing MCP') @3; gw > armor (n-risk 'Model Armor', ns 'tool output screen') @4 [result]; armor > agent @4:bend60; audit (n-state 'trace + audit log') -- gw @5:dash. Bespoke hook at step 1: a token counter beside the agent drops from '300 tools · 60K tokens' to '8 tools · 2K tokens' as tool chips fade out (illustrative label on the slide). Step 4: a red injected chip in a tool result is caught at Model Armor and turns grey.

### c04-05-debug-fail-open.html - Debug this: a $1,299 refund ran with no approval prompt
- **id:** `adk-interview-c04-debug-fail-open`
- **type:** debug
- **content:** Kicker: '<span class=pill>Debug this</span> tool confirmation'. Left: buggy code (head 'refund_hitl/agent.py', pre.code.sm, 22 lines). Step 1 symptom (.panel.k-risk): 'In the new staging project, a $1,299 refund ran without the approval prompt. In production the same code asks for approval.' Output pane (head 'output · illustrative'): '[user]: Refund $1299 on order A-1002' then '[refund_hitl]: Done. Refund RF-A-1002 for $1,299.00 has been issued.' Step 2 hint: 'What does needs_approval return when the staging project has no app:approval_limit_usd?' (focus line 21 then 12). Step 3 answer: focus lines 13-14; .gotcha - Symptom: the gate is skipped. Cause: the bare return gives None, which is falsy, so ADK treats it as no confirmation needed; the -> bool hint does nothing at run time (issue #7010, PR #7012 open). Fix: fail closed and return a real bool. Step 4 .code-wrap.good: 'if limit is None:\n        return True   # fail closed' and 'return bool(amount_usd > float(limit))'. Notes: the predicate receives the tool's own arguments, so it must have the same parameter names (or **kwargs); gate irreversible actions in code, never with 'ask before refunding' in the prompt.
- **visual:** data-focus="2:21, 3:13-14". Bespoke Deck.register gate animation beside the code: a refund token ($1,299) moves toward a violet gate. At step 3 the predicate chip shows 'None', the gate swings open (red, 'fail open') and the token passes to issue_refund. At step 4 the chip shows 'True', the gate closes, and the token stops with a violet 'approve?' prompt.
- **code (with the bug; numbered lines are the data-focus targets):**

```python
 1  from google.adk import Agent
 2  from google.adk.tools import FunctionTool, ToolContext
 3  
 4  def issue_refund(order_id: str, amount_usd: float, tool_context: ToolContext) -> dict:
 5      """Issue a refund to the original payment method. Irreversible."""
 6      issued = tool_context.state.get("refunds_issued", [])
 7      tool_context.state["refunds_issued"] = issued + [{"order_id": order_id, "amount_usd": amount_usd}]
 8      return {"status": "success", "refund_id": f"RF-{order_id}", "amount_usd": amount_usd}
 9  
10  def needs_approval(order_id: str, amount_usd: float, tool_context: ToolContext) -> bool:
11      """Same parameters as issue_refund: ADK calls it with the tool's arguments."""
12      limit = tool_context.state.get("app:approval_limit_usd")
13      if limit is None:
14          return                      # limit not configured in this environment
15      return amount_usd > float(limit)
16  
17  root_agent = Agent(
18      name="refund_hitl", model="gemini-3.5-flash",
19      instruction=("You process refunds. Call issue_refund with the order ID and amount. "
20                   "If the tool says the call was rejected, say a supervisor declined it."),
21      tools=[FunctionTool(issue_refund, require_confirmation=needs_approval)],
22  )
```

## Chapter 5: Evals, observability and production  (tone: risk)

Scenario: Shipping the refund agent weekly: eval gates, judges, traces, deploy targets and upgrades.

Research files:
- C:/Users/evija/googleadk2.0/research-v2/adk/00-VERIFIED.md
- C:/Users/evija/googleadk2.0/research-v2/adk/lab-prod.md
- C:/Users/evija/googleadk2.0/research-v2/adk/arxiv-reliability.md
- C:/Users/evija/googleadk2.0/research-v2/adk/gotchas.md
- C:/Users/evija/googleadk2.0/research-v2/adk/industry.md

### c05-01-chapter.html - An agent is production-ready when a gate can fail it
- **id:** `adk-interview-c05-chapter`
- **type:** chapter
- **content:** class='slide chapter'. Chapter number 5. .display: 'Evals, observability and production'. .lede: 'Expect questions on pass^k, judge trust, silent telemetry breaks and safe upgrades.' Tags: adk eval, AgentEvaluator, user simulation, OpenTelemetry, adk deploy.
- **visual:** Self-animating mini-diagram: a pipeline of four boxes (commit, eval gate, canary, prod); a token moves along; on alternate loops the eval gate turns red and the token stops (exit 1), then a fixed token passes. Deterministic loop index decides pass or fail.

### c05-02-qa-evals.html - Report pass^k, check the trajectory, and calibrate the judge
- **id:** `adk-interview-c05-qa-evals`
- **type:** qa
- **content:** Kicker: 'Interview · evaluation'. Three .qa pairs. Q1: 'For a customer-support agent, do you report pass@k or pass^k?' A1: 'pass^k: every attempt must succeed, because each customer gets one attempt. At 75% per trial, pass^3 = 0.75^3 = 42%, while pass@3 = 98% looks fine. In ADK 2.13 run AgentEvaluator.evaluate(..., num_runs=3); the default is 2. adk eval has no repeat flag.' Tags: '0.75^3 = 42%', 'num_runs=3'. Q2: 'EXACT, IN_ORDER or ANY_ORDER trajectory matching?' A2: 'EXACT allows no extra or missing calls. IN_ORDER needs the expected calls in order but allows extras. ANY_ORDER ignores order. EXACT fails a harmless extra lookup and makes a better plan look worse, so keep it for strict regulated flows. Use ignore_args when arguments vary, plus a custom metric for hard rules such as no refund above 500.' Tags: 'IN_ORDER + ignore_args'. Q3: 'Can you trust your LLM judge?' A3: 'Only after you measure it. Shopify raised judge agreement with humans from kappa 0.02 to 0.61 against a human ceiling of 0.69. In user simulation, 57.5% of "satisfied" conversations had failed the task (2609.12191), so add a judge-free completion check on backend state. A pinned temperature-0 judge still flips about 5% of verdicts on reruns (2609.33044).' Tags: 'kappa 0.02 -> 0.61', '57.5%'. Notes: CXBench - 55.5% of runs were false passes (right outcome, non-compliant process), only 13.8% passed both (2610.25954); keep a known-good and a known-bad fixture in every gate (safety_v1 silently became safety_v3, #7258).
- **visual:** Standard .qa layout, three .qa blocks stacked in a .stack.lg. All three .q lines are visible at step 0; each .a reveals on its own data-step (1, 2, 3) with data-fx up. The current pair gets a left accent bar in the chapter tone; earlier pairs dim to 55%. A .tags row under each answer shows the 1-3 numbers to say out loud (tag t-<tone>). A thin bar at the bottom (.bar data-fx=bar) fills 33/66/100% per step. Beside Q1 a bespoke bar pair (Deck.register): pass@3 bar grows to 98% while pass^3 bar grows only to 42%, both from the same three 75% trial dots.

### c05-03-qa-production.html - Production questions test what breaks silently after deploy
- **id:** `adk-interview-c05-qa-production`
- **type:** qa
- **content:** Kicker: 'Interview · deploy and operate'. Three .qa pairs. Q1: 'Agent Runtime, Cloud Run or GKE?' A1: 'Agent Runtime for managed sessions, Memory Bank and the least ops. Cloud Run for a custom API surface and revisions; pass --session_service_uri or sessions fall back to in-memory and die with the instance. GKE for your own cluster, GPUs or self-hosted models; adk deploy gke defaults to ClusterIP, no public IP.' Tags: 'agentengine://', 'ClusterIP'. Q2: 'What in ADK 2.13 can silently break your monitoring?' A2: 'Telemetry now defaults to OTel GenAI semconv 1.44 and the call_llm span is removed, so dashboards keyed on it read zero. Opt back with ADK_TELEMETRY_SCHEMA_VERSION_OPT_IN=otel_semconv_1_36. Under MCP SDK 2.x, MCP calls go untraced. Also ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS defaults to true, so prompts with PII land in traces.' Tags: 'call_llm removed', 'PII in spans'. Q3: 'How do you upgrade ADK safely?' A3: 'Pin google-adk, mcp, a2a-sdk and litellm everywhere: 13 minor releases shipped in 5 months, several with breaking changes. Read the CHANGELOG breaking-changes block, run the eval gate (adk eval exits 1 on failure since 2.13.0), canary the new image and keep the old one deployable. Version skew caused "LlmAgent object has no attribute mode" in the cloud.' Tags: '13 releases / 5 months', 'exit 1'. Notes: Anthropic's April 2026 postmortem - three harness changes caused a quality drop that passed review and tests; run a per-model eval on every prompt or harness change.
- **visual:** Standard .qa layout, three .qa blocks stacked in a .stack.lg. All three .q lines are visible at step 0; each .a reveals on its own data-step (1, 2, 3) with data-fx up. The current pair gets a left accent bar in the chapter tone; earlier pairs dim to 55%. A .tags row under each answer shows the 1-3 numbers to say out loud (tag t-<tone>). A thin bar at the bottom (.bar data-fx=bar) fills 33/66/100% per step. Beside Q1 a three-column target strip (Agent Runtime / Cloud Run / GKE) with one icon-free line each; the chosen column lights per sentence.

### c05-04-whiteboard-release-pipeline.html - Whiteboard: ship the refund agent weekly without a silent regression
- **id:** `adk-interview-c05-whiteboard-release-pipeline`
- **type:** whiteboard
- **content:** Kicker: 'Whiteboard · system design'. Prompt panel (.panel.k-risk): 'The refund agent ships every week. Prompts, tools and the model change. Design the evaluation and release pipeline so a regression cannot reach customers unnoticed.' Step 1 'Clarify first': what is a failure (wrong refund, policy breach, bad tone)? how much traffic for a canary? who labels ground truth? Step 5 .callout.insight: 'Say this: layered evals with some deploy-blocking, k > 1 runs, a calibrated judge plus judge-free state checks, a canary watched on agent SLIs, and failing traces turned into new eval cases.' Numbers (tags): 'Rippling: 300-400 post-merge queries, about 10 deploy-blocking scenarios', 'Shopify judge kappa 0.61 vs human 0.69', 'adk eval exit 1 since 2.13.0', 'MASIF: implicit failures in 54.3% of successful traces'. Notes: agent SLIs - tokens per invocation, LLM calls per invocation (the loop signature), tool error rate, and an online task-success score; user simulation with personas (llm_backed simulator) adds multi-turn cases.
- **visual:** Large data-wires diagram (≈920x560), left to right: pr (n-human 'PR: prompt/tool/model') > offline (n-state 'offline evals', ns 'adk eval, every commit') @1; offline > integ (n-state 'integration', ns 'sandbox + simulator') @2 [exit 0]; integ > block (n-risk 'deploy-blocking', ns '~10 scenarios') @2; block > canary (n-tool 'canary', ns 'agent SLIs') @3; canary > prod (n-agent 'production') @3; prod > traces (n-state 'traces') @4:flow; traces > offline @4:bend-60 [new eval case]. Bespoke hook at step 2: a failing build token turns red at 'deploy-blocking' with an 'exit 1' stamp and goes back to the PR; a fixed token passes. At step 4 a loop pulse runs prod -> traces -> offline to show failing traces becoming eval cases.

### c05-05-debug-cloud-run-sessions.html - Debug this: users lose their conversation after each scale event
- **id:** `adk-interview-c05-debug-cloud-run-sessions`
- **type:** debug
- **content:** Kicker: '<span class=pill>Debug this</span> deployment'. Left: buggy script (.code-wrap.term, head 'deploy.sh', pre.code.sm data-lang=bash, 13 lines). Step 1 symptom (.panel.k-risk): 'After a traffic spike, some users start a new conversation in the middle of a refund. It also happens after each new revision.' Output pane (head 'output · illustrative'): two curl results for the same session id s1, the second returning a 404 or an empty history (mark illustrative). Step 2 hint: 'How many instances can run, and where does each one keep sessions?' (focus line 8 then 6). Step 3 answer: focus line 6; .gotcha - Symptom: sessions disappear. Cause: a SQLite file on the container disk is local to one instance and is lost when the instance is recycled; each new instance has its own empty file. Fix: use a shared session service. Step 4 .code-wrap.good: '--session_service_uri="agentengine://1234567890"' (managed Agent Runtime sessions), or a managed Postgres URL with google-adk[db]. Notes: without the flag at all, the docs say the container falls back to in-memory session and artifact services and sessions are lost whenever an instance is recycled; do not ship --with_ui to production; keep --no-allow-unauthenticated.
- **visual:** data-focus="2:8, 3:6". Bespoke Deck.register animation: a load balancer box sends requests for session s1 to instance A (with a small 'sessions.db' cylinder holding s1). At step 2 a second instance B appears (scale-out) with an empty cylinder; the next s1 request goes to B and the history panel empties (red). At step 3 instance A is recycled and its cylinder disappears. At step 4 both instances connect to one shared green 'Agent Runtime sessions' cylinder and s1 survives every request.
- **code (with the bug; numbered lines are the data-focus targets):**

```bash
 1  # deploy.sh: refund_agent on Cloud Run (google-adk==2.13.0)
 2  export PROJECT=my-proj REGION=us-central1
 3  pip install "google-adk[gcp]==2.13.0"
 4  adk deploy cloud_run --project=$PROJECT --region=$REGION \
 5    --service_name=refund-agent \
 6    --session_service_uri="sqlite:///./sessions.db" \
 7    refund_agent \
 8    -- --no-allow-unauthenticated --min-instances=1
 9  
10  # smoke test
11  URL=$(gcloud run services describe refund-agent --region=$REGION --format='value(status.url)')
12  TOKEN=$(gcloud auth print-identity-token)
13  curl -X POST -H "Authorization: Bearer $TOKEN" $URL/apps/refund_agent/users/u1/sessions/s1
```
