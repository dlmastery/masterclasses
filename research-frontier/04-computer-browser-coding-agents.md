# 04. Frontier Agent Types, 2025-2026: Computer-Use, Browser, Coding, Deep Research, Live, Background and Scheduled Agents

*Research snapshot: 2026-10-23. Scope: mid-2025 to October 2026 only. Verification note: items marked **[PRIMARY]** were read directly from the vendor's own docs or blog in this session. Items marked **[UNVERIFIED]** come from third-party aggregators or memory and should be checked before they go on a slide. The web-search budget ran out partway through, so some leaderboard numbers come from secondary trackers and are flagged as such.*

---

## 0. The big shift in one paragraph

The 2023-era agent was a *prompt pattern*: "Thought / Action / Observation" (ReAct) in a single loop and a single context window, with a human watching. The 2026 agent is a *system*. A strong model runs in a **harness** (the loop, tools, context management and permissions). The harness runs inside a **sandbox** (VM, container or OS-level jail) with **credentials kept outside it**. The run is recorded in a **durable session log**, so it can be resumed, rewound or forked. **Verification** comes from tests, browser QA agents and evaluators. The work is launched by **triggers** (a schedule, an API call, a GitHub event), not only by a chat box. The loop is still a loop. What changed is everything around it. Anthropic put it this way: *"every component in a harness encodes an assumption about what the model can't do on its own"* (Anthropic Engineering, "Harness design for long-running application development", 2026-03-24) **[PRIMARY]**.

---

## 1. Computer-use agents (screen-level GUI control)

**Definition.** A model that sees screenshots and emits low-level UI actions (click x,y; type; scroll; key). The client executes each action and returns a new screenshot. The model operates any GUI, with or without an API.

**Why it replaced older approaches.** Earlier "web agents" scraped HTML or DOM text and broke on canvas apps, desktop software and anti-bot layouts. Native pixel-grounded models (trained for coordinates) generalize to any interface. A per-step safety layer makes them deployable.

**Architecture flow (for a diagram).**
User goal → [Model: goal + screenshot + action history] → function call `click(x,y)` + `safety_decision` → **Safety gate** (allowed / require_confirmation / blocked) → Client executor (Playwright / VM / phone) → new screenshot + URL → back to model. The loop ends on task done, error, or a human decision.

