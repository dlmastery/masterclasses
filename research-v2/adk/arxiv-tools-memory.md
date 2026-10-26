# arXiv sweep (2026-07-23 .. 2026-10-23): tool use and MCP, tool selection at scale, memory, self-improvement, agentic RL, computer-use, cost/latency

Compiled 2026-10-23 for the ADK 2.0 hands-on deck (google-adk 2.13.0).

**Method.** I ran arXiv API queries sorted by submittedDate (MCP, memory, self-improving, agentic RL, computer-use, cost/latency), plus 25 Hugging Face Papers API searches filtered to publishedAt >= 2026-07-23 (402 hits). I triaged the results by topic fit and practical impact. For each pick I read the abstract. For 8 papers I also read the arXiv HTML full text: 2610.23449, 2610.14334, 2609.35381, 2610.28577, 2610.22732, 2607.22798, 2609.27334, and the parts of the others cited below.

**Caveats.**
- All numbers are copied from the papers. They are preprints and have not been peer-reviewed.
- Model names such as "GPT-6 Astra" and "Claude Opus 4.8" appear as the papers report them.
- Where a field (usually affiliation) could not be read, it is marked [UNVERIFIED].
- None of these papers was in the older research folders. Those cited arXiv IDs only up to 2605.x.

ADK hooks named in the takeaways come from the existing deck research:
- `McpToolset(tool_filter=...)`
- `before_tool_callback` / `after_tool_callback` / `on_tool_error_callback` (as a plugin or on the agent)
- `App(events_compaction_config=EventsCompactionConfig(...))`
- `ContextCacheConfig`
- `load_memory` / `PreloadMemoryTool`
- `VertexAiMemoryBankService`
- `SkillToolset`
- `ComputerUseToolset`
- `require_confirmation`

Code is a sketch. Check callback signatures against `google/adk-python` `src/google/adk/plugins/base_plugin.py` before putting it on a slide.

---

## Ranked by practical impact (what an ADK engineer can change on Monday)

### 1. MCP error messages written for developers hurt the most capable agents most
- **arXiv:** 2609.35381 (v2). Submitted 2026-09-28.
- **Authors:** Xiaonan Xu (Georgia Institute of Technology) and Wenjing Wu (CU Boulder).
- **Problem:** Many MCP servers wrap human-facing APIs. Their errors say "run this command", "edit config", "open a web page" or "wait". A tool-only agent cannot do any of these, but it tries to obey anyway.
- **Method:**
  1. Audited 150 popular MCP servers and 3,001 error messages.
  2. Classified the "next step" sentence in each.
  3. Injected credential-expiry and rate-limit errors into Berkeley Function Calling Leaderboard (BFCL) tasks for 5 OpenAI models (24 scenarios × 3 runs).
  4. Compared four variants of the error text: original step, cause only, step rewritten to name a server tool, and step deleted by a one-sentence pre-filter prompt.
- **Key numbers:**
  - 949 of 3,001 errors prescribe a next step. Half of those depend on something the server cannot see.
  - Credential errors: 62 of 67 steps ask for a terminal command, a config change or a web page.
  - Expired credentials with a terminal-command step: mean recovery 45%. GPT-6 Astra drops to 6%. The loss grows from 18 points (GPT-5.5) to 69 points (GPT-6 Astra).
  - Cause only: 82%. Login tool named ("Call ticket_login first."): 84%. Step deleted by prompt: 82%.
  - Rate limit with GitHub's "Wait before retrying.": 6% recovery. Naming the call to repeat ("Wait a few seconds and call place_order again"): 88%.
- **Monday takeaway:**
  - If you own an MCP server or a `FunctionTool`, write each error as `<cause>. <call tool X with Y>`. Never write "run `cli --auth`".
  - If you consume third-party MCP servers, add an `after_tool_callback` / `on_tool_error_callback` plugin. It strips imperative "next step" sentences (one cheap Flash-Lite call or a regex) and keeps the cause.
  - For 429s, rewrite the message to "retry `<tool_name>` with the same args" and back off in code.
- **Limitations:**
  - OpenAI models only.
  - BFCL-style single tasks.
  - Two error classes (credentials, rate limit).
- **Slide idea:** "The error message is a prompt."
  - Left: the raw error text. Each sentence fades in, and the "Please run: reddit-mcp-buddy --auth" line flashes red.
  - Right: a bar chart (45% → 84%; 6% → 88%). The bars grow when the rewrite slides in over the original.

### 2. GatewayBench: unified capability and security evaluation for MCP gateways
- **arXiv:** 2610.23449. Submitted 2026-10-16.
- **Authors:** Yitian Zheng (Tsinghua), Zhaorun Chen (UChicago), Haoyu Li, Bo Li (UIUC).
- **Problem:** Enterprises put a gateway between the agent and many MCP servers. Nobody had measured how gateway design changes success, cost and attack resilience as the tool surface grows.
- **Method:**
  1. 524 tasks in 6 domains.
  2. A pool of 11,118 real tools from 251 MCP servers.
  3. Injects 0 to 1,500 task-irrelevant tools.
  4. Compares 7 gateways in two paradigms. **Flattened** exposes every tool in one list: AgentCore, Agentgateway, LiteLLM, Lunar MCPX. **Hierarchical** has the agent first discover or select a server or category, then the tools: Enkrypt, Strata, Bifrost.
  5. Runs benign and adversarial tasks (tool-injection and environment-injection) on the OpenAI Agents SDK and OpenClaw harnesses.
