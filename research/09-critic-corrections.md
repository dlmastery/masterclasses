# 09 — Critic pass: corrections, gap research, and the 60-slide arc

Research date: 2026-10-23. Inputs: research files 01–08 in this folder. Each correction was checked against a primary source today: the PyPI JSON API, the GitHub API (`gh api`), raw files on `google/adk-python` `main` (CHANGELOG.md, README.md, `src/`), the raw Markdown of adk.dev pages (`/index.md`), the arXiv API, modelcontextprotocol.io, a2a-protocol.org, aaif.io and Google blogs. HTTP status codes for the codelab URLs come from `curl -L`. As a control, a made-up codelab path returns 404, so a 200 means the page really exists.
Limitation: the shared web-search budget ran out partway through this pass. Everything below was checked by fetching known primary URLs directly. Items that would still need a search are marked [UNVERIFIED].

**Baseline facts (verified today):**
- `google-adk` **2.13.0**. PyPI upload 2026-10-23 18:26 UTC, GitHub release v2.13.0 2026-10-23, CHANGELOG entry dated 2026-10-22. `requires_python >=3.11`.
- 2.0.0 GA on 2026-05-19 (PyPI and adk.dev/2.0).
- Go 2.0 GA 2026-06-30, TypeScript 2.0 GA 2026-08-21 (adk.dev/2.0).
- The 1.x line ends at 1.39.1 (2026-08-27).

---

## 1. Corrections table (contradictions between files, resolved against primary sources)

