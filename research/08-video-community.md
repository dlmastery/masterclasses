# 08 — Video, Community & Reference Samples for Google ADK (2025–2026)

Research date: 2026-10-23. Sources are primary where possible: YouTube metadata via oEmbed and watch-page `uploadDate`, the GitHub REST API, PyPI JSON, pypistats, and official Google blogs and codelabs. Items marked **[UNVERIFIED]** could not be confirmed against a primary source. The web-search budget ran out partway through, so a few Next '26 and I/O '26 session recordings could not be located.

---

## 1. Timeline at a glance (verified via PyPI `google-adk` upload dates)

| Date | Event | Source |
|---|---|---|
| 2025-04-09 | ADK announced at Google Cloud Next '25; `google-adk` 0.1.0 on PyPI | PyPI; developers.googleblog.com launch post |
| 2025-04-10 | "Introducing Agent Development Kit" video (Google for Developers) | YouTube |
| 2025-05-20 | `google-adk` **1.0.0** (Google I/O 2025 week) | PyPI |
| 2025-07-08 | The Agent Factory podcast, Episode 1 | YouTube |
| 2025-11-10 to 14 | Kaggle 5-Day AI Agents Intensive (codelabs built on ADK) | Kaggle Learn guide |
| 2026-03-18 | `google-adk` 2.0.0a1 (first 2.0 alpha) | PyPI |
| 2026-04-21 | 2.0.0b1 | PyPI |
| 2026-04-22 | Google Cloud Next '26 (Las Vegas): ADK billed as a "graph-based framework" | Cloud blog wrap-up |
| 2026-05-19 | **ADK 2.0.0 GA (Python)** at Google I/O 2026 | PyPI; Virtualization Review |
| 2026-05-29 | ADK Community Call (May 2026): "Python 2.0 GA, Kotlin & Android" | YouTube |
| 2026-06-15 to 19 | Kaggle 5-Day AI Agents: Intensive **Vibe Coding** course | Kaggle |
| 2026-07-07 | 2.4.0 | PyPI |
| 2026-09-09 to 10-02 | `google/adk-samples` drops its legacy samples; `python/` folder removed | GitHub commits |
| 2026-10-23 | **2.13.0** (latest at time of writing) | PyPI |

Release cadence: 2.0.0 through 2.13.0 shipped in about 5 months, roughly one release every two weeks. That matches the README's line that releases come "roughly bi-weekly" (github.com/google/adk-python).

---

## 2. Adoption stats (snapshot 2026-10-23)

**GitHub stars** (GitHub REST API `stargazers_count`):

| Repo | Stars | Forks |
|---|---|---|
| google/adk-python | **21,982** | 4,224 |
| google/adk-recipes (formerly google/adk-samples) | **10,523** | 2,939 |
| google/adk-go | 8,890 | – |
| GoogleCloudPlatform/agent-starter-pack | 6,569 | – |
| google/adk-java | 1,755 | – |
| google/adk-docs | 1,525 | – |
| google/adk-js (TypeScript) | 1,448 | – |
| google/adk-kotlin | 294 | – |

**PyPI downloads** for `google-adk` (pypistats.org API, `recent`):
- last day: **403,771**
- last week: **2,316,962**
- last month: **10,109,331** (about 10.1M per month)

**Kaggle 5-Day AI Agents Intensive** ("Inside Kaggle's AI Agents intensive course with Google", blog.google, 2025-12-18):
- 1.5M+ learners, 11,000+ capstone submissions, 160,000+ on Kaggle Discord
- 2M whitepaper views, 3.3M notebook views

**Enterprise context from Next '26** (Cloud blog wrap-up, these are not ADK-specific): 1,302 public AI customer stories; GE Appliances is "deploying more than 800 AI agents with Gemini Enterprise"; Tata Steel has "a fleet of more than 300 specialized AI agents in just nine months"; and an Agent Marketplace launched "with more than 70 pre-built agents."

---

## 3. Videos and talks (verified title, channel, URL, date)

### Official Google channels

1. **"Introducing Agent Development Kit"**, Google for Developers, 2025-04-10. https://www.youtube.com/watch?v=zgrOwow_uTQ
   - Presenters: PM Anand Iyer, Tech Lead Bo Yang, DevRel Ivan Nardini. Demo: a multi-agent, multi-modal travel planner.
   - Takeaway (description): ADK is "model-agnostic, deployment-agnostic, interoperable" and "makes agent development feel like software development". It comes with native multimodal streaming and a built-in debugging UI.