- **Key numbers:**
  - GPT-5.4 with 0 noise tools: flattened TSR 87.2% vs hierarchical 85.1%. Indirect attack success: 47.2% vs 30.9%.
  - Scaling to 1,500 tools: flattened TSR drops 87.2 → 83.3. Hierarchical stays at 85.1 → 85.6.
  - Tokens per turn: flattened ~8.3k → 233.3k. Hierarchical 9.1k → 12.6k.
  - Latency at 1,500 tools: flattened 64.1 s vs hierarchical 38.7 s. At 0 tools: 20.8 s vs 30.1 s.
  - With weaker GPT-5.1, hierarchical gateways "collapse" (TSR 47.5%; Enkrypt 23.3%). Their low attack success there is incapacity, not robustness.
- **Monday takeaway:**
  - Below ~50 tools, a flat list is fine and faster.
  - Above that, expose a two-level surface. In ADK, give each MCP server its own sub-agent (`AgentTool` or Workflow branch) with a `tool_filter`, so the root agent picks the server first.
  - Pair hierarchical routing only with a strong model.
  - Re-measure tokens per turn when tools are added. It is the canary metric.
- **Limitations:**
  - Results depend strongly on the model × harness pairing.
  - Gateways are tested in their default configurations.
- **Slide idea:** A two-panel animation.
  - Flat: the tool list scrolls down to 1,500 entries while a tokens-per-turn counter spins to 233k.
  - Hierarchical: a tree expands only one branch while its counter stays at 12.6k.
  - Finally, a crossover line chart of TSR vs. number of tools draws in.

### 3. Which metadata matters for LLM tool selection in MCP?
- **arXiv:** 2610.14334. Submitted 2026-10-09.
- **Authors:** Xiaofan Li (University of Delaware), Fengchun Qiao (USF), Xing Gao (Delaware).
- **Problem:** Models choose among functionally equivalent MCP tools from metadata alone. The paper asks which metadata field decides the choice.
- **Method:**
  1. Analyzed 367,174 MCP tool definitions.
  2. Ran controlled single-factor interventions (server name, tool name, description, parameter schema) with candidate positions balanced.
  3. Fit position effects with conditional logistic regression.
  4. Tested 5 models (GPT-5.4 mini, Claude Sonnet 4.6, Gemini 3.5 Flash, DeepSeek V4 Pro, Qwen3.7-Plus) on 5 tasks (send email, weather, create issue, place order, create PR).
- **Key numbers:**
  - The parameter schema is the strongest lever. Median 3-tool coefficient is 3.82 (log-odds) vs 1.48 for server name.
  - Separate top-level params beat grouped or composite ones. On Create Issue, the flat variant was chosen in 93.3–100% of trials.
  - Renaming `to` → `recipient_id` cut selection to 1–10%. `receiver` kept 35–51%.
  - Descriptions that explain params: 21 of 30 estimates significant, all positive.
  - Tool name: only 6 of 29 significant.
  - Position bias: with names-only differences, the first-listed tool won 92–100% of the time.
- **Monday takeaway:**
  - In ADK `FunctionTool`s, use flat, typed, well-named top-level parameters (no `params: dict`). Explain each one in the docstring, which becomes the description.
  - If you have near-duplicate tools across MCP servers, ordering decides the winner. Dedupe with `tool_filter` instead of hoping.
  - In evals, shuffle tool order.
- **Limitations:**
  - Single-turn English requests.
  - 5 tasks.
  - Effects vary by model.
- **Slide idea:** "Same function, different schema."
  - Two tool cards side by side. Morph `{"to": ...}` into `{"recipient_id": ...}`.
  - A selection-rate gauge drops from ~45% to ~5%.
  - Then a "first in list" spotlight sweeps over the cards to show position bias.

### 4. TokenEconomizer: experience-driven black-box cost control for coding agents
- **arXiv:** 2610.22732. Submitted 2026-10-15.
- **Authors:** Aaron J. Li et al. (Microsoft Research). Code: github.com/microsoft/TokenEconomizer.
- **Problem:** Agents that work repeatedly on the same repo pay the same environment-specific token costs every task.
- **Method:** An external controller that changes only the instruction prefix, the tool set and the event stream. It has three parts.
  - **Micro-skills.** Every 5 tasks, an LLM proposes at most 4 candidates from digests of the last 8 trajectories. Regex detectors confirm each candidate. A skill activates after 3 confirmations on non-overlapping files and is injected when its need rate is ≥ 0.4. It retires on contradictions (decay 0.8, contradiction weight 5).
  - **Tool pruning.** A tool never called for 3 consecutive tasks is dropped. An LLM judge also reviews the never-called tools. The full catalog is restored every 5 tasks for a re-audit.
  - **Failure-loop guard.** The turn budget is 1.25 × the p90 of turns on prior successful tasks. Rule triggers call an LLM judge, which needs confidence ≥ 0.7. The guard first redirects the agent, then terminates the run. A hard stop at 2.5 × budget applies when the strict stall rule holds.
