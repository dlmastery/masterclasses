# Industry practice: production agents in 2025–2026 (ADK and other frameworks)

Research date: 2026-10-23. Target: google-adk 2.13.0 (PyPI JSON checked 2026-10-23: `"version": "2.13.0"`).
Deck use: case-study slides, the "what top teams do" slide, the handout checklist, and the AgentOps/cost chapter.

**Reading rules**
- Every number below is quoted from the primary page named in the row. When a page gives no number, I write "no number given". I did not round, merge or estimate numbers.
- "Vendor-published" means the page belongs to the vendor that sells the platform (Google, Anthropic, LangChain, AWS). Treat those outcome numbers as marketing-grade.
- `[UNVERIFIED]` = I could not confirm it in a primary source.
- Older research for this deck already covers the core vendor guides (Anthropic "Building effective agents", multi-agent research system, context engineering, Manus, Cognition, OpenAI practical guide, LangChain State of Agent Engineering, OWASP agentic top 10). See `research-adk-platform/08-best-practices-2026.md` §0. This file does not repeat them. It adds named production systems, numbers, and the 2026 sources that file does not have.

---

## 0. One-slide summary (what industry actually does in 2026)

1. **Use one agent with few tools first.** Shopify, Vercel and Rippling all made the same move: fewer, more general tools, with instructions loaded just in time.
2. **Put state and control flow in code, not in the prompt.** Palo Alto Networks hit OOM errors when it ran 140 questions in one agent context. The fix was one question per call, state in a FastAPI orchestrator, and Pub/Sub for write-back.
3. **Use deterministic validators at every write.** Rippling ("what to do" comes from the LLM, "how to format it" comes from code), Google's zero-trust post (signed writes), and the Google Cloud polymorphic-schema post (a Cloud Run validator per field).
4. **Calibrate judges against humans before you trust them.** At Shopify, judge Cohen's κ went from 0.02 to 0.61, against a human baseline of 0.69.
5. **Layer your evals and make some of them block deploys.** Rippling: offline on every commit, 300–400 integration queries after merge, about 10 deploy-blocking scenarios, and continuous runs on production data several times a day.
6. **Treat cost as an equation you can decompose.** Uber: spend = users × sessions × turns × requests × tokens × price. Usage grew 9.4x while total spend stayed flat.
7. **Pick models per workload on a Pareto frontier, not by brand.** Uber, Zendesk ("cost per task, not token price") and Atlassian (Gemini Flash for volume, Claude for long work).
8. **Watch prompt and harness changes like code changes.** Anthropic's April 2026 postmortem: three small harness/prompt changes caused a quality drop that no eval caught.

---

## 1. Case-study index (24 entries)

| # | Company / system | Framework / platform | Date of source | Headline number (quoted) | Type |
|---|---|---|---|---|---|
| C1 | Palo Alto Networks — Document of Record agent | **ADK + Agent Engine**, RAG Engine, GKE, Pub/Sub | 2026-01-14 | "approximately 2.5 hours per DOR" before optimization; "140+" questions | Engineering post (co-written with Google) |
| C2 | Comcast — Xfinity Assistant | **ADK + Agent Runtime**, multi-agent | 2026-04-22 | no number given | Customer quote |
| C3 | Payhawk — Financial Controller Agent | **Agent Platform + Memory Bank** | 2026-04-22 | "reducing submission time by over 50%" | Customer quote |
| C4 | Gurunavi — "UMAME!" restaurant app | **Memory Bank** | 2026-04-22 | "will improve user satisfaction by 30% or more" (a forecast) | Customer quote |
| C5 | Color Health — Color Assistant | **ADK + Agent Engine/Runtime** | 2025-11-05 / 2026-04-22 | no number given | Customer quote |
| C6 | PayPal — agentic commerce | **ADK** dev UI/CLI tracing, AP2 | 2025-11-05 / 2026-04-22 | no number given | Customer quote |
| C7 | L'Oréal — Beauty Tech Agentic Platform | **ADK + MCP** | 2026-04-22 | no number given | Customer quote |
| C8 | Geotab — AI Agent Center of Excellence | **ADK** | 2025-11-05 / 2026-04-22 | no number given | Customer quote |
| C9 | Google ADK team — overnight optimization of ADK itself | Gemini 4 Argon in Antigravity `/goal` | 2026-10-13 | 6 proposals → "2 shipped, 4 rejected"; 158-turn run "65.6 s reduced to 56.1 s" | Engineering post |
| C10 | Google Cloud Applied ML — model-upgrade agent | ADK loop + autoraters (recommended) | 2026-07-16 | "hours instead of months" (no measured figure) | Engineering post |
| C11 | Kyndryl → Temporal × ADK integration | **ADK + Temporal** (durable execution) | 2026-04-20 | no number given | Engineering post |
| C12 | Uber — software factory cost program | In-house harnesses, MCP gateway, managed agents | 2026-08-27 | "weekly agentic requests grew 9.4x"; "Cost per session fell 52% from its June peak" | Engineering post |
| C13 | Uber — uReview AI code review | Multi-stage LLM pipeline | 2025-08-12 | "75%" useful; "~65,000" diffs/week; "~1,500 hours weekly" saved | Engineering post |
| C14 | Shopify — Sidekick | Custom agentic loop, GRPO | 2025-08-26 | judge κ "0.02 … to 0.61" (human "0.69") | Engineering post |
| C15 | Rippling — AI across every product | **LangChain Deep Agents** + LangSmith | 2026-06-01 | re-rankers cut context "100 to 500x"; ">1 million" users | Vendor case study |
| C16 | ServiceNow — GTM orchestration | **LangGraph** + LangSmith | 2025-11-17 | no number given (testing phase) | Vendor case study |
| C17 | Klarna — customer assistant | **LangGraph** + LangSmith | 2025-02-12 | "80%" faster resolution; "700 full-time staff" equivalent | Vendor case study |
| C18 | Zendesk — custom agent builder | **Claude Agent SDK** + Bedrock | page © 2026 | "1 million custom agent executions in the first seven weeks" | Vendor case study |
| C19 | Atlassian — Rovo / AI gateway | **Gemini Enterprise Agent Platform** gateway, GKE; Gemini + Claude | page © 2026 | ">5 million AI agents running … each month" | Vendor case study |
| C20 | Intercom — Fin | Bedrock + Claude, 15–20 LLM subcomponents | page © 2026 | "56%" average resolution in 30 days | Vendor case study (AWS) |
| C21 | Vercel — d0 text-to-SQL agent | AI SDK + Claude Opus 4.5 | 2025-12-22 | 274.8 s → 77.4 s; 80% → 100% on 5 queries | Engineering post |
| C22 | Gemini Enterprise fleet adopters (KPMG, Rede Américas, Grupo Boticário, Sami Saúde, others) | Gemini Enterprise / Agent Platform | list updated 2026-04-22 | KPMG "90% Gemini Enterprise adoption with over a hundred agents in the first month" | Vendor list |
| C23 | Google "Project Chrysalis" — governed self-evolving SRE agent | **ADK**, Model Armor, KMS, OPA | 2026-10-22 | **simulated**: P99 519.8 ms → 18.2 ms | Reference architecture (not production) |
| C24 | Databricks platform telemetry | Databricks (Agent Bricks) | © 2026 page; press 2026-01-27 | multi-agent systems "grew by 327% in less than four months" | Vendor telemetry |