2. **"Getting started with Agent Development Kit"**, Google for Developers, 2025-04-16. https://www.youtube.com/watch?v=44C8u0CDtSo
3. **"Agents, their frameworks and when to use them | The Agent Factory Podcast"**, Google Cloud Tech, 2025-07-08. https://www.youtube.com/watch?v=aLYrV61rJG4
   - Episode 1. Hosts: Shir Meir Lador and Ivan Nardini. Covers what an agent actually is, why you need a framework, and the trade-offs between LangChain, LangGraph, crewAI and ADK.
4. **"Agent evaluation with ADK & Vertex AI | The Agent Factory Podcast"**, Google Cloud Tech, 2025-10-03. https://www.youtube.com/watch?v=vTjlLiFgFno
   - Recap blog: "Agent Factory Recap: A Deep Dive into Agent Evaluation, Practical Tooling, and Multi-Agent Systems" (Annie Wang, Mollie Pettit, 2025-10-20). https://cloud.google.com/blog/topics/developers-practitioners/agent-factory-recap-a-deep-dive-into-agent-evaluation-practical-tooling-and-multi-agent-systems
   - **Five-step inner loop:** (1) define the golden path by correcting a response in the Eval tab, (2) run the case and watch it fail, (3) find the root cause in the Trace view (the agent chose `lookup_product_information` instead of `get_product_details`), (4) fix the ambiguous instruction, (5) validate after hot reload. The ADK Web UI handles the inner loop; Vertex AI Gen AI Evaluation (LLM-as-judge) handles the outer loop.
5. **"Agent Factory Recap: Securing AI Agents in Production"** (blog for the security episode; Aron Eidelman, Mollie Pettit, 2025-10-23). https://cloud.google.com/blog/topics/developers-practitioners/agent-factory-recap-securing-ai-agents-in-production
   - Quote: "Within the Agent Development Kit (ADK), we can use callbacks to validate actions before they execute."
   - Quote: "the ADK plugin is specific to callbacks, while Model Armor provides a consistent, API-driven policy that can be applied across all agents."
   - The post also says ADK ships a built-in **PII redaction plugin**.
6. Other Agent Factory recaps (Cloud blog, developers-practitioners): "AI Agents for Data Engineering and Data Science"; "Supercharging Agents on GKE with Agent Sandbox and Pod Snapshots"; "Antigravity and Nano Banana Pro with Remik"; "Build an AI Workforce with Gemini 3". Dates are **[UNVERIFIED]**. Playlist: https://music.youtube.com/podcast/aLYrV61rJG4
7. **"Build long-running agents with Google's Agentic Stack | The Agent Factory"**, Google Cloud Tech, 2026-06-01. https://www.youtube.com/watch?v=VGpfnbr7rso
   - Links out to Agent Studio and ADK 2.0. Topic: long-running, resumable agents.
8. **"ADK Community Call (May 2026) - Python 2.0 GA, Kotlin & Android, Agents CLI, Skills"**, Google Cloud Events, 2026-05-29. https://www.youtube.com/watch?v=vbqKmK0rArI
   - From the description: ADK 2.0 GA "with graph-based workflows and collaborative agents"; first release of **ADK for Kotlin and Android** "with on-device Gemini Nano and MLKit support"; a demo of the new **Agents CLI** "for managing the full agent lifecycle with coding agents"; **Skills** "for progressive disclosure and reducing prompt bloat", including a **Skill Registry** for remote skill loading.
   - Community spotlight: *Beever Atlas*, which turns team chats into a self-organizing wiki. The Q&A covered migrating from 1.x.
9. **"Intro to multi-agent systems with ADK"**, Google Cloud Tech, 2026-06-08. Speaker: Greg Baugues. https://www.youtube.com/watch?v=0Z0GUDakR_A
   - Builds a first agent with custom tools (date, Google Search), uses the web UI for debugging, then a multi-agent system to "reduce hallucinations".