- **Key numbers:**
  - Claude Code, Codex and Copilot CLI: average token cost −18.4% to −30.9% on SWE-Bench streams (277 tasks, 6 repos). Pass@1 rose in 4 of 5 settings and fell 1.0 point in the fifth.
  - Web-Bench: −16.0% to −21.2%. Security auditing: −6.4% to −19.6%.
  - Tool pruning is the largest single lever.
- **Monday takeaway:** You can build all three parts in ADK.
  - Tool usage counts in a plugin plus a dynamic `tool_filter` or toolset predicate (pruning).
  - A turn counter in `before_model_callback` that injects a "try a materially different approach" message at 1.25 × p90, then ends the invocation (loop guard).
  - Confirmed micro-skills as a `SkillToolset` skill or a static instruction block placed before the task (cache-friendly).
- **Limitations:**
  - Needs a success signal in production.
  - Can prune a needed tool. The re-audit mitigates this.
  - Only 3 harnesses tested.
- **Slide idea:** A cost waterfall. The bar falls in three steps (prune, then skills, then loop guard). Each step's mechanism icon pops in, and a "re-audit every 5 tasks" clock ticks.

### 5. Cache engineering for agents (AKV)
- **arXiv:** 2610.28577. Submitted 2026-10-20.
- **Authors:** Tianyu Fu et al. (Tsinghua NICS-EFC; corresponding author Yu Wang). Code: github.com/thu-nics/AKV.
- **Problem:** Summarizing or trimming history changes the prefix. This invalidates the KV cache and forces an expensive re-prefill, and over-trimming hurts accuracy.
- **Method:**
  - Leave the text trajectory unchanged and operate on the KV cache directly. `drop` excludes chosen entries from future attention. `repos` re-applies RoPE so the retained keys get contiguous positions.
  - Operations go in a `cache` field next to `messages` in the API request. A "Cache-As-Tool" variant lets the agent decide itself.
  - Policy: keep the KV of the latest 12 tool responses, drop older tool-response KV, and keep all reasoning KV.
  - The AKV serving engine keeps a stateless API while managing history-dependent cache states internally.
- **Key numbers:**
  - Versus threshold-triggered summarization (96K/192K): +1.7 average score and −27.7% average cost on BrowseComp-Plus, xbench-DeepSearch, GAIA-Text and SWE-bench Verified (MiniMax-M2.7, GPT-OSS-120B, MiroThinker-1.7-Mini).
  - About 1.18× output throughput and 1.51× better P95 latency.
  - A policy refined by recursive self-improvement saves a further 7.1%.
- **Monday takeaway:**
  - On a hosted Gemini API you cannot drop KV. The transferable lesson is: **old tool outputs are the cheapest thing to forget; keep reasoning.**
  - In ADK, prefer a rolling window that masks or truncates old *tool responses* (a `before_model_callback` or a context-filter plugin) over whole-history summarization.
  - Keep the stable prefix (`static_instruction`) at the front so `ContextCacheConfig` caching survives.
- **Limitations:**
  - Needs a self-hosted serving engine.
  - No agents were trained under this scheme yet.
  - Linear-attention models are not supported.
- **Slide idea:** A strip of KV blocks.
  - Summarization: the whole strip goes red ("re-prefill").
  - Cache engineering: only the old tool-response blocks grey out, and the reasoning blocks slide left (repos).
  - A cost meter falls by 27.7%.

### 6. StateAct: program state before pixels for long-horizon computer-use agents
- **arXiv:** 2607.22798. Submitted 2026-07-24.
- **Authors:** Yan Yang et al. (Salesforce AI Research).
- **Problem:** A screenshot is a lossy render of program state. Agents that drive by pixels are slow, expensive and hard to verify.
- **Method:**
  1. A code-first main agent (persistent bash, Python, file editor, plan checklist, delegation). It has no mouse.
  2. A GUI subagent is called only for "irreducibly visual" subgoals. A separate web subagent works on the DOM and JavaScript.
  3. Subgoals go to fresh-context subagents (about 4.2 per task, at most 50 turns each).
  4. An independent **finish gate** sees only the original task and read-only machine access, not the agent's history. It checks the deliverable for missing, unsaved, wrong-path or wrong-format output, with up to 3 correction rounds.
- **Key numbers:**
  - OSWorld 2.0 with Claude Opus 4.8: binary success 20.6% → 26.9%, partial 54.8% → 61.6%.
  - About $7.8 per task vs about $72 screenshot-only (about 9× cheaper).
  - GUI subagent used on 28 of 108 tasks, 1.1% of steps.
  - Code-only (no GUI) reaches 45.9% partial.
  - The gate correctly rejected 8 runs but passed 68 imperfect ones. It catches structure, not wrong values.
- **Monday takeaway:**
  - Do not reach for `ComputerUseToolset` first. Give the root agent code execution and API/DOM tools, and wrap the computer-use agent as an `AgentTool` that is called rarely.
  - Add a fresh-context verifier node to the Workflow that sees only the task and the artifact.
