# 06: Agents That Improve: Memory, Self-Improvement, and Agentic RL (frontier as of Oct 2026)

> Research date: 2026-10-23. Scope: mid-2025 to Oct 2026 only. Sources are primary (vendor docs/blogs, arXiv) unless marked otherwise. `[UNVERIFIED]` means I could not confirm the item against a primary source in this session. The web-search budget ran out partway through, so the later checks were direct fetches of known primary URLs.

---

## 0. The thesis for the deck, in one slide

The 2023 picture of an agent ("ReAct 1.0") was a stateless loop: Thought, Action, Observation, repeat, with a prompt template doing all the work. It forgot everything at session end, never got better from experience, and the model had not been trained to act as an agent. Agents in 2026 differ on three axes:

1. **They remember.** Long-term memory is a managed service or a set of files the agent edits itself. Examples: Vertex AI / Agent Platform Memory Bank, the Claude memory tool and Managed Agents memory, Letta MemFS, Mem0, Zep.
2. **They improve in token space.** The agent turns its own trajectories into reusable strategies, playbooks, or skills, with no change to the weights. Examples: ACE, ReasoningBank, Agent Workflow Memory, Claude "dreaming", Letta sleep-time agents and Mods.
3. **They improve in weight space.** Labs train the model itself on multi-turn tool use with RL in synthetic environments. Examples: Kimi K2 / K2-Thinking, DeepSeek-V3.2, Search-R1, verl agent loops, OpenAI RFT. Training also makes reasoning that is interleaved with tool calls a native capability of the model, not a prompt pattern. Examples: Claude adaptive thinking, Gemini thought signatures, DeepSeek reasoning retention.

The ReAct loop survives only as the outermost skeleton. Each ingredient around it changed.

---

## 1. Long-term memory as a managed service

### 1.1 Vertex AI Agent Engine Memory Bank (now "Agent Platform Memory Bank")

**Definition.** Memory Bank is a managed service. It extracts facts from conversations asynchronously, consolidates them into scoped long-term memories, and serves them back by similarity search.

**Dates and sources**
- Public preview announced **July 8, 2025** in the Google Cloud Blog post "Announcing Vertex AI Agent Engine Memory Bank available for everyone in preview", by Kimberly Milam and George Lee. https://cloud.google.com/blog/products/ai-machine-learning/vertex-ai-memory-bank-in-public-preview
- The research behind it is Google's ACL 2025 paper "In Prospect and Retrospect: Reflective Memory Management for Long-term Personalized Dialogue Agents" (arXiv 2503.08026, Tan et al., Google Cloud AI Research). It reports more than 10% accuracy improvement on LongMemEval over a no-memory-management baseline. *Prospective reflection* summarizes at utterance, turn, and session granularity. *Retrospective reflection* refines retrieval with online RL, using the evidence the LLM cites as the signal.
- The docs now live under `docs.cloud.google.com/gemini-enterprise-agent-platform/scale/memory-bank/...`. The product has been folded into the Gemini Enterprise Agent Platform; the old `agent-builder/agent-engine/memory-bank` URLs still resolve.

**Architecture flow (diagram)**
`Session events` → **Extraction**. A Gemini model keeps only information that matches a configured *memory topic*. → **Consolidation**. Candidates are compared with existing memories in the same *scope*, and the service decides CREATE / UPDATE / DELETE. → **Revisions**. Each memory keeps `extracted_memories` and the final `fact` for every generation request. → **Retrieval**. Either fetch all memories or run a similarity search; results go into the prompt.

**Details verified in the docs**
- Quote: "Only information that matches at least one of your instance's memory topics will be persisted."
- **Managed topics** (defaults): user personal info, user preferences, key conversation details, and explicit remember/forget instructions. **Custom topics** take a label plus a description, and few-shot examples are recommended.
- **Scope**: a dict such as `{"user_id": "123"}`. With Sessions as the source, the scope defaults to the session's `user_id`.
- Consolidation compares against the latest revision by default. `revisions_per_candidate_count` lets it look further back, and `REQUIRE_EXACT_MATCH` narrows the comparison set.
- `GenerateMemories` is a long-running operation. Production code passes `wait_for_completion=False`. `IngestEvents` streams events in and buffers them by volume or time.
- Enterprise controls: VPC-SC, CMEK, data residency, HIPAA, IAM Conditions on memories.

```python
# Async memory generation (Agent Platform SDK)
client.memory_banks.memories.generate(
    ...,
    config={"wait_for_completion": False},
)
```