10. **"Graph Engineering with ADK"**, Google Cloud Tech, 2026-09-10. https://www.youtube.com/watch?v=Mzr7byMFy_4
    - Uses a marathon-race demo to show "why large monolithic prompts hallucinate and how graph architecture fixes them". Patterns: **fan-out** for parallel execution, **join nodes** for deterministic aggregation, **deterministic vs. LLM routers**. Runs "an entire multi-branch workflow on just a single LLM call". Paired with the ADK2 codelab (below).
11. **"Google ADK 2.0 workflows tutorial: Building reliable multi-agent systems"**, Google Cloud Tech, 2026-09-17. Miguel Gutierrez (Solutions Engineer) with Martin Omander. https://www.youtube.com/watch?v=fOIGMZusCs8
    - Quotable: "Stop prompting and start routing!"

### Kaggle

12. **"DAY 1 Livestream - 5-Day AI Agents: Intensive Vibe Coding Course With Google"**, Kaggle, 2026-06-19 upload. https://www.youtube.com/watch?v=7iic3Zj427M
    - Learn guide: https://www.kaggle.com/learn-guide/5-day-agents-vibecoding
13. The original **5-Day AI Agents Intensive** (Nov 10–14, 2025) is now self-paced at https://www.kaggle.com/learn-guide/5-day-agents. Its Day 1 notebook "Day 1a - From Prompt to Action" covers a first ADK agent and the ADK Web UI: https://www.kaggle.com/code/kaggle5daysofai/day-1a-from-prompt-to-action. The direct 2025 livestream URLs are **[UNVERIFIED]**.

### Conference pages

14. **Google I/O 2025, "Building AI agents on Google Cloud"** (technical session 32). https://io.google/2025/explore/technical-session-32/ — covers ADK, A2A, Cloud Run and Vertex AI runtimes. The recording URL is **[UNVERIFIED]**.
15. **Google Cloud Next '26 wrap-up** ("260 things we announced"). https://cloud.google.com/blog/topics/google-cloud-next/google-cloud-next-2026-wrap-up
    - Item 2: ADK "Unlocks more powerful reasoning by organizing agents into a network of sub-agents. This new, graph-based framework allows you to define clear, reliable logic for how agents work together".
    - Item 3: Agent Studio can "export your logic directly into ADK".
    - Item 94: BigQuery Agent Analytics plugin logs ADK and LangGraph interactions to BigQuery.
    - Item 219: Secret Manager integration with ADK is GA.
    - Next '26 showcase codelab: "Build Rich Agent Experiences with ADK + A2UI".
16. **I/O 2026** (Virtualization Review, 2026-05-19, secondary source): https://virtualizationreview.com/articles/2026/05/19/google-io-26-fills-out-enterprise-agent-stack-with-managed-agents-adk-2.0.aspx
    - Google describes a **four-rung** model: Agent Studio (no-code) → Managed Agents API (new) → Antigravity → **ADK 2.0 (code-first)**. A2A lets an agent on any rung act as a sub-agent on another.
    - Three collaboration modes: **chat**, **task** (sub-agent can ask the user for input, then returns control), **single_turn** (parallel, no user interaction). Kotlin is in beta as "ADK for Android".
    - Official I/O 2026 session recordings: **[UNVERIFIED]**, could not be located before the search budget ran out.

### Community (third-party, label as such on slides)
- "ADK 2.0 is Here and It's a Total Game-Changer", AI with Surya, 2026-04-22. https://www.youtube.com/watch?v=xyhzznb0vtg (pre-GA, based on the beta)
- "What is Google ADK 2.0 Workflow Runtime?", Standarity, 2026-06-12. https://www.youtube.com/watch?v=lLsXATh6dwQ
- "Hands-On Graph Based Workflows with ADK 2.0: From Agentic AI to Agentic Engineering", 10XROADMAP, 2026-06-22. https://www.youtube.com/watch?v=oPd64jUdUWI
- "Google ADK Tutorial: Build Multi-Agent AI Systems from Scratch", KodeKloud, 2026-02-11. https://www.youtube.com/watch?v=wgOCzHXKw4c
- "Google ADK: Agent Development Kit", AI Makerspace, 2025-05-28. https://www.youtube.com/watch?v=xj5VRmkwlYk
- DeepLearning.AI short course "Building Live Voice Agents with Google's ADK": https://www.deeplearning.ai/courses/building-live-voice-agents-with-googles-adk (date **[UNVERIFIED]**)