- **Limitations:**
  - One backbone.
  - 108 tasks.
  - No help on render-only tasks.
  - A weaker GUI model drops partial success to 43.2%.
- **Slide idea:** A diagram. The main agent ("code") sits in the centre, the GUI subagent is a small satellite that lights up only 1.1% of the time, and a gate sits at the exit. A $72 vs $7.8 price tag flips over.

### 7. Just-in-Time Memory (JitMem): curate memory at read time, not write time
- **arXiv:** 2609.27334. Submitted 2026-09-23.
- **Authors:** Yefan Zhou et al. (Salesforce AI Research; Shafiq Joty).
- **Problem:** Reflection, workflow and skill memories summarize at *write* time, before the future query is known. This loses information and makes credit assignment hard.
- **Method:**
  1. Store only raw successful trajectories (filtered by an LLM judge).
  2. At task start, retrieve top-k by BM25 on the task description.
  3. A curator LLM writes a compact, task-specific payload (relevant past experience, strategies, guidance) and prepends it to the executor prompt.
  4. Train the curator with GRPO on the same task's success (Qwen3-8B, 100 steps).
- **Key numbers:**
  - ALFWorld 77.4 vs SkillOS 61.2 (+16.2). WebShop 32.8 vs 16.5 (+16.3). τ²-bench 75.6 vs ReasoningBank 71.7 (+3.9).
  - The untrained curator already wins (ALFWorld 60.5 vs ReasoningBank 55.7).
  - It cuts executor tokens and steps. With a GPT-5.4 executor: 9.8K input tokens and 11.6 steps, vs 19.7K and 16.2 for ReasoningBank.
- **Monday takeaway:**
  - Store raw session traces (Memory Bank or your own store) and keep summaries out of the write path.
  - Add a "memory curator" step before the main agent: a cheap `LlmAgent` in a Workflow node that receives the retrieved traces and the new task and writes the payload into state.
  - The untrained curator is already competitive.
- **Limitations:**
  - BM25 may not scale.
  - One extra LLM call per task.
  - No gain on τ²-bench Airline and Retail.
- **Slide idea:** Two timelines.
  - Write-time: the trajectory is compressed into a tiny card at the end of the task, and information falls off.
  - JitMem: the raw trace is stored whole. When a new task arrives, a curator lens focuses it into a payload.
  - A bar chart shows +16 points.

### 8. Demystifying agent skills: why they work, until they don't
- **arXiv:** 2608.14036. Submitted 2026-08-14.
- **Authors:** Zhiyuan Jiang et al. (UC San Diego).
- **Problem:** Skills (SKILL.md-style packages) improve aggregate success, but nobody knows why or when they fail.
- **Method:**
  1. Controlled experiments across benchmarks, harnesses and LLMs.
  2. Varied representation, outcome annotation, retrieval difficulty and cross-framework transfer.
  3. 8,135 normalized trials, plus open coding of paired trajectories into 12 skill-use modes.
- **Key numbers:**
  - Skills beat Workflow Memory by 6.06 points.
  - 65.7% of the wins are "procedural anchoring" (stabilizing action). Only 4.5% are knowledge injection.
  - As the skill pool grows 5 → 100, actual-use precision falls 29.6% → 3.3%.
- **Monday takeaway:**
  - Write skills as **procedures** (ordered steps, checks, commands), not fact dumps.
  - Keep each agent's skill pool small (curate per sub-agent with `SkillToolset`). Measure "skill loaded and actually followed", not just "skill loaded".
- **Limitations:**
  - Benchmark tasks only.
  - The taxonomy comes from 238 labels.
- **Slide idea:** A precision curve drawn in as the pool size slider goes 5 → 100. A pie chart (65.7% anchoring) assembles slice by slice.

### 9. Judged useless, queried anyway: agents don't stop on their own evidence
- **arXiv:** 2610.06191. Submitted 2026-10-05.
- **Authors:** Chubin Zhang et al. (NTU Singapore).
- **Problem:** When a tool keeps returning junk, agents keep calling it.
- **Method:**
  1. A retrieval environment with controlled source failures. The agent's judgment of each result is logged separately from its stop/continue decisions.
  2. 7 agents tested.
  3. Prompt cues (budgets, call costs, stop rules) compared with a harness-enforced "integration step": after 5 consecutive results the agent itself judged useless, it must answer.
- **Key numbers:**
  - Agents label failing-source results useless 97–100% of the time, yet rarely stop.
  - Prompted stop rules are followed "at most partly".
  - The harness rule raises failing-source success for every model and keeps the stopping point fixed when the budget doubles. A pre-registered replication on 300 new questions confirms the effect.
- **Monday takeaway:**
  - Enforce stopping in code. Have a tool return a `useful: bool` field, or ask the model to state its judgment.
  - Count consecutive `false` values in `after_tool_callback`. At N=5, make the next tool call fail with "answer now from what you have", or end the loop with an escalation.
  - Do not rely on "stop if not useful" in the instruction.
- **Limitations:**
  - Retrieval tasks only.
  - Synthetic failures.
- **Slide idea:** A counter shows "useless ✔ useless ✔ useless ✔" while the agent keeps calling. Then the harness gate drops in at 5 and the arrow redirects to "Answer".

