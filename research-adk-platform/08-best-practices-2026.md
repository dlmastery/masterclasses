# 08 — Agent Engineering Best Practices (consolidated, as of 2026-10-23)

Research date: 2026-10-23.
Method: every source below was fetched directly in this session unless marked otherwise. WebSearch was unavailable (session budget exhausted), so pages were reached by known URLs only, and newer posts may be missing.
Cross-references: ADK 2.x API details live in `research/01`–`07` (same repo). This file covers what the major vendors **agree on** and maps each practice to ADK 2.x.
Tags: **[UNVERIFIED]** = not confirmed this session. **[SKETCH]** = illustrative code, not copied from a source.

---

## 0. The sources (exact titles, URLs, dates)

| # | Title | Publisher | Date | URL |
|---|---|---|---|---|
| A1 | Building effective agents | Anthropic | 2024-12-19 (the page now notes that tooling has changed) | https://www.anthropic.com/engineering/building-effective-agents |
| A2 | How we built our multi-agent research system | Anthropic | 2025-06-13 | https://www.anthropic.com/engineering/multi-agent-research-system |
| A3 | Writing effective tools for agents — with agents | Anthropic | 2025-09-11 | https://www.anthropic.com/engineering/writing-tools-for-agents |
| A4 | Effective context engineering for AI agents | Anthropic | 2025-09-29 | https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents |
| A5 | Building agents with the Claude Agent SDK | Anthropic | 2025-09-29 | https://claude.com/blog/building-agents-with-the-claude-agent-sdk |
| A6 | Code execution with MCP: Building more efficient agents | Anthropic | 2025-11-04 | https://www.anthropic.com/engineering/code-execution-with-mcp |
| A7 | Introducing advanced tool use on the Claude Developer Platform | Anthropic | 2025-11-24 | https://www.anthropic.com/engineering/advanced-tool-use |
| A8 | Effective harnesses for long-running agents | Anthropic (Justin Young) | 2025-11-26 | https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents |
| A9 | Demystifying evals for AI agents | Anthropic | 2026-01-09 | https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents |
| A10 | Vision (docs) | Anthropic | live docs, read 2026-10-23 | https://platform.claude.com/docs/en/build-with-claude/vision |
| O1 | A practical guide to building agents (PDF, 34 pp) | OpenAI | 2025 [month UNVERIFIED; widely reported as April 2025] | https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf |
| O2 | GPT-5 Prompting Guide (cookbook; now marked "archived recipe") | OpenAI | 2025 [date not on page] | https://developers.openai.com/cookbook/examples/gpt-5/gpt-5_prompting_guide |
| O3 | OpenAI Agents SDK docs | OpenAI | live | https://openai.github.io/openai-agents-python/ |
| G1 | Gemini 3 developer guide | Google | live | https://ai.google.dev/gemini-api/docs/gemini-3 |
| G2 | Prompt design strategies | Google | live | https://ai.google.dev/gemini-api/docs/prompting-strategies |
| G3 | Media resolution | Google | live | https://ai.google.dev/gemini-api/docs/media-resolution |
| G4 | Video understanding / Files API | Google | live | https://ai.google.dev/gemini-api/docs/video-understanding , https://ai.google.dev/gemini-api/docs/files |
| G5 | ADK docs: Safety, Plugins, Artifacts, Context caching | Google | live | https://adk.dev/safety/ , https://adk.dev/plugins/ , https://adk.dev/artifacts/ , https://adk.dev/context/caching/ |
| G6 | Kaggle whitepapers: Introduction to Agents; Agent Quality; Prototype to Production | Google | Nov 2025 | https://www.kaggle.com/learn-guide/5-day-agents (details in `research/06` §10) |
| G7 | Google Cloud "Startup technical guide: AI agents" | Google Cloud | 2025 **[UNVERIFIED: not fetched; no search budget]** | — |
| L1 | State of Agent Engineering | LangChain | 2026-06-12 (survey Nov 18 – Dec 2, 2025) | https://www.langchain.com/state-of-agent-engineering |
| H1 | 12-Factor Agents | HumanLayer (Dex Horthy) | 2025 | https://github.com/humanlayer/12-factor-agents |
| S1 | The lethal trifecta for AI agents | Simon Willison | 2025-06-16 | https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/ |
| S2 | Agents Rule of Two: A Practical Approach to AI Agent Security | Meta AI | 2025-10-31 | https://ai.meta.com/blog/practical-ai-agent-security/ |
| S3 | OWASP Top 10 for Agentic Applications for 2026 | OWASP GenAI Security Project | 2025-12-09 | https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/ |

---

## 1. The ten-second version (title slide)

1. **Start with the simplest thing that works.** Use one LLM call, then a workflow, then one agent with tools. Go multi-agent last. (A1, O1)
2. **Context is the product.** Aim for "the smallest possible set of high-signal tokens" (A4). An agent is "a system dedicated to the art of context window curation" (G6).
3. **Tools are an interface for the model (ACI).** Design them as carefully as UX: few, well-named, token-frugal, and hard to misuse. (A1, A3)
4. **Evals before features.** Start with 20–50 tasks drawn from real failures and read the transcripts. (A2, A9)
5. **Assume prompt injection works.** Use least privilege, the Rule of Two, deterministic guardrails outside the model, and HITL for irreversible actions. (S1, S2, O1)
6. **Own the loop and the state.** Make runs resumable, idempotent, traced, and versioned. (H1, A2, A8)

---

## 2. Start simple — the complexity ladder

**Anthropic's definitions (A1):**
- **Workflows** are "systems where LLMs and tools are orchestrated through predefined code paths."
- **Agents** are "systems where LLMs dynamically direct their own processes and tool usage."

