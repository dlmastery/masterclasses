# 02 — Modern Agent Harness Architectures (state of the art, Oct 2026)

*Research date: 2026-10-23. Scope: mid-2025 to Oct 2026. Every source was fetched directly unless it is marked [UNVERIFIED]. Some OpenAI pages returned HTTP 403, so a few OpenAI claims rely on secondary reporting and are labelled that way.*

---

## 0. The one-slide thesis

The old picture of an agent was a ReAct loop: *Thought → Action → Observation*, repeated inside a single growing prompt. That picture is gone. In 2026 the unit of design is the **harness**, meaning everything around the model: the loop, the tools, the context policy, the filesystem or sandbox, subagents, skills, durable state and verification. Three shifts drove the change:

1. **Context is the scarce resource, not reasoning.** Anthropic calls this "context rot" and an "attention budget" (*Effective context engineering for AI agents*, Sep 29 2025).
2. **Determinism belongs in code, and judgment belongs in the model.** This is why Google ADK 2.0 added graph workflows, and why the agents themselves now write their orchestration as code (Claude Code dynamic workflows, Code Mode).
3. **Agents now run for hours or days.** They need durable execution, external memory (files, progress logs, git) and separate evaluators, not just a bigger context window.

> "Harness includes context engineering, architectural constraints, and garbage collection." — Martin Fowler, quoted in InfoQ, Feb 21 2026

> "Each harness component encodes an assumption about what the model can't do alone… those assumptions should be stress-tested with each new model." — paraphrase of Prithvi Rajasekaran, *Harness design for long-running apps*, Anthropic, Mar 24 2026

---

## 1. "Deep agents": the four-part harness