### 10. Closed-world resolution against tool hallucination
- **arXiv:** 2609.19425. Submitted 2026-09-16.
- **Authors:** Laxmipriya Ganesh Iyer (affiliation [UNVERIFIED]).
- **Problem:** Agents call tools that do not exist, or pass undeclared arguments. Selection and permission gates assume the call refers to a real tool, so they cannot catch this.
- **Method:**
  - A taxonomy: H1–H5 for single-registry hallucination, M1–M5 for merged MCP namespaces (collisions, shadowing).
  - A "Resolution Rung": a training-free closed-world resolver (registry membership plus signature check) that must run *before* any policy gate.
  - Released the Hallucinated-Tools Benchmark (HTB).
- **Key numbers:**
  - 322 real hallucinations across 10 hosted models.
  - Fabricated-tool calls concentrate on raw-JSON surfaces (34 vs 3 with native function calling).
  - Scale does not help (a 675B model matches a 7–8B one).
  - 154 hallucinations on the live merged-MCP surface, including from frontier models that were clean on a single registry.
- **Monday takeaway:**
  - Use native function calling, not "emit JSON in text".
  - When you mount several `McpToolset`s, set a per-server prefix (tool-name prefix) so names cannot collide or shadow each other.
  - In `before_tool_callback`, reject unknown args against the schema and return a corrective error rather than letting the call through.
- **Limitations:**
  - Mostly a measurement study.
  - One residual class (schema-valid borrowed arguments) cannot be caught.
- **Slide idea:** Two registries merge into one namespace. Two `search` tools collide, sparks fly, and a "resolver" turnstile sits before the policy gate.

### 11. Screenshots or tools? Hybrid GUI-MCP computer-use agents
- **arXiv:** 2608.03327. Submitted 2026-08-04 (v1 per arXiv API; was 2026-08-06).
- **Authors:** Siqi Fan et al. Affiliation [UNVERIFIED]. Code: github.com/redai-infra/hybrid-routing-agent.
- **Problem:** Does giving a CUA MCP tools help?
- **Method:**
  - Identical GUI+MCP harness on OSWorld-MCP (309 tasks, 5 runs).
  - Multi-turn RL with a dense tool-use bonus.
  - A context rule: after a successful tool call, drop the next screenshot and halve the image history, then retrain under that rule.
- **Key numbers:**
  - The same MCP tools give +4.0 pp to a reasoning model and −5.9 pp to a non-reasoning one.
  - The reasoning model uses tools on only 55 of 309 tasks (23.9% of tool-reachable ones). The paper calls this the "adoption gap".
  - The tool bonus raises adoption 0.03 → 0.33, but held-out accuracy does not follow.
  - The compressed and retrained agent reaches 37.8% vs 33.0% at 53% of the input cost.
- **Monday takeaway:**
  - Adding tools can hurt weaker models. A/B test before adding.
  - In ADK computer-use agents, drop the screenshot after a successful API tool call and cap image history (a `before_model_callback` that strips old image parts).
- **Limitations:**
  - One benchmark.
  - The adoption gain did not transfer to competence.
- **Slide idea:** A split screen. A screenshot stack shrinks by half as the "tool succeeded" badge appears, and the cost meter goes to 53%.

### 12. WebFovea: when the model is right but the click is wrong
- **arXiv:** 2610.03036. Submitted 2026-10-02 (v1 per arXiv API; was 2026-10-07).
- **Authors:** Jiangang Han (solo; affiliation [UNVERIFIED]). Code: github.com/jianganghan/WebFovea.
- **Problem:** On live websites, many failures happen in the harness, not in the model.
- **Method:** Treat each step as a four-stage round trip: (1) parse the reply into an action, (2) the action takes effect, (3) the result is reported back faithfully, (4) the model sees what it needs. Harden each stage and add rule and budget guardrails.
- **Key numbers:**
  - 2nd place in the WebRetriever Challenge 2026.
  - Same model throughout. The hidden-set score rose 31.0 → 57.0 from harness changes alone.
  - Bugs found: a coordinate-space mismatch that put every click at 3/4 of the intended position; silent failures on native dropdowns, iframes and text boxes; self-generated chat-template tokens in 4.9% of episodes.
- **Monday takeaway:** Write harness unit tests for the browser tool.
  - Assert that screenshot coordinates match viewport coordinates (device-pixel-ratio scaling).
  - Verify that every action changed the DOM.
  - Return explicit "no effect" errors.
  - Strip chat-template tokens from model output before parsing.
- **Limitations:**
  - A single competition.
  - Live-site variance.
- **Slide idea:** Four checkpoints on a loop (parse, effect, report, observe). The "click at 3/4 coordinates" bug is animated with a cursor landing short of the button.

### 13. StateM: harness scaling on Terminal-Bench 2.1
- **arXiv:** 2608.15089. Submitted 2026-08-15.
- **Authors:** Ziheng Qin et al. Affiliation [UNVERIFIED]; Zhangyang (Atlas) Wang is a co-author. Code: github.com/henryqin1997/statem.
- **Problem:** Long-horizon agents lose mutable state, forget lessons, skip procedures and stop early.
- **Method:**
  - Runtime built from durable states, phase-local context, checked transitions, recoverable runbooks, and versioned "golden rules".
  - Postmortem findings are turned into executable preconditions.