---

## 2. Case studies in detail

### C1. Palo Alto Networks — Customer Intelligence "Document of Record" (ADK + Agent Engine) ★ best ADK case for the deck
Source: https://cloud.google.com/blog/topics/partners/palo-alto-networks-customer-intelligence-agentic-design (2026-01-14; authors Spandan Mishra and Pavan Madhira of PANW, with Google GSD AI Incubation and Professional Services).

**Problem.** Pre-sales teams build a "360-degree standardized view of the customer". Doing this by hand from Salesforce plus internal knowledge bases "could take days".

**Architecture, in order**
1. A Salesforce trigger calls a **FastAPI webserver on GKE**, which acts as the orchestrator.
2. The orchestrator pulls account metadata from Salesforce and prepares "a predefined list of over 140 standard questions".
3. The orchestrator sends questions to **Vertex AI Agent Engine** (two ADK agent endpoints) "in batches of five", multi-threaded, so that Agent Engine scales horizontally.
4. **Gemini 2.5 Flash** rewrites each question. Both agents then query **Vertex AI RAG Engine**, with Vertex AI Search as the backend over GCS documents.
5. Each agent answers on its own and gives a relevance score: the "proportion of the claims in the answer that are grounded in the facts". The orchestrator keeps the better answer.
6. A verification step labels each answer with **low / medium / high** confidence for the human reader.
7. The finished document goes to **Pub/Sub**, and a separate service writes it back to Salesforce.

**Numbers.** 140+ questions, batches of 5, 2 agent endpoints, 3 confidence levels. Runtime before optimization: "approximately 2.5 hours per DOR". The page does not give the runtime after optimization ("by a substantial margin").

**Lessons (the best ones for the deck)**
- Sending all 140 questions through one agent context caused **"Out of Memory" errors**. Fix: one question per agent call, with state kept in the orchestrator.
- Orchestrator and agent in the same GKE cluster gave "frequent pod crashes". Fix: run the orchestrator as its own service and the agent on a managed runtime.
- Parallelize I/O-bound LLM calls from the orchestrator. Use async messaging for write-back.
- Use the gaps as a signal. Weak answers show where documentation is missing.

**Slide line:** "A bounded per-item agent, a stateful orchestrator in code, grounded answers with confidence labels, and asynchronous write-back."

### C2–C8. Google Cloud customer quotes about ADK and Agent Platform
Sources: "Introducing Gemini Enterprise Agent Platform", https://cloud.google.com/blog/products/ai-machine-learning/introducing-gemini-enterprise-agent-platform (2026-04-22), and "More ways to build and scale AI agents with Vertex AI Agent Builder", https://cloud.google.com/blog/products/ai-machine-learning/more-ways-to-build-and-scale-ai-agents-with-vertex-ai-agent-builder/ (2025-11-05).

| Company | What they built (quoted or close paraphrase) | Number |
|---|---|---|
| **Comcast** | "rebuilding Comcast's Xfinity Assistant with Agent Development Kit (ADK)… deploy a sophisticated multi-agent architecture that increases digital containment" | no number given |
| **Payhawk** | Financial Controller Agent with Memory Bank "remembers a user's habits to auto-submit expenses" | "reducing submission time by over 50%" |
| **Gurunavi** | "UMAME!" restaurant discovery. The agent "remembers a user's past actions and preferences" | "will improve user satisfaction by 30% or more" (a forecast, not a measurement) |
| **Color Health** | Color Assistant (ADK, scaled on Agent Runtime) checks screening eligibility, connects patients to clinicians, and schedules care | no outcome number given |
| **PayPal** | Uses the "ADK CLI and visual tools to inspect agent interactions, follow state changes, and manage multi-agent workflows". Also uses AP2 for agent payments | no number given |
| **L'Oréal** | "Beauty Tech Agentic Platform"; ADK agents connected "through Model Context Protocol (MCP)… to our single sources of truth" | no number given |
| **Geotab** | ADK is "the framework for our AI Agent Center of Excellence… a single, governable path to production" | no number given |
| **Burns & McDonnell** | An ADK agent that "turns decades of project data into real-time, actionable intelligence… combining deterministic business rules with probabilistic reasoning" | no number given |

Platform numbers from the same 2026-04-22 post: "More than six trillion tokens are processed monthly on Gemini models through ADK"; Agent Runtime "delivers sub-second cold starts"; agents can "run autonomously for days at a time". The 2025-11-05 post says ADK was downloaded "over 7 million times".
**Teaching point:** most Google ADK customer evidence is short testimonials without architecture or metrics. Use C1 (PANW) and C9 (the ADK team itself) for engineering depth. Say this openly on the slide.

### C9. Google ADK team — "Optimizing a 200,000-line Python codebase overnight with Gemini 4 Argon"
Source: https://developers.googleblog.com/en/optimizing-a-200000-line-python-codebase-overnight-with-gemini-4-argon/ (2026-10-13; George Weale, Bo Yang, Andrew Biernat).
- **Target:** the ADK Python codebase itself, "About 205,000 lines… nearly 800 source files", with 16,892 unit tests run.
- **Setup:** Round 1 used a single-paragraph prompt with no repo guidance. Round 2 used a `/goal` prompt and asked for an *unmerged PR with before/after numbers*. The repo's `.agents/skills` `SKILL.md` index pointed to `references/` files. Argon read 12 guideline files before it edited any code.
- **Run:** It built a baseline on 4 workloads (startup, a 200-step conversation, a 20-sub-agent handoff, a 12-node workflow), 30 runs each. It then proposed 6 optimizations across 32 files. It found a bug in its own multi-agent cache and reran all tests. The run took 11 hours unattended.
- **Result:** maintainers "shipped 2 changes and rejected 4". Cold `import google.adk` was "21% faster". Session preparation was "about 40% lower in long sessions". A 158-turn run went from "65.6 s reduced to 56.1 s".
- **Gotchas found:** a rejected import-removal passed all 16,892 open-source tests but "25 internal Google test targets failed" (lazy imports break `mock.patch` targets). A 17% multi-agent cache gain held only on a synthetic benchmark and was rejected. Round 1 changed a public JSON schema.
- **ADK ops tip from the post:** "send a warm-up request before taking live traffic, so the first user doesn't pay the one-time import cost."
- **Slide line:** "The agent explores, the maintainer subtracts." Use a holdout benchmark the agent never sees (`bench_turn.py`).

### C10. Google Cloud Applied ML — agentic model upgrades
Source: https://cloud.google.com/blog/products/compute/lessons-in-accelerating-foundation-model-upgrades (2026-07-16; Radhika Mani, Ting Liu).
- **Evolution:** hands-on discovery, then a rigid automated workflow ("too rigid for different data formats and edge cases"), then a flexible agent. The post says this "completes model upgrades in hours instead of months" but gives no measured figure.
- **Recipe given:** (1) deploy **autoraters** in place of manual review, (2) build an agentic loop with **ADK** on Agent Platform, (3) orchestrate with Antigravity.
- **Partner example:** a dubbing team gave the system a ground-truth set and a baseline prompt. It "autonomously hill-climbed the prompt quality", and the service moved off a fine-tuned custom model.
- **Teaching point:** the next model migration is coming in weeks, not years. "Since 2023, we've announced six major model evolutions." Your eval set is what makes migration cheap.

