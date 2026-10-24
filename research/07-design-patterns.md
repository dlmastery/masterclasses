# 07 — Agentic Design Patterns (from first principles to ADK 2.x)

Research date: 2026-10-23. ADK version context: **google-adk 2.13.0** on PyPI (released 2026-10-23). **ADK Python 2.0.0 went GA on 2026-05-19**, followed by Go 2.0.0 (2026-06-30) and TypeScript 2.0.0 (2026-08-21). Sources: https://pypi.org/project/google-adk/ and https://adk.dev/2.0/

> Convention: **[VERIFIED]** means checked against a primary source today. **[UNVERIFIED]** means not confirmed against a primary source, so check it before it goes on a slide. Code is adapted from official docs. Where a docs page gave no Python code, I mark the sketch **[SKETCH]**.

---

## 0. The four canonical catalogs (what the deck should cite)

| Catalog | Author / org | Date | # patterns | URL |
|---|---|---|---|---|
| "Agentic Design Patterns" (Ng, The Batch) | Andrew Ng, DeepLearning.AI | 2024-03-20 | 4 | https://www.deeplearning.ai/the-batch/how-agents-can-improve-llm-performance/ |
| "Building effective agents" | Erik Schluntz & Barry Zhang, Anthropic | 2024-12-19 | 1 building block + 5 workflows + agents | https://www.anthropic.com/engineering/building-effective-agents |
| *Agentic Design Patterns: A Hands-On Guide to Building Intelligent Systems* | Antonio Gulli (Google, Office of the CTO) | Springer Cham, 2025 (Hoepli lists 11/2025) | 21 | https://link.springer.com/doi/10.1007/978-3-032-01402-3 |
| "Choose a design pattern for your agentic AI system" | Google Cloud Architecture Center | last updated 2026-05-28 | 12 | https://docs.cloud.google.com/architecture/choose-design-pattern-agentic-ai-system |

Notes on the Gulli book:
- DOI 10.1007/978-3-032-01402-3. Print ISBN 9783032014016, per the Hoepli listing.
- Page counts in sources conflict: Hoepli says "approx. 175 p.", a search summary says 427 pages, and the free Google Docs draft was widely reported as ~424 pages (PyTorch Korea post). **[UNVERIFIED — use "400+ page draft"]**
- PPC Land reported a scheduled release date of 2025-12-03 and called Gulli a "distinguished engineer in the CTO Office" at Google. **[secondary source]**

### Andrew Ng's 4 patterns (The Batch, 2024-03-20)
1. **Reflection**: the LLM examines its own work and finds ways to improve it.
2. **Tool Use**: the LLM calls tools such as web search, code execution, and APIs.
3. **Planning**: the LLM writes and runs a multi-step plan, splitting the goal into sub-tasks.
4. **Multi-agent collaboration**: several specialised agents split up the work, "much like a company hiring multiple employees".

Quotable numbers (verbatim, HumanEval):
- "GPT-3.5 (zero shot) was 48.1% correct."
- "GPT-4 (zero shot) does better at 67.0%."
- "wrapped in an agent loop, GPT-3.5 achieves up to 95.1%."

Teaching point: the workflow mattered more than the model generation.

Companion course: DeepLearning.AI "Agentic AI" (Andrew Ng), https://www.deeplearning.ai/courses/agentic-ai/

### Anthropic "Building effective agents" (2024-12-19)
- **Building block:** the *augmented LLM*, an LLM with retrieval, tools and memory.
- **Workflows** are "systems where LLMs and tools are orchestrated through predefined code paths". There are five:
  1. **Prompt chaining**: use it for fixed subtasks; it trades latency for accuracy.
  2. **Routing**: use it for distinct input categories that you can classify accurately.
  3. **Parallelization**: comes in two variants, *sectioning* and *voting*.
  4. **Orchestrator-workers**: use it when "you can't predict the subtasks needed".
  5. **Evaluator-optimizer**: use it when there are "clear evaluation criteria, and iterative refinement provides measurable value".
- **Agents** are "systems where LLMs dynamically direct their own processes and tool usage".

Quotable lines (verbatim):
- "the most successful implementations weren't using complex frameworks or specialized libraries"
- "finding the simplest solution possible, and only increasing complexity when needed"
- "They are typically just LLMs using tools based on environmental feedback in a loop."
- "adding complexity only when it demonstrably improves outcomes"

The page now carries a banner saying that much of its tooling has changed since 12/2024.

### Gulli's 21 patterns (book chapter order, verified against the Hoepli TOC)
Grouping into levels follows the system-design.space review at https://system-design.space/en/chapter/agentic-design-patterns-book/

**Level 1 — Flow control**
1. **Prompt Chaining**: each model call's output feeds the next step.
2. **Routing**: classify the request, then dispatch it to a specialised handler.
3. **Parallelization**: run independent branches concurrently, then merge the results.

**Level 2 — The agent loop**
4. **Reflection**: critique the draft and revise it.
5. **Tool Use** (function calling).
6. **Planning**: decompose the goal into steps and re-plan as observations arrive.