### Quotable lines
- "ADK is the same framework powering agents within Google products like Agentspace" (Erwin Huizenga and Bo Yang, "Agent Development Kit: Making it easy to build multi-agent applications", developers.googleblog.com, 2025-04-09). https://developers.googleblog.com/en/agent-development-kit-easy-to-build-multi-agent-applications/
- "Clear, distinct descriptions are vital!" (same post, on LLM-driven delegation)
- "code-first Python framework for building, evaluating, and deploying sophisticated AI agents" (adk-python README)
- "Stop prompting and start routing!" (Google Cloud Tech, fOIGMZusCs8)
- Note: the often-repeated "agents in under 100 lines of code" claim does **not** appear in the launch blog post. It traces to Japanese press coverage of Next '25 **[UNVERIFIED as a Google quote]**.

---

## 4. Codelab: ADK 2 Orchestration (primary)

**"ADK 2 Orchestration: Graph, Collaborative & Dynamic Workflows"**, https://codelabs.developers.google.com/adk2/instructions. It pins **ADK 2.3.0** and builds a "Marathon Race Day Coach" in levels:

- **Prologue:** a mega-prompt agent that invents its own inputs, used as the motivating failure.
- **L0:** `Agent` plus a deterministic tool, executed by a `Runner`.
- **L1:** a function node chained to an agent node in a `Workflow`.
- **L2a:** parallel fan-out, then a `JoinNode`.
- **L2b:** deterministic router, so only one LLM call runs.
- **L3a:** collaborative agents in `chat` vs `single_turn` mode.
- **L3b:** task mode with `finish_task` returning a validated object.
- **L4a/L4b:** dynamic fan-out and recursion, with the depth limit enforced in code.
- **L5:** choosing a pattern by asking "who decides the next step?"

```python
# Source: codelabs.developers.google.com/adk2/instructions (L1 + L2b)
def fetch_conditions(node_input):                # function node: 0 LLM calls
    return Event(output=Conditions(temp_f=78, wind_mph=12, conditions="sunny").model_dump())

advise = Agent(name="advise", model=MODEL, mode="single_turn",
               input_schema=Conditions, instruction="...give pacing + gear advice...")
workflow = Workflow(edges=[(START, fetch_conditions, advise)])

def route_by_weather(node_input):                # an if-statement, 0 LLM calls
    temp = node_input["fetch_weather"]["temp_f"]
    route = "HOT" if temp >= 70 else "COLD" if temp <= 40 else "NORMAL"
    return Event(output=node_input, route=route)
(route_by_weather, {"HOT": hot_strategy, "NORMAL": normal_strategy, "COLD": cold_strategy})
```

```python
# Source: same codelab, L4b (recursive dynamic fan-out)
@node(parallel_worker=True, rerun_on_resume=True)
async def research_topic(ctx, node_input):
    finding = coerce(await ctx.run_node(research_agent, node_input=...), ResearchFinding)
    if finding.needs_deeper and finding.deeper_questions and depth < MAX_DEPTH:  # boundary in CODE
        children = await ctx.run_node(research_topic, node_input=deeper)
    yield Event(output={..., "children": children})
```

---

## 5. google/adk-samples → google/adk-recipes: what happened

The GitHub API redirects `google/adk-samples` (repo id 958830671, created 2025-04-01) to **`google/adk-recipes`**. The new description is "A collection of agent recipes, reference patterns, and vertical plugins built with Agent Development Kit (ADK)." Old links still redirect.

- **2026-09-09**, commit 3fd76ce: "Deleted the 9 old/obsolete samples from the repo (#2591)". This removed **customer-service** and **academic-research**, among others.
- **2026-09-29**, commit 3ec2724: "Deleted the 8 samples/recipes marked for deletion. (#2666)". This removed **data-science**, memory-bank, personalized-shopping, youtube-analyst and adk-ae-oauth.
- **2026-10-02**, commit ede41c7: "chore: delete retired python/ folder and clean up legacy references (#2759)". This removed **travel-concierge** and the rest of the old layout.