### C11. Kyndryl and Temporal — durable ADK agents
Sources: https://temporal.io/blog/google-adk-temporal-integration-bts (2026-04-20, Tim Conley and Drew Hoskins); docs https://docs.temporal.io/develop/python/integrations/google-adk (labeled "Pre-release").
- **Kyndryl's first version:** ADK agents ran as HTTP services. Each Temporal Activity wrapped "one A2A JSON-RPC request". This gave durability only at the agent-call boundary.
- **Official integration:** "the agentic loop runs in the Workflow, and each LLM call and tool call is its own Activity." A failed LLM call retries "that exact call with the same context history and same inputs", not the whole agent.
- **Upstream change needed:** ADK time and UUID calls were moved behind `google.adk.platform.time` / `uuid` so that replay is deterministic.
- **Quote for the slide:** "The agentic loop is actually a deterministic sequence of non-deterministic things."
- Production numbers for Kyndryl: none given.
- Runnable code is in §4.3.

### C12. Uber — "Running a Software Factory Efficiently at Uber Scale" ★ best cost case
Source: https://uber.com/us/en/blog/efficient-software-factory (2026-08-27; Uday Kiran Medisetty).
- **Scale:** "More than 70% of pull requests are attributed to local or cloud agents". "Over 3,600 agent skills", ">30K skill executions per day". Weekly active users grew 7x and weekly agentic requests grew 9.4x (Feb–Aug 2026). "Total AI spend has been relatively stable since April."
- **Unit cost:** cost per 1,000 model requests fell about 34% from peak. Cost per session fell 52% from the June peak.
- **The equation:** `Total spend = users × sessions/user × turns/session × requests/turn × tokens/request × price/token`.
- **Levers, with Uber's numbers:**
  - Subagents default to a cheaper model. The post calls this "the most impactful lever".
  - Automatic compaction at **400K tokens**, even on 1M-context models.
  - Reasoning effort defaults to **Medium**.
  - Interactive prompt-cache TTL moved from **5 min to 1 h**, because idle gaps were invalidating the cache. Subagents keep 5 min.
  - MCP tool schemas cost "about 50K–70K tokens for 100+ tools". Fixes: CLI tool resolution through a gateway, and on-demand tool search.
  - **Code mode:** one SQL example went from 903 to 402 tokens. A wide-table query went from 1,431,594 to 900 tokens. There are 25+ pre-built code-mode skills.
  - **Grounding** via an AI Context Graph (24M nodes, 80M edges). A grounded query took 38 s and was correct. The ungrounded one took 20 min and was wrong.
  - **Budgets without hard caps:** a live cost counter in the status line, Slack nudges at 50/80/100% of expected spend, manager sign-off for tier upgrades, and a dashboard that flags **16 anti-patterns** (for example "Opus use for simple tasks", "oversized MCP payloads").
- **Model selection:** build a benchmark from real work, run it on a model-agnostic harness, move to the Pareto-optimal model, and re-check "every few weeks".

### C13. Uber — uReview (AI code review at scale)
Source: https://www.uber.com/en-US/blog/ureview/ (2025-08-12).
- **Pipeline:** filter low-signal files → three generators (Standard, Best Practices, AppSec) → **a second prompt scores confidence, with thresholds per assistant, language and category** → semantic de-duplication → a category classifier suppresses categories with low historical value → inline comments with Useful/Not Useful buttons → Kafka → Hive.
- **Models:** the best F1 came from Claude-4-Sonnet as generator with o4-mini-high as grader. The runner-up was 4.5 F1 points lower.
- **Numbers:** "~65,000" diffs/week, ">90%" analyzed, 75% of comments marked useful, >65% addressed (human comments: 51%), 4-minute median CI review, "~1,500 hours weekly" saved.
- **Lessons:** "Precision Is More Valuable than Volume". Single-shot prompting produced hallucinations and duplicates; generate → grade → filter fixed it. Style nits score poorly. Run in CI, not the IDE.

### C14. Shopify — Sidekick
Source: https://shopify.engineering/building-production-ready-agentic-systems (2025-08-26; Andrew McNamara, Ben Lafferty, Michael Garner; ICML 2025 talk).
- **Tool-count bands:** 0–20 tools give clear boundaries. At 20–50, boundaries blur. At 50+, "multiple ways to do the same task". They call the failure mode "Death by a Thousand Instructions".
- **Fix:** **just-in-time instructions** returned *with tool results*. This keeps the system prompt cache stable and the guidance local.
- **Evals:** Ground-truth sets come from sampled real conversations, labeled by at least 3 experts. Judge κ rose from 0.02 to 0.61, against a human ceiling of 0.69. Test: randomly swap a human into the judge group; if people cannot tell which is the judge, the judge is trustworthy.
- **Merchant simulator** for pre-production A/B. **GRPO** with "N-Stage Gated Rewards" (procedural checks plus LLM judges).
- **Reward hacking seen:** opt-out hacking, tag hacking, made-up IDs and enum values. After the fixes, syntax validity went from about 93% to about 99%, and judge correlation from 0.66 to 0.75.
- **Advice:** "Avoid multi-agent architectures early."

### C15. Rippling — AI-native in 6 months (LangChain Deep Agents)
Source: https://www.langchain.com/blog/how-rippling-went-ai-native-across-every-product-in-6-months-with-deep-agents-and-langsmith (2026-06-01).
- **Topology:** a supervisor with 5–7 subagents. *Read* agents (HR, payroll, IT, finance, plus Salesforce, Carta and GitHub), *RAG* agents (handbooks, policies), and *Action* agents (bonus uploads, title normalization).
- **Context:** a semantic-layer search finds the domain, then a **scoped skill is injected** through middleware. Re-rankers cut context **100–500x**. The data spans thousands of tables and hundreds of thousands of fields.
- **Variable pinning:** a REPL variable store lets the agent refer to named variables instead of raw IDs, because "LLMs hallucinate when reciting long alphanumeric IDs".
- **Deterministic formatting:** Action agents use sandboxed code to turn CSVs into the formats internal tools expect.
- **Eval layers:** offline mocks on every commit → 300–400 post-merge integration queries on a full sandbox → about 10 **deploy-blocking** scenarios → continuous production runs several times a day. A **self-healing loop** pulls failing traces, an agent proposes fixes, evals rerun, and a human merges the PR.
- **Quote:** "Build the systems that LLMs are already familiar with" (SQL, code execution).

### C16. ServiceNow — GTM orchestration layer (LangGraph)
Source: https://www.langchain.com/blog/customers-servicenow (2025-11-17).
- A supervisor covers 8 customer-journey stages. Subgraphs are composed into larger graphs. Map-reduce uses the `Send` API. Engineers can pause, approve, rewind, or restart a step with new inputs.
- **Per-agent custom scorers** with thresholds. RAG agents are scored on chunk relevancy and groundedness. **Runs that pass the thresholds are added to the golden dataset automatically.**
- Status: testing with QA engineers. No numbers given.