- **Key numbers:**
  - GPT-5.5 xhigh: 83.1% reference → 92.1%. GPT-5.6 Sol xhigh: 95.3% raw.
  - GPT-5.6 Luna: 76.7 → 85.4%.
  - DeepSeek-V4 Flash: 82.7 → 88.1% for less than $38 of adaptation.
  - Final-score API spend about $15 vs $574.68 for the GPT reference.
- **Monday takeaway:**
  - Model the long task as an ADK Workflow graph with explicit state and checked transitions (a node validates before the edge fires).
  - Encode postmortem lessons as code-level preconditions, not as more prompt text.
- **Limitations:**
  - Task-family-specific runbooks. Gains on BusinessBench held-out sets were small (0.55 to 1.34 points).
- **Slide idea:** A state machine lights up phase by phase. A failed transition bounces back to a runbook node. A "$574 → $15" ticker runs alongside.

### 14. "My credentials, please": filesystem capability laundering in MCP servers
- **arXiv:** 2610.22301. Submitted 2026-10-15.
- **Authors:** Zeqian Huang et al. Affiliation [UNVERIFIED].
- **Problem:** Approving a local MCP tool call grants the whole server process host filesystem access, not just the declared operation.
- **Method:** MCP-FSD.
  1. Screen server categories.
  2. Infer least-privilege boundaries per tool.
  3. Plant credential fixtures outside those boundaries.
  4. Run paired dynamic exploits inside and outside sandboxes.
- **Key numbers:**
  - Scanned 21,097 servers from 9 registries.
  - 787 of 4,806 triaged servers (16.4%) have filesystem capabilities despite non-filesystem labels.
  - 150 confirmed vulnerable instances.
  - 13 advisories, including 2 CVEs in Anthropic's Git MCP server.
- **Monday takeaway:**
  - Run stdio MCP servers in a container with only the needed directory mounted.
  - Validate path arguments in `before_tool_callback` against an allow-list root.
  - Do not treat "user approved the call" as a sandbox.
- **Limitations:** Covers the filesystem class only.
- **Slide idea:** A "get_weather" tool card flips over to show `open("~/.aws/credentials")`. A container wall then slides in.

### 15. A2M: trace-optimized agent hijacking in the MCP ecosystem
- **arXiv:** 2609.26761. Submitted 2026-09-22.
- **Authors:** Laizhen Li et al. Affiliation [UNVERIFIED]; Kejiang Ye is a co-author. Code: github.com/Lilaizhen/A2M.
- **Problem:** Agents choose third-party tools by semantic match, so attackers can game the metadata and the tool returns.
- **Method:** A two-stage black-box attack.
  1. **Attraction:** optimize tool metadata to raise the invocation probability.
  2. **Manipulation:** refine adversarial tool returns using execution traces.
- **Key numbers (LiveMCPBench, GLM-4.6):**
  - Malicious tool invocation rate 93.6%.
  - Token cost 32.4× baseline under "cognitive DoS".
  - Attack success 74.4%.
  - Transfer to 4 other models without re-optimization: 63.6%, 2.7× and 24.5%.
- **Monday takeaway:**
  - Pin MCP servers and versions. Filter to approved tools with `tool_filter`.
  - Set a per-invocation token and tool-call budget (catches cognitive DoS).
  - Treat tool outputs as data. Isolate high-risk tools behind `require_confirmation`.
- **Limitations:**
  - One benchmark.
  - Transfer is weaker than the direct attack.
- **Slide idea:** A magnet labelled "optimized description" pulls the agent's arrow to a rogue tool. A token counter then explodes to 32×.

### 16. SkillJack: persistent skill backdoors in self-evolving agents (plus memory injection, 2610.28810)
- **arXiv:** 2608.03509. Submitted 2026-08-04.
- **Authors:** Zonghao Ying et al. (Tencent).
- **Problem:** Self-evolving agents turn trajectories into reusable skills. Poisoned experiences become durable behaviours.
- **Method:** Poison trajectories, then let the agent's own extractor (SkillX, Anything2Skill) distil them into skills. Three properties make this work:
  - Sanitization whitewashing.
  - Cross-layer promotion.
  - Persistence after the source records are deleted.
- **Key numbers:**
  - Safety detection falls from 98.5% on poisoned trajectories to 11.4% on the extracted skills (SkillX).
  - Attack success 56.2% and 89.2%.
  - 80% persist after the poisoned records are deleted.
- **Companion paper:** 2610.28810 (2026-10-20, Barcha Correia et al.; affiliation [UNVERIFIED]). It shows cross-session memory injection on ChatGPT Instant 5.3, Claude Sonnet 4.6 and Gemini 3 Flash through personal memories, projects, skills, org instructions and MCP resources. All NIST attack goals are achievable. About half of the derived mitigations are unimplemented.
- **Monday takeaway:**
  - Gate memory and skill writes: keep provenance (session ID, user, tool source) on every `add_session_to_memory` record or generated skill.
  - Scan the *extracted* artifact, not only the source.
  - Require human review before an auto-generated skill is promoted to the shared `SkillToolset`.