**Definition.** Harrison Chase, *Deep Agents*, LangChain blog, **Jul 30 2025** (https://www.langchain.com/blog/deep-agents). The post says a plain tool-calling loop gives "shallow" agents that "fail to plan and act over longer, more complex tasks". Deep Research, Manus and Claude Code avoid this with four components:

1. A **detailed system prompt** that includes tool instructions and example behaviours
2. A **planning tool**, which is a todo list (`write_todos`). In Claude Code this tool is essentially a no-op: its value is that it makes the model recite the plan.
3. **Subagents** that go deep on a subtask in an isolated context
4. A **filesystem** used for notes and as a shared workspace

**Why it replaced ReAct.** ReAct keeps every observation in the prompt, so long tasks overflow the window and the agent drifts off goal. Deep agents move state *out* of the prompt and into files and the todo list. They move exploration *out* of the main context and into subagents.

**Implementation: `deepagents`** (https://github.com/langchain-ai/deepagents, about 30.5k stars as of Oct 2026). It runs on LangGraph, and `create_deep_agent()` returns a compiled LangGraph graph. Per the official docs (https://docs.langchain.com/oss/python/deepagents/overview), the built-in tools are:

| Tool | Purpose |
|---|---|
| `ls`, `read_file`, `write_file`, `edit_file`, `delete` (>=0.7), `glob`, `grep` | virtual filesystem |
| `execute` | shell, available only with sandbox backends |
| `task` | spawn a subagent with an isolated context |
| `write_todos` | plan; opt-in via `TodoListMiddleware` since v0.7 |

- **Pluggable backends** for the virtual filesystem: `StateBackend` (in graph state), `FilesystemBackend` (local disk), `StoreBackend` (LangGraph store, persists across threads), `CompositeBackend` (routes by path prefix), and sandbox backends.
- **Skills** follow the Agent Skills standard and use progressive disclosure.
- **Memory** comes from `AGENTS.md` files. Memory is always loaded, while skills load lazily.
- A CLI coding agent, "Deep Agents Code", is also available.

```python
from deepagents import create_deep_agent
from langchain.agents.middleware import TodoListMiddleware

def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"

agent = create_deep_agent(
    model="anthropic:claude-sonnet-5",
    tools=[get_weather],
    system_prompt="You are a helpful assistant",
    middleware=[TodoListMiddleware()],   # planning is opt-in since v0.7
)
agent.invoke({"messages": [{"role": "user", "content": "what is the weather in sf"}]})
```

**Architecture flow for a diagram.** The user task goes to the main agent, whose context holds the system prompt and the todo list. The main agent calls `write_todos` to write a plan. For each todo, it either works directly with `read_file`/`grep`/`edit_file`, or calls `task(...)` to start a subagent with a fresh context window. The subagent does its own tool calls, writes its large outputs to `/notes/x.md`, and returns a summary of about 1–2k tokens. The main agent updates the todos, and summarisation middleware compacts old turns. When every todo is done, the main agent writes the final artefact to a file.

**Failure modes.** Token blow-up from planning plus subagents, which reviewers flag often. Subagents returning bloated or lossy summaries. A todo list that drifts from reality. Hacker News critics argue that "nothing fundamentally new" is here; the defence is that the novelty is in packaging good defaults, not in a new algorithm.

---

## 2. Claude Agent SDK and the Claude Code architecture

**Primary sources**
- *Building agents with the Claude Agent SDK*, Thariq Shihipar, **Sep 29 2025** (https://claude.com/blog/building-agents-with-the-claude-agent-sdk). The Claude Code SDK was renamed the Claude Agent SDK. The loop is **"gather context → take action → verify work → repeat."** Subagents are on by default. They give parallelism and context isolation, and each returns only relevant results. Compaction "automatically summarizes previous messages when the context limit approaches."
- Docs: https://code.claude.com/docs/en/agent-sdk/overview. The SDK is "Claude Code as a library". It ships built-in tools (Read/Write/Edit/Bash/Glob/Grep/WebSearch), **hooks**, **subagents**, **MCP**, **permissions**, **sessions** (resume/fork), skills, commands and memory loaded from `.claude/`, and **plugins**.
- Hosted variant: **Claude Managed Agents**, a hosted harness with sessions in an Anthropic cloud sandbox or a self-hosted sandbox.

**Design philosophy: "give the agent a computer."** Rather than writing a bespoke tool for every API, the agent gets bash and a filesystem and finds context itself with `grep`/`tail`. This is agentic search, not up-front RAG. In *Effective context engineering*, Anthropic calls this **just-in-time retrieval**: keep "lightweight identifiers (file paths, stored queries, web links)" and load the content only when it is needed.

```python
# Claude Agent SDK (Python) — minimal pattern
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions

async def main():
    async for msg in query(
        prompt="Find and fix the failing test in tests/",
        options=ClaudeAgentOptions(allowed_tools=["Read", "Edit", "Bash", "Grep"],
                                   permission_mode="acceptEdits"),
    ):
        print(msg)
asyncio.run(main())
```
*(The API shape follows the SDK quickstart. Check the current option names against the Python reference before using this on a slide.)*

### 2a. Scaling Managed Agents: separate the brain from the hands
*Scaling Managed Agents: Decoupling the brain from the hands*, Lance Martin, Gabe Cemaj, Michael Cohen, **Apr 8 2026** (https://www.anthropic.com/engineering/managed-agents).

- Three separate virtualised parts:
  - The **Session** is an append-only event log kept *outside* the context window.
  - The **Harness** is the loop that calls Claude and routes tool calls.
  - The **Sandbox** is where code runs and files change.
- The interfaces are `execute(name, input) → string`, `provision({resources})`, `wake(sessionId)`, `getSession(id)`, `emitEvent(id, event)` and `getEvents()`.
- If a container dies, the harness sees an ordinary tool-call error. If the harness crashes, it restarts with `wake(sessionId)` and replays the log.
- Credentials never enter the sandbox. MCP calls go through a proxy that pulls secrets from a vault.
- **Numbers.** Provisioning containers lazily cut **p50 TTFT about 60%** and **p95 by more than 90%**.
- Quote: Anthropic is "opinionated about the shape of these interfaces, not about what runs behind them."

### 2b. Dynamic workflows: the agent writes its own harness
*A harness for every task: dynamic workflows in Claude Code*, Thariq Shihipar and Sid Bidasaria, **Jun 2 2026** (https://claude.dev/blog/a-harness-for-every-task-dynamic-workflows-in-claude-code/).

- A workflow is a **JavaScript file that Claude writes**. Its primitives are `agent(prompt, {schema, model, isolation:"worktree"|"remote", agentType})`, `parallel()` and `pipeline()`. Workflows can resume after an interruption.
- It fixes three failure modes of a single context:
  - **agentic laziness**, for example "addressing 35 of the 50 items in a security review"
  - **self-preferential bias** when the agent verifies its own work
  - **goal drift**: "Each summarization step is lossy"
- Patterns: classify-and-act, fan-out-and-synthesize, adversarial verification, generate-and-filter, tournament, and loop-until-done.
- **Numbers** from sample runs:
  - `review-changes`: 14 agents, 482k tokens, 6m12s
  - `deep-research`: 22 agents, 1.1M tokens, 11m3s
  - Sorting more than 1,000 rows in one prompt degrades quality, which is why the post uses a tournament sort.
- Caveat: "most traditional coding tasks do not need a panel of 5 reviewers."

---

## 3. Long-horizon agents: the harness patterns that work

### 3a. Initializer agent + coding agent
*Effective harnesses for long-running agents*, Justin Young, **Nov 26 2025** (https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents).

- The problem: each session starts without memory, and compaction alone was not enough, even for Opus 4.5 building a claude.ai clone.
- The **initializer agent** runs in session 1. It writes `init.sh`, `claude-progress.txt`, a **feature list in JSON** (more than 200 features, each `passes:false`) and an initial git commit.
- The **coding agent** runs in sessions 2…N. Each session reads the progress file and git log, runs `init.sh`, picks **one** feature, tests it end-to-end with Puppeteer MCP, flips `passes` to true, commits, and updates the progress file.
- The feature list is JSON rather than Markdown because "the model is less likely to overwrite it."
- The two agents differ **only in their first user prompt**. They share the same system prompt, tools and harness.
- The failure modes it fixes: declaring victory early, leaving undocumented bugs, marking features done without testing, and wasting time working out how to run the app.

### 3b. Planner → Generator → Evaluator (GAN-inspired)
*Harness design for long-running apps*, Prithvi Rajasekaran, **Mar 24 2026** (https://www.anthropic.com/engineering/harness-design-long-running-apps).

- **Self-evaluation leniency.** Agents praise their own mediocre work, and a **separately tuned evaluator** using Playwright on the live app works far better. Older models such as Sonnet 4.5 also showed "context anxiety": they wrapped up early as they neared the limit.
- **Retro game maker on Opus 4.5.** Solo run: 20 min, $9, and the core game did not respond to input. Full harness: **6 h, $200**, and the app worked.
- **DAW on Opus 4.6 with a simplified harness:** **3 h 50 min, $124.70** in total. Planner $0.46. Three build and QA rounds.
- **Scaffolding removed as models improved:**
  - Context resets were dropped with Opus 4.5.
  - Sprint decomposition was dropped with Opus 4.6.
  - Per-sprint evaluation became one QA pass at the end.
  - The **planner was kept**, because without it the generator under-scopes.
- The lesson: harness complexity does not shrink as models improve; it *moves*. Re-test every component with each new model.

### 3c. Context-engineering rules from production (Manus)
*Context Engineering for AI Agents: Lessons from Building Manus*, Yichao "Peak" Ji, **Jul 18 2025** (https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus).

- The **KV-cache hit rate** is "the single most important metric". The input:output token ratio is about **100:1**, and cached input is 10× cheaper ($0.30 vs $3 per MTok on Sonnet). Keep prefixes stable and the context append-only.
- **Mask, don't remove** tools mid-task, because changing the tool list breaks the cache.
- Treat the **filesystem as the ultimate context**, and compress reversibly (keep the URL, drop the page).
- **Recite** the plan through `todo.md` so goals stay at the end of the context.
- **Keep errors in the context** so the model updates its beliefs.
- **Don't few-shot yourself into a rut**: add controlled variation.
- A typical task uses about 50 tool calls, and the team rebuilt the framework 4 times.

---

## 4. Agent loop vs workflow: Anthropic's updated view

- *Building effective agents*, Erik Schluntz and Barry Zhang, **Dec 19 2024** (https://www.anthropic.com/engineering/building-effective-agents).
  - **Workflows** are "systems where LLMs and tools are orchestrated through predefined code paths." **Agents** are systems where the LLM directs its own process.
  - The five patterns: prompt chaining, routing, parallelization, orchestrator-workers and evaluator-optimizer.
  - The guidance: "finding the simplest solution possible."
- **2026 update.** The page now opens with a banner: "Much of the tooling landscape described in this post has changed since December 2024". It points to Claude Managed Agents as the current approach.
- **What has changed in practice:**
  1. The five patterns survive, but they are now **composed at runtime by the agent itself**. In Claude Code dynamic workflows, evaluator-optimizer becomes "adversarial verification" and orchestrator-workers becomes "fan-out-and-synthesize".
  2. **Frameworks are hybrid.** ADK 2.0 graph and dynamic workflows, LangGraph and Vercel Workflow all let you put an autonomous agent node inside a deterministic graph.
  3. The deciding question is no longer "agent or workflow?" but **"which parts must be deterministic (money, compliance, routing) and which need judgment?"**

---

## 5. Google ADK 2.0: graph workflows plus collaborative agents

**Release dates** (https://adk.dev/2.0/): ADK **Python 2.0 GA May 19 2026**, **Go 2.0 GA Jun 30 2026**, **TypeScript 2.0 GA Aug 21 2026**. Python workflows had been in preview since March 2026.

**Blog:** *Why we built ADK 2.0*, Swapnil Agarwal, Alan Blount and Frank Guan, **Jul 1 2026** (https://developers.googleblog.com/why-we-built-adk-20/).

- The problem in production: agents "loop endlessly, bypass business logic, or fail silently". Using an LLM for routing and error handling is "slower, more expensive, and less consistent than deterministic code."
- Quote: **"Developers shouldn't have to choose between flexibility and predictability."**
- Numbers, which the post labels illustrative (gemini-3.5-flash, mocked APIs). A refund task took **5,152 → 2,265 tokens (~50%)** and **7.2 s → 5.7 s latency (~20%)**, comparing a vanilla agent with a workflow.

**What changed technically.** ADK moved from a hierarchical agent executor to a **graph-based Workflow Runtime**. Agents, tools and functions are all **nodes**, and `BaseAgent` now extends `BaseNode`. Each node gets `retryConfig`, `timeout`, `inputSchema`, `outputSchema`, `stateSchema` and `rerunOnResume`. ADK 2.0 offers three workflow types:
- **Graph-based**: static edges with conditional routes. A router node emits a `route` value, an array value fans out, and `JoinNode` handles fan-in in Go.
- **Dynamic**: native Python control flow and asyncio, embeddable as a sub-workflow.
- **Collaborative**: a coordinator plus subagents. ADK auto-generates one delegation tool per subagent.

```python
# ADK 2.0 static graph (verbatim from Google Developers Blog, Jul 1 2026)
workflow = Workflow(
    name="Refund_Workflow",
    edges=[
        (START, fetch_purchase_history, analyze_complaint_agent),
        (analyze_complaint_agent, route_complaint, {True: issue_refund, False: close_ticket}),
        (issue_refund, draft_email_agent, close_ticket),
    ]
)
```

```python
# ADK 2.0 collaborative workflow with subagent modes (condensed from adk.dev/workflows/collaboration)
weather_agent = Agent(name="weather_checker", mode="single_turn", tools=[...])
flight_agent  = Agent(name="flight_booker", mode="task",
                      input_schema=FlightInput, output_schema=FlightResult, tools=[...])
root = Agent(name="travel_planner", sub_agents=[weather_agent, flight_agent])
```

**Subagent modes:**

| Mode | User interaction | Return to parent | Parallel runs |
|---|---|---|---|
| `chat` (default) | full | manual `transfer_to_agent` | no |
| `task` | clarifying questions only | automatic via `finish_task` | no |
| `single_turn` | none | automatic | yes |

- Don't set `mode` on the root agent.
- `task` agents must be leaves.
- In Python v2.0.0, `task` mode is disabled inside graph workflows.

**Migration gotchas (good interview material):**
- Events gain `node_info`/`output` fields, so rigid DB schemas break, and running **2.0 code on 1.x databases risks data loss**.
- `SequentialAgent`, `ParallelAgent` and `LoopAgent` are deprecated but still work.
- Overrides of `_run_async_impl()` are bypassed; use callbacks instead.
- Don't catch broad `Exception` in tools, because it disables automatic retries. Never swallow `BaseException`, because it traps `NodeInterruptedError` and breaks HITL pause/resume.
- Configure retries with `RetryConfig`.

**Architecture flow for a diagram.** START → `fetch_purchase_history` (a deterministic function node, with retries) → `analyze_complaint_agent` (an LLM node in `single_turn` mode with a typed output schema) → router (a code node) → True: `issue_refund` (a tool node, optionally behind a human-input pause) → `draft_email_agent` (LLM) → `close_ticket`; False: `close_ticket`. Every node yields events into the session, which allows replay or resume.

---

## 6. OpenAI Agents SDK and Codex

- **Agents SDK** (https://openai.github.io/openai-agents-python/). Its primitives are Agents, handoffs and agents-as-tools, guardrails, sessions, tracing, MCP, HITL and voice. New since 2026: **Sandbox agents** (`SandboxAgent`) with a `Manifest` that defines workspace files and repos, sandbox clients (Unix-local, Docker, hosted), and **Capabilities**: Filesystem, Shell, **Skills** (lazy-loaded), **Memory** and **Compaction**. Sessions can resume via `SandboxRunConfig.session`/`snapshot`. Secondary reports date this to an April 2026 update ("model-native harness… AGENTS.md support") [date UNVERIFIED].

```python
agent = SandboxAgent(
    name="Sandbox engineer",
    model=model,
    instructions="Read `repo/task.md` before editing files. ... mention the exact verification command you ran.",
    default_manifest=Manifest(entries={"repo": LocalDir(src=HOST_REPO_DIR)}),
    capabilities=Capabilities.default() + [
        Skills(lazy_from=LocalDirLazySkillSource(source=LocalDir(src=HOST_SKILLS_DIR)))],
)
result = await Runner.run(agent, "Open `repo/task.md`, fix the issue, run the targeted test...",
    run_config=RunConfig(sandbox=SandboxRunConfig(client=UnixLocalSandboxClient())))
```

- **Harness engineering at OpenAI**: InfoQ, Feb 21 2026, citing https://openai.com/index/harness-engineering/ (I could not fetch the original, which returned 403).
  - A five-month internal project shipped a beta of **about 1M lines of code with no manually written source**.
  - Engineers designed environments, intent and feedback loops. A structured docs directory of maps, exec plans and specs was the "single source of truth", validated by linters and CI.
  - Structural tests enforce the layering Types → Config → Repo → Service → Runtime → UI.
  - Agents used logs, metrics and spans to reproduce bugs.
- **Codex App Server and one harness.** Secondary reports from Feb 2026 say the Codex web app, CLI, IDE extension and Mac app all run the same harness [UNVERIFIED, from secondary sources].
- **Codex harness open-sourced** (Apache-2.0, Aug 2026) [UNVERIFIED, single secondary outlet].
- **Agents API**, public beta, Sep 2026 (https://openai.com/index/introducing-the-agents-api/). OpenAI's page, as quoted in search results, says it brings "that same harness and infrastructure that powers Codex to developers". OpenAI hosts the harness, and you choose the compute: an OpenAI sandbox, your own infrastructure, or a partner. [Partially verified: the page returned 403 to the fetch, and the quote comes from the search snippet.]
- **Takeaway.** OpenAI and Anthropic have converged on one product shape: **a hosted harness plus a pluggable sandbox plus a durable session**.

---

## 7. Durable execution: agents that survive crashes, deploys and humans

**Why it matters.** A six-hour agent run that dies at hour five must not repeat five hours of LLM calls and side effects. Durable execution **journals each non-deterministic step**, meaning LLM calls and tool calls, and replays the journal after a crash. Waits for a human take no compute.

| System | Model | Agent integration (verified) |
|---|---|---|
| **Temporal** | The workflow is deterministic code; Activities hold side effects | *Production-ready agents with the OpenAI Agents SDK + Temporal*, Cornelia Davis, Jul 30 2025. "every agent invocation is executed through a Temporal Activity". **GA on Mar 23 2026** (Python). |
| **Restate** | `ctx.run()` journals each step | *Durable AI Loops: Fault Tolerance across Frameworks and without Handcuffs*, Ewen, van Dongen and Shilman, Jun 19 2025. Middleware for the Vercel AI SDK and the OpenAI Agents SDK. Caveat: parallel tool calls need promise combinators. |
| **DBOS** | Postgres-backed `@DBOS.workflow` / `@DBOS.step` | *Durable Execution for Building Crashproof AI Agents*, Qian Li, Feb 24 2025 (a little before the scope window). `DBOS.recv/send` handles async approvals, and `@tool @DBOS.workflow()` is stackable. |
| **Vercel Workflow SDK** | `"use workflow"` / `"use step"` directives; `sleep("15m")`; `defineHook()`, `createWebhook()` | Workflow SDK **v5** (docs updated Oct 21 2026), with `WorkflowAgent` from the AI SDK. The docs moved from useworkflow.dev to workflow-sdk.dev. |
| **LangGraph** | Checkpointers (`PostgresSaver`/`SqliteSaver`) keyed by `thread_id` | `InMemorySaver` loses state on restart. Deep Agents inherit this from LangGraph. |
| **ADK 2.0** | Node events in the session, `rerunOnResume`, `RetryConfig`, `NodeInterruptedError` for HITL | Built into the Workflow Runtime. |
| **Anthropic Managed Agents** | An append-only session log with `wake(sessionId)` | Harness restarts are treated as routine. |

```python
# Temporal + OpenAI Agents SDK (verbatim from Temporal blog)
@workflow.defn
class HelloWorldAgent:
   @workflow.run
   async def run(self, prompt: str) -> str:
       agent = Agent(name="Assistant", instructions="You only respond in haikus.")
       result = await Runner.run(agent, input=prompt)
       return result.final_output
```

```ts
// Restate: journal a tool's side effect
execute: async ({ city }) => {
  const result = await restate_ctx.run(() => fetchWeather(city)); // replayed after crash
  return await parseWeatherResponse(result);
}
```

**Failure modes:**
- Non-determinism inside workflow code, such as `Date.now()` or random numbers, breaks replay.
- Changing the code while runs are in flight needs workflow versioning.
- Parallel tool calls complicate replay.
- An in-memory checkpointer in production gives no durability at all.

---

## 8. Agent Skills and progressive disclosure

*Equipping agents for the real world with Agent Skills*, Barry Zhang, Keith Lazuka and Mahesh Murag, **Oct 16 2025** (https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills). The **open standard** was published **Dec 18 2025**.

- A skill is a set of "organized folders of instructions, scripts, and resources that agents can discover and load dynamically."
- It loads in three levels of **progressive disclosure**:
  1. **Metadata.** `name` and `description` from the YAML frontmatter go into the system prompt at startup, at a cost of tens of tokens per skill.
  2. **SKILL.md body.** The full file loads only when the skill looks relevant.
  3. **Linked files and scripts**, for example `forms.md` in the PDF skill. These are read or executed only when needed. Scripts run without their *source* entering the context.

```markdown
---
name: pdf-forms
description: Fill and extract PDF form fields. Use when the user mentions PDF forms.
---
# PDF forms
1. Run `python scripts/extract_fields.py <file>` to list fields.
2. For complex forms, read `forms.md`.
```

- **Adoption, all verified in docs during this research:**
  - Claude Code and the Agent SDK load skills from `.claude/skills`.
  - LangChain Deep Agents use "the Agent Skills standard".
  - The OpenAI Agents SDK has `Skills(lazy_from=...)`.
  - Claude Code dynamic workflows can be shared via a skill.
- **Why it replaced older approaches.** Giant system prompts and "one tool per capability" spend the context budget up front. Skills spend almost nothing until they are used, and they let an agent *save working code as a reusable skill*, as the code-execution post describes.
- **Failure modes:**
  - Vague descriptions mean a skill never triggers, or triggers wrongly.
  - Too many skills bloat Level 1.
  - Untrusted skills are a supply-chain and prompt-injection vector, because they bundle executable scripts.

---

## 9. Code execution with MCP ("Code Mode")

- **Cloudflare:** *Code Mode: the better way to use MCP*, Kenton Varda and Sunil Pai, **Sep 26 2025** (https://blog.cloudflare.com/code-mode/).
  - Convert MCP tools into a **TypeScript API** and have the model write code against it.
  - Quote: **"LLMs are better at writing code to call MCP, than at calling MCP directly"**, because models have seen far more real TypeScript than synthetic tool-call examples.
  - The code runs in a fresh **V8 isolate** for each snippet via the **Worker Loader API**, with `globalOutbound: null` so it has no internet access. Bindings keep API keys away from the generated code.
- **Anthropic:** *Code execution with MCP: Building more efficient agents*, Adam Jones and Conor Kelly, **Nov 4 2025** (https://www.anthropic.com/engineering/code-execution-with-mcp).
  - MCP servers are presented as a **file tree**: one folder per server and one file per tool. The agent `ls`/reads only the tools it needs, or uses a `search_tools` call.
  - Data is filtered in the sandbox, so the model sees 5 rows instead of 10,000.
  - Loops and retries run as ordinary code.
  - A PII tokenizer keeps raw PII out of the model's context.
  - Working code can be saved as a **Skill**.
  - **150,000 → 2,000 tokens (98.7% saving)** in the example. A 2-hour transcript would otherwise cost about 50k tokens, twice.
  - Caveat: you now need sandboxing, resource limits and monitoring.
- **Productised:** *Introducing advanced tool use on the Claude Developer Platform*, Bin Wu et al., **Nov 24 2025** (https://www.anthropic.com/engineering/advanced-tool-use).
  - **Tool Search Tool** (`defer_loading: true`). 50+ MCP tools took about 72K tokens up front; with tool search they took about 8.7K (−85%). Opus 4 accuracy went from 49% to 74%, and Opus 4.5 from 79.5% to 88.1%.
  - **Programmatic Tool Calling** (`"allowed_callers": ["code_execution_20250825"]`). Tokens went from 43,588 to 27,297 (−37%), and about 200KB of raw data became about 1KB in context.
  - **Tool Use Examples** (`input_examples`). Accuracy on complex parameters went from 72% to 90%.
- Independent test (AIMultiple, a third party): the success rate was the same, with about 78% fewer input tokens, about 120% more output tokens and slightly higher latency.

**Architecture flow for a diagram.** User → model, whose context holds only the tool index → the model writes a TS/Python script that imports `servers/gdrive/getDocument` and `servers/salesforce/updateRecord` → the sandbox runs it, and the MCP calls go through bindings or a credential proxy → the script filters and joins the data and prints a 5-line summary → only that summary returns to the model.

---

## 10. Tool design for agents

*Writing effective tools for agents — with agents*, Ken Aizawa, **Sep 11 2025** (https://www.anthropic.com/engineering/writing-tools-for-agents).

1. **Fewer, higher-level tools.** "More tools don't always lead to better outcomes." Use `search_logs` rather than `read_logs`, and `schedule_event` rather than separate list and create tools.
2. **Namespacing**, such as `asana_search` and `asana_projects_search`. Prefix and suffix naming measurably change eval results, so test them.
3. **Meaningful context.** Return `name` rather than `uuid`/`mime_type`, and add a `response_format` enum (`"detailed"` or `"concise"`). Example: a detailed response took 206 tokens and a concise one 72.
4. **Token efficiency.** Use pagination, filtering and truncation with sane defaults; Claude Code caps tool output at 25k tokens. Write **actionable error messages** rather than tracebacks.
5. **Prompt-engineer the descriptions** as if writing for a new hire, with unambiguous parameters (`user_id`, not `user`).
6. **Process.** Prototype as a local MCP server, write realistic multi-step evals, let Claude Code analyse the transcripts and rewrite the tools, and check against a held-out set. Refined tool descriptions helped Sonnet 3.5 reach SOTA on SWE-bench Verified.

---

## 11. Cross-cutting failure modes (one table for the deck)

| Failure | Symptom | 2026 fix |
|---|---|---|
| Context rot | quality drops as the window fills | compaction, subagents, files, JIT retrieval |
| Goal drift | constraints lost after summarisation | todo recitation, progress files, JSON feature lists |
| Agentic laziness | "35 of 50 items" | fan-out with one agent per item; feature list with one feature per session |
| Self-preferential bias | an agent passes its own bad work | separate evaluator or adversarial verifier using Playwright |
| Premature victory | "done" with features untested | `passes` fields, E2E tests, sprint contracts |
| Tool bloat | 55–72K tokens before the first message | tool search, code mode, skills |
| Cache busting | high latency and cost | stable prefixes, mask rather than remove tools |
| Crash mid-run | lost hours and duplicated side effects | durable execution (Temporal, Restate, DBOS, Workflow SDK, checkpointers) |
| LLM doing routing | loops, skipped business rules | ADK 2.0 graph and deterministic nodes |
| Sandbox escape and secret leakage | keys exfiltrated | credential proxy, `globalOutbound:null`, secrets kept out of the sandbox |

---

## 12. Likely interview questions and crisp answers

1. **What is an agent harness?** Everything except the weights: the loop, tools, context policy (compaction and retrieval), sandbox and filesystem, subagents, skills, durable session state, permissions, hooks and verification. The same model can score very differently depending on its harness.
2. **What are the four parts of a deep agent?** A detailed system prompt, a planning tool (todos), subagents with isolated context, and a filesystem for notes and workspace. They fix the shallow-agent problem of long tasks overflowing the context.
3. **Why use subagents, if not for "roles"?** **Context isolation** and parallelism. A subagent burns 50k tokens exploring and returns a summary of about 1–2k. A separate verifier also avoids self-preferential bias.
4. **Agent or workflow?** Make the parts deterministic where correctness, money or compliance demand it: routing, retries, approvals. Use LLM nodes for judgment. ADK 2.0 reports about 50% fewer tokens on a refund task (an illustrative figure). Start simple and add autonomy only where evals show a gain.
5. **What is progressive disclosure?** Only skill metadata sits in the prompt. The SKILL.md body loads when relevant, and linked files and scripts load on demand. The cost stays near zero until a skill is used.
6. **Why does code mode beat direct tool calls?** Intermediate data stays in the sandbox, models write real code better than synthetic tool JSON, and loops and filters cost no tokens. Anthropic's example went from 150k to 2k tokens. The cost is that you must run a secure sandbox.
7. **How do you keep a 6-hour agent coherent?** Externalise state: a progress file, a JSON feature list and git commits. Do one feature per session, verify end-to-end, use a separate evaluator, and use compaction or context resets. Run it on durable execution.
8. **What does durable execution buy you?** Each LLM and tool step is journaled, so after a crash or deploy the run replays to the last completed step without re-running side effects. Human waits consume no compute. The catch is that workflow code must be deterministic.
9. **What changed from ADK 1.x to 2.0?** ADK moved from a hierarchical agent executor to a graph Workflow Runtime. Every agent, tool and function is a node with schemas, retries and timeouts. Subagent modes (`chat`/`task`/`single_turn`) were added, the Sequential/Parallel/Loop agents were deprecated, the event schema changed, and 1.x databases risk data loss under 2.0.
10. **Name three tool-design rules.** Consolidate tools around workflows, namespace them, and return concise high-signal fields with actionable errors and pagination. Then iterate with evals and let an agent rewrite the tools.
11. **Why "brain vs hands"?** Separating the harness from the sandbox and from the session log means a dead container is just a tool error, a crashed harness replays from the log, secrets stay out of the sandbox, and containers can be provisioned lazily (p50 TTFT −60%).
12. **Will harnesses disappear as models improve?** No, they shift. Anthropic dropped context resets and sprints as Opus improved but kept the planner and the evaluator. Re-test each component's assumption with every new model.

---

## 13. Slide ideas (with the animation that explains each one)

1. **"From loop to harness."** Start with a small ReAct circle (Thought → Act → Observe) that fills with text until it overflows and turns red. Zoom out: the circle becomes one small box labelled *model loop* inside a large harness diagram, and the other blocks fade in one at a time (Tools, Context policy, Filesystem, Subagents, Skills, Durable session, Evaluator).
2. **"Deep agent anatomy."** Four puzzle pieces (System prompt, Todos, Subagents, Filesystem) slide together around a central agent. Then the todo list animates: checkboxes tick, one item spawns a subagent bubble with its own clean context bar, and the bubble collapses into a "1.5k summary" chip that flies back.
3. **"Context budget meter."** A horizontal token bar at the top. Show the same task twice. ReAct: the bar fills to 100% and the quality line drops ("context rot"). Deep agent: writes to files and returns from subagents push the bar back down, and the quality line stays flat.
4. **"Brain vs hands."** Three boxes: Brain (harness plus Claude), Hands (sandbox) and Session (append-only log tape). Kill the sandbox with an explosion icon; the brain shows a "tool error" and provisions a new one. Kill the brain; a new brain calls `wake(sessionId)` and the tape replays. Show the p50 −60% and p95 −90% counters.
5. **"ADK 2.0 refund graph."** Draw the nodes left to right: deterministic nodes in grey, LLM nodes in a Google blue gradient. A token flows along the edges, and at the router node it splits into True and False paths. A side counter compares the vanilla agent (5,152 tokens, 7.2 s) with the workflow (2,265, 5.7 s), with an "illustrative" footnote.
6. **"Code Mode: 150k → 2k."** Left: the model shuttles 10,000 rows back and forth through its context, and the context bar explodes. Right: the model writes a 6-line script, which drops into a sandbox cube; the rows are filtered inside the cube and only 5 rows emerge. A counter animates 150,000 → 2,000 (−98.7%).
7. **"Progressive disclosure staircase."** Three steps. Step 1: skill names and descriptions (tiny chips, all always visible). Step 2: one chip expands into a SKILL.md page when the user mentions "PDF form". Step 3: the page links to `forms.md` and `fill.py`; the script runs but only its output enters the context. A token cost label grows only on use.
8. **"Long-horizon relay race."** Sessions 1→N are runners passing a baton made of the progress file, the feature-list JSON and the git log. Each runner flips exactly one `passes:false → true` with a Playwright check mark. Contrast this with a single runner who sprints, declares victory and collapses.
9. **"Planner / Generator / Evaluator."** A triangle in which the evaluator sends red rubric scores back to the generator through 3 rounds. A cost ticker reaches $124.70 / 3h50m. Then strike through the scaffolding removed per model generation (context resets → Opus 4.5, sprints → Opus 4.6) while the planner and evaluator stay lit.
10. **"Durable execution replay."** A timeline of steps (LLM, tool, LLM, human approval, tool). A crash cuts the timeline at step 4. On restart, steps 1–3 replay instantly from the journal (ghosted, no side effects), and step 4 resumes. The human approval shows a sleeping clock with "0 compute". Footer logos: Temporal, Restate, DBOS, Workflow SDK, LangGraph, ADK.

---

## Source list (all fetched 2026-10-23 unless marked)
- LangChain, *Deep Agents* (Jul 30 2025): https://www.langchain.com/blog/deep-agents · docs: https://docs.langchain.com/oss/python/deepagents/overview · repo: https://github.com/langchain-ai/deepagents
- Anthropic, *Building effective agents* (Dec 19 2024, with 2026 banner): https://www.anthropic.com/engineering/building-effective-agents
- Anthropic, *Writing effective tools for agents — with agents* (Sep 11 2025): https://www.anthropic.com/engineering/writing-tools-for-agents
- Anthropic, *Effective context engineering for AI agents* (Sep 29 2025): https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- Anthropic, *Building agents with the Claude Agent SDK* (Sep 29 2025): https://claude.com/blog/building-agents-with-the-claude-agent-sdk
- Anthropic, *Equipping agents for the real world with Agent Skills* (Oct 16 2025; open standard Dec 18 2025): https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills
- Anthropic, *Code execution with MCP* (Nov 4 2025): https://www.anthropic.com/engineering/code-execution-with-mcp
- Anthropic, *Introducing advanced tool use* (Nov 24 2025): https://www.anthropic.com/engineering/advanced-tool-use
- Anthropic, *Effective harnesses for long-running agents* (Nov 26 2025): https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
- Anthropic, *Harness design for long-running apps* (Mar 24 2026): https://www.anthropic.com/engineering/harness-design-long-running-apps
- Anthropic, *Scaling Managed Agents* (Apr 8 2026): https://www.anthropic.com/engineering/managed-agents
- Anthropic, *A harness for every task: dynamic workflows in Claude Code* (Jun 2 2026): https://claude.dev/blog/a-harness-for-every-task-dynamic-workflows-in-claude-code/
- Claude Agent SDK docs: https://code.claude.com/docs/en/agent-sdk/overview
- Cloudflare, *Code Mode: the better way to use MCP* (Sep 26 2025): https://blog.cloudflare.com/code-mode/
- Manus, *Context Engineering for AI Agents* (Jul 18 2025): https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus
- Google, *Why we built ADK 2.0* (Jul 1 2026): https://developers.googleblog.com/why-we-built-adk-20/ · https://adk.dev/2.0/ · https://adk.dev/workflows/ · https://adk.dev/graphs/ · https://adk.dev/workflows/collaboration/
- OpenAI Agents SDK docs and Sandbox agents: https://openai.github.io/openai-agents-python/ · https://openai.github.io/openai-agents-python/sandbox_agents/
- OpenAI *Agents API* (Sep 2026, 403 on fetch): https://openai.com/index/introducing-the-agents-api/ · *Harness engineering* (via InfoQ, Feb 21 2026): https://www.infoq.com/news/2026/02/openai-harness-engineering-codex
- Temporal, *Production-ready agents with the OpenAI Agents SDK + Temporal* (Jul 30 2025; GA Mar 23 2026): https://temporal.io/blog/announcing-openai-agents-sdk-integration
- Restate, *Durable AI Loops* (Jun 19 2025): https://www.restate.dev/blog/durable-ai-loops-fault-tolerance-across-frameworks-and-without-handcuffs
- DBOS, *Durable Execution for Building Crashproof AI Agents* (Feb 24 2025): https://www.dbos.dev/blog/durable-execution-crashproof-ai-agents
- Vercel Workflow SDK v5: https://workflow-sdk.dev/ (llms.txt, docs updated Oct 21 2026)
- LangGraph persistence and durable execution: https://docs.langchain.com/oss/python/langgraph/durable-execution
- [Not fetched, title only] AI Engineer Europe 2026 talk, "How to Build Agents That Run for Hours (Without Losing the Plot)", Ash Prabaker and Andrew Wilson (Anthropic): https://ai.engineer/talks/how-to-build-agents-that-run-for-hours-without-losing-the-plot