### C17. Klarna — customer assistant (LangGraph)
Source: https://www.langchain.com/blog/customers-klarna (2025-02-12).
- "Over 85 million active users". "2.5 million conversations to date". Work "equivalent to 700 full-time staff". "Reduced average customer query resolution time by 80%". About 70% of repetitive tasks automated.
- Architecture: controllable graph routing, scenario-specific prompts that cut tokens and latency, and test-driven development with LangSmith.
- Caution: press reports in 2025 said Klarna later hired human support staff again. `[UNVERIFIED — not checked in a primary source]`. Use this as a discussion prompt, not as a fact.

### C18. Zendesk — custom agents on Claude
Source: https://claude.com/customers/zendesk (no date on page; © 2026).
- **Build:** a five-person team used Claude Code and the Claude Agent SDK. Claude Sonnet 4.6 runs on Amazon Bedrock in Zendesk's AWS regions. Models are chosen with an internal system that scores **15 metrics**.
- **Routing:** simple requests use one call. Hard tasks plan first. After each run the agent "saves what it learned as a reusable skill".
- **Numbers:** "1 million custom agent executions in the first seven weeks". "Up to 80% reduction in human handle times". "Up to 10% increase in automated resolution". Four months from PoC to early access. Setup takes about 30 minutes.
- **Lesson:** "Judge models by cost per task, not token price." A competitor model needed 4–5 planning turns where Sonnet often needed 1.

### C19. Atlassian — Rovo on a multi-model gateway
Source: https://claude.com/customers/atlassian (no date on page; © 2026).
- An AI model gateway built on **Gemini Enterprise Agent Platform** as the primary routing path, on GKE with GPUs and TPUs.
- **Gemini Flash** is the default for high-volume customer agents. **Claude** handles complex, long-running work. Teams benchmark quality and cost before they deploy.
- "More than 5 million AI agents running in customer business workflows each month". "Over 350,000 customers".
- Quote: "A long-term roadmap in the world of AI is probably no more than three months these days." Design so you can swap models.

### C20. Intercom — Fin
Source: https://aws.amazon.com/solutions/case-studies/intercom-anthropic/ (no date; © 2026).
- "15–20 different subcomponents, each paired with a specific large language model". These cover answer verification, policy compliance and generation.
- "56%" average resolution within 30 days of deployment. Top customers reach "80–90%". Over 4,000 customers.
- Pricing of $0.99 per resolution appears only in third-party reviews `[UNVERIFIED on an Intercom page]`. It is a good example of outcome-based pricing.

### C21. Vercel — d0: "We removed 80% of our agent's tools"
Source: https://vercel.com/blog/we-removed-80-percent-of-our-agents-tools (2025-12-22; Andrew Qu).
- **v1:** 17 specialized tools and heavy prompt and context engineering. **v2:** a file-system agent that greps the semantic layer (YAML/MD/JSON) with Unix tools. The code sample shows 2 tools: `ExecuteCommand`, `ExecuteSQL`.
- **On 5 test queries:** 274.8 s → 77.4 s (3.5x). 4/5 → 5/5 correct. About 102k → 61k tokens. About 12 → 7 steps. The worst v1 case was 724 s, 100 steps and 145,463 tokens, and it still failed.
- **Caveat the post gives:** this worked because the semantic layer was well named and documented. **Caveat for the deck:** n = 5 queries.

### C22. Gemini Enterprise and Agent Platform fleet adopters
Source: https://cloud.google.com/transform/101-real-world-generative-ai-use-cases-from-industry-leaders ("1,302 real-world gen AI use cases", updated 2026-04-22).
- **KPMG:** "90% Gemini Enterprise adoption with over a hundred agents in the first month".
- **Rede Américas:** contract comparison, "estimates an 80% reduction in manual analyst effort".
- **Sami Saúde:** attendance-sheet analysis went from "hours to under 15 minutes". Authorization reviews went "from 30 minutes to 3".
- **Grupo Boticário:** "reducing stockouts by up to 40%". Planning time went "from 49 hours to 3".
- **TCS:** "more than 3,000 industry-focused AI agents".
- **Zazzle:** "uses Gemini ADK and CCaaS" for chat-based product discovery. No number given.
- **Temporal:** an ADK integration "for mission-critical use cases that require strong execution guarantees".
- **Red Hat Lightspeed Agent** and **Dynatrace** are built on **A2A** into Gemini Enterprise.
- Next '26 numbers (GE Appliances "more than 800 AI agents", Tata Steel "more than 300") are already in `research/08-video-community.md`.

### C23. Project Chrysalis — governed, self-evolving SRE agent (reference architecture, **simulated**)
Source: https://developers.googleblog.com/architecting-governed-self-evolving-ai-agents-on-gemini-agent-platform/ (2026-10-22; Anant Nawalgaria).
- An ADK supervisor router triages a simulated cache stampede. A hotpatch must pass 3 gates before it mounts. Step-level Shapley attribution (AgentEvolver) assigns credit to each action. A new specialist agent is added to the graph **only after human approval**.
- **Governance chain:** Model Armor on ingress, AST sandboxing, Cloud KMS signing with Binary Authorization, OPA policy (SLA floor 10.0 req/s), dual-custody sign-off by SREs, and Cloud Logging.
- **Simulated numbers:** time to mitigation went "15 to 45 minutes down to 1.8 seconds". P99 went "519.8 ms down to 18.2 ms".
- **Gotcha for the deck:** the chosen policy uses 5.0 req/s, which is below the post's own 10.0 req/s OPA floor, and the post does not explain this. Use it as an exercise: "find the policy conflict".

### C24. Databricks — platform telemetry
Source: https://www.databricks.com/resources/ebook/state-of-ai-agents (© 2026). Press coverage dated 2026-01-27.
- "multi-agent systems … grew by 327% in less than four months".
- "Companies that use evaluation tools get nearly 6x more AI projects into production". With AI governance it is "over 12x more".
- From press coverage only: telemetry from 20,000+ organizations, and 77% of customers use 2+ models `[UNVERIFIED on the Databricks page]`.
- Caution: this is correlation, not causation. Teams that already ship may simply adopt evals more.

---

## 3. Patterns that recur across the cases

| Pattern | Seen in | ADK 2.13 mechanism |
|---|---|---|
| Bounded agent per item; state and loop in code | PANW, Temporal, Rippling | Workflow graph / FunctionNode orchestrator; one `run_async` per item; `output_key` into state |
| Few general tools, instructions loaded just in time | Shopify, Vercel, Rippling, Uber (tool search) | Skills / `SkillToolset`; `McpToolset(tool_filter=[...])`; instructions returned inside tool results |
| Deterministic validation at write boundaries | Rippling, GC polymorphic-schema post, zero-trust post, Uber uReview grader | `before_tool_callback`, `output_schema`, FunctionNode validator, `require_confirmation` |
| Generate → grade → filter | uReview, PANW (two agents + groundedness), Intercom (verification subcomponents) | Workflow: LLM node → judge node → route |
| Layered evals, some blocking deploys | Rippling, ServiceNow, Zendesk (15 metrics) | `adk eval` / pytest in CI; user simulation; Agent Platform eval |
| Judges calibrated to humans | Shopify | Custom metric plus a human-label agreement check (yours to build) |
| Pareto model choice per workload; cheap subagents | Uber, Zendesk, Atlassian | Per-agent `model=`; `FallbackModel` (2.x); LiteLLM |
| Cache and compaction as cost levers | Uber (1 h TTL, 400K compaction) | `ContextCacheConfig`, `static_instruction`, `EventsCompactionConfig` |
| Durable execution | Temporal/Kyndryl, PANW Pub/Sub | Temporal plugin; `ResumabilityConfig`; Agent Engine sessions |
| Memory as a product feature | Payhawk, Gurunavi | `VertexAiMemoryBankService`, `preload_memory` / `load_memory` |
| Multi-model gateway | Atlassian, L'Oréal ("multi-LLM flexibility") | LiteLLM / Model Garden; Agent Gateway |
| Human merges, agent proposes | ADK team (2 of 6 shipped), Rippling self-healing | `RequestInput`; PR-as-artifact |