**Level 3 — State and coordination**
7. **Multi-Agent** (collaboration and roles).
8. **Memory Management**: short-term state, long-term facts, and context rules.
9. **Learning and Adaptation**: change behaviour based on past outcomes.
10. **Model Context Protocol (MCP)**: a standard boundary for tools and resources.
11. **Goal Setting and Monitoring**: goals, progress criteria, and completion checks.

**Level 4 — Contact with reality**
12. **Exception Handling and Recovery**: classify errors, bound retries, restore state, and stop safely.
13. **Human-in-the-Loop**.
14. **Knowledge Retrieval (RAG)**.

**Level 5 — Operating at scale**
15. **Inter-Agent Communication (A2A)**.
16. **Resource-Aware Optimization**: choose the model, tool and reasoning depth by cost, latency and budget.
17. **Reasoning Techniques**: CoT, ToT, self-consistency, and similar.
18. **Guardrails/Safety Patterns**.
19. **Evaluation and Monitoring**: quality, cost, latency, and trajectory.
20. **Prioritization**: pick the next task by value, risk and urgency.
21. **Exploration and Discovery**: search when the right route is unknown.

Appendices cover advanced prompting, GUI and real-world agents, frameworks overview (incl. AgentSpace), and CLI/coding agents. Exact appendix titles are **[UNVERIFIED]**.

Third-party companion repos (not official):
- https://github.com/evoiz/Agentic-Design-Patterns (chapter notebooks)
- an ADK implementation repo by danielesalatti. **[UNVERIFIED URL]**

### Google Cloud Architecture Center — 12 patterns (updated 2026-05-28)
1. Single-agent
2. Sequential
3. Parallel
4. Loop
5. Review & critique (generator-critic)
6. Iterative refinement
7. Coordinator
8. Hierarchical task decomposition
9. Swarm
10. ReAct
11. Human-in-the-loop
12. Custom logic

The page groups these into deterministic, dynamic orchestration, iterative, and special requirements.

### Mapping across catalogs (great slide)
| Concept | Ng | Anthropic | Gulli ch. | GCP | ADK 2.x primitive |
|---|---|---|---|---|---|
| Chain | — | Prompt chaining | 1 | Sequential | `Workflow(edges=[("START", a, b, c)])` / `SequentialAgent` |
| Route | — | Routing | 2 | Coordinator | `Event(route=...)` + dict edges; LLM `sub_agents` transfer |
| Parallel | — | Parallelization | 3 | Parallel | `JoinNode` / `ParallelAgent` / `asyncio.gather(ctx.run_node…)` |
| Reflect | Reflection | Evaluator-optimizer | 4 | Review & critique, Iterative refinement | loop node / `LoopAgent` + `exit_loop` |
| Tools | Tool use | Augmented LLM | 5, 10 | Single-agent | `tools=[fn, McpToolset, AgentTool]` |
| Plan | Planning | Orchestrator-workers | 6 | Hierarchical decomposition | `PlanReActPlanner`, `BuiltInPlanner`, coordinator |
| Multi-agent | Multi-agent | Orchestrator-workers | 7, 15 | Coordinator, Swarm | `sub_agents`, `mode="task"/"single_turn"`, A2A |
| HITL | — | (checkpoints) | 13 | HITL | `RequestInput`, `FunctionTool(require_confirmation=…)` |
| Memory | — | Augmented LLM | 8 | — | `MemoryService`, `preload_memory`, `load_memory` |
| RAG | — | Augmented LLM | 14 | — | `VertexAiRagRetrieval`, search tools |
| Guardrails | — | — | 18 | — | callbacks, plugins, Model Armor |
| Resource-aware | — | — | 16 | — | model per agent, `RoutedLlm` (TS, experimental) |

---

## 1. ADK 2.x mental model for patterns

**Graphs replace the hierarchy.** "The Workflow Runtime replaces hierarchical agent execution with a graph-based engine". Agents, Tools and Functions each run as **nodes** in a graph. In Python, `BaseAgent` extends `BaseNode`. Source: https://adk.dev/2.0/

ADK 2.x offers three workflow styles:
- **Graph-based**: `Workflow(edges=[...])`. See https://adk.dev/graphs/
- **Dynamic**: code-driven, using `@node` and `ctx.run_node`. See https://adk.dev/graphs/dynamic/
- **Collaborative**: a coordinator `Agent` with `sub_agents` and per-subagent `mode`. See https://adk.dev/workflows/collaboration/

**Templates are superseded.** The 1.x `SequentialAgent`, `ParallelAgent` and `LoopAgent` docs say: "Starting in ADK 2.0 for Python and Go, templated workflows have been superseded". They remain documented under https://adk.dev/agents/workflow-agents/. Teach them as legacy that is still common in tutorials.

**Other 2.x runtime facts:**
- Retries use `RetryConfig(max_attempts=3)`.
- Human-in-the-loop pauses use `NodeInterruptedError`. Catching `BaseException` traps it and breaks the pause.
- The Go version adds `JoinNode`, per-node retries and timeouts, and merges `ToolContext` and `CallbackContext`.
- Python is moving to a single unified `Context` type for new code.