| # | Topic | What the files say | Primary-source verdict | Source |
|---|---|---|---|---|
| C1 | **Minimum Python** | 05 says 3.10+. 01, 03 and 04 say 3.11+. adk.dev/2.0 and get-started/python say "Python 3.10 or later". | **Both are right, for different versions.** PyPI `requires_python` is `>=3.10` for 2.0.0 through 2.11.0 and `>=3.11` from **2.12.0 (2026-10-13)**. The README says "Python 3.11+" and ships constraints for 3.11–3.15. The adk.dev pages are out of date. **Slide:** "Python 3.11+ (ADK ≥2.12; 2.0–2.11 accepted 3.10)". | pypi.org/pypi/google-adk/json; README.md |
| C2 | **`mode="task"` inside graph workflows** | 01 and 02 say it is disabled (docs banner). 03 says the codelab reports it works from 2.5.0. | **It works in current releases.** The docs banner still reads "disabled for use in graph-based workflows in ADK Python v2.0.0 … expected to be re-enabled". The README's Task API bullet now lists "task agents as workflow nodes". The CHANGELOG has 2.5.0 "Support state-based resumption for task-mode agent workflow nodes" and 2.12.0 "support task sub-agent delegation and resume in task-mode wrapper". **Slide:** "Task agents as graph nodes: ≥2.5.0. The docs banner is out of date." | README.md; CHANGELOG.md; adk.dev/workflows/collaboration/index.md |
| C3 | **`mode` on the root agent** | 02, 04 and 07 quote "Do not configure a root agent with the mode setting." | The docs still say this. However, CHANGELOG 2.7.0 contains "**agent:** add native task mode support to root LlmAgent". **Teach** the docs rule for coordinators. Mention root task mode only as a 2.7+ capability [behaviour UNVERIFIED]. | CHANGELOG.md L1193 |
| C4 | **RetryConfig defaults** | 01, 03 and 07 imply `max_attempts=3`. 02 says the default is 5. | `max_attempts=3` is only the **example** on the migration page. Source `_retry_config.py` says: "If not specified, default to **5**" (this count includes the original attempt). The other defaults are `initial_delay` 1.0 s, `max_delay` 60 s, `backoff_factor` 2.0 and `jitter` 1.0. `exceptions=None` means retry on every exception. | src/google/adk/workflow/_retry_config.py |
| C5 | **Are `_run_async_impl` overrides "silently ignored"?** | 01, 03 and 04 repeat the docs. 02 shows that source still calls them. 08 shows 1.x-style `BaseAgent` and `SequentialAgent` recipes (deep-search, llm-auditor) still running on `main`. | adk.dev/2.0 does say "The Workflow Graph engine completely bypasses these legacy overrides … silently ignored." The template agents still work standalone, and they carry `@deprecated` ("…will be removed in a future version. Workflow cannot yet be used as an LlmAgent sub-agent"). **Teach:** don't depend on 1.x overrides inside a `Workflow`, and write new orchestration as graph or `@node` code. | adk.dev/2.0/index.md L48; sequential_agent.py L88 |
| C6 | **Currency-agent codelab URL** | 05 cites `/codelabs/currency-agent`. 03 says that URL is dead. | `codelabs.developers.google.com/codelabs/currency-agent` returns **404**. Use **https://codelabs.developers.google.com/getting-started-mcp-a2a-adk** (200). | curl |
| C7 | **Samples repo name** | 01, 05 and 07 say `google/adk-samples`. 08 says it is now `adk-recipes`. | `gh api repos/google/adk-samples` resolves to **`google/adk-recipes`** (10,523 stars), described as "A collection of agent recipes, reference patterns, and vertical plugins…". customer-service, academic-research, data-science and travel-concierge were **deleted** in Sep–Oct 2026. Link those through the snapshot `f290c5ce…`. | GitHub API |
| C8 | **A2A Agent Card path** | 03 (Creative Studio, ADK 1.31.1) uses `/.well-known/agent.json`. 05 uses `agent-card.json`. | The A2A spec, **Latest Released Version 1.0.0**, says "GET /.well-known/agent-card.json". Use ADK's `AGENT_CARD_WELL_KNOWN_PATH` constant, and treat `agent.json` as the pre-0.3 legacy name. | a2a-protocol.org/latest/specification/ |
| C9 | **"95 out of 100" quote** | 01 quotes "95 out of 100 times". | That exact phrase is **not** in the post. The closest line is "you might get the exact desired outcome 95 times" (in a 100-run framing). Post details: "Why we built ADK 2.0", **2026-07-01**, by Swapnil Agarwal, Alan Blount and Frank Guan. | developers.googleblog.com/en/why-we-built-adk-20/ |
| C10 | **Status of the 5,152→2,265 token benchmark** | 02 calls it a third-party (ecorpit) claim [UNVERIFIED]. 01 says it is from the Google blog. | It is **primary**, from the Google blog above. Tokens per run went 5,152 → 2,265 (~50%) and latency 7.2 s → 5.7 s (~20%). The blog labels it "illustrative", run on `gemini-3.5-flash` with mock API responses. Footnote it that way on the slide. | same |
| C11 | **First ADK release** | 01 says 0.0.1 on 2025-03-17. 08 says 0.1.0 on 2025-04-09. | Both are true. **0.0.1** was a placeholder upload on 2025-03-17, then 0.0.2 on 04-08, then **0.1.0 on 2025-04-09**, the launch day at Cloud Next '25. **1.0.0** came on 2025-05-20. | PyPI |
| C12 | **2.x release dates** | 01 mixes CHANGELOG dates with PyPI dates. | The two sources differ by a day for several releases (CHANGELOG / PyPI): 2.3.0 06-17/06-18, 2.6.0 07-29/07-30, 2.8.0 08-25/08-26, 2.10.0 09-24/09-25, 2.11.0 10-01/10-02, 2.13.0 10-22/10-23. **Slides use the PyPI upload date.** | PyPI vs CHANGELOG |
| C13 | **`McpToolset` vs `MCPToolset`** | 05 marks the alias [UNVERIFIED]. | **Both** names are exported from `google.adk.tools.mcp_tool` (`__init__.py`), as is `to_mcp_server`. Teach `McpToolset`. | mcp_tool/__init__.py |
| C14 | **Source of "Sessions from 2.0 readable by 1.28+"** | 05 attributes it to the README. | The claim is no longer in the current README. It appears verbatim in the **PyPI 2.0.0 long description**: "Sessions generated by ADK 2.0 are readable by ADK 1.28+ (extra fields will be ignored), but are incompatible with older 1.x versions." | pypi.org/pypi/google-adk/2.0.0/json |
| C15 | **MCP 2026-07-28 "stateless"** | 05 marks it [UNVERIFIED]. | **Verified** in the spec changelog: SEP-2567 removes protocol sessions and `Mcp-Session-Id`. SEP-2575 removes the `initialize` handshake and puts the version and capabilities in each request's `_meta`. It also adds a mandatory `server/discover` and replaces GET/subscribe with `subscriptions/listen`. SEP-2663 moves Tasks into an extension. SEP-2322 adds Multi Round-Trip Requests (`resultType: "input_required"`). SEP-2577 deprecates Roots, Sampling and Logging. | modelcontextprotocol.io/specification/2026-07-28/changelog |
| C16 | **A2A dates** | 05 says "v1.0 Mar 2026" and "joined the Agentic AI Foundation Aug 2026". | **Verified**: release v1.0.0 on **2026-03-12** and v1.0.1 on 2026-05-28 (a2aproject/A2A, 26,273 stars). The AAIF blog "A2A joins AAIF's open agentic stack" is dated **2026-08-17** and says it is "backed by over 150 organizations". The AAIF itself launched in Dec 2025 (Axios, secondary). | GitHub API; aaif.io/blog/a2a-joins-aaif |
| C17 | **MCP Toolbox version** | 03 says v1.13.1. 05 says v1.15.0. | **v1.15.0** was released 2026-10-23, after v1.14.0 (10-08) and v1.13.1 (09-25). Use 1.15.0. | GitHub API googleapis/mcp-toolbox |
| C18 | **TypeScript release tag** | 01 says "adk-v2.3.0". | The actual tags are `main-v2.3.0` and `integrations-v2.3.0` (2026-10-13). Go is v2.6.0 (10-13), with 1.x at v1.9.0. Java is v1.13.0 (10-21) and has no 2.0. | GitHub API |
| C19 | **ADK Go 2.0 blog** | 02 and 03 use different URL forms. | Both URLs resolve. Title: "ADK for Go 2.0: build agent workflows as a graph", 2026-06-30, by Toni Klopfenstein and Sampath Kumar Maddula. Both "A graph is an agent." and "any node can pause the graph and ask a human a question" are verbatim. | developers.googleblog.com/en/announcing-adk-go-20/ |
| C20 | **Gulli book** | 07 gives a page-count conflict. | Crossref: *Agentic Design Patterns*, Antonio **Gullí**, Springer Nature Switzerland, 2025. ISBN 9783032014016 (print), 9783032014023 (eBook). Page count still [UNVERIFIED]; say "21 patterns", not a page count. | api.crossref.org |
| C21 | **Kaggle 1.5M figure** | 06 cites KDnuggets (secondary). | Cite the primary blog.google recap (2025-12-18), as 03 and 08 do. | — |
| C22 | **Google Search tool "only compatible with Gemini 2 models"** | 05 quotes the docs. | That docs line is outdated, since the same page's examples use `gemini-flash-latest`. Don't put it on a slide. | adk.dev/integrations/google-search |
| C23 | **Default model** | 04 says `gemini-3.5-flash`. | **Verified** in `llm_agent.py`: `DEFAULT_MODEL = 'gemini-3.5-flash'`. Doc snippets use the alias `gemini-flash-latest`. | llm_agent.py L289 |
| C24 | **Top-level exports** | 07 shows `from google.adk import Agent, Workflow, Event, Context`. | **Verified**: `__all__ = ['Agent','Context','Event','Runner','Workflow']`, loaded lazily. | src/google/adk/__init__.py |