Rule: "find the simplest solution possible, and only increas[e] complexity when needed."

**OpenAI (O1):** "maximize a single agent's capabilities first … often a single agent with tools is sufficient." Split into more agents only "when your agents fail to follow complicated instructions or consistently select incorrect tools."

**When an agent is worth it (O1):**
- complex decision-making (for example, refund approvals),
- rulesets that are hard to maintain (for example, vendor security reviews),
- heavy reliance on unstructured data.

**The ladder (diagram in words; five rungs, climb only when evals show the lower rung fails):**
`single call + retrieval` → `prompt chain / router (workflow)` → `single agent + tools (loop)` → `orchestrator-workers / manager-as-tools` → `multi-agent with handoffs / A2A`.

**The cost of climbing (A2):** agents use about **4×** the tokens of chat, and multi-agent systems about **15×**. Token usage alone explained about **80%** of performance variance on BrowseComp. "Multi-agent systems work mainly because they help spend enough tokens to solve the problem." Their multi-agent setup (Opus 4 lead, Sonnet 4 subagents) beat single-agent Opus 4 by **90.2%** on Anthropic's internal research eval.

**ADK 2.x mapping:**
- workflow rungs → `Workflow` graph edges / deterministic nodes,
- single agent → `LlmAgent` with tools,
- manager pattern → `AgentTool` / coordinator with `sub_agents`,
- cross-org → `RemoteA2aAgent`.

See `research/02`, `research/07`.

---

## 3. Instructions and system prompts

The vendors converge on six practices:

| Practice | Source | Exact guidance |
|---|---|---|
| Right altitude | A4 | "the Goldilocks zone" between brittle hard-coded logic and vague guidance. Start minimal and add instructions only for observed failures. |
| Few canonical examples, not a rule list | A4 | "examples are the 'pictures' worth a thousand words." |
| Derive routines from existing SOPs | O1 | Turn help-center articles and policies into numbered steps. Each step maps to "a specific action or output". Cover edge cases with conditional branches. |
| No contradictions | O2 | GPT-5 "spends reasoning tokens trying to reconcile" conflicting rules. Audit prompts for ambiguity. |
| Structure + critical-first | G2 | Use XML tags (`<role>`, `<constraints>`, `<context>`, `<task>`) or Markdown headings, with one format per prompt. Persona, constraints, and output format go first. For long context, put data first and the question last ("Based on the information above…"). |
| Metaprompting | O1, O2 | Have a strong model convert documents into instructions, or propose minimal prompt edits for a failure. |

**Agentic system-instruction template (G2, Google).** It was evaluated on agentic benchmarks and covers:
- Plan "Before taking any action" (tool call or reply): policy constraints, order of operations, prerequisites, and user preferences.
- Treat exploratory reads as low risk and state changes as high risk. Prefer calling a tool with the information you have over asking for optional details.
- Keep hypotheses open, including less likely ones.
- Retry transient errors. Otherwise, "must change your strategy or arguments, not repeat the same failed call."
- "Once you've taken an action, you cannot take it back."

**Gemini specifics (G1, G2):**
- Keep `temperature` at its default `1.0` on Gemini 3. Lower values "may cause looping or degraded performance."
- The live G2 page says **Gemini 4 and Gemini 3.6+ ignore custom `temperature`/`top_p`/`top_k`**, so remove them from requests.
- Use `thinking_level` ∈ `minimal|low|medium|high`. Do **not** combine it with the legacy `thinking_budget` (that returns HTTP 400).
- Put the current date and the knowledge cutoff in the system instruction ("Remember it is 2026 this year.").
- The G1 page says the default `thinking_level` is `high`, while `research/04` recorded MEDIUM. **Conflict: verify per model.**

**GPT-5 specifics (O2):**
- `reasoning_effort` (default `medium`) controls eagerness. To make the agent less eager, cap tool calls ("an absolute maximum of 2 tool calls") and give an escape hatch.
- For persistence: "Only terminate your turn when you are sure that the problem is solved."
- Use tool preambles: restate the goal, plan, then narrate progress.
- `verbosity` controls final-answer length only.

**ADK:**
- `instruction` supports `{key}` / `{key?}` state templating (raises if a required key is missing). Jinja2 templates arrived in 2.7.0.
- `static_instruction` holds a never-changing prefix, which maximizes cache hits (§9).
- `GlobalInstructionPlugin` sets app-wide policy.

---

## 4. Tool design (the ACI)

**Principles (A1, A3):**
1. **Choose tools for workflows, not endpoints.** Prefer `search_contacts` over `list_contacts`, and merge multi-step operations (`schedule_event`).
2. **Namespace** by service and resource (`asana_projects_search`). Test prefix vs suffix naming, because it changes results.
3. **Return meaningful context.** Resolve UUIDs to names. Offer a `response_format` enum (`concise`/`detailed`); concise used about **⅓ of the tokens**.
4. **Be token-efficient.** Paginate, filter, and truncate with sensible defaults. Claude Code caps tool responses at **25,000 tokens** by default. Truncation messages should steer the agent to narrower queries.
5. **Write actionable errors**, not tracebacks or opaque codes.
6. **Prompt-engineer the descriptions.** Write them "as you would for a new hire" and use unambiguous parameter names (`user_id`, not `user`). Better descriptions alone brought state-of-the-art SWE-bench Verified results with Claude 3.5 Sonnet. In A2, a Claude agent rewriting tool descriptions cut task time by **40%**.
7. **Poka-yoke** (A1): "Change the arguments so that it is harder to make mistakes." For example, require absolute file paths.
8. **Keep tool sets small and non-overlapping.** Bloated tool sets are a top failure mode (A4).