- **Limitations:**
  - Two research skill systems.
  - 150 trajectories.
- **Slide idea:** A red droplet enters a trajectory, passes through a "skill extractor" filter, and comes out clean-looking but still red inside (98.5% → 11.4% detection).

### 17. Agent Lightning v1.0: harnessed agentic RL
- **arXiv:** 2608.17528. Submitted 2026-08-18.
- **Authors:** Zhiyuan He et al. (Microsoft).
- **Problem:** Production agents run inside their own harness (tools, context, control flow). RL frameworks want to own the environment loop instead.
- **Method:**
  - The deploy-time harness talks to an LLM endpoint proxy. The trainer only sees request/response pairs.
  - Solves retokenization, sample merging, advantage calculation, loss normalization and backend scheduling in about 3,500 lines of code.
  - The approach is adopted by verl Uni-Agent, AReaL 2.0, slime and Polar.
- **Key numbers:** Qwen3.5-9B on SWE-bench Verified rises 41.8% → 56.4% (+14.6) with 6K training examples and modest compute.
- **Monday takeaway:**
  - You can RL-train the model behind an *unchanged* ADK agent by pointing its model at a proxy endpoint (e.g. through LiteLLM / an OpenAI-compatible base URL) and logging request/response pairs plus a reward.
  - Keep training-time and serve-time harness identical.
- **Limitations:**
  - Open-weight models only.
  - Stability issues are documented, not eliminated.
- **Slide idea:** The ADK agent box stays still. A proxy pipe is inserted between it and the model, trajectories flow into a trainer, and updated weights flow back. The SWE-bench bar grows from 41.8 to 56.4.

### 18. A reality check on self-distillation in agentic RL
- **arXiv:** 2610.19789. Submitted 2026-10-14.
- **Authors:** Linhao Zhong et al. (Zhejiang University).
- **Problem:** Many new agentic-RL "self-distillation" methods report gains against reused baselines.
- **Method:** 10 methods vs GRPO on ALFWorld, ScienceWorld, Search-QA and WebShop, at 3 model sizes. 132 runs (12,124 H800 GPU-hours), 8 rollout seeds each.
- **Key numbers:**
  - No method beats GRPO consistently.
  - Strong final scores hide unstable training.
  - Extra compute does not reliably buy accuracy.
- **Monday takeaway:**
  - If you fine-tune an agent model, start with plain GRPO and multiple seeds. Report training curves and GPU-hours.
  - Treat new tricks as hypotheses.
- **Limitations:** Four environments.
- **Slide idea:** A leaderboard where 10 fancy methods' bars wobble with error bars around the flat GRPO line.

### 19. MCPacific: hierarchical map of the MCP ecosystem
- **arXiv:** 2610.05319 (v2). Submitted 2026-10-04.
- **Authors:** Tingxuan Tang et al. Affiliation [UNVERIFIED].
- **Problem:** Hundreds of thousands of MCP servers exist with only coarse marketplace categories.
- **Method:**
  1. Crawled 17 marketplaces: 368,754 listings and 124,267 unique servers.
  2. Statically extracted 1,328,233 tool specs.
  3. Built an LLM-driven taxonomy of 58,915 capabilities, mapped by calibrated embedding routing.
- **Key numbers:**
  - 85% of tools are non-developer.
  - 98.5% of tools have at least one alternative, but about a quarter of capabilities have only one tool.
  - Complexity differs by more than 2.5× in 41% of comparable pairs.
  - Presenting candidates through the taxonomy instead of a flat list adds up to +12 pp Pass@0.75 in crowded candidate sets.
- **Monday takeaway:**
  - Group your tools into capability categories and present them hierarchically: category → tool, the same lesson as GatewayBench.
  - When you choose among alternative servers, compare their maintenance and security signals.
- **Slide idea:** A zoomable treemap (1.3M tools → 58,915 capabilities). Crowded leaves collapse into one category node.

### 20. Heartbeat Thinking: speculative reasoning and tool execution while listening (voice agents)
- **arXiv:** 2610.26233. Submitted 2026-10-19.
- **Authors:** Zhenyu Zhang et al. (Ant International).
- **Problem:** Voice agents wait until the user stops speaking before they reason or call tools.
- **Method:**
  - Periodic "Thinker" invocations read the latest partial transcript and a shared record of completed reasoning and tool results.
  - New speech updates start new invocations without cancelling the running ones or dispatched tools.
  - Completed results fill in missing arguments and trigger dependent calls.
- **Key numbers:**
  - FDBench v3: +16 pp tool coverage and −36.4% mean final-response latency vs a SHANKS-style windowed baseline.
  - Effects on final quality depend on the benchmark (SpeechFCEval, AudioCRAG).
- **Monday takeaway:**
  - For ADK Live (bidi streaming) agents, start idempotent read-only lookups as soon as partial transcripts contain the arguments. Cache their results in state.
  - Do not cancel in-flight tools on every transcript update.
  - Keep write actions until end of turn.
- **Limitations:**
  - Quality gains are mixed.
  - Speculation wastes calls when the user changes their mind.