Spot-checks that held (no contradiction):
- **Telemetry** (01, 04, 06): the default is `otel_semconv_1_44` and `call_llm` is removed. Opt out with `ADK_TELEMETRY_SCHEMA_VERSION_OPT_IN=otel_semconv_1_36` (CHANGELOG 2.13.0).
- **Changelog headline numbers**: "up to 8x faster execution turns for string-model agents" (2.13) and "Cut time to first model request by 40% in long sessions" (2.12).
- **Plugins** were introduced in 1.7.0 (2025-07-16; CHANGELOG: "Plugin is simply a class that packages these individual callback functions together").
- **Ng HumanEval numbers**: 48.1 / 67.0 / 95.1, published 2024-03-20.
- **GCP Architecture Center**: 12 patterns, last updated 2026-05-28.

---

## 2. Codelab and URL status check (2026-10-23)

| Status | URL |
|---|---|
| 200 | https://codelabs.developers.google.com/adk2/instructions — "ADK 2 Orchestration: Graph, Collaborative & Dynamic Workflows" (pins 2.3.0) |
| 200 | https://codelabs.developers.google.com/getting-started-mcp-a2a-adk |
| **404** | https://codelabs.developers.google.com/codelabs/currency-agent (replace it) |
| 200 | https://codelabs.developers.google.com/adk-eval/instructions |
| 200 | https://codelabs.developers.google.com/vibecode-ambient-expense-agent |
| 200 | https://codelabs.developers.google.com/secure-customer-service-agent/instructions |
| 200 | https://codelabs.developers.google.com/next26/adk-deploy-scale |
| 200 | https://codelabs.developers.google.com/codelabs/agent-memory/instructions |
| 200 | https://codelabs.developers.google.com/instavibe-adk-multi-agents/instructions |
| 200 | https://codelabs.developers.google.com/travel-agent-mcp-toolbox-adk |
| 200 | https://codelabs.developers.google.com/codelabs/create-low-code-agent-with-ADK-visual-builder (the path **without** `/codelabs/` returns 404) |
| 200 | …/devsite/codelabs/build-agents-with-adk-foundation, …/ai-creative-studio-adk-a2a, …/next26/multi-agent-system, …/next26/scale-agents, …/next26/dev-keynote/enhancing-agents-with-memory, …/codelabs/cloud-run/use-mcp-server-on-cloud-run-with-an-adk-agent |
| 403 (bot block, not a dead link) | https://www.cloudskillsboost.google/course_templates/1382 |
| 200 | https://adk.dev/llms.txt, https://www.kaggle.com/learn-guide/5-day-agents, https://www.kaggle.com/whitepaper-agents, https://www.kaggle.com/whitepaper-agent-quality |