**ADK integration**, verified at https://adk.dev/sessions/memory/ (the ADK docs moved from google.github.io/adk-docs to **adk.dev**):
- Services: `InMemoryMemoryService` (keyword match, for prototypes), `VertexAiMemoryBankService` (managed extraction plus semantic search), `VertexAiRagMemoryService` (Python only; raw transcripts with vector search).
- Tools: `PreloadMemoryTool` retrieves memories at the start of *every turn*. `LoadMemoryTool` retrieves only *when the agent decides* it needs them.
- Ingestion: `add_session_to_memory`, `add_events_to_memory` (deltas), `add_memory` (explicit `MemoryEntry`).
- CLI: `adk web --memory_service_uri agentengine://<agent_engine_id>`

```python
# ADK (Python) - memory wired via callback; works the same in ADK 2.0
from google.adk.agents import LlmAgent
from google.adk.tools.preload_memory_tool import PreloadMemoryTool

async def save_to_memory(callback_context):
    await callback_context.add_session_to_memory()   # ship session -> Memory Bank

agent = LlmAgent(
    model="gemini-3-flash",            # [UNVERIFIED] pick current model id
    name="concierge",
    instruction="Use remembered user preferences when helpful.",
    tools=[PreloadMemoryTool()],
    after_agent_callback=save_to_memory,
)
```
(The callback method names are verified in the docs. The model id and the exact import path are `[UNVERIFIED]` for 2.0.)

