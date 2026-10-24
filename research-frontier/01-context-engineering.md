# 01 — Context Engineering: The Core Discipline of Agent Design (2025–Oct 2026)

> Research brief for a university deck. Compiled 2026-10-23. Sources are mid-2025 to Oct 2026 primary material, fetched and checked where noted. Anything I could not confirm against a primary source is marked **[UNVERIFIED]**.
> Note: the web-search quota ran out partway through this research. Every item below comes from a primary page fetched directly by URL.

---

## 0. The one-slide thesis

The 2023 picture of an agent ("ReAct 1.0") was a loop of *Thought → Action → Observation*, appended forever to one growing prompt. By 2025–2026 every serious lab had stopped treating the prompt as a transcript. They treat it as **a scarce, per-call compiled view over external state.** The model is fixed. What separates a good agent from a bad one is which tokens it sees on each call.

- Anthropic: context engineering is "the set of strategies for curating and maintaining the optimal set of tokens (information) during LLM inference." (*Effective context engineering for AI agents*, Anthropic Engineering, **2025-09-29**)
- Karpathy, quoted by LangChain: "the delicate art and science of filling the context window with just the right information for the next step." (*Context Engineering*, LangChain blog, **2025-07-02**)
- Cognition: context engineering is "effectively the #1 job of engineers building AI agents." (*Don't Build Multi-Agents*, Walden Yan, **2025-06-12**)
- Google ADK: "Context is a compiled view over a richer stateful system." (*Architecting efficient context-aware multi-agent framework for production*, Hangfei Lin, Google Developers Blog, **2025-12-04**)
- 12-Factor Agents, Factor 3 "Own your context window": "Everything is context engineering." (Dex Horthy / HumanLayer, github.com/humanlayer/12-factor-agents)

---

## 1. Why it replaced "prompt engineering + ReAct loop"

| Old (2022–early 2024) | New (mid-2025 →) | Why it changed |
|---|---|---|
| Hand-tuned static prompt | A pipeline that builds the context for each call | Agents now run about 50 tool calls per task (Manus). Static prompts can't keep up. |
| Append-only transcript, unbounded | Compaction, context editing, offloading | **Context rot.** Quality falls as tokens grow, well before the window limit. |
| Stuff everything up front (big RAG dump) | Just-in-time retrieval through handles and tools | Every token draws on a finite **attention budget** (n² pairwise attention). |
| All tools loaded every call | Progressive disclosure (Skills, Tool Search, tools as files) | Tool definitions alone ran to ~77K tokens before Tool Search; with it, ~8.7K. |
| Role-play multi-agent "teams" | Sub-agents used for **isolation**, returning short summaries | Cognition showed that splitting work across agents spreads decisions too thin. Isolation is the actual win. |
| Cost scales with output tokens | Cost dominated by input and KV-cache hit rate | Manus input:output ≈ **100:1**. Cached input is 10x cheaper. |

### 1.1 Context rot: the empirical driver
**Chroma Research, "Context Rot: How Increasing Input Tokens Impacts LLM Performance"** (Kelly Hong, Anton Troynikov, Jeff Huber; **2025-07-14**; https://www.trychroma.com/research/context-rot)
- Tested **18 LLMs**, including GPT-4.1, Claude 4, Gemini 2.5 and Qwen3.
- "Lower similarity needle-question pairs increases the rate of performance degradation."
- Distractors have a non-uniform impact. Some hurt far more than others.
- A counter-intuitive result: "structural coherence consistently hurts model performance". Shuffled haystacks beat coherent ones across all 18 models.
- Conclusion: performance is not uniform across input length, even on simple tasks. *How* information is presented matters as much as *whether* it is present.

Anthropic's framing of the same result: as context grows, the model's "ability to accurately recall information from that context decreases". Context is a finite resource with diminishing marginal returns. Every token attends to every other token, so n tokens give n² relationships.

### 1.2 Failure taxonomy (Drew Breunig, popularized by LangChain, 2025)
- **Context poisoning**: a hallucination gets into context and is re-cited from then on.
- **Context distraction**: the context is so long the model over-relies on history instead of what it learned in training.
- **Context confusion**: irrelevant material, such as too many tools, steers the output.
- **Context clash**: parts of the context contradict each other, for example an early wrong assumption against later facts.

---

## 2. The canonical framework: Write / Select / Compress / Isolate
(LangChain, *Context Engineering*, 2025-07-02, https://www.langchain.com/blog/context-engineering-for-agents)

1. **Write**: persist information *outside* the window so it survives (scratchpads, memories, plan files). Example: Anthropic's multi-agent researcher saves its plan to memory so truncation can't lose it.
2. **Select**: pull the right thing *in* at the right time (CLAUDE.md and rules files, memory retrieval, RAG over tool descriptions; LangChain cites ~3x better tool-selection accuracy from retrieving tools).
3. **Compress**: keep only the tokens the task needs (summaries, trimming, pruning, compaction). Claude Code auto-compacts at about 95% of the window.
4. **Isolate**: split context across sub-agents, sandboxes, or state fields the LLM never sees. Multi-agent setups can use **up to 15x** more tokens than chat, so isolation has to pay for itself.

**Diagram flow:** four columns around a central "context window" box. Write arrows go *out* to a filesystem or memory store. Select arrows come *in* from the stores. Compress shrinks the box. Isolate splits it into child boxes, each returning a small summary arrow.

---

## 3. Pattern catalogue (definition → why → flow → implementation → failure modes)

### 3.1 KV-cache-aware context design (stable prefix, append-only)
**Definition.** Lay out context so the longest possible prefix is byte-identical across calls. The provider's prefix cache then reuses the attention computation.

**Source.** *Context Engineering for AI Agents: Lessons from Building Manus*, Yichao "Peak" Ji, **2025-07-18**, https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus
- "the KV-cache hit rate is the single most important metric for a production-stage AI agent."
- Average input:output ratio is about **100:1**. With Claude Sonnet, cached input costs **$0.30/MTok** against **$3/MTok** uncached, a **10x** gap.
- Rules: stable prompt prefix (no timestamps to the second), **append-only** context, **deterministic serialization** (stable JSON key order), explicit cache breakpoints where the provider needs them.
- **"Mask, don't remove."** Adding or removing tools mid-task breaks the cache, and earlier steps then reference tools that no longer exist. Manus keeps every tool defined and uses a state machine that "masks the token logits during decoding". Consistent prefixes (`browser_`, `shell_`) make it easy to mask whole groups.

**Google ADK.** The Dec 2025 blog splits context into a *stable prefix* (system instruction, long-lived summaries) and a *variable suffix* (latest turn, new tool output). A `static_instruction` primitive keeps the prefix immutable. ADK context caching (Python ≥ 1.15.0):
```python
from google.adk.apps.app import App
from google.adk.agents.context_cache_config import ContextCacheConfig  # import path per docs [verify in your version]

app = App(
    name="my-agent",
    root_agent=root_agent,
    context_cache_config=ContextCacheConfig(
        min_tokens=2048,    # Minimum tokens to trigger caching
        ttl_seconds=600,    # Store for up to 10 minutes
        cache_intervals=5,  # Refresh after 5 uses
    ),
)
```
Defaults per https://adk.dev/context/caching/: `min_tokens=0`, `ttl_seconds=1800`, `cache_intervals=10`. ADK Python **v2.8.0** (Aug 2026) added Anthropic prompt-cache breakpoints to `ContextCacheConfig` (github.com/google/adk-python/releases).

**Flow.** `[system + tools: frozen, cached] → [compacted summary: semi-stable] → [recent events: append-only] → [new observation]`. Only the tail changes between calls.

**Failure modes.** A timestamp in the system prompt can make every call a cache miss. So can non-deterministic JSON. So can dynamic tool lists, or editing history in the middle instead of at the tail. Compaction itself rewrites the prefix, so each compaction costs one cache miss. That is a reason to compact rarely and in large chunks.

### 3.2 Just-in-time (JIT) retrieval and handles
**Definition.** The context holds lightweight *identifiers* such as file paths, URLs, query names and artifact IDs. The agent dereferences them with tools only when it needs the content.
- Anthropic (2025-09-29): agents keep "lightweight identifiers (file paths, stored queries, web links, etc.)" and load data at runtime. Claude Code uses `head`/`tail`/`grep` on large data instead of loading whole files. Anthropic calls the overall pattern a hybrid: some content (CLAUDE.md) goes in up front, the rest is explored with glob/grep.
- **Why it beat RAG-dump.** Pre-computed embeddings go stale and fill the window with near-miss chunks, which are exactly the distractors Chroma measured. JIT lets the agent navigate progressively, using file names, folder structure and timestamps as metadata.
- **Google ADK Artifacts.** "Large data lives in the artifact store, not the prompt." The agent sees a name and version handle and loads the content with `LoadArtifactsTool` when needed, then offloads it again (Google Dev Blog, 2025-12-04).
- **Progressive disclosure of capabilities (same idea, applied to tools and instructions):**
  - *Agent Skills* (Anthropic, **2025-10-16**): level 1 is `name` + `description` in the system prompt. Level 2 is the full `SKILL.md`, read when relevant. Level 3+ is linked files read on demand.
  - *Tool Search Tool* (Anthropic, **2025-11-24**, *Introducing advanced tool use*): `"defer_loading": true` on a tool definition. About **85%** fewer tokens (~77K → ~8.7K). MCP-eval accuracy: Opus 4 **49% → 74%**, Opus 4.5 **79.5% → 88.1%**.
  - *Code execution with MCP* (Anthropic, **2025-11-04**): MCP servers are exposed as a file tree of code modules. One example workflow drops from **150,000 → 2,000 tokens (−98.7%)**.

**Failure modes.** JIT costs latency, one tool round-trip per lookup. Weak models also navigate badly: they over-explore, or fail to dereference a handle at all. Mitigations: good tool descriptions, plus a small amount of pre-loaded "map" context.

### 3.3 Tool-result offloading to the filesystem
**Definition.** Big observations are written to disk or an artifact store. The context keeps only a pointer and a short preview. The step is **reversible**, because the agent can read the file back.
- Manus: the file system is "unlimited in size, persistent by nature, and directly operable by the agent itself." Compression must be *restorable*: drop the page body, keep the URL.
- Lance Martin's write-up of a Manus webinar (*Context Engineering in Manus*, **2025-10-15**, rlancemartin.github.io): every tool result has a **full** form (in the sandbox) and a **compact** form (a path). Stale results are swapped to compact form while recent ones stay full. Manus uses **fewer than 20 atomic tools** (bash, filesystem, code execution). MCP tools are reached through a CLI from bash, and search uses `glob`/`grep` rather than a vector index.
- LangChain Deep Agents (*Context Management for Deep Agents*, Curme & Daugherty, **2026-01-28**): a tool response **over 20,000 tokens** goes to the filesystem, leaving a path and a **10-line preview**. When context passes **85%** of the window, old write/edit tool *inputs* are replaced with file pointers. Summarization runs only after that.

**Minimal implementation (illustrative, framework-agnostic):**
```python
MAX_INLINE = 20_000  # tokens, Deep Agents default

def wrap_tool_result(call_id: str, result: str, count_tokens) -> str:
    if count_tokens(result) <= MAX_INLINE:
        return result
    path = f"/workspace/tool_outputs/{call_id}.txt"
    open(path, "w").write(result)
    preview = "\n".join(result.splitlines()[:10])
    return f"[offloaded {count_tokens(result)} tokens to {path}]\n{preview}\n…use read_file/grep to inspect."
```

### 3.4 Compaction (summarize-and-restart) and context editing (rule-based clearing)
**Definition.** *Compaction*: when context nears a threshold, summarize the older history into a dense block, keep recent turns verbatim, and continue. *Context editing* is the lighter form: rule-based removal of stale tool results or thinking blocks, with no LLM summarizer.

- Anthropic (2025-09-29): Claude Code compaction keeps architectural decisions, unresolved bugs and implementation details, drops redundant tool output, and continues with the summary plus the **five most recently accessed files**. Clearing old tool results is "the safest, lightest touch form of compaction".
- *Managing context on the Claude Developer Platform* (**2025-09-29**, claude.com/blog/context-management): context editing alone gave **+29%** on an internal agentic-search eval. Memory tool plus context editing gave **+39%**. Token use fell **84%** on a 100-turn web-search eval, and agents finished workflows that otherwise failed.
- By Oct 2026 the Claude API offers **server-side compaction** in two modes: *on demand* (beta header `compact-2026-09-04`, top-level `compaction` parameter) and *at a token threshold*. Both can keep recent turns verbatim and can run in the background (platform.claude.com/docs/en/build-with-claude/compaction, fetched 2026-10-23).
- **Manus ordering rule** (via L. Martin): prefer reversible compaction (full → path) first. Only when that stops helping, summarize **from the full results** using a **fixed schema**.

**Google ADK compaction** (https://adk.dev/context/compaction/). Supported since Python **v1.16.0**, Go v2.3.0, Java v0.2.0, TS v0.6.0. Two strategies; if both are set, token-based wins:
```python
from google.adk.apps.app import App, EventsCompactionConfig
from google.adk.apps.llm_event_summarizer import LlmEventSummarizer
from google.adk.models import Gemini

app = App(
    name="my_compacting_agent_app",
    root_agent=root_agent,
    events_compaction_config=EventsCompactionConfig(
        token_threshold=4000,      # token-based (primary): compact when exceeded
        event_retention_size=5,    # keep last 5 raw events verbatim
        compaction_interval=10,    # sliding window (turn-based) fallback
        overlap_size=2,            # events shared between windows
        summarizer=LlmEventSummarizer(llm=Gemini(model="gemini-flash-latest")),
    ),
)
```
The docs present the token and sliding-window settings as separate examples. Combining all of them in one config is my own composition **[verify that combining is allowed in your version]**. Mechanics: compaction runs inside `SingleFlow` through `CompactionRequestProcessor`. The summary is written back into the session as an event, and the raw events stay in storage. With interval=3 and overlap=1, compaction fires after events 3, 6 and 9, and each window overlaps the previous one by one event. Recent 2.x releases: v2.11.0 keeps credential-request events out of the compaction prompt; v2.13.0 (2026-10-23) adds telemetry counting compactions per workflow.

**Flow (animatable).** The event log grows past the threshold line. The oldest block of events folds into one "summary" card. The last N events stay raw. The raw originals slide down into the session store, still recoverable.

**Failure modes.**
- **Context collapse / brevity bias** (see ACE, §3.7): repeated LLM rewrites erode detail.
- Summarizer drops the one constraint a later step needs. Mitigation: a custom summarization prompt or a fixed schema (intent, artifacts, decisions, open issues, next steps).
- Cache misses after every compaction.
- Poisoning: a hallucination gets baked into the summary and now looks authoritative.

### 3.5 Structured note-taking, scratchpads, and recitation (the "Write" pillar)
**Definition.** The agent writes notes, todo lists and progress logs to persistent storage outside the window, then re-reads them after compaction or a session reset.
- Anthropic's Pokémon example: Claude keeps notes across thousands of steps, e.g. "for the last 1,234 steps I've been training my Pokémon in Route 1, Pikachu has gained 8 levels toward the target of 10". After resets it reads its notes and carries on with multi-hour play.
- **Memory tool** (public beta with Sonnet 4.5, 2025-09-29): Claude reads and writes files in a memory directory that **lives on the developer's own infrastructure**, so they persist across conversations.
- **Manus recitation:** a `todo.md` rewritten every step. "By constantly rewriting the todo list, Manus is reciting its objectives into the end of the context". This pulls the goal back into recent attention and counters lost-in-the-middle. **Later revision** (L. Martin, Oct 2025): about a third of actions went to updating the todo list, so Manus moved planning into a dedicated **planner sub-agent**. That makes a good slide on how fast these patterns change.
- **Long-running harness** (*Effective harnesses for long-running agents*, Anthropic, **2025-11-26**): an *initializer agent* writes `init.sh`, `claude-progress.txt`, a JSON feature list (200+ features, all starting as `"passes": false`) and an initial git commit. Each later *coding agent* reads progress and git log, implements **one** feature, tests end-to-end, commits, and updates the log. JSON was chosen because models are less likely to overwrite it inappropriately than Markdown. Compaction alone was not enough for multi-day projects.
- **Google ADK Memory.** `VertexAiMemoryBankService` (LLM-extracted, consolidated memories) or `InMemoryMemoryService`. Two retrieval styles: `load_memory`, a tool the agent decides to call, and `PreloadMemoryTool`, which retrieves automatically each turn. Saving is done from a callback:
```python
async def auto_save_session_to_memory_callback(callback_context):
    await callback_context.add_session_to_memory()
```
ADK 2.x adds SQLite (v2.11.0) and MongoDB (v2.13.0) memory services, plus a `delete_memory` API (v2.13.0). Google's rule: "Memory must be searchable (not permanently pinned)."

### 3.6 Isolation via sub-agents (the "Isolate" pillar)
**Definition.** Give a sub-task a **clean** context window. The sub-agent may spend tens of thousands of tokens exploring and returns a **condensed 1,000–2,000-token summary** (Anthropic, 2025-09-29).
- **The 2025 debate.** Cognition's *Don't Build Multi-Agents* gives two principles: "Share context, and share full agent traces, not just individual messages" and "Actions carry implicit decisions, and conflicting decisions carry bad results". The Flappy Bird example: one sub-agent builds a Mario-style background, the other a bird that doesn't fit it. Anthropic's research system showed that parallel sub-agents *do* win on breadth-first research. The 2026 synthesis: **use sub-agents for read-heavy, parallel exploration that compresses well. Keep writes and decisions in one thread.**
- Manus: sub-agents exist "to isolate context, not to divide labor by job role". Simple tasks pass only instructions. Complex tasks share the planner's full context. Results come back in a schema enforced by constrained decoding.
- **Google ADK.** `include_contents` on `LlmAgent` controls how much caller history a sub-agent inherits. In `'none'` mode the sub-agent sees only the new prompt (Google Dev Blog, 2025-12-04). `AgentTool` wraps an agent as a callable tool that returns only its final output. ADK 2.0's headline feature is **Graph Workflows**, which make execution paths and data handoffs explicit, so the context each node sees becomes a design-time decision (adk.dev, "New in ADK 2.0"; TS 2.0 GA; Python 2.x line at v2.13.0 as of 2026-10-23).
```python
from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool

researcher = LlmAgent(
    name="researcher", model="gemini-flash-latest",
    instruction="Research the question; return <=300 words with sources.",
    include_contents="none",          # isolated: no parent history
)
root = LlmAgent(
    name="lead", model="gemini-pro-latest",
    instruction="Plan, delegate research, then write the answer.",
    tools=[AgentTool(agent=researcher)],  # parent sees only the summary
)
```
(Model names are placeholders. `include_contents` and `AgentTool` are long-standing ADK APIs.)

**Failure modes.** Token blow-up (up to 15x). Inconsistent decisions across children (Cognition). Lossy summaries back to the parent. A "telephone game" when the parent's intent isn't passed down.

### 3.7 Agentic Context Engineering (ACE): contexts that learn
**Paper.** *Agentic Context Engineering: Evolving Contexts for Self-Improving Language Models*, Qizheng Zhang, Changran Hu, … James Zou, Kunle Olukotun (Stanford, SambaNova, UC Berkeley). arXiv **2510.04618** (v1 2025-10-06, v3 2026-03-29), **ICLR 2026**.

**Definition.** Treat the context (system prompt or agent memory) as an evolving **playbook** of itemized strategies that improves from execution feedback, with no weight updates.

**Architecture (three roles):**
1. **Generator** runs tasks and flags which playbook bullets helped or misled.
2. **Reflector** critiques trajectories and extracts lessons, optionally over several refinement rounds.
3. **Curator** turns lessons into **delta entries** and merges them with **deterministic, non-LLM logic**.

Each bullet carries an ID, helpful/harmful counters and its content. **Grow-and-refine**: new bullets get new IDs, existing ones are updated in place, and semantic dedup runs periodically.

**Why it matters (the context collapse problem).** With Dynamic Cheatsheet on AppWorld, one full LLM rewrite shrank context from **18,282 → 122 tokens**, and accuracy fell from **66.7 → 57.1**, *below* the 63.7 no-adaptation baseline. Monolithic rewriting is dangerous. Incremental deltas fix it.

**Numbers.** +10.6% on agent benchmarks, +8.6% on finance. AppWorld with DeepSeek-V3.1: ReAct baseline 42.4 → ReAct+ACE **59.4** offline, **59.5** online, roughly matching the top leaderboard agent IBM CUGA (60.3) with an open model. Adaptation latency is **−86.9%** on average (−82.3% vs GEPA offline; −91.5% latency and −83.6% token cost vs Dynamic Cheatsheet online).

**Illustrative delta (format paraphrased):**
```json
{"op": "ADD", "section": "api_pitfalls",
 "bullet": {"id": "ctx-00217", "helpful": 0, "harmful": 0,
            "content": "Spotify API: paginate with page_index until empty; never assume 1 page."}}
```
**Failure modes.** Feedback quality bounds learning: noisy signals produce bad bullets. The playbook can grow without limit, which brings context rot back unless retrieval and dedup keep up.

### 3.8 12-Factor Agents: context engineering as software engineering
github.com/humanlayer/12-factor-agents (Dex Horthy). The factors most relevant here:
- **F3 Own your context window.** Build your own event-to-prompt serialization, e.g. XML-tagged events with YAML bodies, instead of relying on the framework's default message list. "you need to get your context into the LLM in the most token- and attention-efficient way you can."
- **F9 Compact errors into context window.** Keep a compact form of each error so the model can self-correct. Pairs with Manus's "keep the wrong stuff in".
- **F10 Small, focused agents.** Short loops keep context short.
- **F12 Make your agent a stateless reducer.** `next_step = f(thread)`. All state is an event log you control, which is exactly ADK's "Session = durable event log; working context = compiled view."

Other Manus rules worth a slide:
- **Keep the wrong stuff in.** Failed actions and stack traces left in context steer the model away from repeating them.
- **Don't get few-shotted.** Repetitive histories cause drift, as in Manus's 20-resume batch. Add controlled variation to serialization templates.

---

## 4. Reference architecture (Google ADK 2.x view, for the master diagram)

```
            ┌──────────── Sources (durable) ────────────┐
            │ Session event log │ Memory Bank │ Artifacts │
            └─────────┬──────────────┬─────────────┬──────┘
                      ▼              ▼             ▼ (handles only)
   Request processors (ordered):  instructions → identity → contents(filter,
   include_contents) → compaction summary → memory preload → caching
                      ▼
   Working context = [static prefix: system + tools]  ← cached
                     [compacted summary]               ← rare rewrite
                     [last N raw events]               ← append-only
                     [new user turn / tool result]     ← tail
                      ▼
                    LLM call → tool calls → large results → artifact store
                      ▼                                      (pointer back)
                 events appended → threshold? → async compaction
```
Talking point: **this is a compiler.** Sources are the program, processors are compiler passes, and the working context is the emitted code for a single call.

---

## 5. Key numbers cheat-sheet
| Number | Meaning | Source |
|---|---|---|
| 100:1 | input:output tokens in Manus | Manus, 2025-07-18 |
| 10x | cached vs uncached input price (Sonnet $0.30 vs $3/MTok) | Manus |
| ~50 | average tool calls per Manus task | Manus |
| 18 | models showing context rot | Chroma, 2025-07-14 |
| +29% / +39% / −84% | context editing / +memory / token reduction | Anthropic, 2025-09-29 |
| 1–2K tokens | typical sub-agent return summary | Anthropic, 2025-09-29 |
| 15x | multi-agent token multiplier vs chat | Anthropic via LangChain |
| 85% | Tool Search token reduction (77K→8.7K) | Anthropic, 2025-11-24 |
| 98.7% | code-exec-with-MCP token saving (150K→2K) | Anthropic, 2025-11-04 |
| 20K / 85% | Deep Agents offload / summarize thresholds | LangChain, 2026-01-28 |
| 18,282→122 | tokens lost in one context-collapse rewrite | ACE paper |
| +10.6% / −86.9% | ACE agent gain / adaptation latency | ACE, ICLR 2026 |
| 95% | Claude Code auto-compact trigger (as of mid-2025) | LangChain, 2025-07-02 |

---

## 6. Likely interview questions (crisp answers)

1. **Prompt engineering vs context engineering?** Prompt engineering writes one good instruction. Context engineering designs the *system* that decides, on every step, which tokens (instructions, tools, memory, retrieved data, history) the model sees.
2. **What is context rot and why does it matter if windows are 1M tokens?** Accuracy falls as input grows, even on simple tasks (Chroma, 18 models). A bigger window raises the ceiling but doesn't fix attention dilution, cost or latency. Smallest high-signal context wins.
3. **Name the four strategies.** Write (persist outside), Select (pull in JIT), Compress (summarize/trim), Isolate (sub-agents/sandboxes).
4. **Why is KV-cache hit rate the #1 production metric?** Agents are input-heavy (100:1), and cached tokens are about 10x cheaper and much faster. Design for a stable prefix, append-only history and deterministic serialization.
5. **Why "mask, don't remove" tools?** Removing tools invalidates the cache and leaves dangling references in history. Constrain decoding (logit masks or allowed-tool lists) instead.
6. **Compaction vs context editing vs offloading?** Editing clears stale results by rule, with no summary. Offloading moves content to a file and is *reversible*. Compaction summarizes with an LLM and is *lossy*. Apply them in that order.
7. **How does ADK do compaction?** `EventsCompactionConfig` on `App`: token threshold with `event_retention_size`, or a sliding window with `compaction_interval`/`overlap_size`. The summary is written back as a session event, and an optional custom `LlmEventSummarizer` can be supplied.
8. **When would you use sub-agents, and when not?** Use them for parallel, read-heavy exploration that compresses into a short summary. Avoid them when sub-tasks make interdependent decisions, because of Cognition's "conflicting decisions carry bad results."
9. **What is ACE and what problem does it solve?** It evolves the context as an itemized playbook (Generator/Reflector/Curator with delta merges) instead of rewriting it. That avoids brevity bias and context collapse: +10.6% on agents, −86.9% adaptation latency.
10. **How do you make an agent survive a context reset?** Structured external state: a progress file, a JSON feature list, git history, the memory tool. Then a startup ritual that reads them (Anthropic long-running harness).
11. **Why keep errors in context?** They are evidence. Removing them makes the model repeat the mistake (Manus; 12-factor F9).
12. **How do you avoid loading 100 tools?** Progressive disclosure: Skills metadata, `defer_loading` with tool search, or tools as code files plus code execution.

---

## 7. Slide ideas (with explanatory animations)

1. **"The model is fixed; the context is the program."** *Animation:* a 2023 ReAct transcript scrolls endlessly and turns red as it grows. It morphs into a compiler diagram (sources → processors → working context) with the caption "Context = compiled view" (ADK quote).
2. **Context rot.** *Animation:* a line chart of accuracy against input tokens for several model lines all bending downward. Distractor tokens drop into a haystack and the needle fades. Then the counter-intuitive beat: shuffled haystack beats coherent (Chroma).
3. **Attention budget = n².** *Animation:* 4 tokens with 16 connecting lines, then 40 tokens with a hairball. A "budget bar" drains as tokens enter.
4. **Write / Select / Compress / Isolate.** *Animation:* a central window box. Write arrows fly out to a disk icon, Select arrows pull cards back in, Compress squeezes the box, Isolate splits it into child windows that each send back a tiny envelope.
5. **KV-cache economics.** *Animation:* a prompt bar with a green "cached prefix" segment and an orange tail. A timestamp gets inserted at the start, the whole bar turns orange, and a cost meter jumps 10x. Undo, and it's green again.
6. **Mask, don't remove.** *Animation:* a tool palette where removing a tool shatters the cache and leaves a ghost reference in history. The alternative: tools are greyed out (masked) and the cache stays intact.
7. **Offload, then compact, then summarize (reversibility ladder).** *Animation:* a 50K-token tool result gets replaced by `path + 10-line preview` as the file drops into a folder. The ladder lights up rung by rung, edit → offload → compact → summarize, labelled "reversible" to "lossy."
8. **ADK compaction live.** *Animation:* events 1–9 stack up, and at the threshold line events 1–3 fold into a summary card while one overlap event stays visible. Show the `EventsCompactionConfig` code beside it with each parameter highlighting in sync.
9. **Notes that survive amnesia.** *Animation:* "shift change" between agent sessions. The context window wipes to blank, the new agent reads `claude-progress.txt`, the feature list JSON and the git log, and resumes. Pokémon note as the punchline.
10. **ACE: contexts that learn without collapsing.** *Animation:* left side, a monolithic prompt rewritten by an LLM shrinks from 18,282 to 122 tokens and the accuracy gauge drops below baseline. Right side, Generator→Reflector→Curator ring adding small bullet deltas with helpful/harmful counters ticking up, and the accuracy gauge rising to 59.5.
11. *(bonus)* **Sub-agents: isolation, not org charts.** *Animation:* the Flappy Bird split producing a Mario background and a mismatched bird (Cognition), next to parallel researchers each returning a 1–2K summary to a lead.

---

## 8. Source list (verified by direct fetch 2026-10-23 unless marked)
- Anthropic Engineering, *Effective context engineering for AI agents*, 2025-09-29: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- Claude blog, *Managing context on the Claude Developer Platform*, 2025-09-29: https://claude.com/blog/context-management
- Anthropic Engineering, *Equipping agents for the real world with Agent Skills*, 2025-10-16: https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills
- Anthropic Engineering, *Code execution with MCP*, 2025-11-04: https://www.anthropic.com/engineering/code-execution-with-mcp
- Anthropic Engineering, *Introducing advanced tool use on the Claude Developer Platform*, 2025-11-24: https://www.anthropic.com/engineering/advanced-tool-use
- Anthropic Engineering, *Effective harnesses for long-running agents*, 2025-11-26: https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
- Claude API docs, *Compaction overview* (beta `compact-2026-09-04`): https://platform.claude.com/docs/en/build-with-claude/compaction
- Manus, Yichao "Peak" Ji, *Context Engineering for AI Agents: Lessons from Building Manus*, 2025-07-18: https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus
- Lance Martin, *Context Engineering in Manus*, 2025-10-15: https://rlancemartin.github.io/2025/10/15/manus/
- LangChain, *Context Engineering*, 2025-07-02: https://www.langchain.com/blog/context-engineering-for-agents
- LangChain, *Context Management for Deep Agents*, 2026-01-28: https://www.langchain.com/blog/context-management-for-deepagents
- Cognition, Walden Yan, *Don't Build Multi-Agents*, 2025-06-12: https://cognition.com/blog/dont-build-multi-agents
- Chroma, *Context Rot*, 2025-07-14: https://www.trychroma.com/research/context-rot
- Zhang et al., *Agentic Context Engineering*, arXiv 2510.04618, ICLR 2026: https://arxiv.org/abs/2510.04618
- HumanLayer, *12-Factor Agents*: https://github.com/humanlayer/12-factor-agents
- Google Developers Blog, Hangfei Lin, *Architecting efficient context-aware multi-agent framework for production*, 2025-12-04: https://developers.googleblog.com/architecting-efficient-context-aware-multi-agent-framework-for-production/
- ADK docs: compaction https://adk.dev/context/compaction/ · caching https://adk.dev/context/caching/ · memory https://adk.dev/sessions/memory/ · home (ADK 2.0 Graph Workflows) https://adk.dev/
- ADK Python releases (v2.13.0, 2026-10-23): https://github.com/google/adk-python/releases
- **[UNVERIFIED]**: exact ADK Python 2.0.0 GA date and full 2.0 changelog (not on the releases page I could see). The ContextCacheConfig import path. Whether token-based and sliding-window parameters can be combined in one `EventsCompactionConfig`. Whether Claude Code's 95% auto-compact threshold is still current in Oct 2026.