- **Slide idea:** An audio waveform scrolls. Heartbeat pulses spawn tool calls under it, and when speech ends the answer is already 36% closer.

---

## Also notable (one line each, verified from the abstract)
- **2607.26637** Filesystem-based memory for LLM agents (2026-07-29). Organized markdown-tree stores roughly halve retrieval cost on large material. Organization erodes over time for all but the strongest manager model. Changing the tool set reshapes the store as much as changing the model.
- **2607.21503** Agentic Context Management (Maximem AI, 2026-07-23; single author). Naive accumulation makes cost quadratic in turns. Crude summarization makes it linear but hits an accuracy cliff. Validated compaction gives linear cost with fidelity. The vendor system reports 92% on LongMemEval and 93.2% on LoCoMo (vendor numbers).
- **2610.11287** REMORY (Fudan/SII, 2026-10-08). Soft "residual memory" tokens appended after a compaction summary approach full-context quality on SummHay using 5.2% of input positions. Fewer repeated tool outputs and tool errors on BrowseComp and Terminal-Bench 2.1.
- **2610.20399** Cortex (ByteDance Seed, 2026-10-14). Consolidates context into LoRA or FFN weight updates. After 50 sequential edits on a 14B model it recovers 88.9% of the context gain and retains 99.8% of non-target performance.
- **2610.22174** Mosaic (HKUST-GZ, 2026-10-15). RL for multi-session trajectories (compaction, subagent forking). Session-level advantages beat broadcasting the trajectory advantage on BrowseComp (Qwen3.5-4B) and use fewer sessions.
- **2610.28785** BRACE/Discord (2026-10-20). For MCP-agent RL, forecast which tasks will produce mixed rewards before spending rollouts. It leads the compared methods on BFCL and NESTFUL.
- **2609.25678** ToolCompass (NTU, 2026-09-22). Post-training that clusters tool calls by function (von Mises-Fisher) to guide trials of unseen tools. Up to +10.71 pp AppWorld out-of-distribution success.
- **2609.38008** HybridCUA (ZJU, 2026-09-29). SFT plus CLI-aware RL to mix GUI and shell actions. HybridCUA-9B scores 53.6% on OSWorld (+14.8 pp over base).
- **2607.28227** Qwen-UI-Agent (Tongyi Lab, 2026-07-30). Unified GUI+CLI action space with batched actions, 10,000+ concurrent RL environments, 100+ turn trajectories. 79.5% on OSWorld-Verified, 73.6% on WebArena, 81.5% on ScreenSpot-Pro.
- **2609.01437** HarnessDev (ByteDance Seed, 2026-09-01). LLM-built harnesses trail human-engineered ones on code and search. Self-evolution gains are unstable and transfer only partly across tasks and models.
- **2609.35760** TokenCast (Southeast Univ., 2026-09-28). Per-segment cost forecasts take 32.8 ms per run. Budget control uses 21.3% fewer tokens than a fixed budget at matched completion.
- **2608.08389** Marginal value estimation for deep-research agents (2026-08-09). *Where* you prune matters more than how. Early (pre-retrieval) pruning saves most. Heuristics cut up to 73% of tokens with little quality loss.
- **2609.33731** HTN planning for multi-server MCP (2026-09-27). Plan once, then execute deterministically across MCP servers with `${context.X}` data binding. This avoids one LLM round-trip per tool call (the same idea as ADK Workflow graphs).

## Cross-paper trends (for a "what the research says" slide)
1. **The harness is the product, and most of it is tool-surface design.**
   - WebFovea (31 → 57 with the same model), StateM (95.3%, $15 vs $575) and StateAct (9× cheaper) all improve without changing the model.
   - GatewayBench and the metadata study show that how tools are *exposed* (hierarchy, schema shape, order, error text) changes success by double digits.
2. **Fewer, better-shaped tools beat more tools.**
   - Flat lists collapse past roughly hundreds of tools (233k tokens per turn).
   - Skill retrieval precision falls to 3.3% at 100 skills.
   - Pruning unused tools is TokenEconomizer's biggest saving.
   - MCP tools hurt a weaker CUA by 5.9 pp.
   - Hierarchy, filtering and per-agent toolsets are the shared fix.
3. **Forget tool outputs, keep reasoning; curate at read time.**
   - Cache engineering (drop old tool KV), hybrid GUI-MCP (drop redundant screenshots), JitMem (raw store, read-time curation), REMORY (residual tokens after the summary) and marginal-value pruning all say that whole-history summarization is the wrong default.
4. **Enforce control in code, not prompts.**
   - Stopping rules (Judged Useless), loop guards (TokenEconomizer), closed-world tool resolution, finish gates (StateAct) and checked transitions (StateM) only work reliably when the harness enforces them. Prompt-only rules are followed "at most partly".
5. **Self-evolving means a new supply-chain attack surface, and the training story is less settled than the papers suggest.**
   - SkillJack, memory injection, A2M and capability laundering show that memory, skills and MCP metadata are persistent attack vectors. Provenance and sandboxing are needed.
   - On the RL side, a 12k-GPU-hour audit finds no self-distillation method consistently beats GRPO. Agent Lightning shows the practical path: RL behind an unchanged harness via a proxy.