**ADK 2.0 context.** Python v2.0.0 went GA on **May 19, 2026**, Go v2.0.0 on **June 30, 2026**, and TypeScript v2.0.0 on **Aug 21, 2026** (https://adk.dev/2.0/). The headline 2.0 feature is **graph workflows**: deterministic graph routes mixed with LLM reasoning, dynamic workflows, and human input. Memory is *not* a 2.0-specific feature; the same MemoryService API carries over. Two 2.0 changes matter for memory and session stores. The Event schema gains `node_info` and `output`, plus `route` and `isolationScope` in TS. Custom session stores with rigid schemas must be migrated.

**ADK context compaction** (short-term memory hygiene that complements long-term memory):
```python
from google.adk.apps.app import App, EventsCompactionConfig
app = App(
    name="my-agent", root_agent=root_agent,
    events_compaction_config=EventsCompactionConfig(
        compaction_interval=3,  # summarize every 3 invocations
        overlap_size=1,         # keep 1 event of overlap between windows
    ),
)
```

### 1.2 Mem0

- Paper: "Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory", arXiv **2504.19413** (Apr 2025). https://arxiv.org/abs/2504.19413
- Pipeline: an extraction phase pulls candidate facts from the latest exchange plus a rolling summary. An update phase has an LLM choose ADD / UPDATE / DELETE / NOOP against the top similar memories. **Mem0g** adds a graph variant with entity and relation triples.
- **Numbers, with their caveats:** a 26% *relative* gain on LLM-as-judge over OpenAI's memory on LoCoMo, and 91% lower p95 latency than full context (1.44 s vs 17.12 s). In the same table, full context scores **72.9%** against Mem0's 66.9% and Mem0g's 68.4%. Memory buys latency and cost, not accuracy, on this benchmark. Letta and Zep have publicly disputed the methodology. (The table values were cross-checked through a secondary reproduction; check Table 2 of the PDF before quoting them on a slide.)

### 1.3 Zep / Graphiti

- "Zep: A Temporal Knowledge Graph Architecture for Agent Memory", arXiv **2501.13956** (Jan 20, 2025). Results: DMR 94.8% vs MemGPT 93.4%, up to +18.5% accuracy on LongMemEval, and 90% lower latency. Its core is **Graphiti**, a "temporally-aware knowledge graph engine": facts carry validity intervals, so a superseded fact is invalidated, not deleted. (The "bi-temporal" label comes from Zep's own docs and is not in the abstract `[UNVERIFIED wording]`.)
- Why it matters: a temporal KG is the main answer to the *stale or contradictory memory* failure mode. It can answer "what did the user prefer before March?"

### 1.4 The 2026 shift: memory becomes files (and the harness owns it)

This is the newest pattern and the most important memory slide in the deck.

**Claude memory tool**, verified at https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool
- Launched **Sep 29, 2025** together with context editing ("Managing context on the Claude Developer Platform", https://www.anthropic.com/news/context-management). Anthropic reported **+39%** over baseline for memory plus context editing on an internal agentic-search eval, and **+29%** for context editing alone. The model on that eval and its details are Anthropic-internal.
- Tool spec `{"type": "memory_20250818", "name": "memory"}`. Commands: `view`, `create`, `str_replace`, `insert`, `delete`, `rename`, all under `/memories`. **It runs client-side**: you own the storage.
- The API auto-injects this system prompt: *"IMPORTANT: ALWAYS VIEW YOUR MEMORY DIRECTORY BEFORE DOING ANYTHING ELSE … ASSUME INTERRUPTION: Your context window might be reset at any moment, so you risk losing any progress that is not recorded in your memory directory."*
- Security: you must block path traversal (for example `/memories/../../secrets.env`).

```python
import anthropic
from anthropic.tools import BetaLocalFilesystemMemoryTool

client = anthropic.Anthropic()
memory = BetaLocalFilesystemMemoryTool(base_path="./memory")
runner = client.beta.messages.tool_runner(
    model="claude-opus-5-5", max_tokens=1024, tools=[memory],
    messages=[{"role": "user",
               "content": "Remember that customer Acme Corp prefers email follow-ups."}],
)
print(runner.until_done().content)
```

**Claude Managed Agents memory**: public beta **Apr 23, 2026** ("Memory for Claude Managed Agents: agents that learn across sessions", https://claude.com/blog/claude-managed-agents-memory)
- Memory "mounts directly onto a filesystem", and agents read and write it with bash and code execution. Stores can be shared with scopes: an org-wide store can be read-only while a per-user store is read-write. Concurrent agents can work on one store without overwriting each other. Every change goes to an **audit log** (which agent and which session) and supports **rollback and redaction**.
- Customer numbers (vendor-reported): **Rakuten**: 97% fewer first-pass errors, 27% lower cost, 34% lower latency. **Wisedocs**: verification 30% faster.
- Quote (Rakuten, Yusuke Kaji): *"Memory in Claude Managed Agents lets us put continuous learning into production at scale."*

**Letta**: from MemGPT memory blocks to git-backed files
- "Benchmarking AI Agent Memory: Is a Filesystem All You Need?" (Aug 12, 2025, https://www.letta.com/blog/benchmarking-ai-agent-memory). A gpt-4o-mini agent with plain `grep`/`search_files`/`open` tools scored **74.0% on LoCoMo**, above Mem0g's 68.5%. Quote: *"simple filesystem tools are sufficient to perform well on retrieval benchmarks."*
- "Letta's Next Phase" (Mar 16, 2026, https://www.letta.com/blog/our-next-phase/) introduced **context repositories / MemFS**. Memory is projected into **git-backed files** that the agent edits with bash, and skills replace server-side MCP integrations. Agents "reflect, consolidate, and improve automatically."
- "Why Memory Isn't a Plugin" (Apr 3, 2026, Sarah Wooders, https://www.letta.com/blog/why-memory-isnt-a-plugin/) gives the deck its best quote: *"Asking to plug memory into an agent harness is like asking to plug driving into a car."* Also: *"retrieval is a small part of memory."*

**Why files replaced vector-only memory**
1. Frontier models are now RL-trained heavily on coding and file tools, so `grep`/`cat`/`str_replace` are their most reliable tools.
2. Files are human-auditable, diffable, versionable with git, and exportable.
3. The agent itself decides *what* to remember and *how to organize it*: just-in-time retrieval, not pre-chunked RAG.
4. Anthropic's "Effective context engineering for AI agents" (Sep 29, 2025) frames it this way: context is an *attention budget* ("Every new token introduced depletes this budget"), and *context rot* means recall degrades as context grows. The remedies are compaction, structured note-taking (NOTES.md), sub-agents, and just-in-time retrieval.

---

## 2. Self-improving agents in token space (no weight updates)

### 2.1 Agent Workflow Memory (AWM): the precursor
- arXiv **2409.07429** (Sep 2024; older than the scope, kept as the baseline everything below is compared against). It induces reusable *workflows* from trajectories, offline or online, and gives **+24.6% / +51.1% relative success** on Mind2Web / WebArena.

### 2.2 ACE: Agentic Context Engineering (Stanford, SambaNova, UC Berkeley)
- "Agentic Context Engineering: Evolving Contexts for Self-Improving Language Models", arXiv **2510.04618** (Oct 2025), ICLR 2026. https://arxiv.org/abs/2510.04618
- **Definition:** the context is an *evolving playbook* of itemized bullets. Each bullet has an ID and **helpful/harmful counters**. Three roles maintain it: a **Generator** (does the task), a **Reflector** (distills lessons from success and failure), and a **Curator** (emits *delta* updates, merged by deterministic non-LLM logic).
- **Why it replaced earlier prompt optimization (GEPA, Dynamic Cheatsheet, full rewrites):** it fixes two named failure modes. *Brevity bias* means optimizers compress away domain detail. *Context collapse* means iterative full rewrites erode content: in one case a full rewrite shrank an **18,282-token context to 122 tokens** and accuracy fell from **66.7 to 57.1**.
- **Grow-and-refine:** append new bullets, update in place, deduplicate by embedding, and refine either eagerly or lazily (when the window overflows).
- **Numbers:** +10.6% on agent tasks (AppWorld) and +8.6% on finance. Adaptation latency is **86.9% lower** on average. Against GEPA on AppWorld offline: 82.3% lower latency and 75.1% fewer rollouts. **ReAct+ACE scores 59.4% on AppWorld vs IBM CUGA's 60.3%**; CUGA was the top production agent, and ACE beats it on the test-challenge split *using open-source DeepSeek-V3.1*.
- **Failure modes the authors state:** it needs a reasonably strong Reflector. Without labels, quality drops (finance offline 81.9 → 77.1). Some tasks, such as HotpotQA, prefer short instructions.

**Architecture flow:** `Query` → Generator (reads playbook) → trajectory + execution feedback → Reflector (multi-round critique, tags bullets helpful/harmful) → Curator (JSON delta: `ADD bullet`, `UPDATE counter`) → deterministic merge → dedupe → playbook v(n+1).

```python
# ACE-style delta, illustrative
delta = {"operations": [
  {"type": "ADD", "section": "api_pitfalls",
   "content": "Venmo API paginates; always loop until page_token is None."},
  {"type": "TAG", "bullet_id": "ctx-00042", "label": "harmful"},
]}
playbook = merge(playbook, delta)      # no LLM rewrite -> no collapse
playbook = dedupe(playbook, embed)     # grow-and-refine
```

### 2.3 ReasoningBank (Google Cloud AI Research, ICLR 2026)
- "ReasoningBank: Scaling Agent Self-Evolving with Reasoning Memory", arXiv **2509.25140** (v1 Sep 29, 2025; v2 Mar 16, 2026). Same Google team as Memory Bank (George Lee, Chen-Yu Lee, Tomas Pfister).
- **Memory item** = {title, one-line description, content}: *distilled strategies*, not raw trajectories. An **LLM-as-judge labels each trajectory success or failure without ground truth**. Successes become strategies; **failures become pitfalls and counterfactual lessons**. Retrieval is embedding top-k (k=1 by default).
- **MaTTS (memory-aware test-time scaling):** *parallel* (self-contrast across N rollouts) or *sequential* (self-refine). It turns extra test-time compute into better memory, which in turn makes later scaling more effective.
- **Numbers:** WebArena +8.3 pts (Gemini-2.5-flash), +7.2 (2.5-pro), +4.6 (Claude-3.7-sonnet). SWE-Bench-Verified 34.2 → 38.8 (flash) and 54.0 → 57.4 (pro). Up to 1.4 fewer steps per task. Learning from failures as well as successes: 46.5 → 49.7, whereas AWM and Synapse do not benefit from failures. A judge that is only about 73% accurate still works, and simulated judges between 70% and 90% accuracy gave similar results.

### 2.4 Productized self-improvement (2026)
- **Claude "dreaming"**, research preview, announced in "New in Claude Managed Agents: dreaming, outcomes, and multiagent orchestration" (https://claude.com/blog/new-in-claude-managed-agents; the page is dated **May 19, 2026**; some press reported May 6). It is *"a scheduled process … that reviews agent sessions and memory stores"*: it finds recurring mistakes and converged workflows and restructures memory. Changes can apply automatically or be human-reviewed. Harvey reported completion rates up about **6x** in tests with dreaming (vendor-reported).
- **Outcomes** (public beta), from the same post: rubric-driven self-correction. A **separate grader in its own context window** checks the output against the rubric, and the agent re-runs if it falls short. Up to **+10 pts task success**, with +8.4% on docx and +10.1% on pptx generation.
- **Letta Mods** (Jun 24, 2026, https://www.letta.com/blog/introducing-mods/) is *harness-level* self-improvement. The agent writes extensions that change its own runtime: new tools, timestamping, a different compaction prompt. *"mods should be created by agents themselves."*
- **Sleep-time compute** (Letta / UC Berkeley, arXiv 2504.13171, Apr 2025) is the theory behind dreaming: precompute over context while idle. It needs about 5x less test-time compute for equal accuracy, gives up to +13% / +18% on Stateful GSM-Symbolic / AIME, and costs 2.5x less per query in the multi-query setting.

**The unifying loop (one diagram):** *Act → Log trajectory → Judge (verifier, rubric, or LLM-judge) → Distill (strategy, pitfall, skill, playbook delta) → Store (files, memory bank) → Retrieve next time → (offline) Consolidate / dream.*

---

## 3. Self-improvement in weight space: agentic RL

### 3.1 Why RL replaced prompted tool use
In ReAct-era agents the model had never been trained to take long chains of actions. It drifted, looped, and fell apart after 10 to 20 steps. Since 2025, labs post-train on **multi-turn trajectories in sandboxed environments with verifiable or rubric rewards**. Long-horizon tool use becomes a learned policy instead of a prompting trick.

### 3.2 Search-R1: the open recipe
- arXiv **2503.09516** (Mar 2025, v5 Aug 2025), from UIUC and Google Cloud AI Research. The model learns to emit `<search>` queries mid-reasoning, using PPO or GRPO with a **simple outcome reward** (exact match). It is +41% (Qwen2.5-7B) and +20% (3B) over RAG baselines.
- **Key trick, retrieved-token masking:** the loss is computed only on tokens the model generated, never on tool output. Every agentic-RL stack now does this.

### 3.3 verl agent loop: the infrastructure pattern
- https://verl.readthedocs.io/en/latest/advance/agent_loop.html. You subclass `AgentLoopBase.run()` and return `prompt_ids`, `response_ids`, and a `response_mask` (1 = LLM tokens, 0 = tool tokens). Rollouts run as **async coroutines** against vLLM or SGLang servers, with sticky sessions per `request_id`. Weights sync from trainer to inference each step, and the KV cache is freed after rollout.
- **Token-in-token-out lesson:** re-applying a chat template to parsed messages causes *decode-encode drift*. verl's authors report that it "kept single-turn PPO from converging". Train on the exact tokens the policy sampled.

### 3.4 Kimi K2 and K2-Thinking (Moonshot)
- "Kimi K2: Open Agentic Intelligence", arXiv **2507.20534** (Jul 28, 2025). A 1T-total / 32B-active MoE trained on 15.5T tokens with **MuonClip** ("zero loss spike"). Post-training uses a **large-scale agentic data synthesis pipeline** plus **joint RL in real and synthetic environments**. Tau2-Bench 66.1, SWE-bench Verified 65.8 (non-thinking).
- **K2-Thinking** (Nov 2025, https://huggingface.co/moonshotai/Kimi-K2-Thinking) was trained end-to-end "to interleave chain-of-thought reasoning with function calls". It keeps *"stable tool-use across 200–300 sequential calls."* HLE scores 44.9 with tools (51.0 heavy) and BrowseComp 60.2. It uses native INT4 QAT and 256K context.

### 3.5 DeepSeek-V3.1 → V3.2
- "DeepSeek-V3.2: Pushing the Frontier of Open Large Language Models", arXiv **2512.02556** (Dec 2, 2025).
- **Agentic task synthesis:** "over 1,800 distinct environments and 85,000 complex prompts". Table 1 breaks it down: search agent 50,275, code agent 24,667, code interpreter 5,908, general agent 4,417. The general-agent pipeline alone synthesizes 1,827 environments.
- **RL:** GRPO, with a post-training budget **above 10% of pre-training cost**, which is large for the field. The high-compute Speciale variant reports IMO/IOI 2025 gold.
- **Thinking-context management for tools:** *"Historical reasoning content is discarded only when a new user message is introduced."* Reasoning persists across tool calls inside a turn. This is the same policy as Claude and Gemini (Section 4).
- (DeepSeek-V3.1, Aug 2025, introduced hybrid think/non-think modes and stronger post-trained tool use. The details here come from memory and have not been re-fetched `[UNVERIFIED specifics]`.)

### 3.6 OpenAI RFT / Agent RFT
- The RFT guide (https://developers.openai.com/api/docs/guides/reinforcement-fine-tuning) describes **programmable graders** (`string_check`, `score_model`, `multi`, Python) and a **"Grading with Tools"** section: you supply the tools on each data point, and the grader rewards tool-call content.
- **Status in Oct 2026:** the page states RFT is "supported on o-series reasoning models only, and currently only for o4-mini". The `o4-mini-2025-04-16` base model shuts down **Oct 23, 2026**, and existing customers can create jobs until **Jan 6, 2027**. For the deck, present RFT as the pattern that proved graded RL fine-tuning could be offered as a product, now being wound down. Do not present it as a current product.
- "Agent RFT" (tool calls to customer endpoints during training) was announced around DevDay Oct 2025 `[UNVERIFIED: the dedicated guide URL now 404s]`.

```json
{"type": "multi",
 "graders": {"compliant": {"type": "string_check",
   "reference": "{{item.compliant}}", "operation": "eq",
   "input": "{{sample.output_json.compliant}}"}},
 "calculate_output": "0.5 * compliant + 0.5 * explanation"}
```

**Agentic RL architecture flow:** `Task synthesizer (env + tools + checker)` → `Async rollout workers` (policy ↔ sandbox, multi-turn, masked tool tokens) → `Reward` (unit tests, exact match, rubric or LLM judge, self-critique) → `GRPO/PPO update` → `Weight sync to inference servers` → repeat.

---

## 4. Model-native agent capabilities: interleaved thinking

**Definition.** The model reasons *between* tool calls inside one assistant turn. It looks at each result before choosing the next action, and that reasoning state persists across calls. In ReAct the "Thought" was visible text written to fit a template. Now the reasoning is trained, often hidden or encrypted, and carried forward by the API.

- **Claude**, verified at platform.claude.com/docs/en/build-with-claude/extended-thinking. Claude 4/4.5 needed the `interleaved-thinking-2025-05-14` beta header. **Adaptive thinking** (`thinking: {type: "adaptive"}` + `output_config: {effort: ...}`) "interleaves automatically", and from Claude 4.7 onward `type: "enabled"` with `budget_tokens` **returns a 400**. Current models named in the docs: Claude Opus 5.5, Sonnet 5 / 5.5, Haiku 5.5, Fable 5.1, Mythos Preview. Opus 4.5 and everything from 4.6 up *keep prior turns' thinking blocks in context*.
  ```python
  client.messages.create(model="claude-opus-5-5", max_tokens=16000,
      thinking={"type": "adaptive"}, output_config={"effort": "high"},
      tools=tools, messages=messages)
  ```
- **Gemini 3.x**, verified at ai.google.dev/gemini-api/docs/thinking#signatures. **Thought signatures** are "An encrypted representation of the model's internal reasoning state". In stateless mode you "**MUST** always resend all `thought` blocks exactly as they were received". In the stateful **Interactions API** (`previous_interaction_id`) the server keeps them. `thinking_level` ∈ {minimal, low, medium, high} depending on model; the docs list gemini-3.8-flash, gemini-3.6-flash, and gemini-3-pro-preview. (The strict 400 on a missing signature during Gemini 3 function calling, launched Nov 2025, was documented at Gemini 3 launch `[UNVERIFIED on current page]`.)
  ```python
  t1 = client.interactions.create(model="gemini-3.8-flash",
        input="Compare GDP growth of Japan and Germany in 2025.",
        generation_config={"thinking_level": "high"})
  t2 = client.interactions.create(model="gemini-3.8-flash",
        previous_interaction_id=t1.id, input="Now as a 3-row table.")
  ```
- **OpenAI GPT-5 era**: Responses API reasoning items are passed back, via `previous_response_id` or encrypted reasoning content, so reasoning persists across tool calls `[UNVERIFIED in this session; well-established since 2025]`.
- **Open models**: DeepSeek-V3.2 keeps reasoning until the next user message. For Kimi K2-Thinking, you append the full assistant message (with its reasoning) back to history.

**Failure mode to teach:** a middleware or framework that strips thinking blocks or signatures, for example by re-serializing messages, silently degrades multi-step tool use, or errors out on Gemini. *Always round-trip the model's own blocks untouched.*

---

## 5. Failure modes (cross-cutting)

| Failure | Where it bites | Mitigation (2026 practice) |
|---|---|---|
| Memory poisoning / prompt injection persisted to memory | Any write-enabled memory | Scoped stores (read-only org memory), audit logs + rollback (Claude MA), topic filters (Memory Bank), human review of dream diffs |
| Stale or contradictory facts | Vector-only stores | Consolidation (UPDATE/DELETE), temporal validity (Zep), revisions |
| Context collapse / brevity bias | LLM-rewritten playbooks | Delta updates + deterministic merge (ACE) |
| Memory bloat → context rot | File memory, playbooks | Dedupe, lazy refine, size caps, expiry, just-in-time reads |
| Learning from wrong signal | Self-judged reflection | Verifiers/rubrics, separate grader context (Outcomes), counters |
| Benchmark theatre | LoCoMo claims | Report vs full-context baseline; use LongMemEval, Letta Memory Bench, Terminal-Bench |
| Reward hacking | Agentic RL | Held-out checkers, rubric + verifiable rewards, sandbox isolation |
| Tokenization drift | RL with chat templates | Token-in-token-out rollouts (verl) |
| Privacy / PII in memory | Personal assistants | CMEK, IAM conditions, redaction from history, path traversal guards |

---

## 6. Likely interview questions with crisp answers

1. **Short-term vs long-term memory in ADK?** Short-term is *Session + State + events*, kept small with `EventsCompactionConfig`. Long-term is a *MemoryService* (Memory Bank), filled through `add_session_to_memory` and read with `PreloadMemoryTool` (every turn) or `LoadMemoryTool` (agent-decided).
2. **Why not just use a 1M-token context?** Cost, latency, and context rot. Mem0's paper shows full context is about 12x slower at p95 (17.1 s vs 1.4 s) for a few points of accuracy. Anthropic treats context as a finite attention budget.
3. **What does Memory Bank's consolidation do?** It compares newly extracted facts against existing memories in the same scope and creates, updates, or deletes, so duplicates and contradictions don't pile up. Every change is kept as a revision.
4. **Why are files winning as the memory substrate?** Models are RL-trained heavily on file and bash tools. Files are auditable, diffable, and git-versioned, and the agent controls what it remembers and how it organizes it. Letta's filesystem agent scored 74% on LoCoMo against Mem0g's 68.5%.
5. **What is context collapse, and how does ACE avoid it?** Repeated LLM rewrites of a context erode its detail (18k tokens shrank to 122, accuracy fell 66.7 → 57.1). ACE uses itemized bullets, deltas from a Curator, deterministic merging, and embedding dedupe.
6. **ReasoningBank vs AWM?** AWM stores workflows from *successful* trajectories only. ReasoningBank also distills strategies and *pitfalls from failures*, using an LLM judge with no labels, and MaTTS feeds extra test-time compute into memory quality.
7. **Token-space vs weight-space learning?** Token space (memory, playbooks, skills) is instant, per-tenant, auditable, and reversible. Weight space (agentic RL) generalizes across tasks and long horizons but is expensive and global. Production systems do both: labs train the weights, and products learn in tokens.
8. **What makes agentic RL different from RLHF?** It is multi-turn, with environment interaction and verifiable or rubric rewards. Tool tokens are masked out of the loss, rollouts are async, and you need environment synthesis at scale (DeepSeek-V3.2: about 1,800 environments, 85k prompts).
9. **What is interleaved thinking, and what breaks it?** The model reasons between tool calls within a turn, and that state persists. It breaks when thinking blocks or thought signatures are stripped or modified. On Claude 4.7+, `budget_tokens` mode returns a 400; use adaptive plus effort.
10. **How do you keep a self-improving agent safe?** Scoped and permissioned memory, audit and rollback, a separate grader context, human review of consolidation ("dreaming") diffs, write filters (topics), and regression evals before promoting learned skills.
11. **How would you evaluate a memory system?** Compare against a full-context baseline on LongMemEval or the Letta Memory Benchmark, track accuracy, p95 latency, and tokens per query, and add adversarial update and contradiction tests.

---

## 7. Slide ideas (with the animation that explains each)

1. **"From goldfish to colleague."** Left: a ReAct loop that resets to blank at session end (animated wipe). Right: the same loop with a memory store that fills up with each session. *Animation:* three sessions play in sequence. On the left the user repeats "I'm vegetarian" every time; on the right the agent recalls it from session 2 onward.
2. **"Memory Bank pipeline."** Session events → Extract (topic filter) → Consolidate (C/U/D) → Revisions → Retrieve. *Animation:* the user says "I moved to Berlin". The old memory card "lives in Paris" flips to UPDATE and the revision history stacks up underneath it.
3. **"Preload vs Load memory in ADK."** Two lanes. *Animation:* in lane 1, memories enter the prompt on every turn (a steady stream of tokens). In lane 2, the agent calls `load_memory` only on turn 3. A token-cost counter ticks up in each lane.
4. **"Memory is a filesystem."** A `/memories` tree with `view`, `str_replace`, and git commits. *Animation:* the agent runs `view /memories`, then edits `preferences.md`, then a git diff appears. Final frame: an audit log row "agent X, session Y" with a rollback button.
5. **"Context collapse vs ACE deltas."** *Animation:* a big context block goes through repeated rewrites and shrinks from 18,282 to 122 tokens while an accuracy gauge drops 66.7 → 57.1. Then an ACE playbook shows bullets with helpful/harmful counters, and small delta chips slide in without anything being lost.
6. **"Learning from failure (ReasoningBank)."** *Animation:* two trajectories, one green and one red. An LLM judge stamps each. The green one distills into a "strategy" card, the red one into a "pitfall" card, and both drop into the bank. On the next task, the right card is pulled back in by similarity.
7. **"The agent dreams."** A timeline of day-time sessions and night-time consolidation. *Animation:* scattered memory notes cluster overnight into a few high-signal files. A diff panel with "approve" lets a human sign off. Harvey's "~6x completion" callout appears with a vendor-reported tag.
8. **"Weight-space learning: the agentic RL factory."** Environment synthesizer → async rollouts → reward → GRPO → weight sync. *Animation:* hundreds of sandbox tiles spin up (counter reaching 1,800 environments and 85k prompts). Tool-output tokens turn grey (masked), and only the model's tokens light up for the gradient.
9. **"Interleaved thinking, model-native."** *Animation:* a horizontal turn where think, tool, think, tool alternate. A lock-icon "thought signature" travels with each call. Then a middleware strips the signature, the chain breaks, and a red "400" appears.
10. **"Two clocks of improvement."** Token space (minutes: memory, playbooks, skills, Mods) vs weight space (months: RL post-training). *Animation:* the fast clock spins per session and the slow clock ticks per model release. Both arrows feed one agent icon labelled "2026 agent".

---

## 8. Source list (primary)

- Google Cloud Blog, "Announcing Vertex AI Agent Engine Memory Bank available for everyone in preview" (2025-07-08): https://cloud.google.com/blog/products/ai-machine-learning/vertex-ai-memory-bank-in-public-preview
- Memory Bank "Generate memories" docs: https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/memory-bank/generate-memories
- Tan et al., "In Prospect and Retrospect: Reflective Memory Management…" ACL 2025: https://arxiv.org/abs/2503.08026
- ADK Memory: https://adk.dev/sessions/memory/ · ADK 2.0: https://adk.dev/2.0/ · Compaction: https://adk.dev/context/compaction/
- Mem0 paper: https://arxiv.org/abs/2504.19413 · Zep paper: https://arxiv.org/abs/2501.13956
- Claude memory tool docs: https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool · Context management (2025-09-29): https://www.anthropic.com/news/context-management
- Anthropic Engineering, "Effective context engineering for AI agents" (2025-09-29): https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- Claude Managed Agents memory (2026-04-23): https://claude.com/blog/claude-managed-agents-memory · Dreaming/Outcomes/Multiagent (2026-05-19): https://claude.com/blog/new-in-claude-managed-agents
- Claude extended/adaptive thinking docs: https://platform.claude.com/docs/en/build-with-claude/extended-thinking
- Letta: "Is a Filesystem All You Need?" (2025-08-12) https://www.letta.com/blog/benchmarking-ai-agent-memory · "Letta's Next Phase" (2026-03-16) https://www.letta.com/blog/our-next-phase/ · "Why Memory Isn't a Plugin" (2026-04-03) https://www.letta.com/blog/why-memory-isnt-a-plugin/ · "Introducing Mods" (2026-06-24) https://www.letta.com/blog/introducing-mods/
- Sleep-time compute: https://arxiv.org/abs/2504.13171
- AWM: https://arxiv.org/abs/2409.07429 · ACE: https://arxiv.org/abs/2510.04618 · ReasoningBank: https://arxiv.org/abs/2509.25140
- Search-R1: https://arxiv.org/abs/2503.09516 · verl agent loop: https://verl.readthedocs.io/en/latest/advance/agent_loop.html
- Kimi K2: https://arxiv.org/abs/2507.20534 · K2-Thinking: https://huggingface.co/moonshotai/Kimi-K2-Thinking
- DeepSeek-V3.2: https://arxiv.org/abs/2512.02556
- OpenAI RFT guide: https://developers.openai.com/api/docs/guides/reinforcement-fine-tuning
- Gemini thinking / thought signatures: https://ai.google.dev/gemini-api/docs/thinking