**New layout** (README):
- `core/`: "canonical patterns curated by the `agents-cli` team". These are meant to be "consumed and composed by tooling", e.g. Antigravity CLI and agents-cli. Recipes: ambient-expense-agent, ambient-quality-agent, cross-session-memory, deep-search, genmedia-for-commerce, long-horizon-harness, oauth-user-consent-flow, rag-agent-search, rag-vector-search, safety-plugins.
- `contrib/`: community and vertical deployable agents across languages. Python: financial-advisor, llm-auditor, brand-search-optimization, small-business-loan-agent, multiformat-hybrid-rag, retail-product-search, retail-virtual-tryon, and others. Also financial-advisor in **Go, Java, Kotlin and TypeScript**, plus llm-auditor in Kotlin.
- `plugins/`: vertical skill plugins (`SKILL.md` + `EVAL.yaml`), e.g. `plugins/retail/skills/product-search`.
- Disclaimer: "Recipes are for demonstration and as starting points, not production use."

**Teaching point:** the repo has shifted from samples for humans to read toward recipes for coding agents to compose, which mirrors the agents-cli and Skills direction announced in May 2026.

At its widest (snapshot f290c5c, before 2026-03-01), `python/agents` held about 45 samples, including: RAG, academic-research, ai-security-agent, auto-insurance-agent, blog-writer, brand-search-optimization, camel, customer-service, data-engineering, data-science, deep-search, financial-advisor, fomc-research, image-scoring, incident-management, llm-auditor, machine-learning-engineering, marketing-agency, medical-pre-authorization, order-processing, personalized-shopping, policy-as-code, realtime-conversational-agent, short-movie-agents, software-bug-assistant, swe-benchmark-agent, tau2-benchmark-agent, travel-concierge and youtube-analyst.

---

## 6. Sample architectures → design patterns

