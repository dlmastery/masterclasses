# Multi-Agent Systems: State of the Art, October 2026

Research date: 2026-10-23. Scope: mid-2025 to October 2026 only. Every claim below was checked against a primary source fetched on 2026-10-23 unless marked **[UNVERIFIED]**. Code is quoted from official docs unless marked *illustrative*.

---

## 0. The one-slide thesis

The 2023-24 picture of a multi-agent system was an open chat room of role-played personas (AutoGen group chats, CrewAI "crews", ReAct loops passing messages around). By 2026 the field has settled on something narrower and more reliable:

1. **One agent owns the writes and the user-facing thread.** Other agents add *intelligence* (search, review, planning, verification) and return *compressed* results. Cognition: "multi-agent systems work best today when writes stay single-threaded."
2. **Subagents are mostly a context-engineering tool,** not an org chart. You spawn one to keep its exploration out of the main context. It returns 1-2k tokens.
3. **Deterministic graphs hold the structure, and LLMs make the choices inside each node.** Google ADK 2.0 (GA 19 May 2026) rebuilt itself around a graph engine. "A graph is an agent."
4. **The protocols have matured.** MCP (agent to tool) went stateless in 2026-07-28. A2A (agent to agent) hit v1.0 with signed Agent Cards. AP2 (agent to payment) added cryptographic mandates. MCP lives in the Linux Foundation's Agentic AI Foundation, and A2A is a Linux Foundation project.
5. **Cost is the main constraint.** Multi-agent systems use about 15x the tokens of chat, so the pattern pays off only on high-value, parallel tasks.

---

## 1. Anthropic: "How we built our multi-agent research system"

**Source:** Anthropic Engineering, published **13 June 2025**. Authors: Jeremy Hadfield, Barry Zhang, Kenneth Lien, Florian Scholz, Jeremy Fox, Daniel Ford. https://www.anthropic.com/engineering/multi-agent-research-system

### Definition: orchestrator-worker
- **LeadResearcher** (Claude Opus 4) analyzes the query, plans with extended thinking, and **saves the plan to memory**, because context beyond 200k tokens gets truncated. It spawns subagents in parallel, synthesizes their output, and decides whether to keep going.
- **Subagents** (Claude Sonnet 4) each get an objective, an output format, tool guidance and task boundaries. They search independently with *interleaved thinking*, which lets them evaluate tool results between calls, and return findings.
- **CitationAgent** runs last and attributes each claim in the report to a source.

### Architecture flow (diagram script)
User query -> Lead (think, then plan, then write the plan to Memory) -> fan-out to 3-5 subagents running in parallel, each calling 3+ tools in parallel -> each returns a condensed result -> Lead synthesizes. If gaps remain, the Lead spawns another wave. When the Lead is done -> CitationAgent -> final report with citations.

### Numbers
| Metric | Value |
|---|---|
| Multi-agent (Opus 4 lead + Sonnet 4 subagents) vs. single-agent Opus 4, internal research eval | **+90.2%** |
| BrowseComp variance explained by 3 factors (tokens, tool calls, model) | **95%** |
| Variance explained by **token usage alone** | **80%** |
| Tokens: agent vs. chat | **~4x** |
| Tokens: multi-agent vs. chat | **~15x** |
| Research-time reduction on complex queries from parallelism | **up to 90%** |
| Task time cut after a "tool-testing agent" rewrote a bad MCP tool description | **40%** |
| Initial eval set size | **~20 queries** |

**Effort-scaling rules embedded in the prompt:**
- Simple fact-finding: 1 agent, 3-10 tool calls.
- Direct comparison: 2-4 subagents, 10-15 calls each.
- Complex research: more than 10 subagents.

### Why it replaced the older approach
A single ReAct loop is sequential and runs inside one context window. Breadth-first research hits the context ceiling and wall-clock limits. Multi-agent here works mainly as **a way to spend more tokens in parallel across separate context windows**. The post's own reading of the 80%-variance result is that performance comes from token budget, and the architecture is how you buy that budget.

### When it is not a fit (quoted from the post)
- Domains where all agents need the same context, or where agents depend heavily on one another.
- "Most coding tasks", which have fewer parallelizable parts than research.
- Tasks whose value doesn't justify the token cost.
- Real-time coordination. LLM agents don't yet handle real-time coordination and delegation well.

### Failure modes they observed
- Spawning **50 subagents for a simple query**.
- Endless searching for sources that don't exist.
- Subagents distracting each other with too many updates.
- Duplicated work because the division of labor was vague.
- Choosing SEO content farms over authoritative sources.
- Searching the web for information that exists only in Slack, i.e. picking the wrong tool.