---

## 4. Runnable ADK code for the patterns above

> **VERIFIED against google-adk 2.13.0 source (tag v2.13.0) by the verifier on 2026-10-23** for §4.1, §4.2, §4.4 and §4.5 (`InMemoryRunner(app=)`, `static_instruction` accepts `str` via `types.ContentUnion`, `ContextCacheConfig`/`EventsCompactionConfig` fields and pair validators, agent-level `before_tool_callback(tool, args, tool_context)`). §4.3 is verified against `temporalio` 1.34.0. `hr_db`, `payroll`, `issue_refund` and `rag_tool` are placeholders you supply.

APIs were checked against `google/adk-python` `main` source on 2026-10-23: `apps/app.py`, `apps/_configs.py`, `agents/context_cache_config.py`, `agents/llm_agent.py`, `plugins/__init__.py`, `plugins/reflect_retry_tool_plugin.py`. Model IDs are placeholders. Check them against the current Gemini model list before the lecture.

### 4.1 PANW pattern: an orchestrator in code, one bounded agent call per question, 5 in flight
```python
import asyncio
from google.adk.agents import LlmAgent
from google.adk.apps.app import App
from google.adk.runners import InMemoryRunner
from google.genai import types

answerer = LlmAgent(
    name="dor_answerer",
    model="gemini-2.5-flash",
    static_instruction="Answer ONE customer question from retrieved facts. "
                       "Return 'UNKNOWN' if the facts do not support an answer.",
    # tools=[rag_tool],   # e.g. a Vertex AI RAG Engine retrieval tool
)
app = App(name="dor", root_agent=answerer)
runner = InMemoryRunner(app=app)
sem = asyncio.Semaphore(5)            # PANW: "batches of five"

async def answer(q: str) -> tuple[str, str]:
    async with sem:
        s = await runner.session_service.create_session(app_name="dor", user_id="dor")
        final = ""
        async for ev in runner.run_async(
            user_id="dor", session_id=s.id,
            new_message=types.Content(role="user", parts=[types.Part(text=q)])):
            if ev.is_final_response() and ev.content and ev.content.parts:
                final = "".join(p.text or "" for p in ev.content.parts)
        return q, final                # a fresh session per question, so context never grows

async def build_dor(questions: list[str]) -> dict[str, str]:
    return dict(await asyncio.gather(*(answer(q) for q in questions)))
```
Teaching point: the document lives in **your** process, not in the agent's context. That is the fix for PANW's OOM error. On Agent Engine you call the deployed endpoint in the same way.

### 4.2 Uber cost levers in ADK: cache the stable prefix, compact long sessions, retry tool errors
```python
from google.adk.apps.app import App, EventsCompactionConfig
from google.adk.agents.context_cache_config import ContextCacheConfig
from google.adk.plugins import ReflectAndRetryToolPlugin

app = App(
    name="support",
    root_agent=root_agent,                       # put the long policy text in static_instruction
    context_cache_config=ContextCacheConfig(
        min_tokens=4096,      # Gemini 3 minimum is 4096 (2.5: 2048), per the source docstring
        ttl_seconds=3600,     # Uber moved interactive TTL 5 min -> 1 h
        cache_intervals=10),  # reuse the cache for up to 10 invocations (allowed range 1..100)
    events_compaction_config=EventsCompactionConfig(
        token_threshold=400_000,   # Uber compacts at 400K even on 1M-context models
        event_retention_size=10),  # keep the last 10 raw events
    plugins=[ReflectAndRetryToolPlugin(max_retries=2)],
)
```
Gotchas verified in source:
- `token_threshold` and `event_retention_size` **must be set together**. So must `compaction_interval` and `overlap_size`. You must set at least one pair, or a `ValueError` is raised.
- No cache is created on the first request of a session. Caching starts on turn 2.
- `ContextCacheConfig` has `extra="forbid"`, so a misspelled field raises an error.
- `ContextCacheConfig` defaults are `cache_intervals=10` and `ttl_seconds=1800`.

### 4.3 Temporal: durable ADK (Kyndryl pattern), verbatim from Temporal docs (pre-release)
VERIFIED against `temporalio` 1.34.0 source (tag `1.34.0`, `temporalio/contrib/google_adk_agents/__init__.py` exports `GoogleAdkPlugin`, `TemporalModel`; `workflow.py` L193 defines `activity_as_tool`). Note: on `sdk-python` `main` this module is now a compatibility shim that re-exports `temporalio.google_adk` from the new standalone package `temporalio-google-adk` (PyPI 0.0.1, 2026-10-07). Teach the 1.34.0 import path and mention the move.
```python
from datetime import timedelta
from temporalio import workflow
import temporalio.contrib.google_adk_agents.workflow          # activity_as_tool lives here
from temporalio.contrib.google_adk_agents import GoogleAdkPlugin, TemporalModel
from google.adk import Agent

@workflow.defn
class WeatherAgentWorkflow:
    @workflow.run
    async def run(self, prompt: str) -> str:
        weather_tool = temporalio.contrib.google_adk_agents.workflow.activity_as_tool(
            get_weather, start_to_close_timeout=timedelta(seconds=60)
        )
        agent = Agent(
            name="weather_agent",
            model=TemporalModel("gemini-2.5-flash"),   # each model call = an `invoke_model` Activity
            instruction="Use the get_weather tool to answer weather questions.",
            tools=[weather_tool],
        )
```
Worker setup: `plugin = GoogleAdkPlugin()`. Use the **same** plugin instance on Client and Worker. The Worker needs the model credentials (`GOOGLE_API_KEY`). Streaming is marked "experimental". The docs excerpt does not show import lines.

### 4.4 Zero-trust write gate (from Google's 2026-08-17 post, adapted to an ADK callback)
The post's rule is "System prompts are soft constraints". Enforce the refund ceiling in code:
```python
from typing import Any, Optional
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext

def refund_gate(tool: BaseTool, args: dict[str, Any], tool_context: ToolContext) -> Optional[dict]:
    if tool.name == "issue_refund":
        order_total = tool_context.state.get("order_total")      # set by trusted code, not the LLM
        if order_total is None or float(args.get("amount", 0)) > float(order_total):
            return {"status": "blocked", "reason": "refund exceeds order total"}  # skips the tool
    return None                                                   # None = allow the call

agent = LlmAgent(name="refunds", model="gemini-2.5-flash",
                 tools=[issue_refund], before_tool_callback=refund_gate)
```
Callback signature verified: `Callable[[BaseTool, dict[str, Any], ToolContext], Optional[dict]]` (`llm_agent.py`). The post's own demo uses an HMAC-signed payload and a gateway, not an ADK callback. The callback above is my adaptation, and the post contains no ADK callback code. Pair the callback with unit tests in CI, as the post recommends: test a blocked token, a blocked refund hijack, a blocked out-of-bounds UPDATE, and an allowed valid UPDATE.