---

## 3. Gap research (topics a complete course needs that files 01–08 lack)

### G1. First principles: what an "agent" is, as a lineage of papers (all verified on arXiv)

| Year | Paper | arXiv | First author | Why it's on a slide |
|---|---|---|---|---|
| 2022-01 | Chain-of-Thought Prompting Elicits Reasoning in LLMs | 2201.11903 | Jason Wei | Reasoning as text |
| 2022-10 | ReAct: Synergizing Reasoning and Acting | 2210.03629 | Shunyu Yao | Thought→Action→Observation loop (ICLR 2023) |
| 2023-02 | Toolformer: LMs Can Teach Themselves to Use Tools | 2302.04761 | Timo Schick | Tool use learned by the model |
| 2023-03 | Reflexion | 2303.11366 | Noah Shinn | Verbal self-feedback |
| 2023-03 | Self-Refine | 2303.17651 | Aman Madaan | Generator-critic |
| 2023-04 | Generative Agents | 2304.03442 | Joon Sung Park | Memory + reflection + planning |
| 2023-05 | Plan-and-Solve Prompting | 2305.04091 | Lei Wang | Plan-then-execute |
| 2023-05 | Tree of Thoughts | 2305.10601 | Shunyu Yao | Search over thoughts |
| 2023-05 | ReWOO: Decoupling Reasoning from Observations | 2305.18323 | Binfeng Xu | Planner/worker split (resolves 07's [UNVERIFIED]) |
| 2023-08 | AutoGen | 2308.08155 | Qingyun Wu | Multi-agent conversation framework |
| 2023-08 | MetaGPT | 2308.00352 | Sirui Hong | SOP-driven roles |
| 2023-10 | MemGPT: Towards LLMs as Operating Systems | 2310.08560 | Charles Packer | Tiered memory |
| 2023-12 | An LLM Compiler for Parallel Function Calling | 2312.04511 | Sehoon Kim | Parallel tool DAGs (resolves 07's [UNVERIFIED]) |

Slide idea: a single timeline that runs from the papers to ADK primitives. CoT → `BuiltInPlanner`; ReAct → every `LlmAgent` with tools and `PlanReActPlanner`; Self-Refine/Reflexion → loop/back-edge; LLMCompiler → `JoinNode` fan-out; MemGPT → Session/Memory/Artifacts tiers.

### G2. Context engineering, a core module the files only touch on
- **Primary:** "Architecting efficient context-aware multi-agent framework for production", Google Developers Blog, **2025-12-04**, Hangfei Lin (Tech Lead). https://developers.googleblog.com/en/architecting-efficient-context-aware-multi-agent-framework-for-production/
  - Quotes: "Context is a compiled view over a richer stateful system." / "Context engineering stops being prompt gymnastics and starts looking like systems engineering." / "Every model call and sub-agent sees the minimum context required."
  - Principles:
    1. Separate storage (Session event log) from presentation (working context).
    2. Assemble context through ordered, named processors.
    3. Scope by default.
    4. Use tiers: working context, Session, Memory, Artifacts (a handle pattern).
    5. Compact and filter history.
    6. Put stable content first for caching.
    7. Reframe history at agent handoffs so one agent does not mistake another's actions for its own.
  - Maps to ADK: `include_contents='none'`, `EventsCompactionConfig`, `ContextCacheConfig` + `static_instruction`, `ContextFilterPlugin`, artifacts, `preload_memory`/`load_memory`, Skills.
- **Research:** ACE, "Agentic Context Engineering: Evolving Contexts for Self-Improving Language Models", arXiv 2510.04618 (2025-10-06), Qizheng Zhang et al. Contexts become "evolving playbooks", with "+10.6% on agents and +8.6% on finance". It names two failure modes: "brevity bias" and "context collapse".
- **Skills (progressive disclosure), verified on adk.dev/skills.** Supported in Python v1.25.0, TS v0.6.1, Go v1.2.0 and Kotlin v0.1.0, all **Experimental**. There are three levels: **L1** metadata (`SKILL.md` frontmatter), **L2** instructions (`SKILL.md` body, loaded via the `load_skill` tool) and **L3** resources (references, assets, scripts). Open format: https://agentskills.io
```python
# Source: https://adk.dev/skills/ (Python)
import pathlib
from google.adk import Agent
from google.adk.skills import load_skill_from_dir
from google.adk.tools import skill_toolset

weather_skill = load_skill_from_dir(
    pathlib.Path(__file__).parent / "skills" / "weather-skill")
my_skill_toolset = skill_toolset.SkillToolset(skills=[weather_skill])
root_agent = Agent(name="skill_user_agent", tools=[my_skill_toolset])
```

### G3. When *not* to go multi-agent (evidence the deck needs for balance)
- **Anthropic, "How we built our multi-agent research system"** (2025-06-13), https://www.anthropic.com/engineering/multi-agent-research-system
  - The multi-agent setup (Opus 4 lead + Sonnet 4 subagents) "outperformed single-agent Claude Opus 4 by **90.2%**" on an internal research eval.
  - Agents use about **4×** the tokens of chat, and multi-agent systems about **15×**.
  - Token usage alone explains **80%** of the performance variance on BrowseComp, and three factors explain 95%.
- **Google Research et al., "Towards a Science of Scaling Agent Systems"**, arXiv **2512.08296** (2025-12-09), Yubin Kim et al.
  - Setup: **260 configurations**, 6 benchmarks, 5 architectures (single-agent plus Independent/Centralized/Decentralized/Hybrid multi-agent) and 3 LLM families.
  - Results relative to a single agent range from "**+80.8%** on decomposable financial reasoning to **−70.0%** on sequential planning".
  - "Coordination yields diminishing returns once single-agent baselines exceed certain performance."
  - Architectures without centralized verification propagate errors more.
- **"Why Do Multi-Agent LLM Systems Fail?"** (MAST), arXiv **2503.13657** (2025-03-17), Mert Cemri et al. 1,600+ annotated traces across 7 frameworks, **14 failure modes** in **3 categories** (system design, inter-agent misalignment, task verification), and κ = 0.88.
- Teaching line: *a graph with one LLM call often beats a team of five agents.* That is the ADK 2.0 thesis, with numbers behind it.

### G4. Prompt-injection security by design (deeper than guardrail callbacks)
- **CaMeL**, "Defeating Prompt Injections by Design", arXiv **2503.18813** (2025-03-24), Edoardo Debenedetti et al. This verifies the citation that 06 left [UNVERIFIED].
  - CaMeL extracts the control and data flow from the *trusted* query, so "untrusted data … can never impact the program flow". Capabilities enforce data-flow policies.
  - Result: **77%** of AgentDojo tasks solved with provable security, vs **84%** undefended.
  - Code: https://github.com/google-research/camel-prompt-injection
- **"Design Patterns for Securing LLM Agents against Prompt Injections"**, arXiv **2506.08837** (2025-06-10), Luca Beurer-Kellner et al. (14 authors). It offers principled patterns "with provable resistance to prompt injection" [list the six patterns only after reading the PDF; UNVERIFIED names].
- ADK link: a graph `Workflow` with deterministic routing is a plan-then-execute / CaMeL-like control-flow isolation. The "Why we built ADK 2.0" blog argues the same: the graph limits which actions are possible.

### G5. Benchmarks, for the "state of the art" slide
- **τ-bench**, arXiv **2406.12045** (2024-06-17), Shunyu Yao et al. A simulated user plus domain APIs and policies. It introduces **pass^k**. Finding: "gpt-4o succeed on <50% of the tasks … pass^8 <25% in retail".
  - This is the best single slide on *reliability vs capability*, and it maps directly to ADK user simulation (`adk eval_set add_eval_case --scenarios_file`).
- **SWE-bench**, arXiv 2310.06770 (Jimenez et al.). **GAIA**, arXiv 2311.12983 (Mialon et al.).
- **Current leaderboard numbers (late 2026) are [UNVERIFIED] in this pass.** Pull them live from swebench.com, the τ²-bench leaderboard and the GAIA HF leaderboard the week of the lecture, and date-stamp the slide.

### G6. Agent optimization (`adk optimize`) is unexplained in the files
- ADK 2.3.0 added `GEPARootAgentOptimizer`. The CLI has `adk optimize`, and agents-cli has `eval optimize (GEPA)`.
- Paper: **"GEPA: Reflective Prompt Evolution Can Outperform Reinforcement Learning"**, arXiv **2507.19457** (2025-07-25), Lakshya A Agrawal et al. Results:
  - Beats GRPO "by 6% on average and by up to 20%, while using up to **35x fewer rollouts**".
  - Beats MIPROv2 "by over 10%".
- Related: **AFlow**, "Automating Agentic Workflow Generation", arXiv 2410.10762. It uses MCTS over workflow graphs, reports +5.7% average, and lets smaller models beat GPT-4o "at 4.55% of its inference cost".
- Slide: the eval→optimize flywheel. The golden set feeds `adk eval`, which feeds GEPA reflective mutation, which yields a new instruction, which is re-evaluated.

### G7. The protocol stack beyond MCP and A2A

| Layer | Protocol | Status (verified today) | ADK hook |
|---|---|---|---|
| Agent↔tools | MCP | Spec **2026-07-28** (stateless; see C15). Under the AAIF. | `McpToolset`, `to_mcp_server` |
| Agent↔agent | A2A | **v1.0.0 (2026-03-12)**, joined AAIF 2026-08-17 | `to_a2a`, `RemoteA2aAgent` |
| Agent↔UI events | **AG-UI** (docs.ag-ui.com) | adk.dev page: "Supported in ADK Python, TypeScript, Go, Java" | `npx copilotkit@latest create -f adk` (adk.dev/integrations/ag-ui) |
| Agent→generative UI | **A2UI** (a2ui.org) | **v0.9.1 current**, v1.0 "Candidate". Ships an A2A extension and "A2UI over MCP" | Next '26 codelab "Build Rich Agent Experiences with ADK + A2UI" (from 08) |
| Agent↔payments | **AP2** (ap2-protocol.org) | Spec with Checkout/Payment **Mandates** and Verifiable Digital Credentials | launch date [UNVERIFIED this pass; recalled as Sep 2025] |

### G8. Framework landscape (one comparison slide)
ADK sits on the four rungs Google described at I/O '26 (08, secondary source): Agent Studio, then Managed Agents API, then Antigravity, then ADK 2.0. Peers to name, each with a primary citation: AutoGen (2308.08155), MetaGPT (2308.00352), LangGraph and CrewAI (both in the Next '26 "Scale Agents" codelab via A2A). Feature-level claims about peers are [UNVERIFIED]. Keep the comparison to *control model* (graph vs conversation vs role SOP) rather than benchmark claims.

### G9. Cost and latency engineering (gather the numbers in one place)
- Workflow vs vanilla agent: −50% tokens and −20% latency (illustrative; Google blog).
- Runtime gains: −40% time-to-first-model-request in long sessions (2.12), and up to 8× faster turns for string-model agents (2.13).
- Context levers: context caching (`ContextCacheConfig(min_tokens=2048, ttl_seconds=600, cache_intervals=5)`), event compaction and `ADK_MAX_LLM_CALLS` (2.8).
- Multi-agent token tax: 15× chat (Anthropic).
- Snippet for the durability slide, with verified defaults:
```python
# Defaults verified in src/google/adk/workflow/_retry_config.py (ADK 2.13.0)
from google.adk import Context, Event, Workflow
from google.adk.workflow import node, RetryConfig

@node(retry_config=RetryConfig(max_attempts=5, initial_delay=1.0,  # 5 = default, incl. 1st try
                               max_delay=60.0, backoff_factor=2.0,
                               exceptions=["HTTPError"]))           # None = retry everything
def get_weather(ctx: Context) -> str:
    yield Event(message=f"attempt {ctx.attempt_count}")
    yield call_flaky_api()          # let exceptions propagate; never catch BaseException

root_agent = Workflow(name="root_agent", edges=[("START", get_weather)])
```
(The pattern is adapted from `contributing/samples/workflows/retry/agent.py`. The `exceptions` list form follows the field docstring.)

---

## 4. Remaining [UNVERIFIED] items to clear before slides are final
1. Exact behaviour of root-agent task mode (2.7.0).
2. Whether `ResumabilityConfig` is still needed for 2.0 Workflows.
3. Python default for `max_parallel_workers` (TypeScript is 8).
4. Whether a node that yields two `Event.output` values raises an error or overwrites.
5. The six pattern names in arXiv 2506.08837.
6. Live leaderboard numbers (SWE-bench Verified, τ²-bench, GAIA).
7. AP2 launch date.
8. Gemini 3.6/3.7/3.8 model ID strings.
9. Recording URLs for I/O '26 and Next '26 sessions.
10. Gulli page count.

---

## 5. Recommended 60-slide narrative arc (first principles → state of the art)

**Section 1 — Why agents? (slides 1–6)**
1. Title: "Agents from first principles to production with Google ADK 2.0 (google-adk 2.13.0, Oct 2026)".
2. The hook: GPT-3.5 in an agent loop reaches 95.1% on HumanEval, beating GPT-4 zero-shot at 67.0% (Ng, 2024-03-20).
3. Definition: an agent is an LLM + tools + a loop + state. Quote Anthropic: "LLMs using tools based on environmental feedback in a loop."
4. Workflows vs agents: the autonomy dial (Anthropic's 5 workflows plus agents).
5. A lineage timeline: CoT → ReAct → Toolformer → Reflexion → Generative Agents → MemGPT → LLMCompiler (G1).
6. The course map, with the eight remaining sections as one road.

**Section 2 — The agent loop, mechanically (7–12)**
7. Function calling step by step: schema from docstring and type hints → `FunctionCall` → `FunctionResponse`.
8. ReAct frame by frame, overlaid on a real ADK event trace.
9. Planning: `BuiltInPlanner` (thinking budget) vs `PlanReActPlanner` tags.
10. Reflection: Self-Refine (~20% absolute) and Reflexion (91% vs 80% pass@1).
11. Why loops fail: cost, non-termination and compounding error. Introduce pass^k from τ-bench.
12. The four catalogs as maps of the same territory: Ng 4, Anthropic 5+1, Gulli 21, GCP 12.

**Section 3 — ADK fundamentals (13–20)**
13. ADK in one picture: Agent, Runner, Session, Events, Services. History: 0.1.0 on 2025-04-09, 1.0 on 2025-05-20, 2.0 on 2026-05-19.
14. Five lines to an agent: `adk create`, then `agent.py`, then `adk web` (Python 3.11+, per C1).
15. Anatomy of `Agent(...)`: identity, brain, hands. Default model `gemini-3.5-flash`.
16. The Runner event loop in 7 steps. The commit-after-yield rule.
17. Four shelves of state: `temp:` ⊂ session ⊂ `user:` ⊂ `app:`.
18. Session vs State vs Memory vs Artifacts, as a 2×2 grid.
19. Callbacks: the hook timeline and the return-None contract.
20. The `App` envelope: plugins, caching, compaction, resumability.

**Section 4 — Tools and protocols (21–28)**
21. The tool zoo: function, built-in, Cloud toolsets, OpenAPI/MCP/Toolbox, integrations.
22. AgentTool vs transfer vs task mode: who holds the baton afterwards.
23. The one-built-in rule and how to escape it (`bypass_multi_tools_limit`).
24. MCP both ways: `McpToolset` (`tool_filter`) and `to_mcp_server`. MCP 2026-07-28 is stateless.
25. Databases without secrets in prompts: MCP Toolbox v1.15.0 and `tools.yaml`.
26. A2A: Agent Card at `/.well-known/agent-card.json`, then a task state machine. v1.0.0 (2026-03-12), AAIF member since 2026-08-17.
27. The protocol stack: MCP / A2A / AG-UI / A2UI / AP2 (G7).
28. OAuth in 7 steps (`adk_request_credential`).

**Section 5 — ADK 2.0: graphs (29–37)**
29. From tree to graph: "A graph is an agent." (Go 2.0 blog).
30. Why deterministic routing: 5,152 → 2,265 tokens and 7.2 s → 5.7 s (illustrative).
31. Sequence: `Workflow(edges=[("START", a, fn, b)])`, with data flowing through `node_input`.
32. Routing: `Event(route=…)`, dict edges, `DEFAULT_ROUTE`, and `ClassifierNode` (2.13).
33. Fan-out/fan-in: tuple fan-out plus `JoinNode`, which emits a dict keyed by node name. Also `parallel_worker=True`.
34. Loops as back-edges, and why cycles are not bounded automatically.
35. Dynamic workflows: `@node` + `ctx.run_node`, `rerun_on_resume=True`, auto-checkpointing.
36. Collaborative teams: chat / task / single_turn. Task nodes in graphs since 2.5 (C2).
37. Choosing a mechanism: "who decides the next step?" (codelab L5).

**Section 6 — Context and memory engineering (38–43)**
38. "Context is a compiled view": the tiered model (G2).
39. Compaction and caching: shrinking the bill for long sessions.
40. Skills L1/L2/L3: progressive disclosure, with a snippet.
41. Memory Bank: save from `after_agent_callback`, recall with `preload_memory`.
42. Artifacts and the handle pattern for large data.
43. Live and bidi streaming: `LiveRequestQueue`, interruption, reconnecting after about 10 minutes.

**Section 7 — Reliability: HITL, durability, multi-agent trade-offs (44–49)**
44. Pause, ask, resume: `RequestInput` in handoff vs re-entry mode.
45. Tool confirmation, the `require_confirmation` predicate, and `LongRunningFunctionTool`.
46. Durability: checkpoints, `RetryConfig` (default 5 attempts, backoff from 1 s up to 60 s), idempotent nodes.
47. Migration gotchas from 1.x to 2.0: the Event schema, the 1.28+ reader rule, no `events.append`, no `BaseException`.
48. When multi-agent helps or hurts: +80.8% vs −70.0% (2512.08296), and Anthropic's 90.2% at 15× tokens.
49. How multi-agent systems fail: MAST's 14 modes in 3 categories.

**Section 8 — Quality: evaluation, observability, optimization (50–54)**
50. Why unit tests can't grade a chef: grade the trajectory and the final response.
51. EvalSets and criteria: EXACT/IN_ORDER/ANY_ORDER, ROUGE vs LLM judge, rubrics.
52. User simulation and pass^k: a τ-bench-style reliability test.
53. OTel traces: `invoke_agent` / `invoke_workflow` / `execute_tool` / `generate_content`. The 2.13 GenAI v2 schema.
54. The optimization flywheel: GEPA (35× fewer rollouts than GRPO) via `adk optimize`.

**Section 9 — Safety and production (55–60)**
55. Defence in depth: identity, in-tool policy, callbacks/plugins, Model Armor (fail-closed), sandbox, VPC-SC.
56. Security by design: CaMeL (77% vs 84% on AgentDojo), with the graph as a control-flow firewall.
57. Deploy: Agent Runtime (formerly Agent Engine), Cloud Run and GKE. agents-cli replaces Agent Starter Pack.
58. Case study, end to end: the ambient expense agent (Pub/Sub → $100 router → LLM review → HITL → eval).
59. State of the art, Oct 2026: release cadence (2.0→2.13 in about 5 months), protocols under AAIF, live-pulled benchmark board (date-stamped).
60. Where to keep learning: QR wall with the ADK2 codelab, adk.dev/llms.txt, adk-recipes, Kaggle guides and the Agent Factory.

---

## Slide ideas (critic's picks — the 8 slides most at risk of being wrong, with the visual that fixes them)
1. **"Which Python?"** A two-bar version strip: 2.0–2.11 accept 3.10, and 2.12+ need 3.11. Animate the bar edge moving at 2026-10-13.
2. **"Task nodes: the docs lag the code"**: a docs banner reading "disabled", stamped "fixed in 2.5.0" with the CHANGELOG line. This also teaches students to read changelogs.
3. **"RetryConfig defaults"**: a backoff curve (1→2→4→8→16 s, capped at 60 s, 5 attempts), with jitter shown as a shaded band.
4. **"MCP went stateless"**: a before/after sequence diagram. Before: initialize, then session id, then calls. After: each request carries `_meta` with version and capabilities, plus `server/discover`.
5. **"A2A grows up"**: a timeline running Apr 2025 launch → Jun 2025 LF → v0.3.0 2025-07-30 → v1.0.0 2026-03-12 → AAIF 2026-08-17.
6. **"More agents ≠ better"**: a diverging bar chart of +80.8% vs −70.0% by task type, with a 15× token badge.
7. **"Security by construction"**: CaMeL's dual-LLM data/control-flow split, morphing into an ADK graph whose routes are fixed in code.
8. **"Samples became recipes"**: a repo tree with deleted samples struck through, and links pinned to snapshot `f290c5ce`.

## Sources (primary, fetched 2026-10-23)
- PyPI: https://pypi.org/pypi/google-adk/json and https://pypi.org/pypi/google-adk/2.0.0/json
- CHANGELOG: https://github.com/google/adk-python/blob/main/CHANGELOG.md · README: https://github.com/google/adk-python
- Source files: `src/google/adk/__init__.py`, `workflow/_retry_config.py`, `agents/llm_agent.py`, `agents/sequential_agent.py`, `tools/mcp_tool/__init__.py`
- Docs: https://adk.dev/2.0/ , https://adk.dev/workflows/collaboration/ , https://adk.dev/skills/ , https://adk.dev/integrations/ag-ui/ , https://adk.dev/graphs/
- Blogs: https://developers.googleblog.com/en/why-we-built-adk-20/ , https://developers.googleblog.com/en/announcing-adk-go-20/ , https://developers.googleblog.com/en/architecting-efficient-context-aware-multi-agent-framework-for-production/ , https://www.anthropic.com/engineering/multi-agent-research-system , https://www.deeplearning.ai/the-batch/how-agents-can-improve-llm-performance/
- Protocols: https://modelcontextprotocol.io/specification/2026-07-28/changelog , https://a2a-protocol.org/latest/specification/ , https://aaif.io/blog/a2a-joins-aaif , https://a2ui.org , https://ap2-protocol.org , https://docs.ag-ui.com
- GCP patterns: https://docs.cloud.google.com/architecture/choose-design-pattern-agentic-ai-system
- arXiv (via the export API): 2201.11903, 2210.03629, 2302.04761, 2303.11366, 2303.17651, 2304.03442, 2305.04091, 2305.10601, 2305.18323, 2308.00352, 2308.08155, 2310.06770, 2310.08560, 2311.12983, 2312.04511, 2406.12045, 2410.10762, 2501.09136, 2503.13657, 2503.18813, 2506.08837, 2507.19457, 2510.04618, 2512.08296
- Crossref: https://api.crossref.org/works/10.1007/978-3-032-01402-3