### Production engineering
- **Rainbow deployments**, so long-running agents aren't killed by a deploy.
- **Resumable execution from checkpoints** combined with retries.
- **Privacy-preserving tracing** that records decision patterns but not conversation content.
- **End-state evaluation** for agents that change persistent state, which judges the final state rather than the path taken.
- **LLM-as-judge** with a single prompt that outputs a 0.0-1.0 score.
- Known bottleneck: the lead **waits synchronously** for each wave. Asynchronous execution is listed as future work.

### Follow-up: context engineering (29 Sep 2025)
"Effective context engineering for AI agents" (https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) recasts subagents as one of three long-horizon techniques: **compaction**, **structured note-taking**, and **sub-agent architectures**. Subagents "return only a condensed, distilled summary of its work (often 1,000-2,000 tokens)", which "achieves a clear separation of concerns."

### Extreme case: "Building a C compiler with a team of parallel Claudes" (5 Feb 2026, Nicholas Carlini)
https://www.anthropic.com/engineering/building-c-compiler
- **16 parallel Claude instances**, each in its own Docker container, working against a shared bare git repo.
- **No orchestrator agent and no messaging.** Agents claim work by writing lock files to `current_tasks/`, and git conflicts force a second agent onto a different task.
- Result: about **100k lines of Rust** that build Linux 6.9 on x86, ARM and RISC-V. Nearly **2,000 sessions** over two weeks, **just under $20,000**, about **2B input and 140M output tokens**.
- Lessons:
  - "the task verifier is nearly perfect, otherwise Claude will solve the wrong problem."
  - When the work was one monolithic task (compiling the kernel), "Having 16 agents running didn't help because each was stuck solving the same task." The fix was to use GCC as an oracle so the work could be split by file.
- Takeaway: **parallelism needs decomposable work and a strong verifier**. Coordination can be as simple as git plus files.

---

## 2. The Cognition debate and how it was reconciled

### Round 1: "Don't Build Multi-Agents" (Walden Yan, 12 June 2025)
https://cognition.com/blog/dont-build-multi-agents (it moved from cognition.ai)

It was published **one day before** the Anthropic post, and the two are now usually taught together.

Two principles:
1. "Share context, and share full agent traces, not just individual messages."
2. "Actions carry implicit decisions, and conflicting decisions carry bad results."

**Flappy Bird example:** the task "build a Flappy Bird clone" is split into two subtasks, the background with pipes and the bird. Subagent 1 builds a Super-Mario-style background. Subagent 2 builds a bird that doesn't look or move like Flappy Bird's. The combiner can't reconcile them. Passing along the original task wasn't enough, because each subagent made its own unstated assumptions.

Recommendation:
- A **single-threaded linear agent** with continuous context ("the simple architecture will get you very far").
- For very long tasks, a **context-compression model** that distills history into key decisions.
- In 2025, multiple collaborating agents "only results in fragile systems."

### Round 2: "Multi-Agents: What's Actually Working" (Walden Yan, 22 April 2026)
https://cognition.com/blog/multi-agents-working

Cognition now ships multi-agent flows inside Devin, on a narrow principle:

> "multi-agent systems work best today when writes stay single-threaded"
> "the unstructured-swarm approach, arbitrary networks of agents negotiating with each other, is mostly a distraction."
> "The practical shape is map-reduce-and-manage"

Three flows that work:
1. **Code-review loop:** Devin writes the code. **Devin Review** starts with a *clean context* and critiques it, and the two iterate before a human sees the PR. Devin Review catches **about 2 bugs per PR, ~58% of them severe**.
2. **"Smart Friend":** a small, fast primary model (SWE-1.5, 950 tok/s) escalates hard steps to a larger model (tested with Sonnet 4.5 in Windsurf). It works when both models are strong, and not yet when the primary is weak.
3. **Manager Devin:** splits a large task, spawns child Devins, and coordinates them **through an internal MCP**. It is live in production.

Open problems Cognition names:
- When a weaker model should escalate.
- How agents share discoveries.
- How to transfer context without overwhelming the receiver.

### The reconciliation (slide-ready)
| Question | Anthropic (Jun 2025) | Cognition v1 (Jun 2025) | Consensus (2026) |
|---|---|---|---|
| Parallel **reads** (research, search, review)? | Yes, +90% | Risky | **Yes**: fan out readers, compress results |
| Parallel **writes** to one artifact? | "Most coding tasks" not a fit | No | **No**, unless the work is partitioned with a hard verifier (C compiler: tests + git locks) |
| Context passing | Detailed task briefs | Full traces | **Detailed brief in, compressed summary out**, plus a clean context for reviewers |
| Topology | Orchestrator-worker | Single thread | **Map-reduce-and-manage**: one writer, many advisors |

