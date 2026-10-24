# 06 — Loop, Graph, Context, Harness and Flow Engineering, Mapped to ADK 2.0

Research date: 2026-10-23. Sources: adk.dev raw Markdown pages; `google/adk-python` on `main` (shallow clone, HEAD `6c20444`, 2026-10-23, CHANGELOG through 2.13.0); the Google Developers Blog; and each term's primary source.
**Method caveat.** The session's WebSearch budget was used up before this file was started, so every fact below comes from a URL I fetched directly or from source code I read. Where I could not fetch a primary page (openai.com returned 403), the claim is marked **[UNVERIFIED]**. Nothing here comes from search snippets.

Product naming: Agentspace → **Gemini Enterprise**. Vertex AI Agent Engine → **Agent Runtime** on the **Gemini Enterprise Agent Platform** (Next '26 codelabs). The CLI verb `adk deploy agent_engine` is unchanged. ADK docs moved from google.github.io/adk-docs to **adk.dev** (301 redirect). Exact rename dates are in file 01/03 of this series; I did not re-check them here.

---

## 0. One-slide thesis

**Prompt engineering (2022–23) → flow engineering (Jan 2024) → context engineering (Jun 2025) → harness engineering (Feb 2026), with loop and graph engineering as the control-flow layer.**
Each step moves the engineer's attention *outward*: from the words in one call, to the sequence of calls, to what each call sees, to the whole environment (tests, linters, progress files, sensors) the agent runs inside. ADK 2.0 (Python GA 2026-05-19) is Google's bet on the control-flow layer. "Workflows separate execution routing from language processing" (*Why we built ADK 2.0*, 2026-07-01).

| Discipline | The question it answers | Who named or popularized it (verified) | ADK 2.0 home |
|---|---|---|---|
| Flow engineering | What sequence of LLM and test steps solves this class of task? | Ridnik, Kredo, Friedman (CodiumAI), arXiv 2401.08500, 2024-01-16 | `Workflow(edges=...)`, dynamic `@node` |
| Context engineering | What exactly does the model see on this step? | Popularized June 2025 by Tobi Lütke and Andrej Karpathy (via Simon Willison, 2025-06-27). Anthropic post 2025-09-29. LangChain post 2025-07-02 | `include_contents`, `static_instruction`, compaction, caching, `ContextFilterPlugin`, artifacts, memory |
| Harness engineering | Whenever the agent makes a mistake, what do I build so it never makes it again? | Mitchell Hashimoto, 2026-02-05. OpenAI post [UNVERIFIED date/author]. Böckeler, martinfowler.com, 2026-04-02 | Plugins, eval sets as regression tests, `RetryConfig`, `ToolCallIntegrityPlugin` |
| Loop engineering | When does the loop stop, retry, reflect or escalate, and what does it cost? | No single verified coiner (see §2). Roots: Huntley's "Ralph" loop (2025-07-14); Anthropic's agent loop (2025-09-29) | `max_llm_calls`, routers, `RetryConfig`, `ReflectAndRetry*Plugin`, `ModelConsultTool`, `abort_signal` |
| Graph engineering | Which edges are hard-coded and which are chosen by the LLM? | Practice term; 12-Factor Agents "Own your control flow"; Harrison Chase 2025-04-20; Google ADK 2.0 blog | `Workflow` edges, `Event(route=)`, `ClassifierNode`, nested workflows |
| Evaluator-optimizer / verifier-in-the-loop | Who checks each step, and how cheap and objective is that check? | Anthropic *Building effective agents* 2024-12-19. Jason Wei "verifier's rule" 2025-07-15 | critic node plus back-edge, `output_schema` grading, `adk eval` rubrics |

---

## 1. Flow engineering (AlphaCodium, 2024)

- **Paper:** "Code Generation with AlphaCodium: From Prompt Engineering to Flow Engineering", Tal Ridnik, Dedy Kredo, Itamar Friedman (CodiumAI, now Qodo), arXiv:2401.08500 v1, **16 Jan 2024**. https://arxiv.org/abs/2401.08500
- **Definition (abstract):** "a test-based, multi-stage, code-oriented iterative flow."
- **Headline number:** "GPT-4 accuracy (pass@5) increased from 19% with a single well-designed direct prompt to 44% with the AlphaCodium flow" on the CodeContests validation set (117 validation and 165 test problems, per the README).
- **Flow stages:** these are the configurable sections of `alpha_codium/settings/configuration.toml` in https://github.com/Codium-ai/AlphaCodium: `self_reflection` → `possible_solutions` → `generate_ai_tests` → `initial_code_generation` → `public_tests` → `ai_tests`. The README shows the pipeline as two phases. Pre-processing is reflection on the problem, then candidate solutions, then AI-generated tests. Code iterations are generate, then run public tests and fix, then run AI tests and fix.
- **Lesson for agents:** quality comes from the *shape of the process* plus *executable verifiers* (tests) placed between steps, not from a longer prompt.

**ADK 2.0 mapping.** AlphaCodium is essentially the docs' dynamic "Loop route" example: generate, lint/compile check, then fix while findings exist (verbatim from https://adk.dev/graphs/dynamic/):
```python
@node # workflow node
async def code_workflow(ctx: Context, user_request: str):
  code = await ctx.run_node(coder_agent, user_request)
  check_resp = await ctx.run_node(compile_lint_check, code)

  while check_resp.findings:
    yield Event(state={"code": code, "findings": check_resp.findings})
    code = await ctx.run_node(fixer_agent, {"code": code, "findings": check_resp.findings})

    check_resp = await ctx.run_node(compile_lint_check, code)

  yield Event(output=code)
```
The docs add: "Unlike a graph cycle, the loop is bounded by its loop condition." The TypeScript variant on the same page adds `const MAX_FIX_ROUNDS = 3; /** Safety bound on the refine loop. */`. **Teaching point:** the Python sample has no round cap. In production, add one: `while check_resp.findings and rounds < MAX_FIX_ROUNDS`.

---

## 2. Loop engineering

### 2.1 Provenance (honest status)
- I could not verify a single coiner of "loop engineering". Huntley's Ralph post does not contain the phrase. Treat it as a 2025–26 practitioner term **[UNVERIFIED origin]**.
- **Geoffrey Huntley, "Ralph Wiggum as a 'software engineer'"**, 2025-07-14, https://ghuntley.com/ralph/. "In its purest form, Ralph is a Bash loop":
  ```bash
  while :; do cat PROMPT.md | claude-code ; done
  ```
  Also from the post: "Ralph works autonomously in a single repository as a single process that performs one task per loop." It has a section titled "loop back is everything". The technique is "deterministically bad in an undeterministic world", meaning the failures are predictable enough to tune: each time a loop fails, you edit PROMPT.md or AGENT.md.
- **Anthropic, "Building agents with the Claude Agent SDK"**, Thariq Shihipar, 2025-09-29 (now at https://claude.com/blog/building-agents-with-the-claude-agent-sdk). The canonical loop is "gather context -> take action -> verify work -> repeat". It lists three verification styles: rules (lint), visual feedback (screenshots via Playwright MCP), and LLM-as-judge ("not very robust", adds latency).
- **12-Factor Agents**, Dex Horthy (HumanLayer), https://github.com/humanlayer/12-factor-agents (screenshot dated 2025-04-03). The README describes the naive loop: the LLM picks a step, code executes it, the result is appended, repeat until "done". It says this "doesn't quite work". Factors 8 "Own your control flow", 9 "Compact Errors into Context Window" and 6 "Launch/Pause/Resume with simple APIs" are loop-engineering rules.

### 2.2 The six levers of a loop (definition used in this deck)
1. **Stop condition.** A verifier passes, or a terminal route, or `escalate`.
2. **Budget.** Caps on iterations, LLM calls, tokens and wall-clock time.
3. **Feedback shape.** What the next iteration sees: the critique, the error, the diff.
4. **Retry policy.** Transient retries (backoff) are a different thing from semantic retries (reflect, then retry).
5. **Escalation.** To a stronger model, to a human, or to an abort.
6. **Durability.** Checkpoint, resume, idempotent side effects.

### 2.3 ADK 2.0 implementation of each lever (all verified in source or docs)

| Lever | ADK primitive | Exact facts |
|---|---|---|
| Global LLM-call budget | `RunConfig.max_llm_calls` | Default **500** (`_DEFAULT_MAX_LLM_CALLS = 500`, `agents/run_config.py`). Env override `ADK_MAX_LLM_CALLS` (2.8.0). A value ≤ 0 means unbounded (a warning is logged). When the cap is exceeded, `InvocationContext` raises `LlmCallsLimitExceededError("Max number of llm calls limit of `N` exceeded")`. |
| Iteration cap (1.x) | `LoopAgent(max_iterations=N)` + `exit_loop` tool | `exit_loop` sets `tool_context.actions.escalate = True` and `skip_summarization = True`. 2.9.0: "treat a max_iterations of zero as zero loop passes". Deprecated in favour of `Workflow`, and rejected *inside* `Workflow` graphs since 2.5.0. |
| Iteration cap (2.0 graph) | **None built in.** You bound it in the router. | The routes page says to make sure the exit condition eventually becomes true, or to use a dynamic workflow so you control the bound (https://adk.dev/graphs/routes/). |
| Iteration cap (2.0 dynamic) | Ordinary `while`/`for` in a `@node` | TS sample `MAX_FIX_ROUNDS = 3`. |
| Transient retry | `@node(retry_config=RetryConfig(...))` | Defaults: `max_attempts=5` (includes the first attempt), `initial_delay=1.0`, `max_delay=60.0`, `backoff_factor=2.0`, `jitter=1.0`, `exceptions=None` (= all). `ctx.attempt_count` is exposed. |
| Semantic retry, tools | `ReflectAndRetryToolPlugin(max_retries=3, throw_exception_if_retry_exceeded=True, tracking_scope=TrackingScope.INVOCATION)` | Docstring: "self-healing, concurrent-safe error recovery for tool failures … provides structured guidance to the LLM for reflection and correction". Counters are per tool, and a success resets that tool's counter. Override `extract_error_from_result` to catch soft errors such as `{"status": "error"}`. Since 1.16.0. |
| Semantic retry, model | `ReflectAndRetryModelPlugin(max_retries=3, …, on_model_errors=[types.FinishReason…])` | 2.6.0. The injected guidance says "This is retry attempt **{retry_count}** of **{max_retries}**". |
| Per-node timeout | `@node(timeout=...)` → `NodeTimeoutError` | Exported from `google.adk.workflow`. |
| Escalate to a stronger model | `ModelConsultTool(model=..., max_uses=2, session_max_uses=5)` + `ForceEscalationPlugin` | 2.11.0. "Lets an executor agent consult a stronger advisor model mid-generation … the bulk of token generation stays at executor rates." The docstring example pairs `gemini-3.5-flash` (executor) with `gemini-3.1-pro-preview` (advisor). `thinking_level` defaults to `'high'`. `ForceEscalationPlugin` "Forces `model_consult` calls that a weak executor would otherwise skip." |
| Escalate to a human | `RequestInput(...)`, `@node(require_confirmation=...)` (2.12), `FunctionTool(require_confirmation=)` | The workflow pauses and the invocation ends. It resumes with `ctx.resume_inputs[interrupt_id]`. |
| Abort | `abort_signal: asyncio.Event` on `Runner.run_async` (2.11.0) | `/run_sse` cancels when the client disconnects. |
| Model outage | Model failover (2.9.0) | [UNVERIFIED exact config key; check the 2.9.0 CHANGELOG] |
| Durability | Node checkpoints, `rerun_on_resume`, at-least-once tools | 2.9.0 behaviour change: "A node that failed now runs again when the workflow resumes", so node bodies must be idempotent. |

**Plugin wiring (verified signatures):**
```python
from google.adk.apps import App
from google.adk.plugins import ReflectAndRetryToolPlugin, ReflectAndRetryModelPlugin
from google.adk.agents.run_config import RunConfig

app = App(
    name="coder",
    root_agent=root_agent,
    plugins=[
        ReflectAndRetryToolPlugin(max_retries=3),               # semantic tool retry
        ReflectAndRetryModelPlugin(max_retries=2),              # malformed / blocked model output
    ],
)
# per-run budget (or export ADK_MAX_LLM_CALLS=60)
run_config = RunConfig(max_llm_calls=60)
```
Source: `src/google/adk/plugins/__init__.py` (`__all__` exports both plugin classes), `agents/run_config.py`.

### 2.4 Loop failure modes (real ones, from ADK's own CHANGELOG)
- 2.2.0 fix: "terminate infinite retry loop in LoadSkillResourceTool on RESOURCE_NOT_FOUND". 2.4.0: the same bug in `RunSkillScriptTool` on SCRIPT_NOT_FOUND. **Lesson:** a non-retriable error that is reported back as retriable creates an infinite reflect loop.
- 2.6.0: "prevent transfer_to_agent loop on resumable invocation replay". 2.9.0: "add transfer_reason to transfer_to_agent to prevent loops". **Lesson:** agents bounce a task between each other (ping-pong delegation).
- 2.12.0: "harden SetModelResponseTool fallback to prevent infinite loops". **Lesson:** a structured-output repair loop can spin forever.
- 2.13.0: "make JoinNode in a loop wait for each iteration's predecessors" and "disambiguate RequestInput interrupt_id across rerun loop iterations". **Lesson:** state from iteration *k* leaking into iteration *k+1* is a graph-loop bug class of its own.
- Generic failure modes: (a) a sycophantic critic that approves on round 1; (b) a critic that never approves (no convergence); (c) oscillation between two drafts; (d) premature "victory" (Anthropic's long-running harness post, see §5); (e) context bloat with each iteration, where every critique is appended; (f) a swallowed exception (`except Exception:`), so `RetryConfig` never fires. The adk.dev/2.0 migration page warns about (f). Never catch `BaseException`, because that traps `NodeInterruptedError` and breaks HITL.

---

## 3. Graph engineering: explicit edges vs autonomous loops

### 3.1 Sources
- **"Why we built ADK 2.0"**, Google Developers Blog, 2026-07-01, by Swapnil Agarwal, Alan Blount and Frank Guan. https://developers.googleblog.com/en/why-we-built-adk-20/
  - "For production-grade reliability, you need full deterministic control over your application flow."
  - "Instead of relying on an LLM loop, you map the refund process as a deterministic directed graph", with "transitions … evaluated programmatically in code."
  - "agents can get stuck in infinite loops", becoming "more prone to loops, redundant tool executions, or failure to complete the task."
  - "If you can clearly map the workflow, use determinism." Use agents when "The task involves processing unstructured or ambiguous inputs."
  - Illustrative benchmark (refund example, `gemini-3.5-flash`, mock APIs): **5,152 → 2,265 tokens** and **7.2 s → 5.7 s** for an ADK 2.0 workflow compared with a vanilla tool-calling agent (from file 01, same post).
- **Harrison Chase, "How to think about agent frameworks"**, 2025-04-20, https://www.langchain.com/blog/how-to-think-about-agent-frameworks:
  - "Nearly all of the 'agentic systems' we see in production are a combination of 'workflows' and 'agents'."
  - "As your system becomes more agentic, it will become less predictable."
  - "The hard part of building reliable agentic systems is making sure the LLM has the appropriate context at each step."
- **Anthropic, "Building effective agents"**, Erik Schluntz and Barry Zhang, 2024-12-19, https://www.anthropic.com/engineering/building-effective-agents. Workflows are "predefined code paths" and agents "dynamically direct their own processes". It gives five workflow patterns (prompt chaining, routing, parallelization, orchestrator-workers, evaluator-optimizer). Its advice: find "the simplest solution possible, and only increasing complexity when needed."

### 3.2 Decision rule: when to hard-code an edge
Hard-code an edge (a plain function router) when **any** of these hold:
1. The next step is *determined by data* (a field, a threshold, a status code).
2. The step has an irreversible side effect (payment, email, deploy).
3. Compliance needs an auditable path.
4. A cheap verifier already decides it (tests pass or fail).

Use an **LLM router** (agent node with `output_schema` + function router, or `ClassifierNode`) when the decision depends on unstructured intent. Use an **autonomous loop** (an `Agent` with tools) only *inside* a node whose blast radius is bounded by the graph.

### 3.3 The three ADK 2.0 router grades (verified code)

**(a) Deterministic router:** a plain function that emits `Event(route=...)`. https://adk.dev/graphs/
```python
def router(node_input: str):
    routes = [r.strip() for r in node_input.split(",")]
    return Event(route=routes)          # a list fans out to several branches
```

**(b) LLM-as-router with a typed schema:** `contributing/samples/workflows/loop/agent.py`
```python
class Feedback(BaseModel):
  grade: Literal["tech-related", "unrelated"]
  feedback: str

evaluate_headline = Agent(name="evaluate_headline",
    instruction="Grade whether the headline is related to technology or software engineering.",
    output_schema=Feedback, output_key="feedback")

def route_headline(node_input: Feedback):
  return Event(route=node_input.grade)

root_agent = Workflow(name="root_agent", edges=[
    ("START", process_input, generate_headline, evaluate_headline, route_headline),
    (route_headline, {"unrelated": generate_headline}),   # back-edge = critique loop
])
```
The `Literal[...]` type in `output_schema` constrains the LLM to valid edge labels. That is graph engineering's main defence against hallucinated routes.

**(c) Calibrated classifier router (2.13.0, labs):** `contributing/samples/workflows/classifier_node/agent.py`
```python
from google.adk.labs.classifiers import Binary, Choice, ClassifierNode, LlmClassifier
classifier = LlmClassifier(model="gemini-3.5-flash")
triage = ClassifierNode(name="triage", classifier=classifier,
    question=Choice(instructions="Which team should handle this support ticket?",
        criteria={"billing": "Invoices, refunds, or subscription charges",
                  "technical": "Bugs, errors, outages, or API problems",
                  "general": "Product questions and anything else"}),
    answer_key="triage_answer")
is_urgent = ClassifierNode(name="is_urgent", classifier=classifier,
    question=Binary(instructions="Is this an outage, or does it block the customer's production use?"),
    threshold=0.7, answer_key="urgency_answer")
root_agent = Workflow(name="root_agent", edges=[
    ("START", process_input, triage),
    (triage, {"billing": billing_agent, "technical": is_urgent, "general": faq_agent}),
    (is_urgent, {True: page_oncall, False: eng_queue}),
])
```
CHANGELOG 2.13.0: `TypesafeClassifier` uses TypeSafe's Jev models, which return "calibrated probabilities in a single forward pass, much faster than an LLM." The `threshold=0.7` gives a confidence-gated edge.

### 3.4 Graphs as YAML (declarative graph engineering, 2.9.0+)
Verbatim `contributing/samples/workflows/loop_config/root_agent.yaml`:
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
`evaluate_headline.yaml`:
```yaml
agent_class: LlmAgent
name: evaluate_headline
instruction: |
  Grade whether the headline is related to technology or software engineering.
output_schema:
  name: loop_config.agent.Feedback
output_key: feedback
```
Semantics, from the sample README:
- `.agent.x` resolves a Python function in `agent.py` to a function node.
- Reusing a YAML filename across edges reuses the *same agent instance*, which is what keeps the loop a true cycle.
- `output_schema.name` points to a Pydantic class.

### 3.5 Graph topologies to teach
- Chain: `("START", a, b, c)`.
- Conditional: `(router, {"X": n1, "Y": n2})` with `DEFAULT_ROUTE` as a catch-all.
- Fan-out/fan-in: a tuple of nodes, then a `JoinNode` that receives a dict keyed by predecessor name.
- Map: `@node(parallel_worker=True)`.
- Cycle: a back-edge.
- Nesting: a `Workflow` used as a node.
- Escape hatch: dynamic `@node` + `ctx.run_node()` for recursion and data-dependent loops.
- Concurrency cap: `Workflow(max_concurrency=N)` applies only to graph-scheduled nodes, not to `run_node` children ("throttling them would cause deadlock").

---

## 4. Context engineering

- **Popularization:** Simon Willison, "Context engineering", 2025-06-27 (https://simonwillison.net/2025/Jun/27/context-engineering/), quotes Tobi Lütke: "the art of providing all the context for the task to be plausibly solvable by the LLM." He quotes Karpathy: "filling the context window with just the right information for the next step." [Exact tweet dates UNVERIFIED; both are late June 2025.]
- **LangChain, "Context Engineering for Agents"**, 2025-07-02 (byline: LangChain Team). Four strategies: **Write** (scratchpad/memory), **Select** (retrieve back in), **Compress** (summarize/trim), **Isolate** (sub-agents, sandboxes, state fields). It credits **Drew Breunig** with four failure modes: Context **Poisoning** ("When a hallucination makes it into the context"), **Distraction**, **Confusion**, **Clash**.
- **Anthropic, "Effective context engineering for AI agents"**, 2025-09-29, https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents: "finding the smallest possible set of high-signal tokens that maximize the likelihood of some desired outcome."
- **Google's ADK version:** Hangfei Lin, "Architecting efficient context-aware multi-agent framework for production", Google Developers Blog, **2025-12-04**. "Context is a compiled view over a richer stateful system." "the Session is your ground truth; the working context is merely a computed projection." Its principles are "Separate storage from presentation", "Explicit transformations" and "Scope by default". Its tiers are working context, session, memory and artifacts. It introduces "narrative casting": reframing a prior agent's messages during handoff so the new agent does not mistake them for its own.

**ADK mapping (Write/Select/Compress/Isolate):**

| Strategy | ADK primitive |
|---|---|
| Write | `output_key`, `Event(state=...)`, `ArtifactService`, `MemoryService` (`MongoDbMemoryService` 2.13, `sqlite://` memory 2.11) |
| Select | `{state_key}` / `{key?}` templating, `<Class.field from node>` placeholders, `load_memory` / `preload_memory`, `LoadArtifactsTool`, Jinja2 instructions (2.7.0, `use_jinja2=True`) |
| Compress | `EventsCompactionConfig(token_threshold=4000, event_retention_size=5)` or a sliding window (`compaction_interval`, `overlap_size`), `ContextFilterPlugin` |
| Isolate | `include_contents='none'` (`Literal['default','none']` in `llm_agent.py`), branches and `isolation_scope`, `single_turn` sub-agents, node-to-node `node_input` passing that skips session state |
| Cache | `ContextCacheConfig(min_tokens=2048, ttl_seconds=600, cache_intervals=5)` + `static_instruction` (the stable prefix goes first) |

**Graph engineering as context engineering.** The ADK 2.0 blog argues that workflows reduce context bloat because tool outputs don't pile up in a single model's context. Each graph node gets only its `node_input`. That is "Isolate" enforced by the architecture.

---

## 5. Harness engineering

- **Coined: Mitchell Hashimoto, "My AI Adoption Journey"**, 2026-02-05, step 5 "Engineer the Harness", https://mitchellh.com/writing/my-ai-adoption-journey: "I've grown to calling this 'harness engineering.' It is the idea that anytime you find an agent makes a mistake, you take the time to engineer a solution" so that it doesn't repeat it.
- **OpenAI, "Harness engineering" post** (https://openai.com/index/harness-engineering/). The fetch returned 403. My recollection, which I could not check against the page: author Ryan Lopopolo, Feb 2026, a team shipping a product with roughly 1M lines of code written by Codex and no hand-written code. **[UNVERIFIED: author, date, all numbers]**. Böckeler (below) quotes its conclusion verbatim: "Our most difficult challenges now center on designing environments, feedback loops, and control systems." She also describes its layered architecture enforced by custom linters and structural tests, and recurring "garbage collection" agents that scan for drift.
- **Birgitta Böckeler (Thoughtworks), "Harness engineering for coding agent users"**, martinfowler.com, **2026-04-02**, https://martinfowler.com/articles/exploring-gen-ai/harness-engineering.html. Taxonomy:
  - **Guides** are *feedforward*: conventions, instructions, codemods.
  - **Sensors** are *feedback*: linters, tests, AI review.
  - Each control is either **computational** (deterministic) or **inferential** (LLM-based).
  - Context engineering is how these controls reach the agent.
- **Anthropic, "Effective harnesses for long-running agents"**, Justin Young, **2025-11-26**, https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents.
  - An *initializer agent* writes `init.sh`, `claude-progress.txt`, and an initial git commit.
  - A JSON **feature list** starts with every feature failing. Agents may only flip `passes`, because JSON is less likely to be overwritten than Markdown.
  - Each session does one feature, then a clean commit and a progress note. Each session starts by reading the git log and progress file and running a smoke test.
  - Agents test end-to-end via browser automation (Puppeteer MCP).
  - Failure modes named: declaring victory too early, leaving undocumented progress, marking features done prematurely.
  - Quote: "It is unacceptable to remove or edit tests because this could lead to missing or buggy functionality."

**ADK mapping of a harness (guides + sensors):**
- **Guides:** `instruction` / `static_instruction`, Agent Skills (`SkillToolset`, skill lifecycle `ADK_ENABLE_SKILL_LIFECYCLE=1`, 2.10), `output_schema`, typed `input_schema`, graph topology itself.
- **Computational sensors:** function nodes (lint, tests, schema validators), `RetryConfig`, `ToolCallIntegrityPlugin`. `ToolCallIntegrityPlugin` stamps each function call with `"v1:" + HMAC-SHA256` in `custom_metadata` and refuses to run a tool whose stored call fails to verify. Its docstring notes that tools run as workflow nodes are *not* checked, because "their arguments come from the workflow graph".
- **Inferential sensors:** critic `Agent` nodes, `ClassifierNode`, Model Armor plugin (2.8).
- **The Hashimoto loop in ADK:** every production failure becomes an eval case (`adk eval_set add_eval_case`) and a CI gate (`adk eval` / `AgentEvaluator.evaluate`). Since 2.10, `AgentEvaluator` raises `ValueError` if zero cases ran.
- **Observability as a sensor:** `AutoTracingPlugin` (2.2) and OTel GenAI v2 spans (default in 2.13.0).
- **Outer optimization loop:** `adk optimize` / `GEPARootAgentOptimizer` (2.3.0) evolves the prompt against the eval set. This is harness engineering automated [UNVERIFIED flags; see file 06 of this series].

---

## 6. Evaluator-optimizer and verifier-in-the-loop (per-step verification)

- **Anthropic evaluator-optimizer** (2024-12-19): use it when there are "clear evaluation criteria, and iterative refinement provides measurable value."
- **Jason Wei, "Asymmetry of verification and verifier's rule"**, 2025-07-15, https://www.jasonwei.net/blog/asymmetry-of-verification-and-verifiers-law: "The ease of training AI to solve a task is proportional to how verifiable the task is." He lists five properties: objective truth, fast to verify, scalable to verify, low noise, continuous reward. **Design rule:** put the strongest *cheap* verifier at each step. Use code checks first and an LLM judge last (Anthropic's SDK post makes the same ordering).
- **Verifier ladder:**
  1. schema (`output_schema` Pydantic)
  2. rule or function node (lint, unit test, SQL dry-run)
  3. calibrated classifier (`ClassifierNode` with `threshold`)
  4. LLM critic node
  5. stronger-model consult (`ModelConsultTool`)
  6. human (`RequestInput`)

**Bounded verifier loop in ADK 2.0.** This is composed from verified APIs; the code is mine, not from the docs. A function node can take `ctx: Context` next to `node_input`, as `page_oncall` does in the classifier sample.
```python
from google.adk import Agent, Context, Event, Workflow

MAX_ROUNDS = 3

def route_headline(node_input: Feedback, ctx: Context):
    rounds = ctx.state.get("rounds", 0) + 1
    if node_input.grade == "tech-related":
        return Event(route="pass", state={"rounds": rounds})
    if rounds >= MAX_ROUNDS:
        return Event(route="give_up", state={"rounds": rounds})   # escalate
    return Event(route="revise", state={"rounds": rounds})

root_agent = Workflow(name="bounded_critic", edges=[
    ("START", process_input, generate_headline, evaluate_headline, route_headline),
    (route_headline, {"revise": generate_headline,
                      "pass": publish,
                      "give_up": human_review}),     # human_review yields RequestInput
])
```
This gives explicit stop (`pass`), budget (`MAX_ROUNDS`), feedback (`{feedback?}` in the generator instruction), and escalation (`give_up` goes to HITL).

**Offline evals (verifiers for the whole loop):** from https://adk.dev/evaluate/criteria/.
- `tool_trajectory_avg_score`: exact trajectory match.
- `response_match_score`: ROUGE-1.
- `final_response_match_v2`: LLM-judged.
- `rubric_based_final_response_quality_v1` and `rubric_based_tool_use_quality_v1`.
- `rubric_based_multi_turn_trajectory_quality_v1`.
- `hallucinations_v1`: groundedness.
- `safety_v1`.
- `multi_turn_task_success_v1`, `multi_turn_trajectory_quality_v1`, `multi_turn_tool_use_quality_v1`.
- `per_turn_user_simulator_quality_v1`.
- Always-on **efficiency** criteria (informational, never pass or fail): `tool_call_count_v1`, `inference_call_count_v1`, `token_usage_v1`, `invocation_duration_v1`. These are how you *measure* a loop's budget burn.

Verbatim EvalConfig:
```json
{ "criteria": { "rubric_based_final_response_quality_v1": {
    "threshold": 0.8,
    "judge_model_options": { "judge_model": "gemini-flash-latest", "num_samples": 5 },
    "rubrics": [ { "rubric_id": "conciseness",
      "rubric_content": { "text_property": "The agent's response is direct and to the point." } } ] } } }
```
Per-case rubrics (`EvalCase.rubrics` with `"type": "FINAL_RESPONSE_QUALITY"`) are merged with criterion-level rubrics. Run: `adk eval <agent_dir> <file.evalset.json> --config_file_path eval_config.json`.

---

## 7. Architecture flows (for diagrams, in words)

**A. Hybrid graph with an LLM island.** START → `classify` (ClassifierNode, threshold 0.7) → branches. The "billing" branch goes to a deterministic chain (`lookup_invoice` fn → `refund_policy_check` fn → `require_confirmation` node → `issue_refund` fn). The "general" branch goes to an autonomous `Agent` with search tools, bounded by `max_llm_calls`. The two branches meet at `format_reply` and end at END. Colour code: deterministic nodes grey, LLM nodes blue, human nodes orange.

**B. Generator–verifier loop.** `generate` (LLM) → `verify` (function: tests/lint) → router. On `pass`, go to END. On `fail` with round < N, go back to `generate` with the findings written to state. On `fail` with round = N, go to `ModelConsultTool` / stronger model or `RequestInput`. Overlay the budget meter (`inference_call_count_v1`).

**C. Harness ring.** The agent sits at the centre. An inner ring holds guides (instructions, skills, schemas). An outer ring holds sensors: computational ones on the left (tests, lint, HMAC integrity) and inferential ones on the right (critic, classifier, Model Armor). Outermost is the flywheel: production trace → failing eval case → fix the harness → CI gate.

**D. Context compiler (Google's framing).** Sources (session events, memory, artifacts, state) → processors (instructions, contents, compaction, filter plugin, cache prefix) → working context for *one* call → model → events back to the session.

**E. Durable loop.** The node runs, its checkpoint is emitted, and it crashes. On resume, completed nodes are skipped and the failed node re-runs (2.9.0). That is why side effects must be idempotent.

---

## 8. Codelabs and samples (exact titles and URLs)
- **"ADK 2 Orchestration: Graph, Collaborative & Dynamic Workflows"**: https://codelabs.developers.google.com/adk2/instructions (repo `cuppibla/adk2-tutorial`; tested on `google-adk==2.3.0` and 2.0.0b1). The Marathon Race Day Coach example uses a temperature router (HOT ≥70°F, COLD ≤40°F), a JoinNode fan-out, and recursive research with a depth guard.
- **"Evaluating Agents with ADK"**: https://codelabs.developers.google.com/adk-eval/instructions
- **"Build an Agentic Pitch Generator: Orchestration, Evaluation, and Analytics with Google Cloud"**: https://codelabs.developers.google.com/bwg-agentic-masterclass
- Samples: `contributing/samples/workflows/{loop, loop_self, loop_config, retry, route, classifier_node, request_input_rerun, dynamic_nodes, fan_out_fan_in, parallel_worker}`, https://github.com/google/adk-python/tree/main/contributing/samples/workflows
- Docs: https://adk.dev/graphs/ , /graphs/routes/ , /graphs/dynamic/ , /graphs/human-input/ , /evaluate/criteria/ , /context/compaction/ , /context/caching/ , /plugins/
- I found no Google talk titled "loop engineering" or "harness engineering". Next '26 and I/O '26 session titles were not checked this session **[UNVERIFIED]**.

---

## 9. Interview questions (crisp answers)

1. **Q: How do flow engineering and context engineering differ?** A: Flow engineering designs the *sequence* of model and verifier calls (AlphaCodium: 19%→44% pass@5 with the same GPT-4). Context engineering designs *what each call sees*. In ADK, flow means `Workflow` edges and context means `include_contents`, compaction, caching and state templating.
2. **Q: A graph cycle in ADK 2.0 runs forever. Why, and how do you fix it?** A: Graph cycles have no built-in `max_iterations`. The docs say you must make the exit condition eventually true. Keep a counter in `ctx.state` inside the router and add a `give_up` route, or move the loop into a dynamic `@node` with an explicit `for` bound. As a backstop, `RunConfig.max_llm_calls` (default 500) raises `LlmCallsLimitExceededError`.
3. **Q: `RetryConfig` vs `ReflectAndRetryToolPlugin`?** A: `RetryConfig` handles *transient* errors: it re-runs the node with exponential backoff (5 attempts, 1s→60s, factor 2) and the model sees nothing. The plugin handles *semantic* errors: it returns structured reflection guidance to the LLM so the model can fix its arguments, up to `max_retries=3`.
4. **Q: Why did your retries never fire?** A: A broad `except Exception:` inside the node swallowed the error. Let exceptions propagate, and never catch `BaseException` (it traps `NodeInterruptedError` and breaks HITL).
5. **Q: When should an edge be hard-coded rather than chosen by an LLM?** A: When the decision is data-determined, has irreversible side effects, needs auditability, or a cheap verifier exists. In the ADK blog's words: "If you can clearly map the workflow, use determinism."
6. **Q: How do you stop an LLM router from inventing a branch?** A: Constrain it with `output_schema` using a `Literal[...]` grade, route with a function on the typed field, and give it a `DEFAULT_ROUTE`. Or use `ClassifierNode` with calibrated probabilities and a `threshold`.
7. **Q: What is harness engineering, and who named it?** A: Mitchell Hashimoto (2026-02-05): every time the agent makes a mistake, engineer a fix into the environment. Böckeler splits harness controls into guides (feedforward) and sensors (feedback), each either computational or inferential. In ADK, every failure becomes an eval case plus a CI gate.
8. **Q: Name four context failure modes.** A: Poisoning, distraction, confusion and clash (Drew Breunig, cited by LangChain). In a graph, isolating each node's `node_input` limits poisoning to one node.
9. **Q: Where do you escalate when the cheap model is stuck?** A: Use `ModelConsultTool` to get advice from a stronger model mid-generation, capped by `max_uses` and `session_max_uses` (`ForceEscalationPlugin` makes the consult mandatory). Otherwise route to `RequestInput` for a human.
10. **Q: What does the verifier's rule imply for agent design?** A: Make every step verifiable: objective, fast, scalable, low-noise and continuous. Prefer tests and schemas over LLM judges, because loops converge only as fast as their verifier is trustworthy.
11. **Q: Your loop resumes after a crash and charges the card twice. Why?** A: Tools and nodes run at least once, and since 2.9.0 failed nodes re-run on resume. Use idempotency keys and put `require_confirmation` on side-effect nodes.
12. **Q: How do you measure loop cost in CI?** A: ADK's always-on efficiency criteria: `inference_call_count_v1`, `tool_call_count_v1`, `token_usage_v1` and `invocation_duration_v1`. Track them per eval case across commits.

---

## 10. Slide ideas (10, each with its explaining animation)

1. **"The Five Engineerings."** Concentric rings grow outward one at a time: Prompt → Flow (2024-01) → Context (2025-06) → Harness (2026-02). A Loop/Graph control-flow band slices through all of them. Each ring labels its coiner and date as it appears.
2. **"AlphaCodium: same model, different flow."** A bar grows from 19% to 44% pass@5. Underneath, the flow stages light up in sequence (reflect → solutions → AI tests → code → public tests ⟲ → AI tests ⟲).
3. **"Anatomy of a loop: six levers."** A circular arrow (gather → act → verify → repeat). Six dials attach one by one: stop, budget, feedback, retry, escalate, durability. Each dial snaps to its ADK primitive (e.g. budget → `max_llm_calls=500`).
4. **"Cycles are not bounded automatically."** An animated token packet circles a graph back-edge while a cost counter spins up. Then a counter badge appears on the router, and on round 3 the packet exits via `give_up` to a human icon.
5. **"Hard edge or LLM edge?"** A decision tree (data-determined? irreversible? auditable? cheap verifier?). Edges in the sample graph turn grey (code) or blue (LLM) as the answers resolve. The ADK quote fades in: "If you can clearly map the workflow, use determinism."
6. **"Three router grades."** Three panels slide in left to right: function router, then `output_schema` + `Literal` router, then `ClassifierNode` with a probability bar and a 0.7 threshold line. The packet routes differently in each.
7. **"Graph as YAML."** The `root_agent.yaml` lines type out. Each line draws its corresponding node or edge on the right-hand canvas, and the `unrelated:` back-edge curves back last.
8. **"Context is a compiled view."** Sources (session, memory, artifacts) flow through a compiler pipeline (compaction, filter, cache prefix) into a single small working-context card. A token gauge drops as each processor runs. Labels: Write/Select/Compress/Isolate.
9. **"The harness ring."** The agent sits in the centre. Guide icons fly in from the left (feedforward) and sensor icons from the right (feedback). Then a red "mistake" appears, becomes a new eval case, and adds a new sensor to the ring (Hashimoto's loop).
10. **"Verifier ladder and the retry split."** A ladder from schema → function test → classifier → LLM critic → stronger model → human, with cost and latency bars rising per rung. A side split shows `RetryConfig` (backoff curve 1-2-4-8…60s, model sees nothing) against `ReflectAndRetryToolPlugin` (the error message is fed back to the LLM and the arguments are corrected).

---

## 11. Uncertain items
- Origin of the phrase "loop engineering" (no verified coiner). The phrase "graph engineering" is likewise a practitioner label, not a named publication.
- OpenAI harness-engineering post: author, date and all figures (page returned 403).
- Exact dates of Lütke's and Karpathy's "context engineering" tweets (late June 2025, via Willison).
- Model-failover configuration key (2.9.0) and `adk optimize` flags.
- `@node(timeout=...)` is typed `float | None` in `workflow/_node.py`. That it is measured in seconds is presumed and not stated in the docstring.
- Next '26 / I/O '26 session titles on these topics were not checked (no search budget).