**Scaling to many tools (A6, A7):**
- **Tool Search Tool + `defer_loading: true`**: about 77K → 8.7K tokens (**−85%**). MCP-eval accuracy rose 49% → 74% on Opus 4 and 79.5% → 88.1% on Opus 4.5.
- **Programmatic tool calling / code execution with MCP**: the model writes code that calls tools, so intermediate data never enters context. One workflow went from 150,000 to 2,000 tokens (**−98.7%**). On complex research, average tokens fell 43,588 → 27,297 (−37%). Caveat: code execution needs a sandbox, resource limits, and monitoring.
- **Tool use examples** in definitions raised complex-parameter accuracy from 72% → 90%.

**12-factor framing (H1):**
- Factor 1: "Natural Language to Tool Calls".
- Factor 4: "Tools are just structured outputs". A tool call is JSON that *your* code decides how to execute.

**ADK 2.x code — a well-shaped tool** (pattern from `research/04`, adapted from https://adk.dev/context/):
```python
from google.adk.tools import ToolContext

def add_to_cart(item: str, tool_context: ToolContext) -> dict:
    """Adds an item to the user's cart."""
    cart = tool_context.state.get("user:cart", [])
    cart.append(item)
    tool_context.state["user:cart"] = cart            # persists across sessions
    tool_context.state["temp:last_op"] = "add"        # gone after this invocation
    return {"status": "success", "cart_size": len(cart)}
```
Teach these points from it:
- The docstring is the tool description.
- Use typed parameters.
- `ToolContext` is found by its type annotation and hidden from the LLM.
- Return a dict with a `status` field (success or error) rather than raising for business errors.

---

## 5. Structured outputs

- **Why:** a schema turns the model into a typed function. That makes routing, evals, and downstream code deterministic (H1 Factor 4).
- **Gemini 3 (G1):** combine `response_format` with built-in tools (Google Search, URL Context, Code Execution) and function calling in one request.
- **ADK:**
  - `LlmAgent(output_schema=PydanticModel, output_key="result")` forces JSON and writes it to state.
  - On models without native schema+tools support, ADK falls back to a `set_model_response` tool (https://adk.dev/agents/llm-agents/).
  - 2.13.0 adds `TypesafeClassifier` + `ClassifierNode` for typed routing (`research/01`).
- **OpenAI Agents SDK:** `output_type=` on an `Agent`. Guardrails return `GuardrailFunctionOutput(output_info=..., tripwire_triggered=...)` (O1 code).
- **Best practice:** keep schemas flat and small, use enums for decisions, and validate after parsing. Treat a schema-validation failure as a retryable error and feed it back compactly (§7).

---

## 6. State and memory design

**Principles:**
- **H1 Factor 5:** "Unify execution state and business state."
- **H1 Factor 12:** "Make your agent a stateless reducer". The next step is a function of (event log), with no hidden in-process state.
- **H1 Factor 3:** "Own your context window". You decide what is rendered, not the framework.
- **Just-in-time context (A4, A5):** keep lightweight references (paths, IDs, stored queries) and load data with tools. The file system is context ("folder structure becomes a form of context engineering"). Start with agentic search (grep/tail); semantic search is "usually faster … but less accurate" (A5).
- **Compaction (A4, A5):** summarize when the window nears full. Clearing tool results is the cheapest form.
- **Structured notes (A4, A8):**
  - Persistent progress files outside the window.
  - A8 uses `claude-progress.txt` plus a **JSON feature list** of 200+ items, all initially "failing". The agent may only flip `passes`.
  - JSON was chosen because the model is "less likely to inappropriately overwrite" it than Markdown.
- **Sub-agents for isolation (A4, A5):** each subagent works in a clean window and returns a condensed summary.

**ADK 2.x mapping** (verified in `research/04`, `research/01`):

| Need | ADK construct |
|---|---|
| Per-session scratch | `session.state` (no prefix) |
| Per-user across sessions | `user:` prefix |
| App-wide config | `app:` prefix |
| This invocation only | `temp:` prefix (never persisted) |
| Long-term semantic memory | `MemoryService` / Vertex AI Memory Bank; `sqlite://` memory in 2.11 |
| Binary blobs (images, PDFs) | Artifacts (`save_artifact` / `load_artifact`, versioned) |
| Long sessions | `EventsCompactionConfig(token_threshold=…, event_retention_size=…)` |
| Isolated child | `include_contents='none'` or `AgentTool` |

Anti-pattern (ADK docs): mutating `session.state` on a fetched session outside an invocation. Such changes "will likely NOT be saved".

---

## 7. Error handling, durability, long-running work

- **H1 Factor 9:** "Compact Errors into Context Window". Feed back a short error and let the model self-correct, with a cap on consecutive errors.
- **G2:** retry transient errors. For other errors, change strategy rather than "repeat the same failed call".
- **O1 HITL trigger #1:** "Exceeding failure thresholds", so escalate after N failed attempts.
- **A2:** restarting long agents from scratch is costly. Checkpoint, resume from the failure point, and combine with retry logic. Use **rainbow deployments** so in-flight agents aren't broken by updates.
- **A8 harness pattern (long-running coding agent):**
  - An **initializer agent** writes `init.sh`, a progress log, and the first git commit.
  - Each **coding session** runs `pwd`, reads the git log and progress, picks one failing feature, runs a smoke test *first*, implements, self-verifies end-to-end (Puppeteer, "as a human user would"), then commits.
  - Failure modes it fixes: declaring victory early, leaving a broken environment, marking features done prematurely, and wasting time rediscovering how to run the app.
- **H1 Factor 6:** "Launch/Pause/Resume with simple APIs."

**ADK 2.x** (`research/01`, `research/02`):
- `RetryConfig(max_attempts=3)` on nodes, with exponential backoff (1s, 2s, 4s…, capped at 60s).
- Resume re-runs only failed or interrupted nodes. Since 2.9, failed nodes re-run on resume.
- `FallbackModel` failover (2.9).
- `ReflectAndRetryToolPlugin` and `ReflectAndRetryModelPlugin`.
- `abort_signal` (2.11).
- `ADK_MAX_LLM_CALLS` caps runaway loops (2.8).
- **Failure mode unique to ADK 2.x:** a broad `except Exception:` in a tool swallows errors, so retries never fire. Catching `BaseException` traps `NodeInterruptedError` and breaks HITL pauses. Also make tools **idempotent**, because execution is at-least-once on resume.

---

## 8. Model selection and routing

- **O1:** "build your agent prototype with the most capable model for every task to establish a performance baseline. From there, try swapping in smaller models." Not every step needs the smartest model; retrieval and intent classification can use a small, fast one.
- **A1:** routing sends easy queries to smaller models.
- **A2:** match effort to complexity. A simple lookup needs one agent and a few tool calls; complex research may justify more than 10 subagents.
- **L1 (survey):** over **¾** of respondents use multiple models, and more than ⅔ use OpenAI GPT models. About ⅓ deploy their own models; 57% do not fine-tune.
- **Knobs, in order of cheapness:**
  1. thinking/reasoning level (`thinking_level`, `reasoning_effort`),
  2. a smaller model for subtasks,
  3. a router/classifier node,
  4. caching (§9).
- **ADK:**
  - per-agent `model=`,
  - `BuiltInPlanner(thinking_config=…)`,
  - `LiteLlm(model="openai/…")` for non-Gemini models,
  - `FallbackModel`,
  - TS `RoutedLlm` / `RoutedAgent` (experimental; Python equivalent [UNVERIFIED], see `research/07` §2.14).
- **Failure modes:**
  - a weak router sends hard queries to the cheap model,
  - the router's own cost is ignored,
  - tone differs between models,
  - evals pass on the big model and silently regress on the small one. Run the full suite per model.

---

## 9. Cost and latency budgets

- **Measure first.**
  - L1: **latency is the #2 barrier** (20%), after quality (32%). Cost is cited less often than in earlier years.
  - A9: track tokens, tool calls, and runtime per task alongside accuracy.
- **Budgets to set explicitly:**
  - max LLM calls per invocation (`ADK_MAX_LLM_CALLS`),
  - max tool calls (prompt-level, O2),
  - max wall-clock per node (ADK node `timeout`),
  - max tokens per tool result (25K pattern, A3),
  - max retries.
- **Prompt/context caching:** place the stable prefix first (`static_instruction`), then dynamic content. ADK code (https://adk.dev/context/caching/, via `research/01`):
```python
from google.adk.agents.context_cache_config import ContextCacheConfig
app = App(name='my-caching-agent-app', root_agent=root_agent,
    context_cache_config=ContextCacheConfig(
        min_tokens=2048, ttl_seconds=600, cache_intervals=5))
```
- **Parallelize:** in A2, parallel subagents and parallel tool calls cut research time by **up to 90%**.
- **Keep data out of the model:** code execution / programmatic tool calling (−37% to −98.7% tokens, §4).
- **Stateful APIs:**
  - O2: switching from Chat Completions to the Responses API and passing `previous_response_id` raised Tau-Bench Retail **73.9% → 78.2%**, because reasoning carries across tool calls.
  - G1: `previous_interaction_id` (Interactions API) manages Gemini thought signatures for you.
  - Stateless clients must echo thought signatures back.
- **ADK:** 2.12 cut time-to-first-model-request by 40% in long sessions; 2.13 claims "up to 8x faster execution turns" for string-model agents (`research/01`).

---

## 10. Multimodal handling (images, PDFs, audio, video, live)

The user explicitly asked about this. Best practices with exact numbers:

**Gemini 3 `media_resolution` (G3)**, set per content item via `resolution`:

| Level | Image | Video / frame | PDF / page | Audio |
|---|---|---|---|---|
| `unspecified` (default) | 1120 | 70 | 560 | 25 tok/s |
| `low` | 280 | 70 | 280 + native text | 25 |
| `medium` | 560 | 70 | 560 + native text | 25 |
| `high` | 1120 | 280 | 1120 + native text | 25 |
| `ultra_high` (per item only) | 2240 | n/a | n/a | n/a |

Recommendations:
- Images → `high`.
- **PDFs → `medium`** ("quality typically saturates here").
- General video → `low`/`medium`. Text-heavy video (OCR) → `high`.
- Lower the resolution if a request exceeds the context window (G1).

The video page (G4) quotes older-generation figures: about 100 tok/s of video at default (66 tok/frame low, 258 tok/frame otherwise, 32 tok/s audio), and about 300 tok/s at high. This is model-generation dependent, so **quote G3 for Gemini 3**.

**Gemini code (G3, verbatim):**
```python
from google import genai
client = genai.Client()
myfile = client.files.upload(file="path/to/image.jpg")
interaction = client.interactions.create(
    model="gemini-3.8-flash",
    input=[
        {"type": "text", "text": "Describe this image:"},
        {"type": "image", "uri": myfile.uri, "mime_type": myfile.mime_type,
         "resolution": "high"},
    ],
)
print(interaction.output_text)
```

**Video (G4):**
- Sampling defaults to 1 fps. Use `processing.fps` (e.g. 0.5) and `start_offset`/`end_offset` clipping to cut cost.
- A 1M-context model handles up to **3 h** of video at low resolution, or **1 h** at high.
- Gemini 2.5+ accepts up to **10 videos** per request.
- Put text **after** the video part. Reference moments as `MM:SS`.

**Upload vs inline (G4):**
- Use the Files API when the total request exceeds **100 MB** (PDFs: **50 MB**), for videos over 10 minutes, or for files you reuse.
- Files API limits: 2 GB per file, 20 GB per project, auto-deleted after **48 h**, free.

**Claude vision (A10):**
- **Put images before text.**
- Label multiple images ("Image 1:", "Image 2:").
- Image cost = ⌈w/28⌉×⌈h/28⌉ visual tokens.
- High-resolution tier (Claude 4.7+): 2,576 px long edge, max 4,784 tokens. Standard tier: 1,568 px, max 1,568 tokens.
- Up to 600 images per API request (100 for 200k-context models). Over 20 images triggers a stricter per-image size limit (resize to ≤2000 px).
- **In agent loops, use the Files API `file_id` rather than base64**, because every turn resends history, and base64 bloats every request.
- Computer-use screenshots that exceed the limits are *rejected*, not downscaled, so resize client-side.
- Limits: images under 200 px, counting, precise spatial coordinates, and AI-image detection.

**Cross-vendor multimodal rules:**
1. Downsample to the minimum fidelity the task needs (cost scales with pixels and frames).
2. Upload once and reference by URI/ID inside loops.
3. Text-heavy media need higher resolution (OCR). Natural images rarely need it.
4. Treat text *inside* images, PDFs, and audio as **untrusted input**: a prompt-injection vector, the same as web pages (S1).
5. Store binaries outside the context (artifacts) and pass references.
6. Eval multimodal paths separately, because resolution changes can regress OCR silently.

**ADK multimodal plumbing** (https://adk.dev/plugins/, https://adk.dev/artifacts/):
- `SaveFilesAsArtifactsPlugin` stores user-uploaded files as Artifacts.
- `MultimodalToolResultsPlugin` lets a function tool return a `types.Part` or `list[types.Part]`.
  - Its source says that under default retention, media parts are now moved into the function response by the framework itself (2.7.0 "Tools can return media"). The plugin remains for text parts.
  - `retention="session"` re-attaches `file_data`/text parts on later turns, while `inline_data` bytes stay one-shot. Source: https://github.com/google/adk-python/blob/main/src/google/adk/plugins/multimodal_tool_results_plugin.py
- Artifact best practices (adk.dev/artifacts):
  - always set an accurate IANA MIME type ("the MIME type does" control behavior, not the extension),
  - use the `user:` prefix only for cross-session user files,
  - handle a `None` return on load,
  - plan cleanup with GCS lifecycle rules.

ADK artifact save (verbatim, adk.dev/artifacts):
```python
report_artifact = types.Part.from_bytes(data=report_bytes, mime_type="application/pdf")
version = await context.save_artifact(filename="generated_report.pdf", artifact=report_artifact)
# event.actions.artifact_delta == {"generated_report.pdf": version}
```

**Live / voice (ADK bidi streaming)**, from https://adk.dev/live/ via `research/04` §10:
- Use `LiveRequestQueue` + `runner.run_live(...)` with `RunConfig(response_modalities=["AUDIO"], session_resumption=…, context_window_compression=…)`.
- "The Live API closes each WebSocket connection after about 10 minutes", so always enable session resumption and context-window compression.
- Handle `interrupted: true` events (barge-in).
- OpenAI equivalents (O3): realtime agents on `gpt-realtime-2.1` and STT→agent→TTS voice pipelines.

---

## 11. Security: least privilege and prompt injection

**Threat models:**
- **Lethal trifecta (S1):** private data + untrusted content + external communication = exfiltration risk. Willison: guardrail products claiming "95% of attacks" are a failing grade in security.
- **Agents Rule of Two (S2):** within one session, an agent may have at most two of:
  - [A] processes untrusted input,
  - [B] accesses sensitive systems or private data,
  - [C] changes state or communicates externally.

  If it needs all three, it must not run autonomously: require HITL or a fresh session.
- **OWASP Agentic Top 10 (S3), released 2025-12-09.** Item names recalled from memory **[UNVERIFIED: the page fetch did not return the list]**:
  - ASI01 Agent Goal Hijack
  - ASI02 Tool Misuse
  - ASI03 Identity & Privilege Abuse
  - ASI04 Agentic Supply Chain
  - ASI05 Unexpected Code Execution
  - ASI06 Memory & Context Poisoning
  - ASI07 Insecure Inter-Agent Communication
  - ASI08 Cascading Failures
  - ASI09 Human-Agent Trust Exploitation
  - ASI10 Rogue Agents

**Layered guardrails (O1):**
- relevance classifier,
- safety classifier (jailbreak/injection),
- PII filter,
- moderation,
- **tool safeguards** (rate every tool low/medium/high by read vs write, reversibility, permissions, and financial impact),
- rules-based checks (blocklists, length limits, regex),
- output validation.

"While a single one is unlikely to provide sufficient protection, using multiple, specialized guardrails together creates more resilient agents." Guardrails must be "coupled with robust authentication and authorization protocols."

**Google defence in depth (G5, G6; detail in `research/06` §9):**
1. identity (Agent-Auth vs User-Auth; agents as principals, least privilege),
2. in-tool policy (e.g. SELECT-only on allow-listed tables),
3. Gemini safety filters,
4. callbacks/plugins (`before_tool_callback`, Gemini-as-judge, Model Armor, PII redaction),
5. hermetic sandboxed code execution,
6. evals and tracing,
7. VPC-SC,
8. **escape model output in the UI** (an injected `<img>` tag can exfiltrate data).

ADK hardening:
- 2.8 "fence relayed agent output so it cannot pose as instructions",
- 2.11 `ToolCallIntegrityPlugin` signs stored function calls,
- A2A requires https for non-loopback agent cards (2.9).

**Supply chain:** the LiteLLM 1.82.7/1.82.8 PyPI compromise (ADK docs advisory: "rotate all secrets and credentials"). Pin and hash dependencies.

**ADK tool guardrail (verbatim, https://adk.dev/safety/):**
```python
def validate_tool_params(tool: BaseTool, args: Dict[str, Any],
                         tool_context: ToolContext) -> Optional[Dict]:
    expected_user_id = tool_context.state.get("session_user_id")
    if args.get("user_id_param") != expected_user_id:
        return {"error": "Tool call blocked: User ID mismatch."}
    return None
```
The key idea: **identity comes from trusted state, never from model-chosen arguments.**

---

## 12. Human-in-the-loop

- **O1 triggers:** (1) exceeding failure thresholds, (2) high-risk actions that are "sensitive, irreversible, or have high stakes" (cancel orders, large refunds, payments), kept "until confidence in the agent's reliability grows".
- **H1 Factor 7:** "Contact humans with tool calls". Approval is a structured tool call that pauses the run, and Factor 6 resumes it.
- **ADK** (https://adk.dev/tools-custom/confirmation/, via `research/05`):
```python
async def confirmation_threshold(amount: int, tool_context: ToolContext) -> bool:
    return amount > 1000
tools = [
    FunctionTool(reimburse, require_confirmation=True),
    FunctionTool(reimburse_big, require_confirmation=confirmation_threshold),
]
```
  - Advanced: `tool_context.request_confirmation(hint=..., payload={...})`. The client answers with an `adk_request_confirmation` FunctionResponse.
  - 2.x graphs: `RequestInput` (2.11) and node-level `require_confirmation` (2.12).
- **Design tips:**
  - Show the human the exact arguments and diff, not the model's prose.
  - Set a timeout and a default-deny.
  - Log the approver identity.
  - Feed every rejection into the eval set.

---

## 13. Observability

- **L1:** **89%** have some observability and **62%** have step-level tracing, so observability is table stakes, while evals lag (§14).
- **Trace everything:** every LLM call (model, tokens, latency), tool call (args, result, error), handoff, and HITL pause. In A2, Anthropic traces decision patterns *without* reading conversation contents (privacy).
- **Standard:** OpenTelemetry GenAI semantic conventions.
  - ADK spans: `invoke_agent`, `invoke_workflow`, `execute_tool`, `generate_content`.
  - **2.13.0 breaking:** OTel GenAI v2 is the default and `call_llm` is removed (`research/06` §6).
  - Export: `adk web --otel_to_cloud`, OTLP env vars, Phoenix/Arize, `BigQueryAgentAnalyticsPlugin`.
  - The OpenAI Agents SDK has tracing built in (O3).
- **Dashboards:** task success, pass^k, p50/p95 latency, tokens per task, tool error rate, HITL rate, escalation rate, and cost per resolved task.

---

## 14. Evals-first

**Vocabulary (A9):**
- task,
- trial,
- grader (code / model / human),
- transcript,
- **outcome** (the real end state: "whether a reservation exists in the database", not what the agent claims),
- harness,
- suite.

**Rules:**
1. Start with **20–50 tasks from real failures** (A9). A2 started with about 20 queries.
2. Prefer deterministic graders, use LLM judges where needed (rubric, pairwise; G6 prefers pairwise win-rate), and calibrate them with humans.
3. **Grade outcomes, not paths**, since agents legitimately take different routes (A2, A9). Add trajectory checks only where the path matters (ADK `tool_trajectory_avg_score`, `research/06`).
4. **pass@k vs pass^k:** at 75% per-trial success, pass^3 = 0.75³ ≈ **42%**. Customer-facing agents need pass^k.
5. Keep **capability evals** (start low, hill-climb) separate from **regression evals** (~100%; graduate saturated capability evals into them).
6. Balance cases where a behavior should and should not happen. Isolate trials (clean environment).
7. **Read transcripts.** A 0% score usually means a broken task or grader. Anthropic's CORE-Bench score went 42% → 95% after fixing grader bugs and the scaffold.
8. Close the flywheel (G6 Agent Quality): every production failure becomes a regression test.

**Adoption gap (L1):** only **52.4%** run offline evals and **37.3%** online evals, while quality is the #1 barrier (32%). This is the core argument for the deck.

**ADK:** `adk eval` (CLI), `adk web` (build the golden set by chatting), pytest in CI, and user simulation for multi-turn. Codelab: https://codelabs.developers.google.com/adk-eval/instructions

---

## 15. Deployment and versioning

- **Version everything that changes behavior:** prompts (H1 Factor 2: "Own your prompts"), tool schemas, model IDs (pin them; `gemini-flash-latest` drifts and may not resolve on regional endpoints), eval sets, and agent configs. Prompt changes go through code review and an eval gate.
- **Eval-gated CI/CD (G6 "Prototype to Production"):** PR → unit tests → `adk eval` regression suite → staging with online evals → canary → **rainbow deployment** for long-running sessions (A2).
- **Event-sourced sessions + idempotent tools** make rollbacks and resumes safe (H1 Factor 12; ADK resume semantics).
- **H1 Factor 11:** "Trigger from anywhere, meet users where they are" (Slack, email, cron, webhooks). ADK: Pub/Sub / Eventarc triggers with OIDC verification (2.9).
- **ADK targets:** `adk deploy cloud_run`, `adk deploy agent_engine` (Agent Runtime / Gemini Enterprise Agent Platform), GKE. `agents-cli` / Agent Starter Pack scaffolds CI/CD (`research/05` §7). Codelab: https://codelabs.developers.google.com/next26/adk-deploy-scale (~35 min, under $5).
- **Migration hygiene:** ADK 2.x is not a drop-in replacement for 1.x (Event schema, BaseNode). Pin `google-adk~=1.0` until the regression suite passes on 2.x (`research/01`).

---

## 16. Failure-mode catalogue (one slide, two columns)

| Symptom | Root cause | Fix (source) |
|---|---|---|
| Declares victory early | No explicit done-criteria | JSON feature list plus a self-verify step (A8) |
| Loops / repeats failed call | No error strategy, low temperature on Gemini 3 | Compact errors, "change strategy", temperature 1.0, `ADK_MAX_LLM_CALLS` (H1, G1, G2) |
| Picks wrong tool | Overlapping or bloated tools, vague descriptions | Consolidate, namespace, rewrite descriptions, tool search (A3, A7) |
| Context rot on long tasks | Everything kept in the window | Compaction, notes, sub-agents, JIT retrieval (A4) |
| Cost blowup | Multi-agent 15× tokens, base64 media resent per turn | Climb the ladder only on eval evidence, Files API IDs, caching (A2, A10) |
| Data exfiltration | Lethal trifecta | Rule of Two, least privilege, HITL, UI escaping (S1, S2, G5) |
| "Works on my laptop" regressions | Unpinned models/prompts, no evals | Version + eval gate (A9, H1) |
| Silent multimodal regressions | Resolution/compression changes | Separate multimodal evals, `media_resolution` per item (G3, A10) |
| HITL pause breaks (ADK) | `except BaseException` | Let `NodeInterruptedError` propagate (ADK 2.0 notes) |
| Duplicate side effects on resume | Non-idempotent tools, at-least-once replay | Idempotency keys (ADK 2.x resume semantics) |

---

## 17. The checklist (handout slide)

**Design**
- [ ] Wrote the task as a workflow first. Can I justify the agent loop with an eval?
- [ ] One agent with tools before any multi-agent design. Each extra agent has a measured win.
- [ ] Prototyped on the most capable model, then down-shifted per step with evals.

**Instructions**
- [ ] System prompt at the "right altitude", structured (XML/Markdown), critical items first.
- [ ] Few canonical examples, no contradictions, current date and cutoff stated.
- [ ] Prompts versioned in git and reviewed like code.

**Tools**
- [ ] Few, namespaced, non-overlapping tools built around workflows.
- [ ] Human-readable returns, pagination, truncation with guidance, a `response_format` option.
- [ ] Actionable error messages. Poka-yoke parameters.
- [ ] Every tool risk-rated (read/write, reversible, money). High risk → confirmation.

**State, memory, context**
- [ ] Event-sourced, resumable state; agent as a stateless reducer.
- [ ] Scoped state (`temp:`/session/`user:`/`app:`), artifacts for binaries.
- [ ] Compaction + caching configured, static prefix first.

**Multimodal**
- [ ] Minimum resolution per task (`media_resolution`, pre-resize), Files API IDs in loops.
- [ ] Media placement per vendor (Claude: image first; Gemini: text after video).
- [ ] Text in media treated as untrusted. Separate multimodal eval cases.

**Reliability**
- [ ] Bounded retries with backoff, failover model, max-LLM-call and timeout budgets.
- [ ] Idempotent tools. No broad `except`.

**Security**
- [ ] Rule of Two holds per session, or HITL is enforced.
- [ ] Identity from trusted context, never from model arguments. Least-privilege credentials.
- [ ] Layered guardrails (classifier + rules + Model Armor/moderation + output validation). UI escapes model output.
- [ ] Dependencies pinned (supply chain).

**Evals and ops**
- [ ] 20–50 real-failure tasks, outcome-graded, pass^k reported.
- [ ] Capability vs regression suites. Transcripts read weekly.
- [ ] OTel GenAI tracing, dashboards for success, latency, cost, and HITL rate.
- [ ] Eval-gated CI/CD, canary/rainbow deploys, pinned model IDs.

---

## 18. Codelabs to cite (from `research/03`, fetched there)

- ADK 2.0 instructions codelab: https://codelabs.developers.google.com/adk2/instructions
- Build agents with ADK, foundation: https://codelabs.developers.google.com/devsite/codelabs/build-agents-with-adk-foundation
- Empowering with tools: https://codelabs.developers.google.com/devsite/codelabs/build-agents-with-adk-empowering-with-tools
- ADK evaluation: https://codelabs.developers.google.com/adk-eval/instructions
- Secure customer service agent: https://codelabs.developers.google.com/secure-customer-service-agent/instructions
- Agent Identity and Auth Manager (on-behalf-of): https://codelabs.developers.google.com/agent-identity-auth-manager
- Multimodal personal expense assistant (1.x era, 2025-05-15): https://codelabs.developers.google.com/personal-expense-assistant-multimodal-adk
- Next '26 memory: https://codelabs.developers.google.com/next26/dev-keynote/enhancing-agents-with-memory
- Next '26 skills: https://codelabs.developers.google.com/next26/dev-keynote/building-agents-with-skills
- Next '26 deploy and scale: https://codelabs.developers.google.com/next26/adk-deploy-scale

---

## 19. Interview questions (crisp answers)

1. **Workflow vs agent?** In a workflow, the code fixes the path. In an agent, the LLM chooses the path and tools in a loop. Default to a workflow and pay for agency only where inputs are open-ended (A1).
2. **When go multi-agent?** When one agent fails to follow complex instructions or picks the wrong tools, or when the work is parallelizable breadth-first research. Expect about 15× the tokens of chat (O1, A2).
3. **What is context engineering?** Curating the smallest high-signal token set per step: system prompt, tools, examples, retrieved data, history, through JIT loading, compaction, notes, and sub-agents (A4).
4. **How do you design a tool for an LLM?** Build it around a workflow, namespace it, return readable and paginated output, write actionable errors and a new-hire-quality description, and make the arguments mistake-proof. Then eval and iterate (A3).
5. **pass@k vs pass^k?** pass@k means at least one success in k attempts; pass^k means all k succeed. At 75% per trial, pass^3 ≈ 42%. Customer-facing agents need pass^k (A9).
6. **Why grade outcomes not trajectories?** Valid agents take different paths. Check the end state (the database row exists), and add trajectory checks only for required steps or safety (A9).
7. **Explain the lethal trifecta / Rule of Two.** Private data + untrusted input + an outbound channel enables exfiltration. Allow at most two of the three per session; otherwise require a human or a fresh session (S1, S2).
8. **Why not let the model pass `user_id`?** The model's arguments are attacker-influenced. Bind identity from trusted session state in a `before_tool_callback` (G5).
9. **How do you keep long-running agents on track?** Use an initializer and a progress file, a JSON feature list, one feature per session, a smoke test first, self-verification, and a git commit (A8).
10. **How do you cut cost without losing quality?** Downshift models per step with evals, lower thinking effort, cache the static prefix, use code execution to keep data out of context, parallelize, and use defer-loaded tools (O1, A6, A7).
11. **Multimodal cost control in Gemini 3?** Set `media_resolution` per item: PDFs at `medium` (560/page), images at `high`, video at `low` unless OCR. Clip and lower fps. Use the Files API above 100 MB or for reused files (G3, G4).
12. **Why should Gemini 3 temperature stay at 1.0?** Google says lower values can cause looping or degraded reasoning. Newer models (3.6+, 4) ignore it (G1, G2).
13. **How does ADK 2.x make agents durable?** Graph nodes are checkpointed, resume re-runs only failed nodes, `RetryConfig` retries, and HITL pauses via confirmation or `RequestInput`. Tools must be idempotent, and you must not swallow `BaseException` (research/01, 02).
14. **What does "own your control flow" mean?** H1 Factor 8: the LLM proposes the next step as structured output; your code decides whether, when, and how to execute it, and can pause, approve, or summarize.

---

## 20. Slide ideas (10, with animation)

1. **"The Complexity Ladder."** Five rungs (call → workflow → agent → orchestrator → multi-agent). *Animation:* a climber advances a rung only when an "eval passed" stamp appears. A token meter beside the ladder shows 1× → 4× → 15×.
2. **"Context Is a Budget."** A context window as a bar filling with colored blocks (system, tools, examples, history, tool results). *Animation:* compaction squeezes history into one block, tool search removes about 85% of tool definitions, and a sub-agent pops out with a clean bar and returns one summary chip.
3. **"Tools Are UX for Models."** Before/after: `list_contacts` returning UUID soup vs `search_contacts` returning names with `response_format=concise`. *Animation:* the token counter drops to ⅓ and the error message morphs from a stack trace into an actionable hint.
4. **"98.7%."** One giant number. *Animation:* a 150K-token stream of tool results flows through the model, then gets rerouted through a sandbox box, and only 2K tokens reach the model (A6).
5. **"pass@k Lies to You."** Two curves diverging as k grows (pass@k → 100%, pass^k → 0). *Animation:* a slider for k with live 0.75^k math.
6. **"The Lethal Trifecta / Rule of Two."** A Venn diagram of A/B/C. *Animation:* the third circle slides in, the center flashes red, and a human-approval gate drops into the intersection.
7. **"Defense in Depth."** Concentric rings (identity → in-tool policy → model filters → callbacks/Model Armor → sandbox → UI escaping). *Animation:* an injected instruction arrow pierces outer rings and is stopped at successive layers. Willison's "95% is failing" appears as a caption.
8. **"Pixels Cost Tokens."** The Gemini `media_resolution` table as a heat-strip, and a Claude 1920×1080 screenshot shown at 1,560 vs 2,691 tokens. *Animation:* the resolution dial turns, image sharpness and token counter change together, and the PDF bar plateaus at `medium` ("saturates here").
9. **"The Long-Running Harness."** Session timeline: initializer writes `init.sh` + progress + feature JSON, then coding sessions loop (read log → smoke test → one feature → verify → commit). *Animation:* each session is a new card with an empty context that rehydrates from files; failing features flip green one by one.
10. **"The Eval Flywheel and the Adoption Gap."** A flywheel (define → instrument → evaluate → feed failures back), next to L1 bars: 89% observability, 62% tracing, 52.4% offline evals, 37.3% online evals. *Animation:* production failures drop out as red dots and get absorbed into the golden set; the flywheel speeds up as the eval bar grows.

---

## 21. Open items / to verify before the lecture

- G7 "Startup technical guide: AI agents" (Google Cloud): not fetched, so exact title, date, and URL are unknown. **[UNVERIFIED]**
- OWASP ASI01–ASI10 names (§11): recalled from memory. Confirm from the PDF.
- Gemini 3 default `thinking_level`: G1 page says `high`, while `research/04` recorded MEDIUM. Check per model.
- O1 publication month and O2 publication date: not stated on the fetched pages.
- LangChain L1 numbers are from the 2026-06-12 report page. The survey closed Dec 2025, so it is the newest available as of this date, but not "October 2026" data.