**Breaking changes in 2.0:** the agent API, event model and session schema all changed. ADK ≥1.28 can read 2.0 sessions, but older 1.x versions cannot (per the PyPI notes).

Imports verified on adk.dev:
```python
from google.adk import Agent, Workflow, Event, Context
from google.adk.workflow import node, JoinNode, BaseNode
from google.adk.events import RequestInput
from google.adk.agents import LlmAgent, LoopAgent, SequentialAgent   # 1.x-style templates
```

---

## 2. Pattern-by-pattern: definition, when to use, failure modes, ADK sketch

### 2.1 Prompt chaining / Sequential pipeline
- **Definition.** A fixed linear sequence of steps, where each step's output becomes the next step's input. In ADK 2.x the workflow engine handles the ordering without a model.
- **Use when** the steps are known and stable. Examples: ETL, and extract → validate → format.
- **Failure modes:**
  - Rigid: it cannot skip steps it does not need.
  - Errors cascade, because a bad step-1 output poisons everything downstream.
  - The slowest step sets the latency.
- **Mitigation:** add programmatic "gates" between steps. Anthropic recommends these.

Source: https://adk.dev/graphs/ (Python, ADK 2.x)
```python
from google.adk import Agent, Workflow, Event

city_generator_agent = Agent(
    name="city_generator_agent", model="gemini-flash-latest",
    instruction="Return the name of a random city. Return only the name.")

def lookup_time_function(node_input: str):
    return {"time_info": "10:10 AM", "city": node_input}   # plain function = node

def completed_message_function(node_input):
    return Event(message=f"{node_input}\n WORKFLOW COMPLETED.")

root_agent = Workflow(
    name="root_agent",
    edges=[("START", city_generator_agent, lookup_time_function,
            completed_message_function)],
)
```
(The original wraps the time lookup in a Pydantic `CityTime` and adds an `input_schema` report agent.)

### 2.2 Routing / Coordinator
- **Definition.** A classifier sends each input to a specialised handler. The classifier can be an LLM, embeddings or rules. In the GCP "coordinator" variant, an LLM breaks a request down and dispatches the sub-tasks dynamically.
- **Use when** inputs fall into distinct categories that are best handled separately. Example: customer support split into bug, support and logistics.
- **Failure modes:**
  - Misclassification sends the request down the wrong path, often silently.
  - Requests that belong to several categories.
  - No default branch.
  - Extra LLM calls add cost and latency.
- **Mitigation:** add a `DEFAULT_ROUTE` and log which route each request took.

Graph routing. Source: https://adk.dev/graphs/
```python
process_message = Agent(name="process_message", model="gemini-flash-latest",
    instruction='Classify into "BUG", "CUSTOMER_SUPPORT" or "LOGISTICS"; '
                'comma-separate if several apply.')

def router(node_input: str):
    return Event(route=[r.strip() for r in node_input.split(",")])

root_agent = Workflow(name="routing_workflow", edges=[
    ("START", process_message, router),
    (router, {"BUG": response_1_bug,
              "CUSTOMER_SUPPORT": response_2_support,
              "LOGISTICS": response_3_logistics}),
])
```
Because the router returns a list, one message can fan out to several routes.

LLM-driven coordinator. Source: https://adk.dev/workflows/collaboration/
```python
from google.adk import Agent
weather_agent = Agent(name="weather_checker", mode="single_turn",
                      tools=[get_weather, geocode_address])
flight_agent  = Agent(name="flight_booker", mode="task",
                      input_schema=FlightInput, output_schema=FlightResult,
                      tools=[search_flights, book_flight])
root = Agent(name="travel_planner", sub_agents=[weather_agent, flight_agent])
# auto-injects delegation tools named weather_checker, flight_booker
```
The `mode` values:
- **`chat`** is the default. The subagent returns to its parent only through a manual transfer.
- **`task`** can ask the user clarifying questions and returns when it calls `finish_task`. It must be a leaf agent. In Python v2.0.0 it is disabled inside graph workflows.
- **`single_turn`** has no user interaction and can run in parallel.

Docs caution: "Do not configure a root agent with the mode setting."

### 2.3 Parallelization (fan-out / gather; sectioning & voting)
- **Definition.** Independent sub-tasks run concurrently and are then merged.
- **Use when:**
  - you need data from many sources at once,
  - you need multiple perspectives, or
  - you want self-consistency voting.
- **Failure modes:**
  - Token and cost blow-up.
  - Conflicting outputs that the merge step cannot reconcile.
  - Race conditions on shared state, so give each branch its own `output_key`.
  - Rate limits.

Source: https://adk.dev/graphs/routes/
```python
from google.adk.workflow import JoinNode
my_join_node = JoinNode(name="my_join_node")
edges = [
    ("START", parallel_task_A, my_join_node),
    ("START", parallel_task_B, my_join_node),
    ("START", parallel_task_C, my_join_node),
    (my_join_node, final_task_D),
]
```

Dynamic map-style parallelism. Source: https://adk.dev/graphs/dynamic/
```python
@node(rerun_on_resume=True)
async def parallel_supervisor(ctx: Context, node_input: list, real_node: BaseNode):
    tasks = [ctx.run_node(real_node, item) for item in node_input]  # futures
    return await asyncio.gather(*tasks)
```