Code was read from snapshot `f290c5ce` (https://github.com/google/adk-recipes/tree/f290c5ce0270fe141785f2ed55e3485fbb50b36d/python/agents) or from current `main`.

### 6.1 llm-auditor: **Sequential pipeline / Critic → Reviser (Reflection)**
`SequentialAgent(sub_agents=[critic_agent, reviser_agent])`. The critic uses `google_search` and an `after_model_callback` that appends grounding references. It is still present, unchanged, in `contrib/python/llm-auditor` on main, which shows that 1.x-style workflow agents still run in 2.x.

```python
# Source: github.com/google/adk-recipes/blob/main/contrib/python/llm-auditor/app/agent.py
from google.adk.agents import SequentialAgent
from .sub_agents.critic import critic_agent
from .sub_agents.reviser import reviser_agent

llm_auditor = SequentialAgent(
    name="llm_auditor",
    description=("Evaluates LLM-generated answers, verifies actual accuracy using the"
                 " web, and refines the response to ensure alignment with real-world knowledge."),
    sub_agents=[critic_agent, reviser_agent],
)
root_agent = llm_auditor
```

### 6.2 financial-advisor: **Coordinator + Agent-as-Tool**
An `LlmAgent` "financial_coordinator" wraps four specialists as tools: data_analyst, trading_analyst, execution_analyst and risk_analyst. It uses `output_key` to write results to state, and is wrapped in `App(root_agent=..., name="app")` on main. The current version includes `app_utils/a2a.py`, which exposes it over **A2A**. It is the one recipe ported to all five languages, which makes it the Rosetta-stone sample.

```python
# Source: github.com/google/adk-recipes/blob/main/contrib/python/financial-advisor/app/agent.py
financial_coordinator = LlmAgent(
    name="financial_coordinator",
    model=MODEL,
    instruction=prompt.FINANCIAL_COORDINATOR_PROMPT,
    output_key="financial_coordinator_output",
    tools=[
        AgentTool(agent=data_analyst_agent),
        AgentTool(agent=trading_analyst_agent),
        AgentTool(agent=execution_analyst_agent),
        AgentTool(agent=risk_analyst_agent),
    ],
)
root_agent = financial_coordinator
app = App(root_agent=root_agent, name="app")
```

### 6.3 academic-research: **Coordinator + Agent-as-Tool (2 specialists)**
`academic_coordinator` (gemini-2.5-pro) with `AgentTool(academic_websearch_agent)` and `AgentTool(academic_newresearch_agent)`, and `output_key="seminal_paper"`. Flow: the user supplies a seminal paper → web search for citing papers → proposals for new research directions. (Removed 2026-09-09.)

### 6.4 travel-concierge: **Hierarchical delegation via `sub_agents` (LLM transfer) + lifecycle phases + state as memory**
The root `Agent` (gemini-2.0-flash-001) has six `sub_agents`: inspiration, planning, booking, pre_trip, in_trip and post_trip. A `before_agent_callback=_load_precreated_itinerary` seeds session state. The README lists its components as "Tools, AgentTools, Memory". It uses Google Places, Search grounding, and an optional Airbnb **MCP** tool. Tracing goes to Arize via OpenInference.
Flow in words: *pre-booking* (inspire → plan flights/seats/hotel → itinerary → book/pay) is followed by *post-booking* (pre-trip visa/medical/storm checks → in-trip monitoring + a "day-of" agent → post-trip feedback that feeds preferences).

### 6.5 customer-service: **Single rich agent + callbacks as guardrails + HITL approval**
"Cymbal Home & Garden" retailer. A single `Agent` with `global_instruction` and 12 tools (cart, recommendations, `approve_discount`, `sync_ask_for_approval`, `update_salesforce_crm`, `schedule_planting_service`, QR code…). It is multimodal and Live (video). It wires all four callback types: `before_agent`, `before_tool`, `after_tool`, and `before_model_callback=rate_limit_callback`. **Lesson:** not every problem needs multiple agents. Policy belongs in callbacks.

### 6.6 data-science: **NL2SQL + NL2Py router with dynamic sub-agents**
`get_root_agent()` assembles tools from a `DATASET_CONFIG_FILE`. It always includes `call_analytics_agent` (code execution). It adds `call_bigquery_agent` and the `bqml_agent` sub-agent for BigQuery, and `call_alloydb_agent` for AlloyDB (through **MCP Toolbox for Databases**). Schemas are injected into the instruction as `<DATASETS><SCHEMA>` blocks, and settings are loaded into `callback_context.state`. Traces go via OTLP to W&B Weave. Default model is `gemini-2.5-flash`.

### 6.7 deep-search (formerly gemini-fullstack): **Plan → HITL approval → Loop-until-pass → Cited report**
Still in `core/`. The structure is `interactive_planner_agent` (with `AgentTool(plan_generator)`), then `research_pipeline = SequentialAgent[section_planner, section_researcher, LoopAgent(max_iterations=…)[research_evaluator, EscalationChecker, enhanced_search_executor], report_composer]`. It ships with a React frontend and a FastAPI backend.

```python
# Source: github.com/google/adk-recipes/blob/main/core/python/deep-search/app/agent.py
class EscalationChecker(BaseAgent):
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        evaluation_result = ctx.session.state.get("research_evaluation")
        if evaluation_result and evaluation_result.get("grade") == "pass":
            yield Event(author=self.name, actions=EventActions(escalate=True))  # break loop
        else:
            yield Event(author=self.name)                                         # keep looping
```

### 6.8 ambient-expense-agent (core, **native ADK 2.0**): **Event-triggered graph + deterministic routing + HITL `RequestInput`**
Pub/Sub trigger → `parse_expense_email` → `route_by_amount`. Amounts under $100 go to `auto_approve`; amounts of $100 or more go to an LLM `review_agent` (`mode="single_turn"`, `input_schema=ExpenseData`), then `request_approval` (yields `RequestInput`, which pauses the workflow), then `process_decision`.

```python
# Source: github.com/google/adk-recipes/blob/main/core/python/ambient-expense-agent/expense_agent/agent.py
from google.adk import Agent, Context, Event, Workflow
from google.adk.events import RequestInput

def route_by_amount(node_input: dict, ctx: Context) -> Event:
    ctx.state["expense_data"] = node_input
    if node_input.get("amount", 0) >= config.review_threshold:
        return Event(route="NEEDS_REVIEW", output=node_input)
    return Event(route="AUTO_APPROVE", output=node_input)

def request_approval(node_input, ctx: Context):
    yield RequestInput(message="Expense requires manager approval. Approve or reject.",
                       payload=ctx.state.get("expense_data", {}))

root_agent = Workflow(name="expense_processor", edges=[
    ("START", parse_expense_email, route_by_amount),
    (route_by_amount, {"AUTO_APPROVE": auto_approve, "NEEDS_REVIEW": review_agent}),
    (review_agent, request_approval, process_decision),
])
```

### 6.9 Other core recipes (patterns only, from imports)
- **long-horizon-harness:** `App` with `ResumabilityConfig`, `EventsCompactionConfig`, `ContextCacheConfig`, an Agent Engine sandbox code executor, a custom summarizer and tool-declaration compaction. This is the context-engineering pattern for long tasks.
- **cross-session-memory:** Memory Bank via `preload_memory_tool`.
- **oauth-user-consent-flow:** 3-legged OAuth for a Drive tool.
- **rag-agent-search / rag-vector-search:** retrieval through Vertex AI Search or Vector Search.
- **safety-plugins:** guardrail plugins around an `LlmAgent` sub-agent.

### Pattern → sample map

| Pattern | Sample |
|---|---|
| Single agent + tools + callbacks | customer-service |
| Sequential pipeline / reflection | llm-auditor |
| Coordinator with AgentTool | financial-advisor, academic-research |
| LLM-driven transfer (sub_agents) | travel-concierge |
| Router + code-exec specialists (NL2SQL/NL2Py) | data-science |
| Loop + custom escalation + HITL plan approval | deep-search |
| 2.0 graph Workflow + route + RequestInput | ambient-expense-agent |
| Fan-out/join, dynamic/recursive workers | ADK2 codelab |
| Long-horizon context management | long-horizon-harness |

---

## 7. Real-world mentions
- Agentspace, now Gemini Enterprise, is built on ADK, per the launch post.
- Next '26 customer agents (GE Appliances, Tata Steel, Highmark Health "Sidekick … $27.9 million in value in 2025") run on Gemini Enterprise. The wrap-up does not say whether they are ADK-built **[UNVERIFIED that these are ADK]**.
- Box Content Cloud + ADK video: https://www.youtube.com/watch?v=lCTVvHWkVAI (channel and date **[UNVERIFIED]**).
- Community project Beever Atlas (May 2026 Community Call spotlight).

---

## 8. Slide ideas

1. **"From 0.1 to 2.13 in 18 months"**: horizontal timeline (Next '25 → I/O '25 1.0 → Kaggle Nov '25 → 2.0a Mar '26 → I/O '26 GA → 2.13 Oct '26). Animation: milestones pop in, with a release-tick density bar showing the bi-weekly cadence.
2. **"Adoption by the numbers"**: four stat tiles (22k stars, 10.1M downloads/month, 1.5M Kaggle learners, 5 language SDKs) plus a bar chart of stars per repo. Animation: count-up numbers.
3. **"The four-rung ladder"**: staircase graphic (Agent Studio → Managed Agents API → Antigravity → ADK 2.0) with A2A arrows linking the rungs. Animation: climb rung by rung.
4. **"Samples became recipes"**: before/after repo tree (`python/agents/*` → `core/ contrib/ plugins/`), with deletion commits as red strike-throughs. Message: recipes are now written for coding agents.
5. **"Six samples, six patterns"**: a 2×3 grid of mini-diagrams (customer-service single agent; llm-auditor A→B; financial-advisor hub-and-spoke AgentTool; travel-concierge tree; data-science router; deep-search loop). Animation: each tile expands to show its code snippet.
6. **"Deep-search loop anatomy"**: flowchart Plan → [HITL approve] → Research → Loop(Evaluate → EscalationChecker → Search) → Compose. Animation: a token travels around the loop until grade="pass" breaks it.
7. **"Your first 2.0 graph: the expense agent"**: a node graph with a diamond router ($100 threshold), an LLM node, and a pause icon for `RequestInput`. Animation: two sample expenses ($45, $1,200) take different paths, and the second freezes for approval.
8. **"Stop prompting, start routing"**: a mega-prompt blob with hallucination warnings morphs into fan-out → join → router (Graph Engineering video). It highlights "multi-branch workflow on a single LLM call".
9. **"Evaluate like Google: the 5-step inner loop"**: a circular diagram (Golden path → Fail → Trace → Fix → Validate) with an outer ring for Vertex AI Gen AI Eval. Source: Agent Factory.
10. **"Where to keep learning"**: a curated QR-code wall (ADK2 codelab, Agent Factory playlist, Kaggle guides, Community Call, adk-recipes).