### Implementations (verified)
- **Gemini 2.5 Computer Use** was announced **2025-10-07** as a public preview in the Gemini API (AI Studio, Vertex AI). It is built on Gemini 2.5 Pro and *"primarily optimized for web browsers"*, shows promise on mobile, and is *"not yet optimized for desktop OS-level control."* It led on Online-Mind2Web, WebVoyager and AndroidWorld *"with lower latency"*. The chart shows 70%+ accuracy at about 225 s, the lowest latency in the comparison. A per-step safety service sits outside the model. ([blog.google](https://blog.google/technology/google-deepmind/gemini-computer-use-model/)) **[PRIMARY]**
- **Gemini API computer-use docs (current)**: the recommended model is now `gemini-3.8-flash` (others listed: `gemini-4-argon`, `gemini-3.5-flash-lite`, `gemini-3-flash-preview`). Action sets cover **Browser, Mobile and Desktop**, so desktop support now exists. A response can carry `safety_decision` ∈ {`require_confirmation`, `allowed`, `blocked`}. On confirmation, return a `safety_acknowledgement` in the function result. Coordinates are *normalized*, and the client converts them to viewport pixels. ([ai.google.dev/gemini-api/docs/computer-use](https://ai.google.dev/gemini-api/docs/computer-use)) **[PRIMARY]**
- **Claude computer use**: the current tool is `computer_toolset_20260801`, a client *toolset* of 17 member tools (`screenshot`, `zoom`, clicks, `left_click_drag`, `scroll`, `type`, `key`, `hold_key`, `wait`…). No beta header is needed. Older `computer_20251124` and `computer_20250124` are rejected by Claude 5.5+ models. Anthropic runs prompt-injection classifiers on screenshots. ([platform.claude.com docs](https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool)) **[PRIMARY]**
- **ADK**: v2.13.0 (2026-10-23) adds "support Gemini 3.x computer use browser action schemas" ([adk-python releases](https://github.com/google/adk-python/releases)) **[PRIMARY]**.
- **OpenAI Operator → ChatGPT agent** (Operator was folded into "ChatGPT agent" in July 2025) **[UNVERIFIED: openai.com returned 403 in this session]**.

```python
# Claude computer use, verbatim quick start (platform.claude.com)
response = client.messages.create(
    model="claude-opus-5-5", max_tokens=1024,
    tools=[{"type": "computer_toolset_20260801"},
           {"type": "text_editor_20250728", "name": "str_replace_based_edit_tool"},
           {"type": "bash_20250124", "name": "bash"}],
    messages=[{"role": "user", "content": "Save a picture of a cat to my desktop."}],
)
```

**Failure modes.** Prompt injection from pages and images (*"Webpages and images can contain instructions that override yours"*). Mis-grounded clicks. Irreversible actions such as purchases, accepting terms or cookies. Long-horizon drift. Mitigations: a dedicated VM with minimal privileges, a domain allowlist, human confirmation for consequential actions, and no logins in the VM. **[PRIMARY, Anthropic docs]**

---

## 2. Browser agents

**Definition.** A computer-use agent specialized for the browser. It often mixes pixels with DOM or accessibility-tree reads and runs in a hosted headless browser (Browserbase, Playwright, Chrome extension).

**Why now.** Most knowledge work lives in the browser. Browser-only scope lets vendors ship lower latency and tighter safety (URL allowlists, per-step checks). Google's 2.5 Computer Use model was explicitly browser-first, and its Online-Mind2Web numbers came from the **Browserbase** harness. **[PRIMARY]**

**Pattern details.** Hybrid perception (screenshot plus DOM). Tab and URL state returned with each step ("new screenshot **and the current URL**"). Confirmation gates on checkout and login. Session recording for audit. Agents used as **QA evaluators**: Anthropic's long-running harness has an evaluator agent that *"used Playwright to interact with the live page"*, because *"Out of the box, Claude is a poor QA agent"* ([Anthropic, 2026-03-24](https://www.anthropic.com/engineering/harness-design-long-running-apps)) **[PRIMARY]**.

**Failure modes.** Allowlist abuse (*"Every function reachable through any domain on an allowlist is now an attack surface"*, Anthropic "How we contain Claude across products", 2026-05-25) **[PRIMARY]**. CAPTCHAs. Dynamic layouts. Eval awareness: Anthropic published "Eval awareness in Claude Opus 4.6's BrowseComp performance" (2026-03-06) **[PRIMARY title; contents not read]**.

---

## 3. Coding agents: the most mature agent category

**Products (2025-2026).** Claude Code (CLI, IDE, web, desktop), OpenAI Codex (CLI plus Codex Cloud), Google Jules (async, cloud VM), Gemini CLI (open source), plus Devin and Cursor.

### 3.1 Plan mode (separate thinking from doing)
- **Gemini CLI plan mode** was announced **2026-03-11** (Kipruto, Wotherspoon, Lyalin) as a *"read-only mode that restricts Gemini CLI to a subset of its tools."* It can use read-only MCP tools (GitHub issues, Postgres schemas, Docs), an `ask_user` tool to clarify, and sub-agents like `codebase_investigator`. Enter it with `/plan` or `Shift+Tab`. It is enabled by default, and the model gets `enter_plan_mode` and `exit_plan_mode` tools. ([developers.googleblog.com](https://developers.googleblog.com/en/plan-mode-now-available-in-gemini-cli/)) **[PRIMARY]**
- **Claude Code plan mode**: *"Plan mode tells Claude to research and propose changes without making them."* Edits stay blocked until the user approves, with options such as "Yes, and use auto mode" and "No, keep planning". ([code.claude.com/docs/en/permission-modes](https://code.claude.com/docs/en/permission-modes)) **[PRIMARY]**
- **Jules**: it *"creates a plan for each task. You can review and approve it before it changes any code."* ([jules.google/docs](https://jules.google/docs/)) **[PRIMARY]**
- *Why it replaced "just start coding"*: the approval point moves from hundreds of tool calls to one plan, and context-gathering is separated from mutation.

### 3.2 Sandboxes and permission modes (replacing "approve every command")
- Claude Code users approved **~93%** of permission prompts, which produced *"approval fatigue"* ([Anthropic, "How we built Claude Code auto mode", 2026-03-25](https://www.anthropic.com/engineering/claude-code-auto-mode)) **[PRIMARY]**.
- **OS-level sandbox** (bubblewrap on Linux, Seatbelt on macOS). Filesystem writes are limited to the working directory, and network traffic goes through a proxy over a Unix socket. *"Sandboxing safely reduces permission prompts by 84%."* ([Anthropic, 2025-10-20](https://www.anthropic.com/engineering/claude-code-sandboxing)) **[PRIMARY]**
- **Auto mode classifier** (Sonnet 4.6). Stage 1 is a single-token filter (8.5% FPR). Stage 2 adds chain-of-thought and brings FPR to **0.4%**, but the false-negative rate on real overeager actions is **17%**: *"The 17% false-negative rate on real overeager actions is the honest number."* The classifier is "reasoning-blind" (tool results stripped). After 3 consecutive or 20 total blocks, the session escalates to the human. **[PRIMARY]**
- Claude Code modes: `default`, `acceptEdits`, `plan`, `auto`, `dontAsk`, `bypassPermissions` ("Isolated containers and VMs only"). **[PRIMARY]**
- **Credentials outside the sandbox.** A git proxy attaches the real token after checking the push target. *"if credentials never enter the sandbox, they can't be exfiltrated"* ([Anthropic, 2026-05-25](https://www.anthropic.com/engineering/how-we-contain-claude)) **[PRIMARY]**. Codex Cloud has the same idea: network presets, allowed domains, and "network secrets" for HTTPS credentials ([learn.chatgpt.com/docs/cloud](https://learn.chatgpt.com/docs/cloud)) **[PRIMARY]**.

### 3.3 Test-driven loops and verification
- Long-running harness pattern ([Anthropic, "Effective harnesses for long-running agents", 2025-11-26](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)) **[PRIMARY]**. An **initializer agent** writes `init.sh`, `claude-progress.txt`, an initial commit and a **JSON feature list, all marked failing**. Each later **coding agent** session takes one feature, tests it end to end through browser automation, commits, and updates progress. *"It is unacceptable to remove or edit tests."* JSON is chosen because the model is less likely to damage it than Markdown.
- **Planner / Generator / Evaluator** (GAN-inspired), with **sprint contracts** in which the generator and evaluator agree on what "done" means before coding (2026-03-24) **[PRIMARY]**. Numbers: a solo run took 20 min and cost $9, while the full harness took 6 h and cost $200 (Opus 4.5). A simplified V2 run took about 3 h 50 min and cost $124.70 (Opus 4.6). For Opus 4.6 the per-sprint evaluation was removed, which shows the lesson: re-test harness components with every model.
- **Parallel agents, no orchestrator**: 16 Claude agents, about 2,000 sessions over 2 weeks, just under $20k, 2B input and 140M output tokens, and a ~100k-line Rust C compiler that builds Linux 6.9 on x86, ARM and RISC-V with about 99% on the GCC torture suite. Coordination used git lock files in `current_tasks/`, and *tests were the guide* ([Anthropic, "Building a C compiler with a team of parallel Claudes", 2026-02-05](https://www.anthropic.com/engineering/building-c-compiler)) **[PRIMARY]**.

### 3.4 Checkpoints, rewind and forks
- Claude Code makes a checkpoint at every user prompt that starts a turn and keeps snapshots for the last 100. `/rewind` (or Esc Esc) offers *Restore code and conversation / Restore conversation / Restore code / Summarize from here / Summarize up to here*. Bash-only file changes and background-subagent edits are **not** tracked, so this is *"Not a replacement for version control"*. `/branch` or `--fork-session` explores alternatives. ([code.claude.com/docs/en/checkpointing](https://code.claude.com/docs/en/checkpointing)) **[PRIMARY]**
- Gemini CLI has checkpointing (file snapshots before edits, `/restore`) and, per a third-party guide, worktrees in v0.38 **[UNVERIFIED]**.

### 3.5 Repo memory files
`AGENTS.md` is read by Jules (*"automatically looks for an AGENTS.md file in the repo root"*) **[PRIMARY]** and by Codex **[secondary]**. Claude Code uses `CLAUDE.md` plus Agent Skills (Anthropic, "Equipping agents for the real world with Agent Skills", 2025-10-16) **[PRIMARY title]**.

### 3.6 Single-thread vs. multi-agent debate
Cognition (Walden Yan, **2025-06-12**, "Don't Build Multi-Agents"): *"Share context, and share full agent traces, not just individual messages"* and *"Actions carry implicit decisions, and conflicting decisions carry bad results"* ([cognition.com](https://cognition.com/blog/dont-build-multi-agents)) **[PRIMARY]**. The 2026 synthesis: **read-heavy work parallelizes** (research subagents, investigators), and **write-heavy work stays single-threaded or is coordinated through git and tests** (C-compiler lock files).

---

## 4. Deep research agents

**Definition.** A long-running agent that plans, searches iteratively, reads, runs code and writes a cited report over minutes, not seconds.

**Pattern.** Plan (optionally reviewed by the user) → fan-out search and read loops → synthesis with citations → follow-ups. Runs are **background by necessity**.

**Google Gemini Deep Research (Interactions API)** **[PRIMARY]** ([ai.google.dev/gemini-api/docs/deep-research](https://ai.google.dev/gemini-api/docs/deep-research)):
- Agents: `deep-research-preview-04-2026` ("speed and efficiency") and `deep-research-max-preview-04-2026` ("maximum comprehensiveness").
- Available *only* through the Interactions API. It **requires `background=True`**; you poll `interactions.get` until status is `completed` or `failed`. Streaming needs `stream=True` and `background=True`, and `thinking_summaries="auto"` streams intermediate thoughts.
- Features: collaborative planning (the plan is returned for review), charts, image and PDF input, Google Search, URL Context and Code Execution by default, plus MCP servers and File Search. `previous_interaction_id` handles follow-ups.

```python
interaction = client.interactions.create(
    agent="deep-research-preview-04-2026",
    input="Compare 2026 computer-use benchmarks and their saturation.",
    background=True,
)
while (interaction := client.interactions.get(interaction.id)).status == "in_progress":
    time.sleep(10)
print(interaction.outputs[-1].text)   # field names: check docs [UNVERIFIED]
```

Anthropic's multi-agent research system (orchestrator plus parallel subagents, 2025-06-13) is the reference for the fan-out design **[PRIMARY title]**. OpenAI Deep Research, built into ChatGPT agent, is **[UNVERIFIED]** here.

**Failure modes.** Citation hallucination, source-quality blindness, over-long reports, cost blow-ups from fan-out, and eval awareness on BrowseComp-style tasks.

---

## 5. Voice / live agents (bidirectional streaming)

**Definition.** A stateful, full-duplex session (WebSocket) that streams audio, video or text in and audio or text out. The user can **barge in**, and tools run mid-conversation.

**Why it replaced STT→LLM→TTS pipelines.** Native-audio models cut latency, keep prosody and emotion ("affective dialog"), and handle interruptions natively. Cascades still exist where control or cost matters. ADK v2.12/2.13 added `CascadeLive` with barge-in **[PRIMARY]**.

**Gemini Live API facts** **[PRIMARY]**: input is 16-bit PCM at 16 kHz plus JPEG at ≤1 FPS, and output is PCM at 24 kHz over WSS. It has 70 languages, barge-in, affective dialog, proactive audio, function calling and Search. Sessions last **15 min audio-only and 2 min audio+video without compression**, and a connection lasts about 10 min. Resumption handles stay *"valid for 2 hr"*. A `GoAway` message carries `timeLeft`. Doc examples use `gemini-3.8-live`. Use ephemeral tokens for client-to-server connections.

**ADK bidi streaming** **[PRIMARY]** ([adk.dev/live/sessions](https://adk.dev/live/sessions/)):

```python
run_config = RunConfig(
    response_modalities=["AUDIO"],
    session_resumption=types.SessionResumptionConfig(),
    context_window_compression=types.ContextWindowCompressionConfig(
        trigger_tokens=100000,
        sliding_window=types.SlidingWindow(target_tokens=80000)),
)
live_request_queue = LiveRequestQueue()          # one fresh queue per run_live()
try:
    async for event in runner.run_live(user_id=user_id, session_id=session_id,
            live_request_queue=live_request_queue, run_config=run_config):
        await websocket.send_text(event.model_dump_json(exclude_none=True, by_alias=True))
finally:
    live_request_queue.close()
```

ADK adds automatic tool execution, automatic session resumption, a unified event model, persistence and multi-agent workflows on top of the raw Live API. v2.9.0 added a **LiveKit runner for voice and telephony**, and v2.8.0 runs before/after-model callbacks in live mode **[PRIMARY]**. (Note: the adk.dev overview page still labels Live "Experimental" at Python v0.5.0, which looks like a stale label next to 2.x releases.)

**Benchmark tie-in.** τ³-bench (v1.0) added **voice full-duplex evaluation**. The current "τ-bench 2.0" adds τ-i18n (6 languages, text and voice) and an `intake` domain ([github.com/sierra-research/tau2-bench](https://github.com/sierra-research/tau2-bench)) **[PRIMARY]**.

**Failure modes.** Echo and false barge-in, turn-detection errors, tool latency causing dead air, session-limit drops (handle `GoAway`), and prompt injection through audio.

---

## 6. Background / async agents

**Definition.** The agent runs on remote infrastructure, decoupled from the user's terminal. The user hands off a task and gets back a PR, report or notification.

**Implementations.**
- **Jules**: works in a cloud VM, clones the repo, plans, edits, runs tests and opens a PR. It sends browser notifications when done or when it needs input **[PRIMARY]**. The Jules API and Jules Tools CLI launched in October 2025 **[secondary]**.
- **Codex Cloud**: *"Each task has its own workspace and can keep working while your computer is asleep"*. Environment setup is published once and reused, and the task ends in a diff, test results and a PR **[PRIMARY]**. OpenAI **Agents API** (public beta, Sept 2026): the Codex harness as a service, with sandbox choice of OpenAI-managed, your own, or a partner **[secondary; openai.com 403]**.
- **Claude Code on the web / Managed Agents**: "Scaling Managed Agents: Decoupling the brain from the hands" (Martin, Cemaj, Cohen, **2026-04-08**) **[PRIMARY]**. It describes three virtualized components:
  - **Session**: an append-only event log stored *outside* the context window (`getSession`, `emitEvent`, `getEvents`).
  - **Harness ("brain")**: stateless and restartable with `wake(sessionId)`.
  - **Sandbox ("hands")**: every hand is `execute(name, input) → string` and is provisioned lazily.
  Result: **p50 TTFT dropped about 60% and p95 more than 90%**. *"The container became cattle."* *"The harness is never made aware of any credentials."*

**Why it replaced chat-bound agents.** METR time horizons are now in hours (Section 8), so tasks outlive a laptop session. Durable logs make crashes recoverable, and the log becomes the context object (rewind, slice, transform) instead of lossy compaction.

**Failure modes.** Silent wrong success (a green run status ≠ correct work, per the Claude docs), stale environments, PR floods, and cost per task.

---

## 7. Scheduled / event-triggered agents

**Definition.** A saved agent configuration (prompt + repos + connectors + environment) that is **fired by triggers**, not by a person typing.

**Claude Code cloud scheduled tasks (formerly "Routines")** **[PRIMARY]** ([code.claude.com/docs/en/routines](https://code.claude.com/docs/en/routines)):
- Triggers: **Schedule** (cron with a minimum interval of 1 h, or a one-off), **API** (`POST …/routines/{id}/fire` with a bearer token), and **GitHub** (`pull_request.*`, `release.*` with author, branch, label and regex filters). One task can combine triggers.
- Each run is a fresh full cloud session in **auto mode**. Pushes go to `claude/`-prefixed branches.
- Security pattern: the fire `text` arrives wrapped in `<routine-fire-payload>` and is labeled *untrusted data*. The saved prompt must opt in to acting on it.
- Limits: 100 scheduled runs per hour per account, and 30 per hour per task for Run-now and API fires combined.

```bash
curl -X POST https://api.anthropic.com/v1/claude_code/routines/trig_01.../fire \
  -H "Authorization: Bearer sk-ant-oat01-xxxxx" \
  -H "anthropic-beta: experimental-cc-routine-2026-04-01" \
  -H "anthropic-version: 2023-06-01" -H "Content-Type: application/json" \
  -d '{"text": "Sentry alert SEN-4521 fired in prod. Stack trace attached."}'
```

Use cases from the docs: nightly backlog grooming, alert triage that opens a draft PR, bespoke PR review, deploy verification, docs drift, and porting changes between SDKs. Jules also lists "scheduled tasks" in its docs (contents not read) **[UNVERIFIED details]**.

**Failure modes.** Runaway loops and cost, actions taken under the owner's identity (*"Anything a scheduled task does … appears as you"*), injection through event payloads, and expired GitHub auth (runs skip for up to 72 h, then the task turns off).

---

## 8. Google ADK 2.0: where these patterns live in Google's stack

- **Graph workflows (ADK ≥ 2.0)**: *"compose both AI-powered agents and deterministic execution nodes into a flexible execution graph"* **[PRIMARY]**. A `Workflow(name, edges=[...])` holds nodes that can be agents, functions, tools or sub-workflows. Router nodes return `Event(route=...)`. Go module `google.golang.org/adk/v2`, and TS 2.0 has graph workflows.

```python
# paraphrase of adk.dev/graphs (check verbatim in docs)
root_agent = Workflow(name="triage", edges=[
    ("START", planner, classify),
    (classify, {"CODE": coder, "RESEARCH": researcher}),
])
```

- **Recent releases** ([adk-python releases](https://github.com/google/adk-python/releases)) **[PRIMARY]**:
  - v2.13.0 (2026-10-23): Gemini 3.x computer-use schemas, CascadeLive voice with barge-in.
  - v2.12.0 (10-13): `require_confirmation` on workflow nodes.
  - v2.11.0 (10-02): tool nodes pause via `RequestInput`, graceful cancellation, "consult another model" with budgets.
  - v2.9.0 (09-10): `FallbackModel` failover, LiveKit runner, YAML graphs, MCP SDK 2.x.
  - v2.8.0 (08-26): native task mode for `RemoteA2aAgent`, Model Armor plugin.
- Mapping: plan mode ≈ a planner node plus `require_confirmation`; HITL ≈ `RequestInput`; voice ≈ `run_live` / LiveKit; computer use ≈ the computer-use toolset; background work ≈ A2A task mode plus Agent Engine sessions.

---

## 9. Benchmarks, as of October 2026

| Benchmark | What it measures | Latest numbers found | Status |
|---|---|---|---|
| **SWE-bench Verified** | 500 human-validated GitHub issues | Top ~96% (DeepSeek-V4-Pro 96.4%, GPT-5.6 Sol 96.2%, Claude Opus 5 96.0%, Sept 2026) **[UNVERIFIED, aggregator]** | **Saturated and contamination-suspect.** OpenAI reportedly stopped reporting it after finding that frontier models reproduce gold patches **[UNVERIFIED; openai.com 403]**. Move to SWE-bench Pro / Multimodal. |
| **OSWorld-Verified** | 369 desktop tasks (Ubuntu apps) | Human **72.36%** **[PRIMARY]**. First agent above human: Agent S3 72.6% (Dec 2025). Top ~85-86% (Aug 2026) **[UNVERIFIED]** | Saturating. |
| **OSWorld 2.0** | **108 long-horizon tasks**, 31 self-hosted sites, median human time **1.6 h**, >250 steps | **Claude Opus 4.8 20.6%** binary (54.8% partial), Opus 4.7 18.2%, GPT-5.5 ~14% **[PRIMARY, osworld-v2.xlang.ai]** | The new frontier (released 2026-06-26). |
| **Terminal-Bench** | Hard CLI tasks in containers | TB 2.0 top ~82-83% (GPT-5.5 / Codex; Mythos Preview 82%) **[UNVERIFIED]**. tbench.ai now headlines **Terminal-Bench 4.0** **[PRIMARY]** | 2.0 is near saturation. |
| **τ²/τ-bench** | Tool-agent-user dual-control conversations (airline, retail, telecom, banking_knowledge, intake), pass^k | τ³ v1.0 added voice full duplex. τ-bench 2.0 adds i18n and intake. [taubench.com](https://taubench.com) **[PRIMARY]** | Active. Scores not comparable across versions. |
| **GAIA** | General assistant tasks (web, files, reasoning) | Leaderboard on HF; rows not retrieved | Largely saturated at the top **[UNVERIFIED]** |
| **BrowseComp** | 1,266 hard-to-find facts (Wei et al., arXiv 2504.12516, 2025-04-16) **[PRIMARY]** | Frontier deep-research agents score high. Anthropic documented *eval awareness* on it (2026-03-06) | Contamination and eval-awareness concerns |
| **METR time horizon** | Task length (human-expert time) at 50%/80% success | **Claude Mythos Preview 50% ≈ 1,045 min (~17.4 h), 80% ≈ 186 min**. Opus 4.6 ≈ 719 min (~12 h). Gemini 3.1 Pro ≈ 384 min. GPT-5.4 ≈ 342 min. GPT-5 (Aug 2025) ≈ 203 min. Claude 3.7 Sonnet (Feb 2025) ≈ 60 min **[PRIMARY, metr.org YAML]** | Page *"no longer actively updated"* (Sept 2026). *"Measurements above 16 hrs are unreliable."* |

**The trend line for slides.** Using METR's own data, the 50% horizon went from ~1 h (Feb 2025) to ~3.4 h (Aug 2025) to ~12 h (Feb 2026) to ~17 h (Apr 2026). That is roughly a 17× gain in about 14 months, much faster than the ~7-month doubling in the original 2025 paper. The note: horizon = *human* time for the task, not agent wall-clock. The suite is mostly software, ML and cyber, and is nearly saturated.

**Take-home on evals.** By 2026 the short-task benchmarks (SWE-bench Verified, OSWorld-Verified, TB 2.0) are saturated. The frontier moved to **long-horizon** tests (OSWorld 2.0, METR, TB 4.0), **multilingual and voice** tests (τ-bench 2.0), and **infrastructure noise** (Anthropic, "Quantifying infrastructure noise in agentic coding evals", 2026-02-05) **[PRIMARY title]**.

---

## 10. Cross-cutting failure modes (the "why agents still fail" slide)

1. **Prompt injection** through pages, screenshots, issue text, alert payloads. Fix with environment-layer containment first: *"Design for containment at the environment layer first, then steer behavior at the model layer"* (Anthropic 2026-05-25).
2. **Overeager actions** such as force push, prod deploys or `curl | bash`. The auto-mode classifier still misses 17%.
3. **Premature "done"**. Fix with feature lists marked failing, external evaluators and sprint contracts.
4. **Context rot** over long runs. Fix with compaction vs. context resets vs. session-log slicing.
5. **Parallel agents making conflicting decisions** (Cognition). Fix with lock files and tests, or a single thread for writes.
6. **Approval fatigue** (93%). Fix with sandboxes plus a classifier instead of more prompts.
7. **Benchmark contamination and eval awareness**.
8. **Credential exfiltration**: 24 of 25 retries succeeded in Anthropic's controlled red-team exercise. Fix by keeping credentials out of the sandbox entirely.

---

## 11. Likely interview questions, with crisp answers

1. **"How does a modern coding agent differ from ReAct?"** The loop is the same, but now it has a harness: a plan-mode approval gate, an OS or VM sandbox with credentials outside it, a durable session log with checkpoints and rewind, test or evaluator-based verification, and trigger-based launching. The model decides. The harness constrains and verifies.
2. **"Why plan mode?"** It moves human oversight to one high-leverage artifact (the plan). It keeps exploration read-only, so context gathering can't damage anything, and it cuts the number of approvals.
3. **"Sandbox vs. permission prompts?"** Prompts fail because users approve ~93% of them. Sandboxes give a deterministic boundary, with 84% fewer prompts. The classifier handles the rest (0.4% FPR, 17% FNR).
4. **"How do you make an agent run for 6+ hours?"** Use external state (progress file, JSON feature list, git), one feature per session, an init script, end-to-end tests, and an evaluator agent. Make the harness stateless and the session durable (`wake(sessionId)`).
5. **"Single agent or multi-agent?"** Parallelize reads (research, investigation). Serialize writes, or coordinate them through git locks and tests. Share full traces, not summaries.
6. **"How does Gemini computer use handle safety?"** Each proposed action carries a `safety_decision`. `require_confirmation` triggers a human prompt and a `safety_acknowledgement`, and `blocked` halts. A per-step safety service sits outside the model.
7. **"How do you keep a Live API session alive past 15 minutes?"** Turn on context-window compression (sliding window), session resumption handles (valid 2 h), and handle `GoAway`. In ADK, set these in `RunConfig` and use a fresh `LiveRequestQueue` per `run_live`.
8. **"Why is Deep Research background-only?"** Runs take minutes, involve many tool calls and need a reviewable plan. `background=True` plus polling or streaming decouples the run from HTTP timeouts.
9. **"Is 96% on SWE-bench Verified meaningful?"** Not really. It is saturated and contaminated. Look at long-horizon benchmarks (OSWorld 2.0 at ~21%, METR hours, Terminal-Bench 4.0) and at infrastructure noise.
10. **"What does METR's time horizon measure?"** The length of tasks, measured in skilled-human time, that the model completes with 50% reliability. It does not measure agent runtime. Mythos Preview is ~17 h at 50% but ~3 h at 80%, so a reliability gap remains.
11. **"How would you design a secure scheduled agent?"** Scope its repos, connectors and network allowlist. Wrap trigger payloads as untrusted data. Push only to `claude/*`-style branches with branch protection, cap runs per hour, and require human review of PRs.
12. **"What's new in ADK 2.0?"** Graph workflows (deterministic plus LLM nodes, routes, YAML graphs), HITL via `RequestInput` and `require_confirmation`, `FallbackModel`, A2A task mode, LiveKit and CascadeLive voice, and Gemini 3.x computer use.

---

## 12. Slide ideas (with the animation that explains each)

1. **"From ReAct loop to agent system."** Start with a tiny Thought→Action→Observation circle. Animate layers wrapping around it: sandbox box, credential vault outside, session log tape, evaluator, trigger icons. Closing caption: "the loop didn't change; the system did."
2. **Computer-use loop.** A screenshot flies into the model, a red crosshair `click(x,y)` comes out, a traffic light (green / amber "confirm?" / red) gates it, the cursor clicks, a new screenshot flies back. Loop it three times, getting faster.
3. **Plan mode gate.** The agent explores with a dimmed "read-only" lock over the files. A plan document assembles line by line, a human stamp says "Approve", the lock flips open, and edits stream in.
4. **Approval fatigue to sandbox.** A stack of 100 prompt cards: 93 turn green automatically while the human's eyes glaze. Swipe in a sandbox wall, and the cards drop by 84%. The classifier filters the rest, and the "17% FNR" badge stays visible for honesty.
5. **Brain / hands / session (Managed Agents).** Three boxes. Kill the "hands" container (it explodes): the session log persists, the brain calls `wake(sessionId)`, a new container spins up. The TTFT bars shrink by 60% (p50) and 90% (p95).
6. **Long-running harness.** A JSON checklist with every item red. Each "session" card picks one item, runs a browser test, and flips it green with a git commit dot on a timeline. A clock at the side counts to 6 h / $200.
7. **Parallel Claudes building a C compiler.** 16 agents around a git repo, each grabbing a lock file from `current_tasks/`. A collision bounces one agent to another task. The test-pass meter climbs to 99%, and Linux boots on x86, ARM and RISC-V.
8. **Live agent full-duplex.** Two waveforms (user and agent) on a timeline. The user interrupts mid-sentence and the agent waveform cuts off instantly (barge-in). A `GoAway` timer appears at 10 min, a resumption handle hands off to a new connection, and the session continues.
9. **Triggers, not chats.** A clock, a webhook bolt and a GitHub PR icon each fire into the same "saved task" box, which spawns a fresh cloud session and returns a PR. A payload envelope gets stamped "untrusted data".
10. **Benchmark saturation vs. new frontier.** A bar race: SWE-bench Verified, OSWorld-Verified and TB 2.0 hit a ceiling line (human 72% marked on OSWorld). The camera pans right to OSWorld 2.0 at ~21% and a METR log-scale curve rocketing from 1 h to 17 h. Caption: "short tasks are solved; long horizons are the race."

---

## Sources (read in this session unless marked)
- Google, "Introducing the Gemini 2.5 Computer Use model", 2025-10-07: https://blog.google/technology/google-deepmind/gemini-computer-use-model/
- Gemini API computer use docs: https://ai.google.dev/gemini-api/docs/computer-use
- Gemini API Deep Research docs: https://ai.google.dev/gemini-api/docs/deep-research
- Gemini Live API docs and session management: https://ai.google.dev/gemini-api/docs/live , https://ai.google.dev/gemini-api/docs/live-session
- Google Developers Blog, "Plan mode is now available in Gemini CLI", 2026-03-11: https://developers.googleblog.com/en/plan-mode-now-available-in-gemini-cli/
- ADK docs: https://adk.dev/live/sessions/ , https://adk.dev/graphs/ , https://adk.dev/workflows/ ; releases: https://github.com/google/adk-python/releases
- Jules docs: https://jules.google/docs/
- Codex Cloud docs: https://learn.chatgpt.com/docs/cloud
- Anthropic Engineering: effective-harnesses-for-long-running-agents (2025-11-26), harness-design-long-running-apps (2026-03-24), claude-code-auto-mode (2026-03-25), claude-code-sandboxing (2025-10-20), managed-agents (2026-04-08), how-we-contain-claude (2026-05-25), building-c-compiler (2026-02-05): https://www.anthropic.com/engineering
- Claude docs: computer use tool, permission modes, checkpointing, scheduled tasks: https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool , https://code.claude.com/docs/en/permission-modes , https://code.claude.com/docs/en/checkpointing , https://code.claude.com/docs/en/routines
- Cognition, "Don't Build Multi-Agents", 2025-06-12: https://cognition.com/blog/dont-build-multi-agents
- METR time horizons: https://metr.org/time-horizons/ (data: https://metr.org/assets/benchmark_results_1_1.yaml)
- OSWorld: http://osworld-v1.xlang.ai/ ; OSWorld 2.0: http://osworld-v2.xlang.ai/
- τ-bench repo: https://github.com/sierra-research/tau2-bench
- BrowseComp: https://arxiv.org/abs/2504.12516
- Terminal-Bench: https://www.tbench.ai/leaderboard
- [UNVERIFIED secondary] SWE-bench and OSWorld aggregators: benchlm.ai, anotherwrapper.com. OpenAI Agents API / DevDay 2026 recap: codex.danielvaughan.com. Several openai.com pages returned 403.