### 4.5 Rippling "variable pinning" in ADK state (my adaptation of the pattern)
```python
def find_employee(name: str, tool_context: ToolContext) -> dict:
    """Look up an employee. Returns a short handle, never the raw ID."""
    emp = hr_db.lookup(name)                        # your code
    handle = f"emp_{len(tool_context.state.get('pins', {})) + 1}"
    pins = dict(tool_context.state.get("pins", {})); pins[handle] = emp.id
    tool_context.state["pins"] = pins
    return {"handle": handle, "title": emp.title}

def give_bonus(handle: str, amount: float, tool_context: ToolContext) -> dict:
    emp_id = tool_context.state["pins"][handle]     # the LLM never re-types a 24-char ID
    return payroll.bonus(emp_id, amount)
```

---

## 5. arXiv, last 3 months (2026-07-23 to 2026-10-23): industry-relevant results
Found with the Hugging Face papers search API (`huggingface.co/api/papers/search`) on 2026-10-23, because the arXiv API returned HTTP 429. IDs and dates come from that API. The summaries quote the abstracts. Preprints are not peer reviewed.

| arXiv | Date | Title | Practical takeaway (from abstract) |
|---|---|---|---|
| 2610.22732 | 2026-10-15 | TokenEconomizer: Experience-Driven Black-Box Cost Control for Coding Agents | An external controller that injects micro-skills, prunes "persistently irrelevant tools" and breaks failure loops cut token cost **18.4–30.9%** "with comparable task success" across Claude Code, Codex and Copilot CLI. This matches Uber's anti-pattern dashboard. |
| 2609.35760 | 2026-09-28 | TokenCast: Forecasting Token Consumption During LLM Agent Execution | Token use for the *same task* "can vary by over an order of magnitude across runs". Online forecasting used **21.3% fewer tokens** than a fixed-budget policy at matched completion. Budget per run, not per call. |
| 2609.26779 | 2026-09-22 | CliffCompaction: Cost-Efficient Compaction for Long-Horizon Coding Agents | Cost "up to 50%" lower under a bounded context. Two key rules: only truncate or drop, "never rephrasing", and "We never compact a compaction". A useful contrast with summarizing compaction (ADK's default summarizer *rewrites*). |
| 2610.12375 | 2026-10-08 | OnTrack: Real-Time Monitoring and Intervention in LLM Agent Trajectories | A streaming monitor costs about 1 ms per step. An abort policy saves "about 18% of compute" on failing runs, and "5 out of 6 aborts were correct". Kill doomed runs early. |
| 2610.25852 | 2026-10-19 | MASIF: Implicit Failures for Process Observability in Multi-Agent Systems | Implicit failures appear in **54.3% of successful** and 75.2% of failed multi-agent traces. Success-only metrics hide process rot. Inspect traces, not only outcomes. |
| 2610.13092 | 2026-10-09 | When Faster Decisions Do Not Make Better Agents | 4,500 executions. A faster, cheaper decision model lowered cost per attempt, but "Mean cost per successful outcome increases in one agent". Measure **cost per delivered outcome**. This matches Zendesk's "cost per task". |
| 2609.39982 | 2026-09-30 | Mid-Harness: Scaling Actions Between Model and Harness for Terminal Agents | Sampling 8 candidate actions and verifying them before execution raised Pass@1 from 50.00% to 68.03% with a strong verifier. With a weak verifier "more action sampling yields little benefit". |
| 2610.22350 | 2026-10-15 | FDE-Gym: The Last Mile of AI Delivery | 95 real delivery tasks from 18 sectors. The best configuration resolves "only 14 of the 95". "Discovering unstated constraints is the primary bottleneck." Requirements discovery is still a human job. |
| 2610.14539 | 2026-10-10 | FDE-Bench | 49 real customer projects. Best delivery score 0.5510 against an FDE reference of 1.0. Delivery success rate "only 6.12%". |
| 2610.27234 | 2026-10-19 | EGI-BENCH: An Enterprise General Intelligence Benchmark Suite | Eight enterprise agent benchmarks behind one CLI. "No single model dominates every capability axis". This supports per-workload routing (Atlassian, Uber). |
| 2610.07258 | 2026-10-05 | Lineage-Aware Memory Governance … in Enterprise AI Agents | Shared agent memory gated only by content leaked 18.8–25.5% across departments. Lineage-gated retrieval removed the leak and kept 81.5–82.6% reuse. Relevant to Memory Bank scoping (`user_id` / scope design). |
| 2609.35886 | 2026-09-27 | Agentic Commerce Bench: Measuring Fraud Detection for Agents That Spend Money | 20 fraud classes. Even after calibration, "eight of twenty classes no better than chance". Relevant to AP2 / PayPal-style agent payments. |
| 2609.30798 | 2026-09-25 | Evaluating Real-Time Voice Agents: From Component Quality to Grounded Outcomes | A survey of 38 sources. Evaluation is shifting to "verifying backend state rather than trusting what the agent claims". |

Removed by the verifier (2026-10-23): 2605.29893 "Redundant or Necessary?" was listed with an HF date of 2026-10-14, but the arXiv API gives v1 = 2026-05-28, outside the window.

Older but essential (outside the window; label it on the slide): **"Measuring Agents in Production"**, arXiv 2512.04123 (Dec 2025; ICLR/ICML 2026). It has 20 case studies and 306 practitioners. "68% execute at most 10 steps before requiring human intervention", 70% prompt off-the-shelf models, and 74% rely mainly on human evaluation (figures as given in search snippets; `[re-check against the PDF]`).

---

## 6. Vendor guidance dated 2026 (new beyond `research-adk-platform/08`)

| Vendor | Title | Date | URL | The one thing to take |
|---|---|---|---|---|
| Google Cloud | I/O '26 news for agent developers | 2026-05-19 | https://cloud.google.com/blog/topics/developers-practitioners/io26-news-for-agent-developers-on-google-cloud | "The graph model is worth the learning curve as soon as you have more than two branching paths." Start with Managed Agents. Port to ADK 2.0 when routing needs to be explicit. Collaboration modes: *chat*, *task*, *single-turn*. |
| Google Developers | Build zero-trust AI agents with ADK | 2026-08-17 | https://developers.googleblog.com/en/build-zero-trust-ai-agents-with-googles-agent-development-kit/ | "System prompts are soft constraints." Signed writes (KMS/HSM), gVisor sandbox (`--network=none`, 64 MB, 0.1 CPU, 5 s), security tests in CI, VPC-SC. |
| Google Cloud | Beyond Static Prompts: polymorphic multi-agent systems with ADK | 2026-07-01 | https://cloud.google.com/blog/topics/developers-practitioners/beyond-static-prompts-with-google-adk | Load only the schema needed for the current intent (about 20,000 → about 200 prompt tokens, an illustrative figure). Use a Cloud Run validator per field. Validate handoff state before sub-agents run. |
| Google Cloud | Three lessons in accelerating foundation model upgrades | 2026-07-16 | (C10) | Autoraters plus an ADK loop make model migration cheap. |
| Google Developers | Three layers, one repo: google/adk-recipes | 2026-10-15 | https://developers.googleblog.com/en/three-layers-one-repo-a-tour-of-googleadk-recipes/ | Every recipe ships `manifest.yaml`. Plugin skills ship `EVAL.yaml` with an **80% pass gate**, and setup stops below it. The post warns that recipes are "not production use". |
| Google Developers | Optimizing a 200,000-line Python codebase overnight | 2026-10-13 | (C9) | Hold out a benchmark the agent never sees. Run downstream test suites. Warm up servers before live traffic. |
| Anthropic | Quantifying infrastructure noise in agentic coding evals | 2026-02-05 | https://www.anthropic.com/engineering/infrastructure-noise | Resource configuration moved Terminal-Bench by **6 points** (p < 0.01). "leaderboard differences below 3 percentage points deserve skepticism". Set a guaranteed allocation *and* a separate kill threshold. |
| Anthropic | An update on recent Claude Code quality reports (postmortem) | 2026-04-23 | https://www.anthropic.com/engineering/april-23-postmortem | Three harness changes (effort high→medium, a caching bug that dropped thinking every turn, a ≤25-word verbosity prompt) caused a drop that passed review, tests and dogfooding. Fixes: per-model eval suite on **every** system-prompt change, soak periods, gradual rollout, and staff using the exact public build. |
| Anthropic | Scaling Managed Agents / Harness design (Apr / Mar 2026) | 2026 | already in `research-frontier/02` | (not repeated) |
| LangChain | Rippling, ServiceNow case studies | 2025-11 / 2026-06 | (C15, C16) | Layered, deploy-blocking evals. Successful runs feed the golden set. |
| Databricks | State of AI Agents | © 2026 | (C24) | Teams with evals and governance ship 6x and 12x more projects (correlation). |
| OpenAI | AgentKit status | 2026 | https://openai.com/index/introducing-agentkit/ (HTTP 403 for me) | A search snippet says OpenAI is winding down Agent Builder and Evals on **2026-11-30** and points code users to the Agents SDK. `[UNVERIFIED — page returned 403]`. Lesson for the deck either way: do not build on a vendor's no-code layer without an exit plan. |
| Hugging Face | — | — | — | I found no 2026 HF production-agent guidance in this pass `[gap]`. |

---

## 7. Best-practices checklist (42 items, each with its source)

**Architecture and scope**
1. Start with **one agent and at most 20 tools**. Treat 20–50 tools as a warning band and 50+ as a redesign. *Shopify C14.*
2. Before adding a tool, try replacing several with one general tool (bash/SQL/code) over well-documented data. *Vercel C21; Rippling C15 ("Build the systems that LLMs are already familiar with").*
3. Do not go multi-agent until a single agent fails measurably. *Shopify C14; Cognition (existing research).*
4. Move to an ADK **graph workflow** once you have more than two branching paths. *Google I/O '26.*
5. Keep the loop and accumulating state in code (Workflow nodes or an orchestrator service). Give each agent call one bounded item. *PANW C1; Temporal C11.*
6. Run the orchestrator and the agent runtime as **separate services**. *PANW C1 (pod crashes when they shared a cluster).*
7. Write back to systems of record **asynchronously** through a queue (Pub/Sub). *PANW C1.*
8. Wrap every LLM call and tool call so it is individually retryable (Temporal Activity or `ReflectAndRetryToolPlugin`). *Temporal C11; ADK source.*

**Context and tools**
9. Load instructions **just in time** with the tool result, not all up front. This keeps the cached prefix stable. *Shopify C14.*
10. Load only the schema or skill for the detected intent. Inject scoped skills. *GC polymorphic post; Rippling C15; Uber tool search C12.*
11. Count your MCP schema tokens. 100+ tools can cost 50K–70K tokens per request. Use `tool_filter` or tool search. *Uber C12; ADK docs ("Always supply tool_filter").*
12. Never make the model re-type long IDs. Pin them to short handles in state. *Rippling C15.*
13. Prefer code mode (a script that batches tool calls) for data-heavy tool chains. *Uber C12 (1,431,594 → 900 tokens).*
14. Ground the agent in a context graph or semantic layer before it searches. *Uber C12 (38 s correct vs 20 min wrong); Vercel C21 (works only with good docs).*

**Validation and safety**
15. Enforce business rules in code (`before_tool_callback`, validators). Do not rely on the prompt for them. *Google zero-trust post.*
16. Separate "what to do" (LLM) from "how to format or write it" (deterministic code). *Rippling C15.*
17. Use **generate → grade → filter**, with confidence thresholds per category. *Uber uReview C13.*
18. Show users a groundedness-based confidence label (low/med/high) instead of a bare answer. *PANW C1.*
19. Run generated code in a hardened sandbox: no network, capped memory and CPU, short timeout. *Google zero-trust post.*
20. Put security rules under unit tests in CI, so a prompt or model change cannot silently remove them. *Google zero-trust post.*
21. Scope shared memory by permission lineage, not only by owner or content. *arXiv 2610.07258.*

**Evaluation**
22. Build the eval set from **sampled real traffic**, labeled by at least 3 domain experts. *Shopify C14.*
23. Calibrate every LLM judge against human agreement (Cohen's κ). Stop when you approach the human ceiling. *Shopify C14 (0.61 vs 0.69).*
24. Layer evals: offline on every commit, integration after merge, ~10 deploy-blocking scenarios, continuous on production. *Rippling C15.*
25. Use per-agent custom scorers with thresholds. Add passing runs to the golden set automatically. *ServiceNow C16.*
26. Gate skill installs on an eval pass rate (`EVAL.yaml`, 80%). *google/adk-recipes.*
27. Keep a **holdout benchmark** the agent and prompt authors never see. *ADK team C9.*
28. Control eval infrastructure: a guaranteed allocation plus a kill threshold. Distrust gaps under 3 points. *Anthropic infra-noise.*
29. Score backend state (what actually changed), not the agent's claim of success. *arXiv 2609.30798; Uber uReview re-runs to check whether comments were addressed.*

**Cost and latency**
30. Decompose spend into users × sessions × turns × requests × tokens × price, and own each term. *Uber C12.*
31. Default subagents to a cheaper model and allow overrides. *Uber C12 ("most impactful lever").*
32. Match cache TTL to how users actually pause. Uber moved interactive TTL from 5 min to 1 h. In ADK, set `ContextCacheConfig.ttl_seconds` and put stable text in `static_instruction`. *Uber C12; ADK source.*
33. Compact before the window is full (Uber: 400K on 1M models). Prefer truncate/drop over rewriting summaries for faithfulness. *Uber C12; CliffCompaction 2609.26779.*
34. Measure **cost per successful outcome**, not cost per token or per call. *Zendesk C18; arXiv 2610.13092.*
35. Give users live cost visibility and soft nudges (50/80/100%) instead of hard caps. Flag anti-patterns automatically. *Uber C12; TokenEconomizer 2610.22732.*
36. Abort trajectories that look doomed early. A streaming monitor costs about 1 ms per step. *OnTrack 2610.12375.*

**AgentOps and rollout**
37. Run a broad per-model eval on every system-prompt or harness change. Add soak periods and gradual rollout. *Anthropic April 2026 postmortem.*
38. Have your own staff use the **exact** public build. *Anthropic postmortem.*
39. Roll out in phases with dashboards and in-product feedback buttons tied to prompt/model metadata. *Uber uReview C13; LinkedIn (secondary) `[UNVERIFIED primary]`.*
40. Re-benchmark the model choice every few weeks, because the Pareto frontier moves. *Uber C12; Atlassian C19 ("roadmap… no more than three months").*
41. Warm up agent servers before they take traffic. *ADK team C9.*
42. Let agents propose fixes from failing traces, and have a human merge. *Rippling C15; ADK team C9.*

---

## 8. What top teams do differently

1. **They measure judges before they trust them.** Most teams use a 0–10 "rate this" judge. Shopify reports κ against humans and a swap test. *(C14)*
2. **They make evals block deploys.** Rippling has about 10 deploy-blocking scenarios on real systems, not a dashboard someone looks at later. *(C15)*
3. **They treat cost as an engineering metric with an owner.** Uber has an equation, a 16-item anti-pattern dashboard, defaults (Medium effort, cheap subagents, 1 h cache) and a re-benchmark cadence. Usage grew 9.4x with flat spend. *(C12)*
4. **They remove things.** Vercel removed 80% of its tools. ADK maintainers shipped 2 of 6 agent proposals. uReview suppresses whole comment categories. Shopify warns about tool sprawl. *(C21, C9, C13, C14)*
5. **They keep the LLM away from the parts that must be exact.** IDs are pinned (Rippling), writes are signed (Google zero-trust), schemas are validated by code (GC polymorphic post), and refund ceilings are enforced outside the prompt.
6. **They design for swapping models.** Atlassian's gateway, L'Oréal's "multi-LLM flexibility", Zendesk's 15-metric rerun on every model release, and Google's autorater-driven migration agent. *(C19, C7, C18, C10)*
7. **They own durability.** Temporal's model is "a deterministic sequence of non-deterministic things". PANW uses Pub/Sub write-back and an external orchestrator. *(C11, C1)*
8. **They watch the harness as closely as the model.** Anthropic's postmortem shows that effort defaults, cache TTL logic and one verbosity line can each lower quality. Top teams version-control and eval these settings. *(Anthropic 2026-04-23)*
9. **They inspect traces, not only outcomes.** 54% of successful multi-agent traces still contain implicit failures (MASIF). ServiceNow found per-node inputs and outputs "significantly easier than parsing through logs". *(arXiv 2610.25852, C16)*
10. **They keep humans where the evidence says agents are still weak.** Requirements discovery (FDE-Gym: 14/95 tasks resolved), irreversible writes, and structural changes to the agent graph (Chrysalis needs dual sign-off).

---

## 9. Gotchas and challenges (one slide each, or a "war stories" carousel)

| Gotcha | Where seen | Fix |
|---|---|---|
| Agent context grows with each item → OOM | PANW C1 | One item per call; state in the orchestrator |
| Agent and orchestrator in one cluster → pod crashes | PANW C1 | Separate services; managed runtime |
| Tool sprawl beyond 20–50 tools | Shopify C14 | JIT instructions, fewer general tools |
| Hallucinated long IDs | Rippling C15 | Variable pinning |
| Reward hacking (opt-out, tag hacking, fake enums) | Shopify C14 | Procedural plus semantic gated rewards |
| Cache invalidated by user idle gaps | Uber C12 | Longer TTL for interactive sessions |
| A caching "optimization" dropped reasoning every turn | Anthropic postmortem | Broad per-model evals on harness changes; soak period |
| Lazy imports broke `mock.patch` in downstream tests | ADK team C9 | Run downstream suites, not only your own |
| Gains only on synthetic benchmarks | ADK team C9 | Holdout real-workload benchmark |
| Infra limits change eval scores by 6 points | Anthropic infra-noise | Guaranteed allocation + kill threshold; report the multiplier |
| Cheaper decisions cost more per success | arXiv 2610.13092 | Track cost per delivered outcome |
| `EventsCompactionConfig` fields given without their pair → `ValueError` | ADK source | Set `token_threshold` + `event_retention_size`, or `compaction_interval` + `overlap_size` |
| No context cache on turn 1; Gemini 3 needs ≥4096 tokens | ADK source docstring | Put a long stable prefix in `static_instruction`; expect savings from turn 2 |
| Vendor no-code layer retired | OpenAI AgentKit `[UNVERIFIED]` | Keep agents in code (ADK/SDK); keep evals portable |
| Self-evolving policy conflicts with its own SLA floor | Chrysalis C23 | Policy checks must run *after* optimization, not only before |

---

## 10. Slide ideas from this file

1. **"PANW in 7 boxes"**: animate Salesforce → FastAPI/GKE → 5 parallel Agent Engine calls → RAG → dual answers + groundedness → confidence label → Pub/Sub → Salesforce. Then show the red "OOM" overlay and the fix.
2. **"Uber's cost equation"**: six multiplying terms. Light up each lever with Uber's number (400K, Medium, 1 h, 50–70K, 903→402).
3. **"Fewer tools win"**: Vercel before/after bars (274.8 s → 77.4 s; 102k → 61k tokens). Note n = 5.
4. **"Judge calibration"**: κ 0.02 → 0.61 against the human line at 0.69 (Shopify).
5. **"The eval pyramid that blocks deploys"**: Rippling's four layers, with the self-healing loop.
6. **"2 of 6 shipped"**: the ADK team's overnight agent run and the maintainer's job of subtracting.
7. **"Three silent regressions"**: Anthropic postmortem timeline (Mar 4, Mar 26, Apr 16 → Apr 20).
8. **"Memory as product"**: Payhawk (>50% faster submission), Gurunavi (a forecast, so label it).
9. **"Durable ADK"**: a Temporal event-history diagram where each model call is an Activity, then a replay.
10. **"What the arXiv says this quarter"**: TokenEconomizer −18–31%, OnTrack −18% compute, MASIF 54% hidden failures, FDE-Gym 14/95.

---

## 11. Open items / unverified
- OpenAI AgentKit / Agent Builder wind-down date (2026-11-30): `[UNVERIFIED]`, page returned 403.
- Intercom $0.99 per resolution: third-party only `[UNVERIFIED]`.
- Klarna rehiring human agents: `[UNVERIFIED]`.
- LinkedIn Hiring Assistant architecture (supervisor + sub-agents): secondary sources only (ZenML, InfoQ abstract) `[UNVERIFIED primary]`.
- Databricks "77% use 2+ models" and "20,000 organizations": press only.
- PANW post-optimization runtime: not published.
- Zendesk, Atlassian and Intercom pages have no publication date. I list them as © 2026.
- "Measuring Agents in Production" percentages come from search snippets. Re-check them against arXiv 2512.04123 before the lecture.
- arXiv API and listing pages returned HTTP 429 during this run. Paper IDs and dates come from the Hugging Face papers API.