### 2.4 Reflection / Generator-Critic / Evaluator-Optimizer / Iterative refinement
- **Definition.** A generator produces a draft. A critic scores it against criteria and either approves it or returns feedback, and the cycle loops. GCP splits this into two patterns:
  - *review & critique*: approve or reject.
  - *iterative refinement*: progressively improve state until a threshold is met.
- **Use when:**
  - there are clear quality criteria, such as code that must pass lint, a security review, or a style guide, and
  - first drafts are usually not good enough.
- **Evidence:**
  - **Self-Refine** (Madaan et al., arXiv 2303.17651, 2023): "~20% absolute on average" improvement across 7 tasks.
  - **Reflexion** (Shinn et al., arXiv 2303.11366, 2023): "91% pass@1 accuracy on the HumanEval" vs 80% for GPT-4.
  - **Ng:** an agent-looped GPT-3.5 reached 95.1% on HumanEval.
- **Failure modes:**
  - Infinite loops or no convergence, so you need a hard cap.
  - A critic that is too lenient, especially when it shares the generator's model and blind spots.
  - Oscillation between versions.
  - Cost that grows with every cycle.
- **Mitigation:** prefer deterministic critics such as tests or linters where you can.

ADK 2.x dynamic loop (generator, deterministic critic, fixer). Source: https://adk.dev/graphs/dynamic/
```python
@node
async def code_workflow(ctx: Context, user_request: str):
    code = await ctx.run_node(coder_agent, user_request)
    check = await ctx.run_node(compile_lint_check, code)
    while check.findings:                       # add an iteration cap in prod
        yield Event(state={"code": code, "findings": check.findings})
        code = await ctx.run_node(fixer_agent,
                                  {"code": code, "findings": check.findings})
        check = await ctx.run_node(compile_lint_check, code)
    yield Event(output=code)
```

ADK 1.x template loop (still the most common in codelabs). Adapted from https://adk.dev/agents/workflow-agents/loop-agents/
```python
from google.adk.agents import LlmAgent, LoopAgent, SequentialAgent
from google.adk.tools.tool_context import ToolContext

def exit_loop(tool_context: ToolContext) -> dict:
    tool_context.actions.escalate = True   # stops the LoopAgent
    return {}

critic  = LlmAgent(name="Critic", model=MODEL, include_contents="none",
    instruction="Review {current_document}. If fine reply exactly 'No major issues found.'",
    output_key="criticism")
refiner = LlmAgent(name="Refiner", model=MODEL, include_contents="none",
    instruction="If {criticism} == 'No major issues found.' call exit_loop; else rewrite.",
    tools=[exit_loop], output_key="current_document")
loop = LoopAgent(name="RefinementLoop", sub_agents=[critic, refiner], max_iterations=5)
root_agent = SequentialAgent(name="IterativeWriting", sub_agents=[writer, loop])
```

### 2.5 Tool use (and MCP)
- **Definition.** The LLM picks a function and its arguments, the runtime executes it, and the result is fed back to the model. MCP standardises how tools are discovered and invoked (Gulli ch. 10).
- **Use when** the task needs fresh data or side effects.
- **Failure modes:**
  - Wrong tool selection, which gets worse as the tool count grows (GCP single-agent tradeoff).
  - Hallucinated arguments.
  - Prompt injection carried in tool outputs.
  - Over-broad permissions.
- **Mitigation** (Anthropic): invest in the "agent-computer interface", with good tool docs and poka-yoke arguments.

ADK: Python functions passed in `tools=[...]` are auto-wrapped as `FunctionTool`. An `AgentTool` lets one agent call another as a tool. `McpToolset` connects to MCP servers (covered in another research file).

### 2.6 ReAct (Reason + Act)
- **Definition.** A single model loops through **Thought → Action → Observation** until it has a final answer or hits a limit.
- **Paper:** Yao et al., "ReAct: Synergizing Reasoning and Acting in Language Models", arXiv 2210.03629 (2022-10-06), ICLR 2023. It beat imitation and RL baselines by **+34% absolute success on ALFWorld** and **+10% on WebShop**.
- **Use when** the task is dynamic and needs continual re-planning based on what the tools return.
- **Failure modes:**
  - Latency, because the loop is sequential.
  - Tool errors propagate into the final answer (GCP).
  - Loops that repeat the same action.
  - Context bloat.
- **ADK:** every `LlmAgent` with tools is natively a ReAct loop, since the model emits function calls and observations come back as function responses. For explicit ReAct-style traces, use `PlanReActPlanner`. Its output tags are `/*PLANNING*/`, `/*ACTION*/`, `/*REASONING*/` and `/*FINAL_ANSWER*/`.

Source: https://adk.dev/agents/llm-agents/
```python
from google.adk import Agent
from google.adk.planners import PlanReActPlanner, BuiltInPlanner
from google.genai import types

react_agent = Agent(name="react_agent", model="gemini-flash-latest",
                    tools=[search, calculator], planner=PlanReActPlanner())

thinking_agent = Agent(name="thinker", model="gemini-flash-latest",
    planner=BuiltInPlanner(thinking_config=types.ThinkingConfig(
        include_thoughts=True, thinking_budget=1024)))
```