Both posts describe the same constraint: **context fragmentation causes conflicting implicit decisions**. Anthropic avoids it by choosing tasks that are read-heavy and parallel. Cognition avoids it by keeping writes in one thread. The 2026 position is that both are right, and you choose based on the read/write profile of the task.

---

## 3. Subagents for context isolation (the dominant 2026 pattern)

**Definition:** a subagent is a child agent with its **own context window**, its own system prompt and a restricted toolset. The parent calls it like a function. It may use 50k+ tokens exploring, but the parent's context only grows by the returned summary.

**Why it replaced older approaches:** long ReAct transcripts suffer from *context rot*, where quality drops as tool output piles up. Subagents trade some loss of fidelity (the summary) for a parent context that stays clean.

**Concrete: Claude Code subagents** (https://code.claude.com/docs/en/sub-agents)
```markdown
---
name: code-reviewer
description: Reviews code for quality and best practices
tools: Read, Glob, Grep
model: sonnet
---

You are a code reviewer. When invoked, analyze the code and provide
specific, actionable feedback on quality, security, and best practices.
```
- Built-in subagents: **Explore** (read-only search), **Plan**, **general-purpose**.
- Stated benefits: preserve context, enforce tool constraints, route to cheaper models (e.g. Haiku), reuse definitions.

**Claude Code agent teams** (experimental, `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`, https://code.claude.com/docs/en/agent-teams). This is the peer-to-peer counterpart:
- A **team lead**, **teammates** (separate sessions), a **shared task list** (pending, in progress, completed, with dependencies and file-locked claiming), and a **mailbox** for direct messages.
- Docs guidance:
  - "Start with 3-5 teammates."
  - "Three focused teammates often outperform five scattered ones."
  - "Two teammates editing the same file leads to overwrites."
  - Token cost "scale[s] linearly."
  - For "sequential tasks, same-file edits, or work with many dependencies, a single session or subagents are more effective."
- Security point: a message from another agent is **not user consent**. A teammate can't approve a permission prompt on your behalf.

**Google ADK 2.0 equivalent:** parallel `task` or `single_turn` subagents "each run in their own session branch and cannot see their peers' events", and the parent gets the collected results (see §7).

---

## 4. Handoffs vs. agents-as-tools

**OpenAI Agents SDK** (https://openai.github.io/openai-agents-python/multi_agent/):
- **Agents as tools** (`Agent.as_tool()`): a manager **keeps control** of the conversation and calls specialists for "a bounded subtask but should not take over the user-facing conversation."
- **Handoffs** (`handoffs=[...]`): a triage agent passes the **whole conversation** to a specialist, which becomes the active agent. Use when "routing itself is part of the workflow."
- Orchestration can also be done in **code**, which is "more deterministic and predictable, in terms of speed, cost and performance."

```python
# illustrative, OpenAI Agents SDK idioms
from agents import Agent
billing = Agent(name="Billing", instructions="Resolve billing issues.")
research = Agent(name="Researcher", instructions="Find facts; return 5 bullets.")

triage = Agent(name="Triage", instructions="Route the user.", handoffs=[billing])      # handoff
manager = Agent(name="Manager", instructions="Answer; delegate lookups.",
                tools=[research.as_tool(tool_name="research",
                                        tool_description="Look up facts")])           # agent-as-tool
```

**Mapping across frameworks:**
| Concept | OpenAI SDK | Google ADK 2.0 | LangGraph | Claude Code |
|---|---|---|---|---|
| Agent-as-tool (caller keeps control) | `as_tool()` | `mode="single_turn"` / `"task"` subagent, or `AgentTool` | supervisor + `forward_message` | Subagent (Agent tool) |
| Handoff (control transfers) | `handoffs=` | `mode="chat"` + `transfer_to_agent` | swarm handoff | n/a |

**Rule of thumb:** use agents-as-tools when the user should see one voice and you want a single place to audit. Use handoffs when each specialist needs a long, multi-turn conversation with the user (support triage, for example).

---

## 5. Swarm vs. hierarchical (supervisor)

**LangChain, "Benchmarking Multi-Agent Architectures"**, Will Fu-Hinthorn, **10 June 2025** (https://www.langchain.com/blog/benchmarking-multi-agent-architectures)

Setup:
- gpt-4o on a modified τ-bench retail split (first 100 examples).
- Up to **six distractor domains**, each with **19 tools** and a wiki, none of them needed for the tasks.

Findings:
- The **single agent** collapses once there are 2 or more distractor domains, and its tokens grow with each one.
- **Swarm** (any agent can hand off to any other, and the active agent replies to the user directly) **slightly outperforms supervisor** throughout and uses fewer tokens.
- **Supervisor** loses accuracy to *translation*, i.e. paraphrasing sub-agent answers.
- Three fixes produced "**a nearly 50% increase in performance**":
  1. Remove handoff messages from the sub-agent's context.
  2. Add a `forward_message` tool so the supervisor can pass a sub-agent's answer through verbatim.
  3. Tune the handoff tool naming (`delegate_to_` vs. `transfer_to_`).

**Interpretation for 2026:**
- **Hierarchical/supervisor** gives you one place for control, audit and policy, and is easy to reason about. Each extra layer adds a paraphrase step, so let workers pass answers through.
- **Swarm/peer** has fewer hops and lower latency, but no central control. Cognition calls *unstructured* swarms "mostly a distraction." Swarm topologies that work in production are constrained: explicit handoff edges plus shared state.
- **Shared-task-list peers** (Claude Code agent teams, the C-compiler git locks) are a third option. Coordination happens through a shared artifact rather than chat.

---

## 6. Protocols: MCP, A2A, AP2

### 6.1 MCP: agent to tools/context
The spec is versioned by date. Changelogs: https://modelcontextprotocol.io/specification/2025-06-18/changelog, `/2025-11-25/changelog`, `/2026-07-28/changelog`.

**2025-06-18**
- **Structured tool output** (`structuredContent` + `outputSchema`).
- **Elicitation**: a server can ask the user for input mid-call.
- **Resource links** in tool results.
- MCP servers classified as **OAuth Resource Servers** (protected-resource metadata), with **RFC 8707 Resource Indicators** required to stop token passthrough.
- **JSON-RPC batching removed**.
- `MCP-Protocol-Version` header required on HTTP.

**2025-11-25** (first anniversary release)
- **Tasks**, experimental, SEP-1686: durable requests with polling and deferred result retrieval.
- **URL-mode elicitation**, SEP-1036, for out-of-band flows such as OAuth or payments.
- **Sampling with tools** (`tools`, `toolChoice`), SEP-1577.
- **Client ID Metadata Documents**, SEP-991, as the recommended client registration.
- OpenID Connect discovery, incremental scope consent via `WWW-Authenticate`, and icons.
- Input-validation errors are returned as tool errors so the model can self-correct.
- JSON Schema 2020-12 is the default dialect.
- Governance formalized: SDK tiers and working groups.

**2026-07-28** (latest revision as of this writing)
- **Stateless MCP:**
  - `initialize` handshake and `Mcp-Session-Id` removed.
  - Every request carries `protocolVersion` and `clientCapabilities` in `_meta`.
  - New required `server/discover` RPC.
- **Multi Round-Trip Requests (MRTR):** replace server-initiated requests (`elicitation/create`, `sampling/createMessage`, `roots/list`). The server returns `resultType: "input_required"` with `inputRequests`, and the client retries the original request with `inputResponses`.
- **Tasks moved out of core** into the official extension `io.modelcontextprotocol/tasks`:
  - Polling via `tasks/get`, plus `tasks/update` for client input.
  - `tasks/list` removed.
  - Servers can return task handles unsolicited.
- **`subscriptions/listen`** replaces the GET stream and `resources/subscribe`.
- **SSE resumability removed**. A broken stream means re-issuing the request.
- **`ttlMs` / `cacheScope`** on list results, and deterministic tool order to improve **prompt-cache hit rates**.
- OpenTelemetry `traceparent` in `_meta`.
- **Deprecated:** Roots, Sampling, Logging, and Dynamic Client Registration (in favor of CIMD). The deprecation window is a minimum of 12 months.

**Governance:** Anthropic donated MCP to the **Agentic AI Foundation (AAIF)** under the Linux Foundation, announced **9 Dec 2025**. The founding projects were MCP, Block's goose and OpenAI's AGENTS.md. Platinum members include AWS, Anthropic, Block, Bloomberg, Cloudflare, Google, Microsoft and OpenAI.

**Why this matters for multi-agent:** Cognition's Manager Devin coordinates child Devins **through an internal MCP**. With Tasks and MRTR, MCP can now carry long-running, resumable, human-in-the-loop work, which overlaps with what A2A was built for.

### 6.2 A2A (Agent2Agent): agent to agent
- **Timeline** (GitHub releases, https://github.com/a2aproject/A2A/releases):
  - v0.2.x through mid-2025.
  - **v0.3.0, 30 Jul 2025**: well-known URI changed to `/.well-known/agent-card.json`.
  - **v1.0.0, 12 Mar 2026**: first stable release, with many breaking changes.
  - **v1.0.1, 28 May 2026**: bug fixes. This is the latest release.
- **Linux Foundation press release, 9 Apr 2026** (one-year mark):
  - **150+ organizations**, up from 50+.
  - **22k+ GitHub stars**.
  - **5 production SDKs**: Python, JS, Java, Go, .NET.
  - Integrated into **Azure AI Foundry, Copilot Studio** and **Amazon Bedrock AgentCore Runtime**.
  - v1.0 adds multi-protocol support, multi-tenancy and **Signed Agent Cards**.
- **v1.0 changes** (https://a2a-protocol.org/latest/whats-new-v1/):
  - Agent Cards can be **signed with JWS (RFC 7515)** over an RFC 8785 canonical form.
  - `url` / `preferredTransport` / `additionalInterfaces` are merged into **`supportedInterfaces[]`**.
  - Three normative bindings: **JSON-RPC, gRPC, HTTP+JSON** (e.g. `POST /message:send`).
  - Task states are now `TASK_STATE_COMPLETED`-style enums.
  - Methods renamed (`message/send` becomes `SendMessage`).
  - Text, File and Data parts unified into one `Part` with a oneof.
  - Cursor pagination.
  - OAuth implicit and password flows removed, and Device Code + PKCE added.
- **[UNVERIFIED]**
  - A secondary blog says A2A became a hosted project of the AAIF on 17 Aug 2026.
  - One trade article claims an "A2A 1.2" promoted at Cloud Next 2026. It conflicts with the GitHub releases, so don't present it.

**Agent Card** (*illustrative, v1.0 shape*)
```json
{
  "name": "flight_booker",
  "description": "Searches and books flights",
  "version": "1.0.0",
  "supportedInterfaces": [
    {"protocolBinding": "JSONRPC", "url": "https://agents.example.com/a2a", "protocolVersion": "1.0"}
  ],
  "skills": [{"id": "book", "name": "Book flight", "tags": ["travel"]}],
  "defaultInputModes": ["text/plain"], "defaultOutputModes": ["application/json"],
  "signatures": [{"protected": "...", "signature": "..."}]
}
```

**MCP vs. A2A in one line:** MCP exposes *tools and context* (transparent, schema-typed functions). A2A exposes *opaque peers* (another team's agent with its own model, memory and policy) through tasks, messages and artifacts.

### 6.3 AP2 (Agent Payments Protocol)
Google Cloud blog, **16 Sep 2025** (https://cloud.google.com/blog/products/ai-machine-learning/announcing-agents-to-payments-ap2-protocol), spec at goo.gle/ap2.
- Problem: payment systems assume a human clicks "buy." AP2 answers three questions: **authorization, authenticity, accountability**.
- **Mandates**, tamper-proof and signed with **Verifiable Credentials**:
  - **Intent Mandate**: the user's instruction. It is signed upfront for delegated purchases, with limits such as price and timing.
  - **Cart Mandate**: an "unchangeable record of the exact items and price."
  - Intent -> Cart -> Payment forms a "**non-repudiable audit trail**."
- Payment-agnostic: cards, real-time bank transfers and stablecoins, the latter through the **A2A x402 extension** built with Coinbase, the Ethereum Foundation and MetaMask.
- Partners: 60+ at launch (Mastercard, AmEx, PayPal, Adyen, Coinbase, Worldpay, Salesforce and others). The April 2026 LF release still says **60+**.
- AP2 extends A2A and MCP. The LF release notes that **UCP** is compatible with AP2 via a mandates extension.

---

## 7. Google ADK 2.0 multi-agent primitives

**Release facts** (PyPI, https://pypi.org/project/google-adk/):
- 2.0.0a1 on 18 Mar 2026, 2.0.0b1 on 21 Apr 2026, **2.0.0 GA on 19 May 2026**.
- Latest is **2.13.0 (23 Oct 2026)**. Releases ship roughly every two weeks. Python 3.11+.
- ADK Go 2.0 announced **30 Jun 2026** (https://developers.googleblog.com/en/announcing-adk-go-20/).
- Migration guide: https://adk.dev/2.0/

**The architectural change:**
- ADK moved "from a hierarchical executor to a graph engine." `BaseAgent` now subclasses **`BaseNode`**. Agents, tools and plain functions are all nodes, and "**A graph is an agent**."
- Events gain `node_info` and `output`.
- Overriding `_run_async_impl` is discouraged in favor of before/after callbacks.
- Don't catch `BaseException`. Doing so traps `NodeInterruptedError` and breaks HITL pauses.

**Three collaboration styles** (from the docs):
1. **Graph workflows**: deterministic routing.
2. **Dynamic workflows**: loops and branching written in code.
3. **Collaborative workflows**: a coordinator plus subagents.

**Coordinator + subagent modes** (https://adk.dev/workflows/collaboration/, verbatim):
```python
from google.adk import Agent

weather_agent = Agent(
    name="weather_checker",
    mode="single_turn",         # no user interaction
    tools=[get_weather, user_info, geocode_address],
)
flight_agent = Agent(
    name="flight_booker",
    mode="task",                # can ask user questions
    input_schema=FlightInput,
    output_schema=FlightResult,
    tools=[search_flights, book_flight],
)
root = Agent(
    name="travel_planner",      # coordinator agent
    sub_agents=[weather_agent, flight_agent],
    # Auto-injects delegation tools named after each subagent
)
```

What the three modes do:
- **`chat`** (default): full user interaction. Control returns to the parent only through `transfer_to_agent`. This is the *handoff* semantic.
- **`task`**: may ask the user clarifying questions, returns automatically when it calls **`finish_task`**, must be a leaf, and supports typed I/O. This is *agent-as-tool with HITL*.
- **`single_turn`**: no user interaction, returns its result automatically, and is the **only mode that can run in parallel**. This is the pure *context-isolated worker*.
- Caveat: in Python 2.0.0, task mode is disabled inside graph workflows, with a future release planned to restore it. Go also forbids task-mode agents as static graph nodes.

**Graph workflow: sequential and fan-out/fan-in** (https://adk.dev/graphs/, /graphs/routes/, verbatim):
```python
from google.adk import Agent, Workflow
root_agent = Workflow(
    name="root_agent",
    edges=[("START", generate_fruit_agent, generate_benefit_agent)],
)

from google.adk.workflow import JoinNode
my_join_node = JoinNode(name="my_join_node")
edges=[
    ("START", parallel_task_A, my_join_node),
    ("START", parallel_task_B, my_join_node),
    ("START", parallel_task_C, my_join_node),
    (my_join_node, final_task_D),
]
```

**Routing:**
- A function returns `Event(route="RUN_TASK_C")`.
- The edge `(router, {"RUN_TASK_B": task_B_node, "RUN_TASK_C": task_C_node})` maps route values to nodes.
- Loops are back-edges. They are not bounded automatically, so you must design the exit condition.

**ADK Go 2.0 extras** (blog):
- Node types: function, emitting function, agent, tool, dynamic, sub-workflow, parallel worker and state-bound.
- `AddFanOut` / `AddFanIn`.
- Per-node retry: 5 attempts, 1s initial delay, 60s cap, 2x backoff, full jitter.
- Per-node timeouts and `WithMaxConcurrency(n)`.
- **Durable HITL** via `NewRequestInputEvent`, which can resume by handing the answer to the next node or by re-running the paused node.
- `ToolContext` and `CallbackContext` unified into `agent.Context`.

**A2A in ADK** (experimental, https://adk.dev/a2a/quickstart-exposing/):
```python
from google.adk.a2a.utils.agent_to_a2a import to_a2a
a2a_app = to_a2a(root_agent, port=8001)   # auto-generates the Agent Card
```
- Remote agents are consumed via `RemoteA2aAgent`.
- Works with `a2a-sdk` 0.3.x (compatibility mode) and **1.x (recommended)**.

**How ADK 2.0 implements the 2026 consensus:**
- The graph holds deterministic structure.
- `single_turn` subagents are parallel, context-isolated readers.
- One `chat` coordinator owns the user thread.
- `task` agents handle bounded HITL subtasks with typed outputs.
- A2A connects agents across organizations.

---

## 8. Cross-cutting failure modes (2026 catalogue)

| Failure | Source | Mitigation |
|---|---|---|
| Conflicting implicit decisions | Cognition (Flappy Bird) | Single writer, or strict partition plus verifier |
| Over-spawning (50 subagents for trivial queries) | Anthropic | Effort-scaling rules in the lead prompt |
| Duplicated work | Anthropic | Explicit objectives and boundaries per subagent |
| Supervisor "translation" loss | LangChain | `forward_message` passthrough; strip routing chatter |
| Everyone stuck on one monolithic task | C compiler | Use an oracle/test to split the work |
| False "done" | C compiler | Near-perfect verifier, CI gates |
| Same-file overwrites | Claude Code agent teams | One owner per file set |
| Token blow-up (15x) | Anthropic | Use only for high-value tasks; cheaper models for workers |
| Agent-message spoofing of consent | Claude Code docs | Treat inter-agent messages as untrusted data |
| Unbounded loops in graphs | ADK docs | Explicit exit conditions, max iterations |
| Swallowing interrupts breaks HITL | ADK 2.0 migration | Don't catch `BaseException`; let `RetryConfig` work |
| Weak-model escalation timing | Cognition 2026 | Open problem; strong primary models |

---

## 9. Likely interview questions with crisp answers

1. **Why did Anthropic's multi-agent system beat single-agent Opus by 90%?**
   It spends more tokens in parallel across separate context windows. Token usage alone explains 80% of BrowseComp variance. The architecture is how they buy the budget without running into context limits.

2. **What does it cost?**
   About 15x the tokens of chat, against about 4x for a single agent. Use it only when the task's value justifies that.

3. **Cognition said don't build multi-agents. Who was right?**
   Both. Fan out parallel readers and keep writes single-threaded. Cognition itself now ships review loops, Smart Friend and Manager Devin under exactly that rule.

4. **Subagent vs. handoff?**
   - Subagent / agent-as-tool: the caller keeps control and gets back a compressed result.
   - Handoff: the conversation transfers to the specialist.
   - In ADK 2.0 terms, `single_turn`/`task` vs. `chat` + `transfer_to_agent`.

5. **Why use subagents if not for parallelism?**
   Context isolation. Exploration noise stays in the child, and the parent receives 1-2k tokens. It also gives you a clean context for unbiased review (Devin Review).

6. **Swarm or supervisor?**
   LangChain found swarm slightly better and cheaper. A supervisor improved by nearly 50% after removing handoff noise and passing answers through verbatim. Choose a supervisor when you need control and audit, and swarm-style handoffs when latency matters. Avoid unstructured swarms.

7. **MCP vs. A2A?**
   MCP connects an agent to transparent tools and context. A2A connects it to an opaque peer agent through tasks and artifacts, discovered via an Agent Card at `/.well-known/agent-card.json`. With Tasks and MRTR, MCP increasingly covers long-running work too.

8. **What changed in MCP 2026-07-28?**
   - Stateless: no initialize, no session ID, version in `_meta`, `server/discover`.
   - MRTR (`input_required`) replaces server-initiated requests.
   - Tasks moved to an extension.
   - Sampling, Roots and Logging deprecated.

9. **What is new in A2A v1.0?**
   - Signed Agent Cards (JWS).
   - `supportedInterfaces[]`.
   - JSON-RPC, gRPC and HTTP+JSON bindings.
   - Unified `Part`.
   - Enum task states.
   - OAuth implicit and password flows removed.

10. **How does AP2 make an agent purchase trustworthy?**
    Signed Verifiable-Credential mandates. An Intent Mandate records what the user authorized, a Cart Mandate records exactly what was bought, and together they make a non-repudiable audit trail.

11. **What is the core change in ADK 2.0?**
    It moved from a hierarchical executor to a graph engine. Agents are nodes (`BaseAgent` subclasses `BaseNode`), workflows are agents, and you get JoinNode fan-in, routing via `Event(route=...)`, durable HITL and per-node retry.

12. **How did 16 Claudes coordinate on the C compiler?**
    No orchestrator. They used a shared git repo, lock files in `current_tasks/` and test suites as the verifier.

13. **How do you evaluate a multi-agent system?**
    - Start with about 20 real queries.
    - LLM-as-judge with a rubric (accuracy, citations, completeness, source quality, tool efficiency).
    - Judge the end state rather than the path.
    - Human review for bias, plus tracing.

---

## 10. Slide ideas (with the animation that explains each)

1. **"From chat room to org chart to graph."** A timeline: 2023 AutoGen group chat (many bubbles talking over each other), then 2025 orchestrator-worker, then 2026 ADK graph. *Animation:* the chaotic bubbles snap into a tree, and the tree's edges straighten into a directed graph with START and Join nodes.

2. **"The 15x slide."** Three bars: chat 1x, agent 4x, multi-agent 15x, next to the +90.2% score. *Animation:* the bars grow in sequence, then a pie fills to show 80% of variance explained by tokens. Punchline text: "you're buying parallel tokens."

3. **Anthropic research system flow.** *Animation:* the lead "thinks" (pulsing), writes the plan to a Memory cylinder, fans out three subagent lanes that each fire parallel tool calls, the lanes shrink into small summary cards flowing back, and the CitationAgent stamps sources on the final report.

4. **Flappy Bird failure.** *Animation:* the task splits into two cards. One renders a Mario background, the other a mismatched bird. They slide together and clash, shown with a red jagged seam. Caption: "actions carry implicit decisions."

5. **The reconciliation: map-reduce-and-manage.** *Animation:* many "reader" agents fan out in blue and return arrows to a single "writer" agent in gold. A writer that tries to fork into two turns red and is blocked. Quote: "writes stay single-threaded."

6. **Subagent context isolation.** Parent context shown as a glass container filling with liquid. *Animation:* without subagents, tool output floods the container (context rot). With subagents, a child container fills to 50k, then a filter drops only a 1-2k "summary droplet" into the parent.

7. **Handoff vs. agent-as-tool.** Split screen. *Animation:* on the left, a user-facing microphone icon **moves** from Triage to Billing (handoff). On the right, the microphone stays with the Manager while a Researcher pops up, returns a card and disappears (as-tool). An overlay maps them to ADK `chat` vs. `single_turn`/`task`.

8. **Swarm vs. supervisor (LangChain).** *Animation:* in the supervisor view, messages pass through a central node that "rewrites" them (text shimmering = translation loss). Then a `forward_message` bypass arrow appears and the score bar jumps by about 50%. Swarm shows direct peer arrows.

9. **The protocol stack.** Three horizontal layers: MCP (agent to tools), A2A (agent to agent), AP2 (agent to payments), with the AAIF/LF logos at the base. *Animation:* an agent pulls in tools via MCP, discovers a remote agent by fetching a signed Agent Card (a lock icon verifies the JWS), delegates a task over A2A, and then an Intent Mandate and a Cart Mandate stack into a receipt chain.

10. **MCP goes stateless (2026-07-28).** *Animation:* a session handshake (two hands, a session ID tag) dissolves, and each request card now carries its own `_meta` badge. An `input_required` result bounces back, the client re-sends with `inputResponses`, and the result reads complete (MRTR loop).

11. **ADK 2.0 in one graph** (bonus). *Animation:* START leads to a coordinator `chat` node, which fans out to three `single_turn` workers (each in its own session branch, shown as separate glass tubes). They converge on a JoinNode, a HITL node pauses with an "Approve $200 refund?" prompt, then the graph resumes to the end. The retry badge flashes on a failed node.

---

## 11. Source list (all fetched 2026-10-23)

- Anthropic, "How we built our multi-agent research system," 13 Jun 2025: https://www.anthropic.com/engineering/multi-agent-research-system
- Anthropic, "Effective context engineering for AI agents," 29 Sep 2025: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- Anthropic, "Building a C compiler with a team of parallel Claudes," 5 Feb 2026: https://www.anthropic.com/engineering/building-c-compiler
- Cognition (Walden Yan), "Don't Build Multi-Agents," 12 Jun 2025: https://cognition.com/blog/dont-build-multi-agents
- Cognition (Walden Yan), "Multi-Agents: What's Actually Working," 22 Apr 2026: https://cognition.com/blog/multi-agents-working
- LangChain, "Benchmarking Multi-Agent Architectures," 10 Jun 2025: https://www.langchain.com/blog/benchmarking-multi-agent-architectures
- OpenAI Agents SDK, Multi-agent orchestration: https://openai.github.io/openai-agents-python/multi_agent/
- Claude Code docs, Subagents: https://code.claude.com/docs/en/sub-agents ; Agent teams: https://code.claude.com/docs/en/agent-teams
- MCP changelogs: https://modelcontextprotocol.io/specification/2025-06-18/changelog ; /2025-11-25/changelog ; /2026-07-28/changelog
- Linux Foundation, AAIF formation, 9 Dec 2025: https://www.linuxfoundation.org/press/linux-foundation-announces-the-formation-of-the-agentic-ai-foundation
- Linux Foundation, "A2A Protocol Surpasses 150 Organizations…," 9 Apr 2026: https://www.linuxfoundation.org/press/a2a-protocol-surpasses-150-organizations-lands-in-major-cloud-platforms-and-sees-enterprise-production-use-in-first-year
- A2A releases: https://github.com/a2aproject/A2A/releases ; What's new in v1: https://a2a-protocol.org/latest/whats-new-v1/
- Google Cloud, "Announcing Agent Payments Protocol (AP2)," 16 Sep 2025: https://cloud.google.com/blog/products/ai-machine-learning/announcing-agents-to-payments-ap2-protocol
- Google ADK: PyPI https://pypi.org/project/google-adk/ ; 2.0 guide https://adk.dev/2.0/ ; collaboration https://adk.dev/workflows/collaboration/ ; graphs https://adk.dev/graphs/ , https://adk.dev/graphs/routes/ ; A2A https://adk.dev/a2a/quickstart-exposing/
- Google Developers Blog, "Announcing ADK for Go 2.0," 30 Jun 2026: https://developers.googleblog.com/en/announcing-adk-go-20/

Research gaps:
- The web-search budget ran out mid-session, so conference-talk sources (AI Engineer World's Fair 2026, I/O 2026, Cloud Next 2026) were not collected.
- The AAIF hosting of A2A (Aug 2026) remains **[UNVERIFIED]**.
