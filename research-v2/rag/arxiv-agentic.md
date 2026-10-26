# arXiv sweep: agentic RAG, deep research, RL search agents, multi-hop retrieval, MCP retrieval
Window: papers first submitted 2026-07-23 .. 2026-10-23. Sweep done 2026-10-23.

**Method.** The arXiv export API returned HTTP 429 (the limit is shared with other agents), so I used arxiv.org/search (abstract field, newest first, 100 results per query). I ran 9 queries: "search agent reinforcement learning", "agentic RAG", "deep research agent", "multi-hop retrieval reasoning", "agentic search", "Model Context Protocol retrieval", "query decomposition retrieval agent", "parallel search agent efficiency" and "reasoning model retrieval test-time". That gave about 300 in-window hits. I picked 20 papers and read the abstract and the arXiv HTML full text (`arxiv.org/html/<id>`) for every one except SCOUT (#4), which has no HTML version. All numbers below come from those pages. Affiliations come from the HTML author blocks. An inferred affiliation is marked [UNVERIFIED].

**Scope vs. older research.** `research-rag/03-agentic-rag.md` already covers Search-R1, R1-Searcher, ReSearch, DeepResearcher, the agentic-RAG survey (2501.09136), the ADK/LangGraph code and the hosted deep-research APIs. Nothing below repeats those. Everything here is new since 2026-07-23.

**Date caveat.** The arXiv ID prefix (YYMM) is the v1 month. For the 2607.* papers I checked the v1 date on the abs page (all are 23–29 Jul 2026).

---

## Ranked list (most practical impact first)

| # | arXiv | Short name | One-line "Monday" change |
|---|---|---|---|
| 1 | 2607.26497 | BM25 Wins at Scale | Above ~10M corpus tokens, put BM25 ranked discovery *before* the agent. Do not let the agent grep the corpus. |
| 2 | 2608.01913 | Diagnosing long-horizon search agents | Log cumulative gold recall per step and stop on "evidence sufficient", not on turn count. |
| 3 | 2609.14412 | Question's Gambit | Replace the agent's first search with clue decomposition → per-clue retrieval → union → rerank. |
| 4 | 2608.23992 | SCOUT (PayPal MCP gateway) | Expose only two MCP meta-tools (`tool_search` with BM25+dense RRF, `execute_tool`). |
| 5 | 2610.25779 | OpenSaC: Search as Code | Let the agent write Python that searches, fuses, reranks and prints only what it needs. |
| 6 | 2610.07960 | IndexAct | Return candidate-set *handles and counts*, not passages, until the agent asks to read. |
| 7 | 2610.14428 | Airbnb portable skill | Try a SKILL.md, one hybrid search tool and an LLM-written wiki index before you build a complex RAG stack. |
| 8 | 2608.12888 | ReFind (agentic BM25 over raw chats) | For chat memory, try agent-controlled BM25 over raw turns before you build a memory graph. |
| 9 | 2607.20891 | MisKnow-Agent | Verify evidence where it *enters the research state*, most of all just before synthesis. |
| 10 | 2610.16998 | Glasseek | Block benchmark domains and sandbox file access in your eval harness. Leakage inflates scores. |
| 11 | 2610.23148 | Grounded Credit Assignment (GCA) | Track the "evidence-supported share of correct answers". RL can raise EM while grounding collapses. |
| 12 | 2610.30435 | SARL | At train time, add a self-assessment pass in a fresh context. Nothing is added at inference. |
| 13 | 2610.24854 | Retrieval Program Learning (RPL, Meta) | Expose `sparse/dense/fuse/dedup/rerank` primitives inside a sandbox, not one `search()` tool. |
| 14 | 2610.25269 | EG-GRPO (Ant Group) | If your synthetic data has evidence annotations, turn the "first citation of each evidence item" into step rewards (w=0.5). |
| 15 | 2610.22331 | KnowGPO (ZJU/Tencent) | Group rollouts by *knowledge acquired* (atomic conditions satisfied), not by surface state. |
| 16 | 2609.36505 | BRIDGE (Cornell) | When co-training, adapt the retriever *before* the policy. Order matters. |
| 17 | 2610.13157 | SOAR (ZJU/Microsoft) | Make internal and external knowledge separate, labeled streams, and reward source consistency. |
| 18 | 2610.21512 | QREF (Fudan) | Add a plug-in query refiner and evidence filter in front of an existing deep-search agent. No policy retraining. |
| 19 | 2609.39912 | TRACE (NYU Shanghai) | For parallel rollouts, select with a learned evidence-aware selector, not majority vote. |
| 20 | 2609.22247 | CHART (Amazon) | If you RL-train an agent, rotate system-prompt harnesses during training, or the behavior breaks after a prompt edit. |

Also notable (short entries at the end): 2608.08389 (stage-aware pruning, −73% tokens), 2609.36344 DeepRewind, 2610.29250 SearchWeaver, 2608.20317 BrowseComp-Plus_CM, 2609.16268 Spurious Tool Use, 2608.22167 MCP-Universe RL, 2609.35774 (post-generation verification beats retrieval tweaks), 2607.24010 (when should Active RAG retrieve).

---

## 1. BM25 Wins at Scale: A Scaling Study of Retrieval-Augmented Generation Paradigms
- **arXiv:** 2607.26497 · v1 2026-07-29 · Pengyu Wang et al., University of Science and Technology of China and MetaStone Technology (Beijing).
- **Problem:** Lexical, dense, graph and agentic RAG are each tested on their own benchmark at one corpus size. Nobody knows how they compare as the corpus grows.
- **Method (diagram):**
  1. EnterpriseRAG-Bench: 511,959 documents, 500 questions, fixed per-question relevant and adversarial documents (the "bedrock").
  2. A ladder of 28 strictly nested tiers, each 1.25× the last, from 1,144 to 511,959 docs (1.7M → 601M tokens).
  3. Every paradigm uses the same reader model and judge: BM25, dense, graph RAG, and a "File-System Agent" that explores the raw corpus with tools at query time.
  4. Token-level cost metering covers both construction and query.
- **Key result:** There is a **crossover, not a single winner**. The File-System Agent leads at the smallest tiers, but at the bedrock it costs **39× more query tokens**. **At ~10M corpus tokens BM25 overtakes it** and leads at every larger tier, with a margin **approaching 20 points at full scale**. Dense retrieval is efficient but less accurate. Graph RAG hits "construction walls" before deployment scale.
- **Monday takeaway:** Let the agent reason over a *ranked* candidate list. Do not let it replace ranking with `ls`/`grep` exploration. In the authors' words: "agentic reasoning works best after ranked discovery rather than in place of it." Keep a BM25 index even if you also have vectors.
- **Limitations:** One enterprise benchmark, one reader model. The crossover point (~10M tokens) depends on the corpus.
- **Slide idea:** A log-x line chart (corpus tokens 1.7M → 601M) with 4 lines. Animation: the lines draw left to right, a vertical marker drops at 10M ("crossover"), then a "39× query tokens" badge pops onto the agent line.

## 2. Diagnosing Search Behavior and Failure Modes in Long-Horizon Search Agents
- **arXiv:** 2608.01913 · v1 2026-08-03 · Qi Liu, Renmin University of China (with NUS: Fengbin Zhu, Tat-Seng Chua).
- **Problem:** Does more search effort buy better answers?
- **Method:**
  1. Six agents (Tongyi-DR, Qwen3.5-35B-A3B, gpt-oss-120b, Kimi K2.6, GLM 5.1, DeepSeek V4 Pro) run in the same ReAct harness with the same retriever (Qwen3-Embedding-8B) on BrowseComp-Plus (830 questions, human qrels).
  2. Measure gold-document recall per step, then sort each error into a **retrieval gap** (RG: evidence never found) or a **utilization gap** (UG: evidence found but misused).
  3. Label each episode productive, redundant or unproductive. Classify each query move as repeat, pivot or add.
- **Key result:** Cumulative recall@25 correlates with accuracy at **Pearson r = 0.99**. Visit precision gives r = 0.50 and final context size r = 0.16 (effectively none). **Only 6–23% of episodes are productive; 77.5–93.6% add no new evidence.** RG causes 51.6–64.1% of errors for five of the six agents. Kimi K2.6 is the exception (52.0% UG, 78.2% gold recall). Near-identical consecutive re-queries are "the cleanest behavioral predictor of failure". Evidence arrives early or never.
- **Monday takeaway:** (a) Add per-step "new evidence?" logging and a stopping rule based on evidence sufficiency. (b) Detect near-duplicate queries (Jaccard overlap) and force a pivot. (c) Diagnose per agent: a retrieval gap needs better queries, a utilization gap needs better verification.
- **Limitations:** Closed corpus with qrels. The cross-agent correlations rest on six points, so the authors back them with a within-question panel.
- **Slide idea:** A trajectory "heat strip" per agent: green = productive, grey = redundant, red = unproductive. Animation: the strips fill step by step. Most of each strip turns grey or red after step ~5, then a "wasted tail" bracket appears.

## 3. Question's Gambit: The First Move Matters in Agentic Deep Search
- **arXiv:** 2609.14412 · v1 2026-09-13 · Radin Hamidi Rad, University of Toronto / Mila (with Waterloo: Charles Clarke; UC Berkeley; McGill). Code: https://github.com/radinhamidi/Question-s-Gambit
- **Problem:** Agents start "cold". The first query mixes several clues, which wastes budget before they get a foothold.
- **Method:**
  1. The **decomposer** turns the question into clues, one constraint each. Clues are independent, not a chain of hops, so they can be searched in parallel.
  2. **Per-clue retrieval:** issue the raw clue → feedback docs → expansion in the corpus's own wording (MUGI-style) → search string = clue ⊕ expansion ⊕ question.
  3. **Union** the per-clue lists → **pointwise rerank** against the full question (the repo uses Cohere Rerank 4 Pro) → top-k "opening context" as the first observation.
  4. The normal ReAct loop continues with Preview / Read / Paginate / Retrieve (BM25).
- **Key result:** BrowseComp-Plus with gpt-5.5 inside Pi-Serini (the strongest reported agentic baseline), with the retriever and the rest of the framework held fixed: accuracy goes from **83.1% to 90.5%**. The gain also transfers to MultiHop-RAG.
- **Monday takeaway:** Wrap your agent's *first* tool call as a deterministic `first_move(question)` pipeline. No retraining is needed. This is the cheapest gain in the sweep.
- **Limitations:** Adds reranker cost and one LLM decomposition call. Evaluated mainly on BrowseComp-Plus.
- **Code sketch (illustrative, my own; the repo's actual tools are TypeScript: `constraint_decomp.ts`, `clue_expansion.ts`, `cohere_rerank.ts`):**
```python
def first_move(q, llm, bm25, rerank, k=10):
    clues = llm.json(f"List the independent constraints in: {q}")  # ["born in 1950s", ...]
    pool = {}
    for c in clues:
        fb = bm25.search(c, k=5)                                    # let the corpus show its wording
        exp = llm.text(f"Rewrite '{c}' using terms from: {[d.snippet for d in fb]}")
        for d in bm25.search(f"{c} {exp} {q}", k=50):
            pool[d.id] = d                                          # union + dedup
    return rerank(q, list(pool.values()), top_n=k)                  # opening context
```
- **Slide idea:** A question card "shatters" into 4 clue chips. Each chip shoots a beam into a corpus grid, the hits merge into one pool, a reranker funnel narrows it to the top 10, and the gauge shows 83.1 → 90.5.

## 4. Hybrid Semantic Tool Discovery for Enterprise MCP Gateway (SCOUT)
- **arXiv:** 2608.23992 · v1 2026-08-25 · Olympia Saha et al. (PayPal deployment per abstract; author affiliations not shown because there is no HTML version [UNVERIFIED beyond the abstract]).
- **Problem:** A proxy MCP gateway exposes 2,000+ tools from 200+ servers. The full schemas fill the context before the user's query arrives. Prompt caching cuts cost but frees no context.
- **Method:**
  1. Treat tool exposure as context selection.
  2. Expose only **two MCP meta-tools: `tool_search` and `execute_tool`**.
  3. `tool_search` runs **hybrid retrieval**: BM25 plus dense vectors, fused with **Reciprocal Rank Fusion**, returning the top-k tool schemas.
  4. Zero-downtime catalog update pipelines keep the index fresh. Clients need no changes.
- **Key result:** In production at PayPal, MCP tool tokens fall from **140.2k (70.1% of context) to 1.3k (0.8%)**, a 99% reduction.
- **Monday takeaway:** With more than ~50 MCP tools, stop listing them all. Put a tool-retrieval index behind a `tool_search` tool. This is RAG over tools.
- **Limitations:** Industry report. The abstract gives no accuracy comparison against full exposure.
- **Code sketch (illustrative pattern, not PayPal's code):**
```python
# MCP server exposing two meta-tools (FastMCP-style)
@mcp.tool()
def tool_search(query: str, k: int = 5) -> list[dict]:
    bm = bm25_rank(query); dn = dense_rank(query)
    return [catalog[t].schema for t in rrf([bm, dn], k=60)[:k]]

@mcp.tool()
def execute_tool(name: str, arguments: dict) -> dict:
    return gateway.call(name, arguments)       # auth/policy/observability chokepoint
```
- **Slide idea:** A context-window bar that is 70% full of tool schemas shrinks to a 0.8% sliver. A counter animates from 140.2k to 1.3k.

## 5. OpenSaC: A Python Library for Search as Code in Deep Research Agents
- **arXiv:** 2610.25779 · v1 2026-10-19 · Qi Liu, Renmin University of China (with NUS, Ji-Rong Wen). Code: https://github.com/liuqi6777/OpenSaC
- **Problem:** The usual loop (think → one search → read) puts every result into the context and costs a model turn for each action.
- **Method:**
  1. The agent writes **programs** that compose search, fetch, rerank, LLM calls and local processing.
  2. Only what the program *prints or returns* becomes an observation. Intermediate results stay in Python variables.
  3. A companion "Search as Code" skill plugs it into existing coding agents (tested with Codex).
- **Key result:** Codex 0.147.0, gpt-5.6-luna, xhigh reasoning, 30-minute budget, leakage-audited paired tasks. **BrowseComp: 82.25% → 85.21%** (+2.96 pp), time −30.3%, tokens 4,102.9k → 2,552.1k (−37.8%), cost −36.4%. **WideSearch:** row F1 60.62 → 59.78 (−0.84), time −29.5%, tokens −13.8%.
- **Monday takeaway:** Give your deep-research agent a code sandbox with a search SDK, not N separate tools. Real API from the README (the README says it is not yet on PyPI; install from the repo):
```python
from opensac import sdk
pool = sdk.search(["retrieval evaluation", "evaluating retrieval quality"], limit=10)  # reformulations fused locally (RRF)
if pool:
    best = sdk.rerank("retrieval evaluation", pool[:100], top_n=min(3, len(pool)))
    doc = sdk.content.fetch(best[0].url)
```
  Providers come from environment variables: `OPENSAC_SEARCH_PROVIDER=serper`, `OPENSAC_FETCH_PROVIDER=jina`, `OPENSAC_RERANK_BASE_URL`, `OPENSAC_LLM_BASE_URL` (OpenAI-compatible). Python 3.12+. The SDK has no automatic retries.
- **Limitations:** One run per task. Small, slightly negative quality change on WideSearch.
- **Slide idea:** Split screen. Left: 12 tool-call bubbles stacking up in the context. Right: one code cell runs and prints 3 lines. Animation: the token meters race, and the right one stops at 62%.

## 6. From Delivery to Stateful Exploration: Rethinking the Index for Agentic Search (IndexAct)
- **arXiv:** 2610.07960 · v1 2026-10-06 · Deogyong Kim, Yonsei University.
- **Problem:** Search tools return passages even when the agent only needs feedback on its candidate set. Narrowing the candidates and reading text are coupled, so the context fills with off-target text: 74.4% of the context in a BM25 retrieval agent comes from non-evidence sources.
- **Method:**
  1. Expose the **inverted index** as an environment. The agent builds persistent candidate sets (`SetRef`, starting from `CORPUS`) with lexical and positional conditions and set operations (AND/OR/NOT-style).
  2. Operations return **state references and statistics** (for example, candidate counts), not text.
  3. The agent explicitly *reads* selected regions only when it needs clues or verification.
  4. States can be reused across steps.
- **Key result (BrowseComp-Plus, same backbone across methods):** **IndexAct 73.5% accuracy**, 60.7% evidence coverage, 13,960 average live-context tokens. Comparisons: Pi-Serini 62.7% / 55.4 / 10,835; RARG 69.4 / 57.2 / 27,896; dense retrieval agent 48.2; BM25 agent 30.5 / 36.5 / 31,243. It is also best on MuSiQue (46.2), HotpotQA (71.8), 2Wiki (69.2) and Bamboogle (71.2). Accuracy holds as the corpus grows.
- **Monday takeaway:** Add a `count(query)` / `refine(set, cond)` tool that returns numbers and handles. Make `read(doc, region)` a separate, explicit tool.
- **Limitations:** Lexical-only conditions. Benchmarks with closed corpora.
- **Slide idea:** A Venn-style funnel. The corpus (100K) shrinks to 3,200, then 41, then 6 as set operations apply, and only the final 6 cards flip over to show text.

## 7. Frustratingly Easy Agentic RAG via Portable Skills: A Case Study in Customer Support
- **arXiv:** 2610.14428 · v1 2026-10-10 · Istok Bako et al., Airbnb, Inc.
- **Problem:** Production customer-support RAG usually needs complex chunking, re-rankers, query rewriters and bespoke agent infrastructure.
- **Method:**
  1. A **portable skill**: a SKILL.md operating manual, lightweight tools (one retrieval API plus deterministic format-check scripts), and a corpus.
  2. An **LLM-generated "Wikipedia-style" navigation layer**: about 2,700 Markdown pages, indexed by *intent* (what each workflow solves), with typed links to source articles by stable ID.
  3. One **hybrid BM25+dense** search over the wiki → dereference IDs → read the source articles. A validator admits only verbatim snippets.
  4. Runs unchanged on harnesses such as Claude Code.
- **Key result:** **99.2% procedural equivalence** with human-approved ground truth and **83.3% evidence sufficiency**. Build time is **1–2 engineer days**. The cost is latency: **~90 s vs ~8–9 s** for the production assistant. Ablation: the search method is "within noise". The navigation layer's content organization is what matters.
- **Monday takeaway:** Before you tune the retriever, invest in an LLM-written intent index over your documents and a SKILL.md. Maintenance becomes editing text.
- **Limitations:** The authors limit their claim to a mature, curated corpus, latency-tolerant work and human review of every case.
- **Slide idea:** A two-column "stack diet". Left: chunker → embedder → reranker → rewriter → router → agent. Right: SKILL.md + 1 search tool + wiki. The left boxes fade out one by one, and the "99.2%" and "90 s" badges land.

## 8. When Your Agent Opens the Chat App: Agent-Controlled Search over Raw Chat Logs Rivals Structured Memory (ReFind)
- **arXiv:** 2608.12888 · v1 2026-08-13 · Ruizhe Li et al., USTC / MetaStone Technology.
- **Problem:** Memory systems pre-build summaries, graphs or trees. How much of their benefit is the structure, and how much is just competent search?
- **Method:**
  1. Leave the archive unmodified. Build a **BM25 index at turn granularity** (k1=1.2, b=0.75, Porter stemming). There is no LLM indexing.
  2. A ReAct loop issues keyword queries and saves notes.
  3. Four chat-native controls: session-aware RRF (turn rank fused with session rank), local context expansion, temporal narrowing, and skipping already-inspected sessions.
  4. A separate reasoning stage answers from the collected evidence.
- **Key result:** MemoryAgentBench (~2,800 questions, GPT-4o-mini): **58.2 mean accuracy vs HippoRAG 2 at 53.2**, the best of all systems compared. LongMemEval-S/M with GPT-5-mini: **93.2 ± 3.3 / 89.3 ± 6.0**.
- **Monday takeaway:** Before you build a memory knowledge graph, build an agentic BM25 baseline over the raw logs.
- **Limitations:** Aimed at precise, evidence-grounded questions. It may be weaker for abstraction or summary questions.
- **Slide idea:** "Structure vs search" scales. The left pan holds summaries, KG and tree (53.2); the right pan holds raw logs + BM25 + an agent (58.2). The scales tip right.

## 9. Is Deep Research Reliable? Misleading Knowledge Induces False Conclusions (MisKnow-Agent)
- **arXiv:** 2607.20891 · v1 2026-07-23 · Pengyu Zhu et al., Shanghai Artificial Intelligence Laboratory. Code and data: github.com/whfeLingYu/MisKnow-Agent
- **Problem:** Can deep-research agents resist credible-looking but false documents?
- **Method:**
  1. From DeepResearch Bench tasks, generate **5,933 misleading documents** that support audited false conclusions, with controlled authority cues and source styles.
  2. Inject them at three stages: cold start, mid-research, or just before synthesis.
  3. Measure the report-level **false-conclusion adoption rate (FCAR)** for DeerFlow and WebThinker (3 backbones) and for Gemini Deep Research.
  4. Defenses: a verification-enhanced prompt (pre-research) and a search-enabled verifier agent (post-research).
- **Key result:** **One misleading document raises mean FCAR from 0% to 54.7%.** Two documents give 59.5%, with a peak of 61.0%, so documents after the first add little. By stage: **cold start 40.5%, mid-research 44.2%, pre-synthesis 85.5%** (77–94% across configurations). Search-result *rank* has limited influence. Defenses cut the no-defense range of 60–76% to 37–57% (pre), 20–58% (post) and 15–62% (combined). They reduce adoption but never remove it.
- **Monday takeaway:** Run verification when evidence is written into the agent's state or notes, and most of all on the documents that reach the final synthesis step. Source authority cues matter more than rank.
- **Limitations:** Synthetic misleading documents. A limited set of frameworks.
- **Slide idea:** A timeline of a research run with a single red document dropped at three positions. The FCAR bar for each drop grows 40 → 44 → 85%.

## 10. Glasseek: A Transparent Recipe for Training and Trustworthy Evaluation of DeepSearch Agents
- **arXiv:** 2610.16998 · v1 2026-10-12 · Cong Pang et al., ShanghaiTech (lead) with NUS, ZJU and others.
- **Problem:** Training pipelines for open deep-search agents are opaque. Context compaction makes training differ from inference. Agents can find benchmark answers on the open web.
- **Method:**
  1. A verifiable pipeline for curating trajectories. All data, weights, recipes and code are released.
  2. **CM-GSPO:** the same policy searches and summarizes, but only the execution sub-trajectories are optimized, so training works across context-compaction boundaries.
  3. An **anti-leakage plugin** (on Hermes-agent): domain/path URL blocking (for example Hugging Face and benchmark repositories), file-system permission limits and a sandbox. Leaks are detected with a regex plus an LLM-judge double check.
- **Key result:** Leakage audit: Agents-A1 shows an **11.2% leakage rate** and drops **63.4 → 58.3** (−5.1) once leaks are blocked. XYZ-Aquila-mini: 9.3%, −2.7. **GPT-5.5 answers up to 28% of BrowseComp with zero retrieval**, against 1.5% for open Qwen3.5-35B-A3B-based models (internal/parametric leakage). Glasseeker-9B scores 61.6 with no leakage and is the authors' state of the art at 9B.
- **Monday takeaway:** Add a domain blocklist and file sandbox to your agent eval harness, and report a closed-book baseline. Otherwise your "deep research" score partly measures memorization and answer lookup.
- **Limitations:** Rule-based blocking can miss mirrors.
- **Slide idea:** A leaderboard where bars shrink when an "anti-leakage" switch flips, plus a callout: "GPT-5.5: 28% with no search at all".

## 11. Grounded Credit Assignment in Reinforcement Learning for Multi-Turn Search Agents (GCA)
- **arXiv:** 2610.23148 · v1 2026-10-16 · Qirui Liu (South China Univ. of Technology), Hao Chen (FiT, Tencent) et al.
- **Problem:** GRPO gives every token the same advantage. RL raises accuracy, but agents learn to answer from memory.
- **Method:**
  1. Two verifiable sub-outcomes: **ToolHit** (a tool response contains the gold answer) and answer correctness.
  2. Correct the credit for search and answer separately. A wrong answer is blamed more than the search that found the evidence. A correct answer that bypasses evidence it could have retrieved gets less credit.
  3. The residual is **capped at 10% of each token's advantage** (η=0.2, λmax=1, cmax=0.5 → κ=0.1). It never flips the sign of the advantage.
  4. No extra models, rollouts or training stages.
- **Key result:** Search-R1 raises EM on all 7 QA benchmarks, but the **evidence-supported share of correct answers drops from 84.0% to 42.9% on Bamboogle** and from 88.3% to 71.8% on MuSiQue. GCA: **+5.7 EM** over Search-R1 (Qwen2.5-3B, GRPO) and **+6.3** (Qwen3-30B-A3B, GSPO). The supported share rises from **76.9% to 93.4%**.
- **Monday takeaway:** Even without RL, add a "SupCor/Acc" metric to your eval: of the correct answers, how many had the answer in retrieved text? Accuracy alone hides parametric guessing.
- **Limitations:** Needs short gold answers for string matching in tool responses (QA-style).
- **Slide idea:** Two meters, EM and "grounded share". Under Search-R1 the EM meter climbs while the grounded meter falls (84 → 43). Under GCA both rise.

## 12. Self-Assessment Reinforcement Learning for Search-State Awareness (SARL)
- **arXiv:** 2610.30435 · v1 2026-10-21 · Taewhoo Lee, Amazon / Korea University (Jaewoo Kang group).
- **Problem:** Search agents do not track what they know and what is missing. They hallucinate or stop too early.
- **Method:**
  1. After an initial answer, the *same policy* re-reads its trajectory in an **isolated context**. It lists the question's constraints, says which ones evidence resolved, and returns COMPLETE or INCOMPLETE.
  2. INCOMPLETE triggers trajectory revision.
  3. Reward: R_total = r_final · α^(n−1) + λ · r_assess. The exponential penalty limits how many assessments the model uses. r_assess comes from the change in answer correctness before vs after the assessment.
  4. At test time no assessment is run. The behavior is internalized.
- **Key result:** Qwen2.5-7B, 45K training set, 8×B200: **+24.3% relative over the strongest baseline**, **+35.9% on multi-hop** and **+27.9% on deep-research** benchmarks. HotpotQA 0.614 and 2Wiki 0.645, against MA-RAG-70B at 0.507 and 0.431. On Llama-3.1-8B, GRPO collapses (52.3 → 44.4) while SARL climbs (51.2 → 54.3).
- **Monday takeaway (prompting version):** Even without training, a "fresh-context self-check" step (list constraints → mark resolved → continue if INCOMPLETE) is cheap to add to an ADK/LangGraph loop. That is the inference-time analogue; the paper's point is that RL removes the need for it.
- **Limitations:** Depends on the base model's ability to self-assess (they verify this in an appendix).
- **Slide idea:** A trajectory card slides into a "fresh room" (an empty context box), and a checklist of constraints ticks ✓✓✗. The ✗ sends an arrow back to search.

## 13. Learning to Program Retrievals: Composing Search Primitives via RL (RPL)
- **arXiv:** 2610.24854 · v1 2026-10-17 · Kyuyoung Kim, KAIST AI / Meta Superintelligence Labs (work done at Meta).
- **Problem:** Fixed pipelines or atomic tools tie retrieval breadth to context consumption.
- **Method:**
  1. The action is a **program** run in a sandbox against a retrieval SDK: `sparse_retrieval(q, top_k)`, `dense_retrieval(q, top_k)`, `fuse(*lists)` (RRF), `dedup(docs)`, `rerank(q, docs, top_k)`.
  2. Local state persists across turns. Only printed output enters the context.
  3. **Program mutation:** grammar-constrained, execution-verified local variants of weak programs are turned into training trajectories and distilled into the policy, which solves sparse-reward exploration.
- **Key result:** Qwen3 trained on NQ+HotpotQA, 7 QA benchmarks: average EM **+11.5% (4B) and +9.0% (8B)** over retrieval-RL baselines. **The 4B RPL model beats all 8B baselines.** Best answer F1 and doc-coverage F1 on corpus-level reasoning, with fewer turns and less context.
- **Monday takeaway:** Same direction as OpenSaC (#5). If you control the agent, expose retrieval *primitives* in a code tool.
- **Limitations:** A sandbox is required. Mutation needs a grammar.
- **Slide idea:** A Lego-block animation: five primitive blocks snap into a program, the program runs, and only 3 lines "print" into the context window.

## 14. EG-GRPO: Evidence-Guided Step-level Credit Assignment for Deep Search Agents
- **arXiv:** 2610.25269 · v1 2026-10-18 · Sijia Luo, Renmin University of China / Ant Group.
- **Method:**
  1. Synthetic deep-search data already has evidence annotations. For each required claim, find the step with the **first supporting citation**.
  2. New evidence acquired at a step becomes a step-level process reward.
  3. The accumulated evidence is an evolving knowledge state. Advantages are estimated relative to that state, with a 3-level fallback normalization.
  4. The step advantage (weight w) is mixed with the trajectory outcome advantage.
- **Key result:** 5 benchmarks (BrowseComp, BrowseComp-ZH, GAIA-text, xBenchDS-2505/2510): average **+4.96 (Qwen3-4B) and +3.64 (30B)** over GRPO. **GAIA 34.8 → 45.9** on 4B. The best weight is **w = 0.5**; w = 0.75 or 1.0 hurts. GRPO agents cut tool calls sharply (premature stopping), while EG-GRPO keeps exploring and evidence coverage rises steadily.
- **Monday takeaway:** If you generate synthetic multi-hop data, keep the evidence annotations. They are free process supervision.
- **Slide idea:** A stacked bar of "evidence collected" across steps, GRPO vs EG-GRPO. The GRPO bar stops early.

## 15. KnowGPO: Knowledge-Grouped Policy Optimization for Search Agents
- **arXiv:** 2610.22331 · v1 2026-10-15 · Siqi Chen, Zhejiang University / Tencent.
- **Method:**
  1. Decompose the information each query needs into **atomic knowledge conditions**.
  2. A trajectory's state at each step is the set of conditions it has satisfied.
  3. Group trajectories with the same knowledge state for within-group comparison (GRPO-style).
  4. The knowledge gain between steps is an environment-grounded process reward.
- **Key result:** Xbench, BrowseComp-ZH and GAIA: **+3.8 to +4.2 points** over GRPO, GiGPO and IGPO. The **8B model rivals or beats most 32B open-source systems**.
- **Monday takeaway:** The same "condition checklist" works as an *eval* metric for agent runs: the share of atomic conditions satisfied.
- **Slide idea:** Rollouts drawn as paths that recolor by knowledge state, so paths in the same state cluster into a group.

## 16. BRIDGE: Bilevel Retrieval-Credit-Aware Agentic Reinforcement Learning
- **arXiv:** 2609.36505 · v1 2026-09-29 · Quan Xiao, Cornell University (with Institute of Science Tokyo and Cisco Research).
- **Problem:** Agentic RL trains only the LLM tokens, so failures caused by bad retrieval are blamed on the policy ("information-credit gap").
- **Method:**
  1. Co-train the retriever and the policy.
  2. Empirical finding: **adapting the retriever first gives a larger reward gain than the reverse order.**
  3. Frame this as bilevel optimization (retriever = upper level). Solve it with a memory-efficient first-order method.
- **Key result:** 7 open-domain QA benchmarks, best average with both 3B and 7B. **Multi-hop average +9.6 EM (3B) and +3.4 EM (7B)** over the strongest baseline. Best results on medical QA as well.
- **Monday takeaway:** If your agent fails on retrieval, fine-tune the embedder or retriever on agent-issued queries *before* you RL-tune the LLM.
- **Slide idea:** Two gears, retriever and policy. The retriever gear turns first and drives the policy gear. Reversing the order shows a smaller gain.

## 17. SOAR: Source-Aware Reinforcement Learning with Precise Credit Assignment for Search Agents
- **arXiv:** 2610.13157 · v1 2026-10-09 · Shengze Huang, Zhejiang University / Microsoft.
- **Method:**
  1. A **Source-Aware Workflow** splits external evidence (E_ext) and internal knowledge (E_int) into parallel, observable streams in the trajectory.
  2. A **Source-Consistent Reward** checks that the answer is consistent with the stated sources.
  3. With explicit attribution, credit can go to the right stream.
- **Key result:** **+7.3% (3B) and +5.4% (7B)** over baselines. **Evidence fabrication −74.8%.**
- **Monday takeaway:** In prompts, ask for `<from_docs>` vs `<from_memory>` sections. That makes fabrication auditable even without training.
- **Slide idea:** Two colored lanes, blue (docs) and orange (memory), merge into an answer. A red "fabrication" lane shrinks by 75%.

## 18. QREF: Improving DeepSearch Agents via Query Refinement and Evidence Filtering
- **arXiv:** 2610.21512 · v1 2026-10-15 · Yujia Chen, Fudan University (Tao Gui, Qi Zhang, Xuanjing Huang group; Tencent co-authors).
- **Method:**
  1. A plug-in **Query Refiner** rewrites each query batch to match the current reasoning intent and to cover complementary ground across the batch. It is trained with SFT, then RL against a real web-search environment.
  2. An **Evidence Filter** keeps results relevant to both the batch and the reasoning objective.
  3. The host agent's policy is unchanged.
- **Key result:** Average relative Pass@1 gain of **+33.55% on WebSailor** and **+11.04% on Tongyi DeepResearch** across 4 benchmarks. The share of query batches without discriminative retrieval anchors drops **95%**.
- **Monday takeaway:** A small trained "query middleware" in front of any search tool is a drop-in upgrade for closed agents you cannot retrain.
- **Slide idea:** Raw agent queries enter a "refiner" box and leave as sharpened, non-overlapping queries. The filter then removes grey noise cards.

## 19. TRACE: Trajectory Selection for Parallel Scaling of Search Agents
- **arXiv:** 2609.39912 · v1 2026-09-30 · Qisheng Zhou, NYU Shanghai. Code: github.com/Jaasssoooonnnnn/TRACE
- **Problem:** With K parallel rollouts, the correct answer is often present, but majority vote fails to pick it.
- **Method:**
  1. Link rollouts through shared queries, evidence content or document identity (a graph).
  2. Propagate information over that graph using frozen text embeddings plus a lightweight learned selector.
  3. Each candidate answer reads its own updated trajectory state and is scored.
  4. It returns an existing answer: no extra search and no generative aggregation.
- **Key result:** Long-horizon FRAMES, GAIA and BrowseComp: **78.6% average, +3.1 pp over majority vote** (K=16). **8 rollouts with TRACE comes within 0.4 pts of majority vote over 64.** At least **10× higher throughput** than generative aggregators (SolAgg, SummAgg, AggAgent).
- **Monday takeaway:** If you already run N parallel research agents, choose the answer by evidence overlap, not by vote. You get the same quality with 8× fewer rollouts.
- **Slide idea:** 16 rollout threads with shared documents lit up as links. Votes say A, evidence links say B, and B wins.

## 20. CHART: A Harness-Rotation Curriculum for Harness-Robust Search Agents
- **arXiv:** 2609.22247 · v1 2026-09-05 · Xinlu Zhang, Amazon (NeurIPS 2026 CL4FMAgents workshop).
- **Problem:** A behavior learned with RL (parallel search) is tied to the training harness. Rewriting the system prompt makes the model fall back to serial search.
- **Method:**
  1. Train Qwen3-30B-A3B-Thinking-2507 for parallel search with GRPO over a pool of harnesses.
  2. Training on a static pool fails: a small pool saturates the parallel-vs-serial reward gap, and a large pool dilutes it.
  3. A **rotating curriculum** "graduates" harnesses whose behavior has been learned and swaps in learnable ones.
- **Key result:** It parallelizes on **89% of held-out-harness turns vs at most 5%** for static pools. Pass@1 is **+5.6 pp** on a new QA task and search environment.
- **Monday takeaway:** After you fine-tune an agent, regression-test it under several rewrites of the system prompt. The gotcha: "we edited the prompt and the agent stopped parallelizing."
- **Slide idea:** A system-prompt card swaps and the agent's search lanes collapse from 4 parallel lanes to 1. With CHART they stay at 4.

---

## Also notable (short)
- **2608.08389 — Not Worth Another Token: Marginal Value Estimation for Efficient Deep Research Agents** (UMass Amherst, with Adobe co-authors [UNVERIFIED org for the Adobe names]). *Where* you prune matters more than the scoring rule. Post-retrieval MMR cuts tokens **375.4k → 114.6k** and explored nodes 29.0 → 8.84 with modest quality loss. Lightweight heuristics cut tokens by up to **73%**. Takeaway: prune subqueries early.
- **2609.36344 — DeepRewind** (UBC). A typed epistemic graph plus a commitment gate and dependency-aware rollback. **Insight recall +3.6 pp, premature commitments −59.1%** vs Open Deep Research on DRBench and LiveDRBench.
- **2610.29250 — SearchWeaver: Let Agents Design How They Search** (Korea Univ./KAIST). A proposer jointly revises corpus artifacts, tools and instructions. GPT-5.4-nano: **BrowseComp-Plus 71.6 → 78.4%**, BRIGHT nDCG@10 **45.7 → 55.0**.
- **2608.20317 — Projecting BrowseComp-Plus onto ClimbMix** (Waterloo, Jimmy Lin). Moves the evidence into a 553M-document web corpus, keeping 57 fully grounded questions. The best agent loses only 5 points of accuracy, but **evidence recall falls from 84.3% to 21.4%** and it makes 63% more search calls. Gotcha: the 100K-document BrowseComp-Plus overstates retrieval ease.
- **2609.16268 — Spurious Tool Use** (Yiwei Yang et al.; org [UNVERIFIED], authors include Julian McAuley and Bill Howe). RL agents learn cue → tool shortcuts. Spurious invocation rises **up to 39%**. Fix: a dense LLM-judge "tool necessity" reward.
- **2608.22167 — MCP-Universe RL** (Salesforce AI Research [UNVERIFIED org; authors Luo, Savarese, Li]). Open-source RL framework that uses MCP servers as environments (container isolation, rollout overlap, veRL/slime backends). It trains SWE, deep-research and tool-use agents on gpt-oss-20b. The abstract gives no headline number.
- **2609.35774 — Post-Generation Verification Dominates Retrieval Optimization** (single author). A 2^4 factorial design: a completeness check (d = +0.48) beats agentic search, which has a small unstable effect. ToC-guided retrieval helps at zero extra LLM calls.
- **2607.24010 — When Should Active RAG Retrieve?** Retrieval *harm* is non-negligible. Simple uncertainty or retrieval-score triggers often rival learned routers. Report realized usage and threshold-transfer error, not one operating point.

---

## Cross-paper trends (for a "what changed in Q3 2026" slide)
1. **The agent drives a ranker; it does not replace one.** BM25 at scale (#1), Question's Gambit (#3), IndexAct (#6) and ReFind (#8) all find that a good *global ranking* (often lexical) plus agent control beats free-form exploration. Accuracy follows **cumulative recall** (r = 0.99, #2), not search volume.
2. **Search as code.** OpenSaC (#5), RPL (#13) and SearchWeaver let the agent write programs over search primitives (search/fuse/dedup/rerank). Intermediate results stay out of the context, with roughly 30–38% fewer tokens and fewer turns.
3. **RL credit assignment for search is the main research thread.** Outcome-only GRPO is being replaced by evidence-grounded step credit: EG-GRPO (first citation), KnowGPO (knowledge state), GCA (ToolHit sub-outcome, 10% cap), SOAR (source streams), BRIDGE (retriever credit), SARL (self-assessment). The shared warning: **EM can rise while grounding collapses** (Bamboogle 84.0% → 42.9%).
4. **Evaluation hygiene is a first-class problem.** Benchmark leakage (−5.1 pts, and GPT-5.5 answers 28% closed-book, #10), corpus realism (recall 84 → 21%, BrowseComp-Plus_CM), harness overfitting (#20) and misleading-document injection (FCAR 0 → 54.7%, 85.5% pre-synthesis, #9). Report closed-book baselines, grounded share and leakage-blocked scores.
5. **MCP turns retrieval into a two-sided interface.** Tool retrieval (SCOUT's `tool_search`, ToolSearcher 2609.30906), MCP servers as RL environments (MCP-Universe RL) and portable skills (#7) all make "retrieve the right *tool or skill*" as important as "retrieve the right *document*".

## Gotchas list (one slide)
- More turns ≠ more accuracy: 77.5–93.6% of search episodes add no new evidence (#2).
- Near-duplicate re-queries are the best early warning of failure (#2).
- RL can teach agents to skip retrieval and answer from memory (#11, #17).
- One credible fake document flips more than half of reports, and 85.5% when it arrives just before synthesis (#9).
- Benchmark scores of open-web agents include answer lookups (#10).
- Changing the system prompt can silently remove RL-learned behaviors (#20).
- Graph RAG hits construction-cost walls before production scale (#1).
- The first query decides a lot: get it right with clue decomposition (#3).