### 2.7 Plan-and-execute (Planning)
- **Definition.** First produce an explicit plan, a list of sub-tasks. Then execute the steps, often with a cheaper model or deterministic workers. Re-plan when new observations invalidate the plan.
- **Lineage:**
  - **Plan-and-Solve Prompting** (Wang et al., arXiv 2305.04091, ACL 2023).
  - ReWOO (arXiv 2305.18323) and LLMCompiler (arXiv 2312.04511). **[UNVERIFIED titles/IDs; I did not fetch them today]**
- **Use when:**
  - the task is long-horizon,
  - you want the plan to be auditable or approved by a human, or
  - you want to cut cost, since only the planner needs a strong model.
- **Failure modes:**
  - Stale plans.
  - Over-planning simple tasks.
  - The executor drifts away from the plan.
  - Plans that cannot be executed with the tools available.

**[SKETCH]** ADK 2.x dynamic workflow, built from the documented primitives:
```python
@node(rerun_on_resume=True)
async def plan_and_execute(ctx: Context, goal: str):
    plan = await ctx.run_node(planner_agent, goal)          # output_schema=Plan(steps: list[str])
    results = []
    for step in plan.steps:
        results.append(await ctx.run_node(executor_agent, step))
    return await ctx.run_node(synthesizer_agent, {"goal": goal, "results": results})
```

### 2.8 Hierarchical task decomposition (orchestrator-workers)
- **Definition.** A root agent splits the task into pieces and delegates them to sub-agents, which may split their pieces further. GCP treats this as a form of the coordinator pattern. Anthropic's equivalent is *orchestrator-workers*, used when "you can't predict the subtasks needed".
- **Use when** the problem is ambiguous and open-ended, such as deep research or large codebase changes.
- **Failure modes:**
  - High complexity and many model calls.
  - Context gets lost across levels.
  - Duplicated work.
  - Errors are hard to attribute to a specific level.
- **Real-world examples:**
  - Google's Deep Research-style agents.
  - ADK sample `adk-samples` "deep-search" / "academic-research" agents. **[UNVERIFIED sample names]**
  - Anthropic's multi-agent Research system. **[UNVERIFIED in this pass]**

ADK 1.x/2.x: use nested `sub_agents`, or wrap sub-agents as tools so the parent keeps control.
```python
from google.adk.tools.agent_tool import AgentTool
research_lead = Agent(name="research_lead", model="gemini-pro-latest",
    instruction="Decompose the question, call specialists, synthesize.",
    tools=[AgentTool(agent=web_researcher), AgentTool(agent=data_analyst)])
```
- **[UNVERIFIED]** `gemini-pro-latest` is used here as an alias string. The docs examples verified today used `gemini-flash-latest`.
- The `AgentTool` import path comes from 1.x docs. Re-check it against 2.13.

### 2.9 Multi-agent collaboration / Swarm / A2A
- **Swarm** (GCP): agents communicate all-to-all and hand off to each other. A dispatcher routes the first request, but no one orchestrates. It is the "most complex and costly multi-agent option" and risks never converging.
- **A2A** (Gulli ch. 15): agents talk across process and vendor boundaries.
- **Failure modes:**
  - Agents loop on each other.
  - Responsibilities are unclear.
  - State conflicts.
  - Evaluation is hard.

### 2.10 Human-in-the-loop (HITL)
- **Definition.** The agent pauses at checkpoints so a person can approve, edit or supply data.
- **Use when** actions are high-stakes or irreversible, or the judgement is subjective. Examples: payments, releasing data, deleting things.
- **Failure modes:**
  - Approval fatigue, where people rubber-stamp requests.
  - A lost pause, for example from catching `BaseException`.
  - Unclear resume semantics.
  - Latency.
  - You need an external UI or queue to collect the human's answer.

ADK 2.x workflow pause. Source: https://adk.dev/graphs/dynamic/
```python
from google.adk.events import RequestInput

@node(rerun_on_resume=False)
async def get_user_approval(ctx: Context, node_input):
    yield RequestInput(message="Please approve this request (Yes/No)")

@node(rerun_on_resume=True)
async def handle_process(ctx: Context, node_input):
    answer = await ctx.run_node(get_user_approval)
    return "Approved" if answer.lower() == "yes" else "Denied"
```

Tool-level confirmation (experimental, ADK Python ≥ 1.14.0). Source: https://adk.dev/tools-custom/confirmation/
```python
from google.adk.tools import FunctionTool, ToolContext

async def needs_approval(amount: int, tool_context: ToolContext) -> bool:
    return amount > 1000                      # conditional HITL

root_agent = Agent(name="hr_finance_assistant", model="gemini-flash-latest",
    tools=[FunctionTool(reimburse, require_confirmation=needs_approval)])
# Advanced: tool_context.request_confirmation(hint=..., payload={...})
#           then read tool_context.tool_confirmation.payload on resume
```
(The imports above were inferred by the fetch summarizer. **[verify]**)

### 2.11 Memory management
- **Definition.** There are two layers:
  - **Short-term:** the session events and state, the context window.
  - **Long-term:** facts that persist across sessions, retrieved on demand.
- **Use when** you need personalisation, multi-session tasks, or learning from past outcomes (Gulli ch. 8–9).
- **Failure modes:**
  - Context bloat.
  - Stale or contradictory memories.
  - Privacy and PII leakage.
  - Memory poisoning through injected content.
  - Over-retrieval.

ADK classes:
- `InMemoryMemoryService` and `VertexAiMemoryBankService`, both in `google.adk.memory`.
- The `preload_memory` and `load_memory` tools, both in `google.adk.tools`.
- `add_session_to_memory(session)`.

Source: https://adk.dev/sessions/memory/
```python
from google.adk.agents import Agent
from google.adk.tools import preload_memory

async def auto_save(callback_context):
    await callback_context.add_session_to_memory()

agent = Agent(model=MODEL, name="Generic_QA_Agent",
              instruction="Answer the user's questions",
              tools=[preload_memory], after_agent_callback=auto_save)
```
Short-term state is handled with `output_key` and `{placeholder}` templating in instructions. A key teaching point: `include_contents="none"` isolates each agent's context.

### 2.12 Agentic RAG (Knowledge retrieval)
- **Definition.** Classic RAG does one retrieve-then-generate pass. Agentic RAG embeds "autonomous AI agents into the RAG pipeline". The agent decides *whether*, *what* and *where* to retrieve, rewrites queries, critiques the results and iterates.
- **Survey:** Singh et al., "Agentic Retrieval-Augmented Generation: A Survey on Agentic RAG", arXiv 2501.09136 (2025-01-15; v4 2026-04-01).
- **Use when:**
  - questions need multiple hops,
  - there are heterogeneous sources (vector store, SQL, web), or
  - there is a high risk of hallucination.
- **Failure modes:**
  - Retrieval loops.
  - Irrelevant chunks treated as truth.
  - Citation drift.
  - Latency and cost.
  - Injection through retrieved documents.

ADK: `VertexAiRagRetrieval`, imported from `google.adk.tools.retrieval.vertex_ai_rag_retrieval` (per the adk.dev knowledge-engine integration page). This was **[UNVERIFIED by direct fetch]**.

**[SKETCH]** Agentic loop: a retriever agent with the RAG tool, a grader critic, and query rewriting.
```python
from google.adk.tools.retrieval.vertex_ai_rag_retrieval import VertexAiRagRetrieval
from vertexai.preview import rag

rag_tool = VertexAiRagRetrieval(name="retrieve_docs",
    description="Retrieve product documentation",
    rag_resources=[rag.RagResource(rag_corpus=CORPUS_NAME)],
    similarity_top_k=10)
retriever = LlmAgent(name="retriever", model=MODEL, tools=[rag_tool],
    instruction="Rewrite the query if needed, retrieve, answer with citations.",
    output_key="answer")
grader = LlmAgent(name="grader", model=MODEL, tools=[exit_loop],
    instruction="If {answer} is grounded & complete call exit_loop, else say what to search next.")
agentic_rag = LoopAgent(name="agentic_rag", sub_agents=[retriever, grader], max_iterations=3)
```

### 2.13 Guardrails / Safety
- **Definition.** Layered checks before, during and after model and tool calls (Gulli ch. 18). The ADK safety docs list five layers:
  1. In-tool guardrails, with policy set in Tool Context.
  2. Callbacks, such as `before_tool_callback` validation.
  3. **Plugins**, which are "the recommended approach for implementing policies that are not specific to a single agent". Examples include a Gemini-Flash-Lite-as-judge and PII redaction.
  4. The **Model Armor plugin**, which ships with ADK.
  5. Sandboxed code execution, which should be "hermetic" with no network.

  Source: https://adk.dev/safety/
- **Quote:** "we can deterministically eliminate classes of rogue actions that we never want the agent to take" (ADK Safety).
- **Failure modes:**
  - False positives that block legitimate users.
  - Prompt injection through tool outputs bypassing input-only filters.
  - Guardrail latency.
  - Inconsistent policies across agents (the fix is plugins).

Callback contract (https://adk.dev/callbacks/types-of-callbacks/): return `None` to proceed, or return an object to short-circuit.
```python
from typing import Optional, Any, Dict
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext
from google.genai import types

def block_secrets(callback_context: CallbackContext,
                  llm_request: LlmRequest) -> Optional[LlmResponse]:
    text = str(llm_request.contents[-1]) if llm_request.contents else ""
    if "password" in text.lower():
        return LlmResponse(content=types.Content(role="model",
            parts=[types.Part(text="I can't help with credentials.")]))
    return None                                  # proceed to the LLM

def limit_refunds(tool: BaseTool, args: Dict[str, Any],
                  tool_context: ToolContext) -> Optional[Dict]:
    if tool.name == "refund" and args.get("amount", 0) > 500:
        return {"error": "Refunds > $500 need human approval."}  # skip tool
    return None

agent = Agent(..., before_model_callback=block_secrets,
              before_tool_callback=limit_refunds)
```
Static content filters are set through `generate_content_config=types.GenerateContentConfig(safety_settings=[types.SafetySetting(...)])`.

### 2.14 Resource-aware optimization / routing (cost, latency, budget)
- **Definition** (Gulli ch. 16). Dynamically choose the model, the tools and the reasoning depth for each request, based on cost, latency and quality budgets. This includes fallback models and graceful degradation.
- **Use when:**
  - traffic is high,
  - the mix is mixed-difficulty (most queries are easy), or
  - SLAs are strict.
- **Failure modes:**
  - A weak classifier sends hard queries to the cheap model, which hurts quality.
  - Thrashing between models.
  - Hidden costs from the classifier itself.
  - Inconsistent tone between models.

ADK:
- Assign a model per agent, e.g. a Flash classifier with Pro specialists.
- Bound reasoning cost with `BuiltInPlanner(thinking_config=ThinkingConfig(thinking_budget=N))`.
- In **ADK TypeScript ≥1.0.0** there are experimental `RoutedLlm` (model routing) and `RoutedAgent` (agent routing), with fallback-on-error and auto-routing-by-complexity examples. Source: https://adk.dev/agents/models/routing/ and https://adk.dev/agents/routing/
- I found no Python equivalent documented today. **[UNVERIFIED for Python]**

**[SKETCH]** Python graph version:
```python
classifier = Agent(name="complexity", model="gemini-flash-lite-latest",   # [UNVERIFIED alias]
    instruction='Reply "SIMPLE" or "COMPLEX" only.')
def pick(node_input: str): return Event(route=node_input.strip())
root_agent = Workflow(name="budget_router", edges=[
    ("START", classifier, pick),
    (pick, {"SIMPLE": flash_agent, "COMPLEX": pro_agent}),
])
```

### 2.15 Exception handling, Goal monitoring, Evaluation (brief)
- **Exception handling** (ch. 12):
  - classify errors as transient or permanent,
  - bound retries (`RetryConfig(max_attempts=3)` in 2.x),
  - restore state from checkpoints (2.x resume re-runs only failed or interrupted child nodes), and
  - stop safely.
  - Anti-pattern: broad `except` blocks in tools, which disable retries.
- **Goal setting and monitoring** (ch. 11): explicit success criteria in state, plus a monitor node or critic that checks progress.
- **Evaluation and monitoring** (ch. 19): ADK `adk eval` with trajectory and response metrics, plus tracing. Covered in another research file.

---

## 3. Decision flow (diagram in words)

1. Start with **one LLM call plus retrieval and examples**. This is Anthropic's advice.
2. Are the steps fixed?
   - **Yes:** use a **Sequential / chain** with gates.
   - **No:** go to 3.
3. Do the inputs fall into distinct categories?
   - **Yes:** use **Routing**, and add a default route.
4. Are the sub-tasks independent?
   - **Yes:** use **Parallel + Join**.
5. Is there a clear quality bar?
   - **Yes:** use a **Generator-critic loop**, with a hard cap and a deterministic critic where possible.
6. Are the sub-tasks unpredictable?
   - **Yes:** use an **Orchestrator / Hierarchical** design.
   - If the work is also open-ended and creative: consider a **Swarm**. It is the last resort.
7. Can't predict the number of steps, and the task depends on tools?
   - **ReAct agent**, with max iterations set.
8. Apply these overlays to every design:
   - **Guardrails** (plugins/callbacks).
   - **HITL** on irreversible actions.
   - **Memory** if multi-session.
   - **Resource-aware routing** at scale.
   - **Eval** always.

---

## 4. Real-world examples (with confidence)
- **Ng's coding example:** GPT-3.5 in an agent loop reached 95.1% on HumanEval, vs 67.0% for GPT-4 zero-shot. **[VERIFIED]**
- **GCP Architecture Center examples:**
  - Coordinator: customer-service routing (order status, returns, refunds).
  - HITL: approving large financial transactions.
  - Generator-critic: security review of generated code.
  - Swarm: product design.

  **[VERIFIED]**
- **Anthropic** names customer support and coding agents (SWE-bench) as the two domains where agents prove most valuable. That is from the appendix of the same post. **[UNVERIFIED wording]**
- **ADK samples:** github.com/google/adk-python/tree/main/contributing/samples/workflows and /multi_agent. **[VERIFIED links from adk.dev/2.0]**

---

## 5. Quotable lines (for slide footers)
- "They are typically just LLMs using tools based on environmental feedback in a loop." — Anthropic, Building effective agents (2024)
- "finding the simplest solution possible, and only increasing complexity when needed" — Anthropic
- "wrapped in an agent loop, GPT-3.5 achieves up to 95.1%." — Andrew Ng, The Batch (2024-03-20)
- "The Workflow Runtime replaces hierarchical agent execution with a graph-based engine." — adk.dev/2.0 (paraphrase-level; check the exact wording)
- "plugins are the recommended approach for implementing policies that are not specific to a single agent." — adk.dev/safety
- "Starting in ADK 2.0 for Python and Go, templated workflows have been superseded." — adk.dev loop-agents page
- "Each of the 21 Design Patterns represents a fundamental building block for creating agents" — publisher description of Gulli (2025)

---

## 6. Sources (exact titles + URLs)
- **Andrew Ng**, "How Agents Can Improve LLM Performance" / "Agentic Design Patterns Part 1", The Batch, 2024-03-20: https://www.deeplearning.ai/the-batch/how-agents-can-improve-llm-performance/
- **Anthropic**, "Building effective agents", 2024-12-19: https://www.anthropic.com/engineering/building-effective-agents
- **A. Gulli**, *Agentic Design Patterns: A Hands-On Guide to Building Intelligent Systems*, Springer, 2025: https://link.springer.com/doi/10.1007/978-3-032-01402-3
- **Google Cloud**, "Choose a design pattern for your agentic AI system": https://docs.cloud.google.com/architecture/choose-design-pattern-agentic-ai-system
- **ADK 2.0 docs:**
  - https://adk.dev/2.0/
  - https://adk.dev/graphs/
  - https://adk.dev/graphs/routes/
  - https://adk.dev/graphs/dynamic/
  - https://adk.dev/workflows/collaboration/
  - https://adk.dev/agents/workflow-agents/loop-agents/
  - https://adk.dev/tools-custom/confirmation/
  - https://adk.dev/sessions/memory/
  - https://adk.dev/callbacks/types-of-callbacks/
  - https://adk.dev/callbacks/design-patterns-and-best-practices/
  - https://adk.dev/safety/
  - https://adk.dev/agents/llm-agents/
  - https://adk.dev/agents/routing/
  - https://adk.dev/agents/models/routing/
- **Papers:**
  - Yao et al., "ReAct: Synergizing Reasoning and Acting in Language Models" (arXiv 2210.03629, ICLR 2023)
  - Shinn et al., "Reflexion: Language Agents with Verbal Reinforcement Learning" (arXiv 2303.11366, NeurIPS 2023 [venue UNVERIFIED])
  - Madaan et al., "Self-Refine: Iterative Refinement with Self-Feedback" (arXiv 2303.17651)
  - Wang et al., "Plan-and-Solve Prompting…" (arXiv 2305.04091, ACL 2023)
  - Singh et al., "Agentic Retrieval-Augmented Generation: A Survey on Agentic RAG" (arXiv 2501.09136)
- **Course:** DeepLearning.AI "Agentic AI" (Andrew Ng): https://www.deeplearning.ai/courses/agentic-ai/

---

## 7. Slide ideas (8)
1. **"Four maps of the same territory"**
   - Visual: a 4-column table (Ng / Anthropic / Gulli / GCP) with rows lighting up as connecting lines link equivalent patterns (the mapping table in §0).
   - Animation: rows appear one at a time.
2. **"Workflows vs Agents: the autonomy dial"**
   - Visual: a horizontal slider running from prompt chain → routing → parallel → evaluator loop → orchestrator → ReAct agent → swarm.
   - Animation: cost and latency bars grow as the dial moves right.
   - Footer: the Anthropic quote.
3. **"Gulli's 21 patterns in 5 levels"**
   - Visual: a pyramid or staircase (Flow control → Agent loop → State & coordination → Contact with reality → Scale), with chapter numbers.
   - Animation: each level builds upward.
4. **"The 95.1% slide"**
   - Visual: bar chart of HumanEval scores: GPT-3.5 zero-shot 48.1, GPT-4 zero-shot 67.0, GPT-3.5 in an agent loop 95.1. Add Reflexion 91 vs GPT-4 80 as a second panel.
   - Message: the workflow beats the model upgrade.
5. **"ReAct, frame by frame"**
   - Visual: a Thought → Action → Observation carousel over a real ADK event trace, with the `PlanReActPlanner` tags highlighted.
   - Animation: a token-stream typing effect.
6. **"ADK 2.0 = graphs"**
   - Visual: `Workflow(edges=[...])` code on the left, the rendered DAG on the right (START → classifier → router → {BUG, SUPPORT, LOGISTICS}). Then a JoinNode fan-in, then a back-edge loop.
   - Animation: each edge tuple lights up the matching arrow.
7. **"Generator-critic loop with an exit door"**
   - Visual: a circular loop between Coder → Lint → Fixer, with a counter showing `max_iterations=5` and an "exit_loop / escalate" door.
   - Animation: the counter ticks up until the door opens.
   - Footer: failure modes (oscillation, lenient critic).
8. **"Defense in depth"**
   - Visual: concentric rings (in-tool policy → before_tool callback → plugin / Gemini judge → Model Armor → sandbox), with an attack arrow stopped at different rings.
   - Animation: a "prompt injection in a tool output" arrow passes the input filter and is stopped by the before_tool callback.
9. **"HITL: pause, persist, resume"**
   - Visual: a timeline with a `RequestInput` pause icon, the session persisted to a DB, a human approval on a phone, and the workflow resuming (`rerun_on_resume`).
   - Callout: never catch `BaseException`.
10. **"Pick a pattern" decision tree**
    - Visual: the flowchart from §3.
    - Interactive: the audience votes on a scenario (refund bot, research assistant, ETL) and the tree highlights the path.
