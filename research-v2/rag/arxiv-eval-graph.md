# arXiv sweep (2026-07-23 .. 2026-10-23): RAG evaluation, faithfulness/attribution, GraphRAG, multimodal RAG, RAG security, RAG memory

How this sweep was done:
- The arXiv API (export.arxiv.org) returned HTTP 429 the whole session. I used arXiv listing search (arxiv.org/search, sorted newest first) for these queries: GraphRAG, RAG poisoning, RAG prompt injection, multimodal RAG, RAG faithfulness, RAG citation attribution, RAG benchmark. Later searches (agent memory, hallucination detection, visual document retrieval) were rate-limited and came back empty, so memory papers come from the other queries.
- For every paper below I read the abstract page. For all 20 ranked papers I also read the arXiv HTML full text (arxiv.org/html/<id>) to get affiliations, mechanism details and numbers.
- "Submitted" means the v1 date on the abstract page. All 20 are inside the window.
- None of these IDs appear in `research-rag/` (that folder only cites papers up to 2510.x).
- Code snippets marked **[SKETCH]** are my own minimal versions of a paper's idea, written for slides. They are not the authors' code and have not been run. Anything I could not check is marked [UNVERIFIED].
- In the HTML full text, numbers inside LaTeX math were stripped by my converter. Where that happened I quote only numbers that appear in plain text or in the abstract.

---

## Ranked list (by practical impact for an engineer)

### 1. 2610.29722 — Retrieval Augmented Generation Compositionality (LASAGNA)
- **Submitted:** 2026-10-21. **Authors:** Ido Levy (IBM; Weizmann Institute), Segev Shlomov (IBM), Leshem Choshen (IBM; Weizmann).
- **Code:** github.com/dolev31/lasagna ; site dolev31.github.io/lasagna
- **Problem:** RAG techniques (chunkers, HyDE, rerankers, compression, CRAG/Self-RAG gates) are evaluated one at a time on stripped-down baselines. Do their gains add up inside a full modern stack?
- **Method (diagram):** One configurable end-to-end pipeline with 8 dimensions: chunking → embedding (BGE-M3/E5/MiniLM) → index-time enrichment (RAPTOR, GraphRAG, contextual retrieval) → vector DB (Milvus/Qdrant/Pinecone/Weaviate/PgVector/OpenSearch) → retrieval (BM25, SPLADE, hybrid-RRF, MMR) → query augmentation (HyDE, RAG-Fusion, decomposition, step-back) → rerank/compress → agentic gates (CRAG, Self-RAG). A D-optimal fractional-factorial design samples the space. Three hypotheses are declared before the data is collected. Results are scored on three tracks: retrieval (NDCG/MRR), faithfulness (RAGAS), and latency.
- **Key results:** 450 configurations, 8 benchmarks, corpora from 5K to 200K docs.
  - Three retrieval techniques predict **+47%** combined but deliver **+17%** together.
  - Optimizing retrieval can hurt faithfulness.
  - The winning composition at 5K docs is not the winner at 200K.
  - Appendix details:
    - The 2019 MS-MARCO MiniLM-L6 cross-encoder ranked above all four recent rerankers tested.
    - Matryoshka truncation of BGE-M3 to 768 dims cut storage and improved NDCG@10.
    - Faithfulness was **highest with hallucination/answer-quality gates disabled**. In one multi-hop example, gate-triggered refinement removed 14 of 15 supporting chunks.
    - HyDE raises NDCG@10 but doubles first-hop latency.
    - At 50K docs, the "standard" profile ran at P95 about 7 s with 0.79 faithfulness. The "balanced" (agentic) profile ran at P95 about 18 s with 0.93 faithfulness.
- **Monday takeaway:**
  - Never ship a component on the basis of an isolated A/B test. Re-run evaluation with the full stack, on a corpus the size of production.
  - Track retrieval and faithfulness separately, because they can move in opposite directions.
  - Test old cheap rerankers before buying new ones.
  - Test whether your CRAG/Self-RAG gate is deleting good evidence.
- **Limitations:** No third-party pre-registration timestamp (the authors say so). The reranker finding may be domain-specific (the authors speculate). Judge: RAGAS with GPT-5.1.
- **Slide idea:** "1 + 1 + 1 ≠ 3". Three bars (each technique's solo gain) stack up to a dashed "+47% predicted" line. Then they collapse with a GSAP spring into one "+17% actual" bar. Second beat: a 5K vs 200K leaderboard whose rows swap places.

### 2. 2610.30755 — Is Complex Agentic Memory Always Needed? Naive RAG Is Stronger Than We Thought
- **Submitted:** 2026-10-22. **Authors:** Zhengye Bao et al. (6 authors; affiliations not clearly shown in the HTML) [UNVERIFIED org].
- **Problem:** Agent memory systems (Mem0, MemOS, EverMemOS, MemMachine, A-MEM, Memora…) mutate, summarize or graph-ify chat history. Is that complexity needed?
- **Method (diagram):** "Raw-RAG" chunks the raw conversation history (no fact extraction, no summaries), runs dense retrieval and a cross-encoder rerank, and sends the top-k to the reader LLM. The paper compares build/store/recall stages against the agentic systems.
- **Key results:**
  - Raw-RAG is first in **6 of 7** benchmark-model settings across LoCoMo, LongMemEval, MEME and MemoryAgentBench, by +0.13 to +5.53 points over the best agentic system.
  - LoCoMo (text-embedding-3-small setting): with a GPT-4.1-mini reader, **93.70** vs MemMachine 91.69 and Mem0 62.92. With GPT-4o-mini, 89.07 vs 88.12.
  - Ingest + search time on 10 MEME episodes: Raw-RAG **305.91 s** vs Mem0 4,142.95 s vs EverMemOS 9,301.48 s.
  - Ablations on MemoryAgentBench:
    - Removing the reranker costs −3.92 points. Returning only 1 item costs −11.73. Top-120 costs −14.57.
    - final-k of 5 to 60 stays within 1.3 points. Chunk sizes from 128 to 1,024 make no significant difference.
    - **Atomic-fact extraction costs −19.62**, raw summaries −5.81, graph expansion −5.78.
  - The Qwen3 setting uses Qwen3-Embedding-4B + Qwen3-Reranker-4B.
- **Monday takeaway:**
  - Before adopting a memory framework, build the 30-line baseline: store raw turns and retrieve them with an embedder plus reranker.
  - Do not throw away the raw history in favor of extracted "facts".
  - Always keep a reranker. A k between 5 and 30 is fine.
- **Limitations:** Evaluated on conversation-QA benchmarks only, not on preference or interaction behavior (see #20). Strong readers resolve state changes. Weak readers may need mutation.
- **Slide idea:** "The 30-line memory that won". Race-bar animation of ingest time: Raw-RAG's bar finishes while Mem0/EverMemOS are still loading. Then the accuracy table flips with Raw-RAG on top. Last beat: a red "−19.6" over "atomic facts".

```python
# [SKETCH] Raw-RAG-style memory: store raw turns, retrieve, rerank. Not the authors' code.
from sentence_transformers import SentenceTransformer, CrossEncoder
import numpy as np
emb = SentenceTransformer("Qwen/Qwen3-Embedding-0.6B")    # paper used the 4B variant
rr  = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")  # paper used Qwen3-Reranker-4B
turns = []                                             # raw "speaker: text [timestamp]" strings
def remember(t): turns.append(t)
def recall(q, k_dense=50, k_final=10):
    E = emb.encode(turns, normalize_embeddings=True); qv = emb.encode(q, normalize_embeddings=True)
    cand = [turns[i] for i in np.argsort(-E @ qv)[:k_dense]]
    s = rr.predict([(q, c) for c in cand])
    return [cand[i] for i in np.argsort(-s)[:k_final]]
```

### 3. 2608.16044 — Coverage Is Not Containment: A Fundamental Limit of Admission-Time Defenses Against Coordinated Poisoning of Vector Retrieval
- **Submitted:** 2026-08-17. **Authors:** Prashant Kumar Pathak (Santa Clara, CA; IEEE email), Tarun Kumar Sharma (Colonia, NJ). Org not stated beyond location.
- **Problem:** Several defenses filter poison at ingestion (for example, reject "hub" documents). Can any ingestion-time filter stop a coordinated attacker?
- **Method (diagram):** The attacker injects m documents. Each one looks unremarkable, but together they form a "cone" around one target query and take over its top-k. The authors prove that for **any** ingestion-time statistic (documents plus reference queries only), the cone cannot be told apart from a legitimate niche upload. The escape is a retrieval-time monitor on the read path. It watches **query demand**: which fresh documents keep winning top-k for which queries, using a sliding window and per-cluster bookkeeping.
- **Key results:**
  - On BGE-large/BEIR, m=10 docs take **10/10** of top-k (9.9/10 on live HNSW).
  - End to end (BGE-large + HNSW + Qwen2.5-7B), the generator emits the planted claim in **88%** of targets vs 0% without injection.
  - The best trained ingestion classifier catches **4.2%** of attacks at 1% FPR. The demand-aware retrieval-time detector catches **100%** at 1% FPR.
  - Sharded stores make ingestion defenses worse: the attacker spreads one document per shard.
- **Monday takeaway:** Layer the defenses. Keep a cheap ingestion hub filter, and add a read-path monitor: log (query cluster, doc id, doc ingest time) for every retrieval and alert when newly ingested docs suddenly dominate a query cluster. Pair this with provenance.
- **Limitations:** The proof is scoped to "ingestion-blind" defenses. The detector needs query logs (a privacy and ops cost). No turnkey exploit is released.
- **Slide idea:** "The front door can't see it". The animation shows 10 harmless-looking dots drifting in one by one and passing a green ingestion gate. Then they form a cone around a query star. Cut to a read-path monitor heat-map that lights up red.

```python
# [SKETCH] demand-aware read-path monitor (idea from 2608.16044; thresholds are illustrative)
from collections import defaultdict, deque
import time
WINDOW = 3600; FRESH = 24*3600
log = defaultdict(deque)  # query_cluster -> deque[(ts, doc_id, doc_ingested_at)]
def on_retrieval(cluster_id, hits):          # call after every vector search
    now = time.time()
    for h in hits: log[cluster_id].append((now, h.id, h.ingested_at))
    while log[cluster_id] and now - log[cluster_id][0][0] > WINDOW: log[cluster_id].popleft()
    rows = log[cluster_id]
    fresh_share = sum(now - ing < FRESH for _, _, ing in rows) / max(len(rows), 1)
    if len(rows) > 50 and fresh_share > 0.6:   # fresh docs suddenly own this query region
        quarantine_candidates = {d for _, d, ing in rows if now - ing < FRESH}
        alert(cluster_id, quarantine_candidates)
```

### 4. 2609.23053 — Attributable Post-Rationalization in RAG Citations: A Controlled Reproduction and an RLVR Comparison
- **Submitted:** 2026-09-19. **Authors:** Mehedi Khan, Md. Shariful Islam Bhuyan (Bangladesh University of Engineering and Technology).
- **Problem:** Citations look like evidence. Models often write the answer first and then attach a citation to whatever passage looks close. Does RL with verifiable rewards (as used for search agents) fix this?
- **Method (diagram), the "planting probe" from Wallat et al. 2025 plus a new no-planting control:**
  1. The model answers from 5 passages, with one citation per sentence.
  2. Take the 4 consecutive claim words with the most characters and append them to a passage the model did **not** cite (the "rel-uncited" variant).
  3. Re-run the same prompt. Match the sentence by Jaccard ≥ 0.3. If the citation moves to the doctored passage, it was surface matching, not evidence.
  4. A no-planting control subtracts citation churn that happens anyway.
- **Key results:** On Wikipedia-based QA, about **1 citation in 7 is unfaithful**. Three RLVR agents trained from the same instruct model post-rationalize at the base model's rate, and one is slightly worse. Everything was run on free-tier Kaggle GPUs (Qwen2.5 family).
- **Monday takeaway:**
  - Add this probe to your eval suite. It needs no labels and costs only 2 generations per claim.
  - Report the "citation-move rate" next to answer accuracy.
  - Do not assume that RL tuned for answer correctness gives you faithful citations.
- **Limitations:** Small models, fixed-context setting, a deterministic span rule.
- **Slide idea:** "The swap test". A live demo: a highlighted 4-word span flies from the answer into passage [3]. The citation marker hops from [1] to [3]. Counter: "1 in 7".

```python
# [SKETCH] planting probe (method per 2609.23053 Sec. 3; generate() = your RAG call returning [(sentence, cited_idx)])
import re
def longest_4gram(s):
    w = s.split(); grams = [" ".join(w[i:i+4]) for i in range(len(w)-3)]
    return max(grams, key=len) if grams else s
def jacc(a, b): A, B = set(a.lower().split()), set(b.lower().split()); return len(A & B) / max(len(A | B), 1)
def probe(q, passages):
    base = generate(q, passages); moved = trials = 0
    for sent, cited in base:
        uncited = [i for i in range(len(passages)) if i not in {c for _, c in base}]
        if not uncited: continue
        j = uncited[0]; doctored = list(passages); doctored[j] += " " + longest_4gram(sent)
        new = generate(q, doctored)
        match = max(new, key=lambda x: jacc(x[0], sent))
        if jacc(match[0], sent) >= 0.3:
            trials += 1; moved += (match[1] == j)
    return moved / max(trials, 1)   # also run a no-planting control and subtract
```

### 5. 2609.15660 — CiteShade: Citation Laundering in Multi-Source Retrieval-Augmented Generation and Its Counterfactual Defense
- **Submitted:** 2026-09-14. **Author:** Guo Fuzheng (single author; affiliation not shown in HTML) [UNVERIFIED org].
- **Problem:** Attacks so far target the answer. The citation channel (the user's audit trail) can be attacked too: the attacker gets a wrong answer **attributed to a trusted source that does not support it**.
- **Method (diagram):** One attacker-controlled source is written as fluent LLM text with no instructions inside. It satisfies 3 necessary conditions: it gets retrieved, it drives the generation, and it makes the model cite a *different*, trusted source. The defense is counterfactual source deletion: drop each source in turn and re-generate. The source whose removal flips the answer is the real driver. Compare it to the cited source.
- **Key results:**
  - Wrong-answer rate rises from **0.01 to 0.68** on multi-source multi-hop QA.
  - Citation laundering rate (CLR) is **0.84** under explicit cite-instruction and **0.64** with none, on the most citation-prone model. Vulnerability tracks the model's propensity to cite, not its scale.
  - Perplexity filtering and citation-support checking are each insufficient: the support checker only inspects the cited source, which is clean.
  - An adaptive attacker still gets a net gain against the counterfactual defense, and the author says so.
- **Monday takeaway:** For high-stakes answers, run a leave-one-source-out check on the top contributing sources. Flag any answer where the source that drives the answer is not the source that is cited. A "citation supports claim" check alone is not enough.
- **Limitations:** Single author. The cost is N extra generations. Leave-one-out fails when several sources jointly determine the output.
- **Slide idea:** "Laundered citation". The answer shows a [Reuters] badge. Remove the sources one at a time (cards fade out). The answer only flips when the anonymous blog card is removed, and the badge turns red.

```python
# [SKETCH] counterfactual source check (idea from 2609.15660)
def driver_sources(q, sources, answer, same):
    drivers = []
    for i in range(len(sources)):
        alt = generate_answer(q, sources[:i] + sources[i+1:])
        if not same(alt, answer): drivers.append(i)
    return drivers
# flag if set(driver_sources(...)) does not intersect set(cited_indices)
```

### 6. 2609.31342 — Stale-Document Poisoning: When Outdated Retrieval Overrides Correct Model Answers
- **Submitted:** 2026-09-25. **Authors:** Md Shamim Ahmed (University of Southern Denmark), Lukas Galke Poech, Richard Röttger.
- **Problem:** The "attacker" can be your own corpus. Outdated but authentic documents (withdrawn medical guidance, superseded law, old API docs) override answers that the model got right without retrieval.
- **Method (diagram):** A benchmark of **317 verified knowledge reversals** (medicine, law, software, platform policy) with dated official sources. The authors measure how often old evidence flips a correct closed-book answer. They vary only the evaluation date, or add an explicit "valid until" statement. Causal interventions show that validity information shapes the decision. The mitigation is a fixed hybrid reranker that combines semantic relevance, document recency and supersession cues.
- **Key results:**
  - Outdated retrieval flips **30% (Llama) / 37% (Qwen)** of answers with no instruction to trust the document. A "follow the document" instruction raises this to **66% / 75%**.
  - Across 4 open models and 4 domains the range is 17 to 91%. Up-to-date evidence is followed 97 to 100% of the time.
  - Dates alone give modest adaptation. Explicit "this stops applying on X" makes large models switch almost perfectly.
  - The recency-aware reranker cuts poisoning by **4.6 to 10.0 points** when dates are accurate.
- **Monday takeaway:**
  - Store `valid_from`, `valid_to` and `superseded_by` metadata at ingestion, not just `last_modified`.
  - Put the validity window into the prompt next to each chunk.
  - Remove "always follow the documents" from system prompts, or qualify it.
- **Limitations:** Gains depend on reliable temporal metadata. The benchmark is 317 items.
- **Slide idea:** "Your corpus is the attacker". A timeline: a 2019 guideline card and a 2025 reversal card. The model's answer flips when the 2019 card is retrieved. Then a "valid_to: 2024-06" tag appears and the answer flips back.

```python
# [SKETCH] validity-aware context formatting + rerank (idea from 2609.31342)
from datetime import date
def score(hit, today=date.today(), w_rel=1.0, w_rec=0.3, w_sup=1.0):
    rec = 1 / (1 + (today - hit.meta["valid_from"]).days / 365)
    sup = -1.0 if hit.meta.get("superseded_by") else 0.0
    return w_rel*hit.rel + w_rec*rec + w_sup*sup
def fmt(hit):
    vt = hit.meta.get("valid_to") or "present"
    return f"[source {hit.id} | valid {hit.meta['valid_from']} .. {vt}]\n{hit.text}"
```

### 7. 2610.21318 — Loud and Clear: Making Visual Evidence Count in Multimodal Document RAG
- **Submitted:** 2026-10-15. **Authors:** Eunchan Jo, Seounghyun Jang, Sangwoo Mo (POSTECH). Code: github.com/Chipmunk-g4/Loud-and-Clear
- **Problem:** Multimodal doc-RAG research focuses on the retriever, yet the generator under-reads retrieved pages even when the right page is retrieved.
- **Method (diagram):**
  - **Loud:** give the VLM a larger visual-token budget and scale the full page at high resolution (better than repeating or tiling the page).
  - **Clear:** reuse the retriever's own token embeddings (ColQwen-style late interaction) to select query-relevant regions. Run OCR on those regions (PaddleOCR PP-OCRv5 detection + PP-OCRv4 recognition, from MinerU 2.5.4). Send page image + region OCR text together.
  - No training and no ground-truth boxes.
- **Key results:**
  - Prior methods give the generator 0.7K to 2.7K visual tokens per query. Raising the page budget from 1K to 32K adds **+15.22** accuracy points on SciEGQA oracle pages.
  - LoC beats the strongest baseline, ColQwen3, by **+8.88 (SciEGQA), +3.09 (ViDoRe-v3), +4.22 (MMLongBench-Doc)** with the same retriever and generator (Qwen3.6-35B-A3B).
  - Page + OCR beats either input alone.
- **Monday takeaway:**
  - Check the image resolution and token budget your pipeline sends to Gemini/Qwen-VL. Defaults are often far too low.
  - Send OCR text of the matched regions alongside the page image.
  - Measure accuracy with oracle pages to separate retrieval failures from reading failures.
- **Limitations:** Higher token cost and latency. Evaluated on 3 benchmarks.
- **Slide idea:** "Turn up the volume". A slider animates the visual-token budget 1K→32K while an accuracy needle climbs +15 points. Then the selected region boxes glow and their OCR text types out beside the page.

### 8. 2610.28340 — DeclineCraft: A RAG Abstention Benchmark for Jointly Measuring Combined Retrieval and Parametric Knowledge
- **Submitted:** 2026-10-20. **Authors:** Atharva Thakur, Abulhair Saparov, Bruno Ribeiro (Purdue). Code: github.com/Thakur-Atharva/declinecraft-benchmark
- **Problem:** Can a RAG system say "I don't know" when neither the corpus nor the model's weights know the answer?
- **Method (diagram):** Unanswerable questions about Minecraft features added *after* the corpus cut-off, with audits for parametric exposure. The cut-off can move forward for future models. Metrics: Correct Abstention Rate (CAR), Answerable Attempt Rate, and Answer Accuracy. It compares no-RAG, single-shot RAG, and iterative RAG (self-assess, up to 2 more retrieval rounds), plus query rewriting and reranking on hybrid retrieval.
- **Key results:** 27 LLMs.
  - Single-shot retrieval raises CAR in 38 of 40 configurations.
  - **Iterative RAG lowers CAR in 30 of 40 configurations (mean −46.4%)**, while accuracy barely moves (68.5% → 69.3%).
  - Adding rewriting + reranking to hybrid retrieval lowers CAR for **all 12** models tested.
  - Model size correlates with accuracy (ρ=+0.60) but not with CAR.
  - Enabling "thinking" without retrieval lowers CAR in 8 of 13 models (by 14 points on average).
- **Monday takeaway:** Every "advanced" retrieval add-on (agentic loops, rewriting, reranking) can make the system **hallucinate more on unanswerable questions**. Add an unanswerable slice to your eval set and track CAR whenever you add agentic retrieval.
- **Limitations:** A single game-wiki domain.
- **Slide idea:** "More retrieval, less humility". Two gauges: accuracy (flat) and abstention (dropping) as the pipeline gains boxes: hybrid → +rewrite → +rerank → +iterate.

### 9. 2609.36700 — Lost in Conversation or Lost in Translation? Diagnosing Multi-Turn Degradation in RAG
- **Submitted:** 2026-09-29. **Authors:** Pranav Handa, Ariful Azad (Texas A&M).
- **Problem:** RAG and GraphRAG are evaluated on single-turn, fully specified queries. Real users build up a multi-hop question over several turns.
- **Method (diagram):** Multi-hop QA questions are "sharded" into underspecified conversations. The study covers 10 LLM assistants × 8 retrieval systems (including GraphRAG variants) across **1.5M simulated conversations**. Failures are split into "lost in translation" (the conversational rewrite distorts the retrieval query) and "lost in conversation" (retrieval succeeds but the LLM fails to combine evidence across turns). The authors also test RECAP/SNOWBALL interventions that consolidate or restate earlier turns.
- **Key results:** Up to **21% relative performance drop**, and **47% more unreliability** (13.4 → 19.7 F1 points of unreliability, FULL vs SHARDED) while aptitude drops only 1.9 points. Consolidation fully recovers single-turn performance for the retrievers least sensitive to query wording, and only partly for the others.
- **Monday takeaway:**
  - Build a multi-turn eval slice by sharding your single-turn gold questions.
  - Log the rewritten retrieval query and score retrieval on it, separately from the answer.
  - Before retrieving, consolidate all user constraints into one standalone query.
- **Limitations:** Simulated users.
- **Slide idea:** "Two ways to get lost". A split screen. Left: a query-rewrite arrow bends away from the target doc. Right: docs are retrieved correctly but the answer box stays empty.

### 10. 2610.26951 — The Bottleneck Is Retrieval, Not Reading: Diagnosing Evidence-Based Generation with RAG for Long Context Question Answering
- **Submitted:** 2026-10-18. **Authors:** Debopriyo Banerjee et al., incl. Preslav Nakov, Veselin Stoyanov (MBZUAI; Inception42). Code: github.com/debobanerjee/LC-EBG
- **Problem:** Answer-only metrics hide grounding failures, and chunked similarity retrieval has structural blind spots.
- **Method (diagram):** "Evidence-based generation" (EBG): the model must return the answer **plus line-level citations**. A joint **Ans+Evid** metric requires both to be correct. Benchmarks: MultiHop-RAG, QASPER-MP (multi-paper), a synthetic two-hop haystack, and evidence-augmented NoLiMa from 10K to 1M characters. It compares RAG with long-context reading across 10 frontier and 3 open models.
- **Key results (qualitative in abstract; exact table numbers not extracted) [numbers UNVERIFIED]:**
  - Similarity retrieval surfaces *any* relevant chunk far more reliably than *all* required chunks for multi-fact queries.
  - Chunking destroys document meta-information (titles, identity) that identity-bearing queries need.
  - The gap between Ans and Ans+Evid widens when context contradicts parametric knowledge.
- **Monday takeaway:**
  - Score "all-evidence recall", not hit@k.
  - Prepend document title and metadata to every chunk (in line with contextual retrieval).
  - For corpora that fit, compare against plain long-context.
- **Limitations:** Long-context comparisons are expensive. Exact numbers need the tables.
- **Slide idea:** "Any vs All". A two-needle haystack: the retriever's spotlight finds needle 1 and misses needle 2. The answer is still "correct", but the Ans+Evid score turns red.

### 11. 2610.18442 — Copying Is Not Grounding: Training Faithful Long-Form RAG with Authored-Sentence Credit
- **Submitted:** 2026-10-13. **Authors:** Hoang Pham (Nanyang Technological University), Duc Anh Vu, Duy Tung Doan (Viettel AI), Cong-Duy Nguyen (VinUniversity), Anh Tuan Luu (NTU/VinUni).
- **Problem:** "Share of supported sentences" faithfulness rewards (and metrics) get gamed by copying passages verbatim. KL or copy penalties just trade copying for short, empty answers or refusals. GRPO gives every sentence the answer-level advantage.
- **Method (diagram):** Reward and advantage are moved from the answer to the **sentence** level. A sentence earns credit only if it is (a) authored, not copied, (b) says more than the question, and (c) is supported by the passages (checker: Bespoke-MiniCheck-7B). Each sentence's advantage is ranked against all sentences sampled for that question, so zero-credit sentences are never reinforced. Held-out evaluators: Gemma-4-31B judge, MiniCheck-Flan-T5-Large, AlignScore.
- **Key results:** Across 4 models and 2 in-domain + 3 held-out corpora, ASC lowers the authored-sentence error rate and increases supported authored sentences by **38% and 46% at the median**. It was the only method to improve in every setting.
- **Monday takeaway:** If you report "faithfulness %" (RAGAS-style), also report the **copy rate** and the number of supported *authored* sentences. A rising faithfulness score can just mean the model is pasting text.
- **Limitations:** Needs RL fine-tuning. The checker's quality bounds the reward.
- **Slide idea:** "The copy hack". Two answers both score 95% faithful. Highlight the copied spans in grey: one answer is 80% grey. Then switch to the ASC metric and its score drops.

### 12. 2609.11065 — MOSAIC: Query-Aware Exploration Policy Adaptation for GraphRAG
- **Submitted:** 2026-09-10. **Authors:** EunKyeong Lee, Kyeong-Jin Oh, Jinwon Kim, Hye Woo Lee et al. (KT Corporation), technical report.
- **Problem:** GraphRAG systems use one traversal recipe for every query. Direct facts, comparisons and mediated multi-hop questions need different neighborhoods.
- **Method (diagram):** An LLM analyzer turns each query's evidence requirements into a **bounded policy** covering seed selection, traversal depth/width, stopping rule and evidence selection. The graph, indexes, scorer and generator stay shared. Training-free.
- **Key results:**
  - GraphRAG-Bench Answer Correctness **76.97 (Medical) and 64.33 (Novel)**, +5.13 and +4.43 over the best prior reported results.
  - Medical Evidence Recall 95.1.
  - +9.96 over the best fixed policy. vs Fixed-Wide it evaluates **81.9% fewer paths** and keeps 47.2% fewer evidence items.
  - Transfers to HotpotQA, MuSiQue and 2Wiki.
- **Monday takeaway:**
  - In a graph retriever (Neo4j VectorCypher, LightRAG), expose depth, fan-out and stop as per-query parameters.
  - Have a cheap LLM call classify the query type (direct / comparison / bridge) and pick them.
- **Limitations:** One extra LLM call per query. A technical report, not peer-reviewed.
- **Slide idea:** "One graph, many walks". The same graph is shown three times. A direct query lights a tight 1-hop disk, a comparison lights two balanced clusters, and a bridge query draws a long thin path.

### 13. 2609.10239 — LiteRAG: Cost-Efficient Graph-Based Retrieval-Augmented Generation
- **Submitted:** 2026-09-09. **Authors:** Daniel Alejandro Coll Tejeda, Pedro García López, Daniel Barcelona-Pons (Universitat Rovira i Virgili).
- **Problem:** GraphRAG Global/DRIFT use the LLM at query time to steer traversal and summarize communities, which is slow and expensive, and the contexts they produce are diffuse and oversized.
- **Method (diagram):** Graph exploration without LLM calls at query time, using query-adaptive score thresholds and **community-aware hub penalization** (down-weight hub nodes that connect everything). The retrieved subgraph becomes compact **reasoning chains** in the prompt (about 2,000-token budget).
- **Key results:** DistComp quality **0.798** (best), latency **>100× lower**, cost **>99% lower** than GraphRAG Global/DRIFT. Matches LinearRAG on UltraDomain with about **14× fewer tokens**.
- **Monday takeaway:** Before paying for LLM-driven graph traversal, try algorithmic traversal with hub penalties and render the result as path strings ("A —rel→ B —rel→ C").
- **Limitations:** DistComp is the authors' own benchmark. Code is "will be released" [UNVERIFIED availability].
- **Slide idea:** "Hubs are noise". A graph where one huge hub node shrinks (penalized) and a clean chain lights up and turns into text lines.

### 14. 2608.24921 — post-graph-rag: A PostgreSQL-Native Bi-Temporal Graph RAG Engine with Temporal Grounding at Synthesis
- **Submitted:** 2026-08-14 (v3 exists). **Author:** Chandan Rajah (independent researcher). Code: github.com/crajah/post-graph-rag
- **Problem:** GraphRAG needs a vector DB, a graph DB and a document store kept in sync. Extractors write junk edges. Graphs only accumulate, so superseded facts look current.
- **Method (diagram):**
  - One PostgreSQL database: pgvector for chunks, edge tables for traversal, community summaries.
  - An extraction validator rejects vague predicates, pronoun entities and bare quantities, normalizes predicates, and resolves entities to one canonical vertex.
  - A **bi-temporal** layer records valid-time (when the fact held) and transaction-time (when the system believed it), and supersedes incompatible older assertions.
  - Validity periods are passed into the synthesis prompt.
- **Key results:**
  - LongMemEval (500 Qs): **94.0%** (gemini-3.6-flash) vs Zep 71.2 (gpt-4o) vs full-context 60.2. Note that the models differ.
  - Temporal grounding in the prompt moves temporal reasoning from **0.496 to 0.881** in a paired ablation.
  - ECT-QA: 0.807 vs TG-RAG 0.599, LightRAG 0.406, GraphRAG 0.405.
- **Monday takeaway:**
  - Put an extraction validator in front of the graph writer.
  - Add `valid_from/valid_to` and `recorded_at` columns to edges.
  - If you already run Postgres, pgvector plus edge tables may be enough.
- **Limitations:** Single author. Comparisons use different backbone LLMs. Self-reported results.
- **Slide idea:** "Facts have lifetimes". An edge "CEO_of" from 2021 to 2024 greys out when a new edge appears. The prompt card shows "(valid 2021-03..2024-07)". The temporal-score bar jumps from 0.50 to 0.88.

### 15. 2608.16096 — The Commercial Tax: Rent-vs-Own Blind Spots in Multi-Hop Retrieval Benchmarks
- **Submitted:** 2026-08-17. **Authors:** Luis M. Sanchez (SGX Analytics / toryx.ai), Kosrow Dehnad (Columbia IEOR). Code: github.com/Toryx-AI/commercial-tax-multihop-retrieval
- **Problem:** Multi-hop leaderboards hide two facts a buyer needs: is the backbone licensed for commercial use, and what does indexing cost?
- **Method:** A license audit of the top MuSiQue systems, plus 13 embedders from 8 vendors on one MuSiQue harness with bootstrap confidence intervals, plus a cost model that separates one-time embedding, graph construction and recurring answering.
- **Key results:**
  - NV-Embed-v2 (the field's anchor) is **CC-BY-NC-4.0**. Three of four leading systems (HippoRAG-2, PropRAG, SAG, KET-RAG) depend on it for their best numbers and do not disclose that.
  - The best commercially licensed embedder trailed by 2.31 Recall@5 (p=0.001) until **NVIDIA Nemotron-3-Embed-8B (released 2026-07-16)**, which reaches parity (+0.24 R@5, p=0.69).
  - Published GraphRAG indexing cost for one 5.64 MB corpus ranges from **USD 2.30 to 24.94**, which extrapolates to about $428K vs $4.6M at 1 TB.
  - At 1 TB, embedding costs 7.5× to 900× less than graph construction.
- **Monday takeaway:** Check the license of every embedder behind a paper's number before copying the recipe. Budget GraphRAG indexing as the dominant cost, not query-time.
- **Limitations:** Cost extrapolation is model-based. Licensing facts are as of the paper date.
- **Slide idea:** "Read the license". A leaderboard; a stamp "NC" slams onto the top three rows. Then a cost bar chart where graph construction towers over embedding.

### 16. 2610.02373 — Hop-Decayed Influence: New Vulnerabilities of Structural Auxiliary Indexing in GraphRAG Pipelines with LLM
- **Submitted:** 2026-10-01. **Authors:** Jisung Park, John Le, Heath Cooper (email domain uow.edu; University of Wollongong inferred) [UNVERIFIED org]. Code: github.com/Jisung-Pacific/HDI-GraphRAG-Attack
- **Problem:** GraphRAG attacks so far poison nodes, edges or triples. The **auxiliary schema-level structures** built offline (community summaries, hierarchical edges, pre-computed scores) are trusted implicitly.
- **Method (diagram):** The 3S framework (Semantics, Structure, Scoring). The HDI attack propagates query-aware influence with hop decay to find high-leverage summaries or scores, then corrupts them after indexing.
- **Key results:** **88 to 94% ASR** on HotpotQA and 2Wiki against Microsoft GraphRAG and HippoRAG2, modifying only **0.016%** of auxiliary structures. Each change affects up to 6 queries (1:N amplification). **Over 99% evasion** of perplexity and paraphrase defenses, because the corrupted artifacts are coherent system-generated text.
- **Monday takeaway:**
  - Treat community summaries and pre-computed scores as security-relevant artifacts.
  - Hash or sign them at build time and verify them at query time.
  - Restrict who can write to the index store after the build.
- **Limitations:** Assumes post-indexing write access.
- **Slide idea:** "Poison the summary, not the data". A GraphRAG community tree; one summary node turns red and the red spreads (hop-decayed glow) to 6 query icons.

### 17. 2610.19133 — TRACER: Trace-Regularized Training Against Indirect Prompt Injection
- **Submitted:** 2026-10-13. **Authors:** Kshitij Mishra, Salem Lahlou, Nils Lukas (MBZUAI). Code: github.com/Mishrakshitij/TRACER
- **Problem:** Prompt-injection robustness depends on the **channel**. The same attack succeeds **18%** of the time as a follow-up user message but **53%** when placed in retrieved context.
- **Method (diagram):** Channel-aware adversarial training. It samples presentation wrappers (RAG context, tool output, agent message) and uses an answer-anchored, evidence-gated reward. ATRC aligns the attacked reasoning trace with the clean-evidence trace when the injection is invalid.
- **Key results:**
  - Qwen2.5-3B, GSM8K: RAG-framed ASR **65.5% → 6.1%** with 78 to 82% clean accuracy kept.
  - Joint RAG+tool training reaches 13.9% average ASR at 3B. One epoch at 7B reaches 9.4%.
- **Monday takeaway:** Red-team prompt injection **through the retrieval channel** specifically. A model hardened against chat injections is not hardened against injections inside retrieved documents.
- **Limitations:** Small models, a math task.
- **Slide idea:** "Same attack, different door". Two doors labelled "chat" (18%) and "retrieved doc" (53%). After TRACER the doc-door bar falls to 6%.

### 18. 2610.24834 — Consistency Is the Attack Surface: Detecting Coordinated Retrieval Poisoning with Embedding Geometry
- **Submitted:** 2026-10-17. **Authors:** Zeyan Li (Shanghai Jiao Tong University), Qirong Guo (HKUST-Guangzhou), Jianfeng Xu (SJTU).
- **Problem:** Consistency or majority defenses (RobustRAG, ReliabilityRAG) assume poison is a minority in context. Coordinated poison becomes the retrieved majority.
- **Method (diagram):** "CoordGuard" audits the top-k evidence embeddings for a **dense, query-anchored cluster** using robustly normalized, query-weighted affinities. It needs no labels or gradients. Modes: always-filter that cluster, or a benign-calibrated gate.
- **Key results:**
  - One injection reaches top-5 in **94.1%** of targeted query-seed rows, and the poison forms a retrieved majority in 52.9%.
  - RobustRAG/ReliabilityRAG ASR_exp is 0.512 vs 0.576 undefended, and they drop clean accuracy from 0.328 to 0.216.
  - CoordGuard always-filter (e5) gets ASR_exp to **0.167** at a 13.6-point clean cost. The Contriever gate keeps clean accuracy at 0.315 with ASR_exp 0.331.
- **Monday takeaway:** A cheap post-retrieval check: if several top-k chunks are near-duplicates of each other *and* of the query, suspect coordination. Deduplicate or down-weight the cluster before generation.
- **Limitations:** A real utility cost. Short-answer NQ protocol.
- **Slide idea:** "Too consistent to be true". Top-k points in 2D: five tight red points hug the query star. Draw a lasso and remove them.

```python
# [SKETCH] coordination audit on retrieved evidence (simplified idea from 2610.24834)
import numpy as np
def suspicious_cluster(qv, D, tau=0.9):           # D: (k, d) normalized chunk embeddings
    S = D @ D.T; np.fill_diagonal(S, 0)
    qsim = D @ qv
    z = (S - np.median(S)) / (np.median(np.abs(S - np.median(S))) + 1e-6)   # robust normalization
    dense = (z > 3).sum(1) >= 2                    # each member tightly bound to >= 2 others
    return np.where(dense & (qsim > np.quantile(qsim, 0.5)))[0]  # query-anchored members
```

### 19. 2610.30193 — Protection Is Not One Event: A Survey of RAG Protection Research by Measured Endpoint
- **Submitted:** 2026-10-21. **Authors:** Peiyang Liu (Peking University) et al., incl. Tencent and Beijing University of Technology.
- **Problem:** RAG defense papers use incompatible metrics and threat models.
- **Method:** An evidence map of **118** full-text-confirmed defense papers, coded by *what was actually measured*. 32 annotators, κ=0.867. Seven-family taxonomy: content disclosure, formal privacy proxies, access control and suppression, corpus-use detection, pipeline integrity and attribution, and others. Includes a controlled testbed.
- **Key results:**
  - Only **17.8%** of studies use content disclosure or reconstruction as their primary endpoint.
  - Most evaluations use non-adaptive attacks.
  - Testbed: a normalized **8-gram guard cuts 20-token verbatim copying to 0.0%**, yet a **3-query adaptive attacker recovers 48.3%** of hidden facts (Qwen3-8B).
- **Monday takeaway:** "No verbatim leakage" ≠ "no leakage". Test private-fact recovery with multi-turn adaptive probes, not n-gram overlap. Enforce ACLs before retrieval.
- **Limitations:** A survey. The testbed is one model.
- **Slide idea:** "The 8-gram wall". A wall blocks verbatim strings (0.0%) while three small question arrows go around it and assemble 48% of a secret.

### 20. 2610.30485 — Why Bother Me Again? Benchmarking Personal Agent Memory for Interaction Preferences (MemPABench)
- **Submitted:** 2026-10-21. **Authors:** Jialin Li, Zhenhao Chen, Hanjun Luo, Hanan Salam (NYU Abu Dhabi).
- **Problem:** Memory benchmarks test factual recall. Real assistants must remember *how* the user wants help (when to clarify, confirm, or just act).
- **Method:** On-policy interactive environment. 4 simulated users × 14 preferences, 99 sessions over 4 months, 5 event-driven preference changes per user. It tests preference selection, delivered behavior, and sensitivity to context and change. Covers 4 memory systems × 4 LLM backbones.
- **Key results:**
  - **Retrieval-based memory (Mem0, MemOS, simple RAG) did not beat No Memory.**
  - File-based memory improved accuracy but applied preferences beyond their contexts.
  - Even with the correct preference in context, overriding the agent's default habits stays hard.
- **Monday takeaway:**
  - Store interaction preferences as explicit, scoped rules (in the style of CLAUDE.md or user-profile files), not as chunks in a vector store.
  - Test preference *changes*, not just recall.
- **Limitations:** Simulated users. Small user count.
- **Slide idea:** Contrast with #2: "Raw-RAG wins on facts, loses on habits". A split slide with the two results.

---

## Also notable (short)
- **2610.05826** Bounded Provisional Visibility (Sony, Google LLC, Fortinet authors). For continuously ingested vector stores, newly ingested items are hidden if verification does not commit by a deadline (fail-closed). Median poisoned retrievals drop from **34 to 7** vs async admission (Milvus). Verify-before-visible delays clean visibility to 6.3 s vs 3 ms. A practical ops pattern for ingest pipelines.
- **2610.21464** Poisoning the Neighborhood. Hub-Satellite poisoning designed for **HNSW** (not exact kNN). On 2M Wikipedia docs: over 72% retrieval success, 31.29% ASR. Existing defenses fail. Lesson: evaluate attacks and defenses on your ANN index, not brute-force search.
- **2608.17153** When Detection Does Not Guarantee Resistance. Defines Cordon Rate (detects poison yet follows it) and Leakage Rate. With DeepSeek-V4-Flash, reasoning lowers Cordon from 0.205 to 0.075 even though detection falls from 0.965 to 0.665. A detector flag is not a safety guarantee.
- **2610.22615** When Does Uncertainty Measure RAG Hallucination Risk? Perplexity gets 0.81 to 0.91 AUROC on targeted unsupported edits, but only when evidence constrains the answer. With only the top-1 passage the signal weakens. Length-matched controls are required.
- **2609.19417** TrioRAG / "Less Is More: Graph-free Multimodal RAG" (Univ. Tübingen + Bosch). Three signals (question, anchor image, VLM-enhanced query) over one multi-vector index with late fusion. Matches graph-based systems with **1.6 to 2.3× faster** inference. Image retrieval of out-of-corpus web photos reaches only 19.3% document recall. Code: github.com/hk-zh/TrioRAG.
- **2609.05518** CrossModalQA. 1,863 open-domain multimodal multi-hop questions (average 3.50 hops). Complete cross-modal retrieval matters more than scaling the generator. Incomplete retrieval can be **worse than closed-book**.
- **2610.01871** Walking the Embedding Space. A black-box extraction attack on image-returning multimodal RAG. 2,500 queries reconstruct up to 611 radiology images, 5.6× a non-adaptive baseline.
- **2610.08571** RAG-PIBench. 4,876 leakage-controlled prompt-injection examples. DistilBERT F1 0.896. TF-IDF+SVM is competitive, so a cheap classifier is a reasonable first gate.
- **2610.19836** EGCForest. Enterprise group-chat memory as Channel/Actor/Artifact forests. Up to +20.85 accuracy over MemOS.
- Outside the window but relevant: **2607.16604** (Coventry University, v1 2026-07-18). LLM-extracted KG used *during retrieval* (entity-bridged expansion) raised gold-evidence completeness on HotpotQA bridge questions from 0.22 to 0.46. KG triples *injected into the prompt* gave no consistent gain and reduced faithfulness.

---

## Cross-paper trends (for a "what changed in 2026 H2" slide)
1. **Simple, well-tuned baselines keep winning.**
   - Raw-RAG beats agentic memory (#2).
   - LASAGNA's old MiniLM cross-encoder beats new rerankers, and its gates hurt faithfulness (#1).
   - Graph-free TrioRAG matches graph systems.
   - LiteRAG replaces LLM traversal with algorithmic traversal (#13).
   - The bar for "complex" components is now "beats dense + rerank inside the full stack, at production corpus size."
2. **Evaluation has moved from answers to evidence.**
   - Ans+Evid joint scoring (#10).
   - Citation-move probes (#4).
   - Driver-vs-cited counterfactuals (#5).
   - Authored-not-copied faithfulness (#11).
   - Abstention rates on unanswerable questions (#8).
   - Multi-turn sharded evals (#9).
   - Answer accuracy alone now overstates RAG quality, often by a lot.
3. **Agentic or iterative retrieval has hidden costs.** It lowers abstention (#8), its gates delete evidence (#1), and multi-turn rewriting distorts queries (#9). Every agentic add-on needs its own eval slice.
4. **RAG security moved from "is the doc malicious?" to "structure, time and channel".**
   - Coordinated cones defeat ingestion filters (#3).
   - Consistency becomes the fingerprint (#18).
   - HNSW topology matters (2610.21464).
   - GraphRAG summaries are an attack surface (#16).
   - Stale-but-authentic docs act as poison (#6).
   - Citations can be laundered (#5).
   - Injections succeed 3× more often via retrieved context (#17).
   - Defenses now live on the read path and use metadata such as demand, validity windows and provenance.
5. **Time is a first-class field.** Bi-temporal edges (#14), validity-aware reranking (#6), provisional visibility windows (2610.05826) and preference changes (#20) all point to the same need: store `valid_from/valid_to/recorded_at` and show it to the model.
6. **Multimodal: the generator's input is the new bottleneck.** Visual-token budget and resolution plus region OCR give +3 to +9 points (#7). Text leakage inflates multimodal scores (2607.16604). Incomplete cross-modal retrieval underperforms closed-book (CrossModalQA).

## Suggested "Monday checklist" slide (one line each, sourced)
- Re-evaluate every component inside the full stack at production corpus size (2610.29722).
- Keep the cross-encoder. Keep raw history. Test k between 5 and 30 (2610.30755).
- Add slices for unanswerable, multi-turn and "all-evidence" questions (2610.28340, 2609.36700, 2610.26951).
- Add the citation planting probe and copy-rate to faithfulness reports (2609.23053, 2610.18442).
- Store validity metadata and render it next to each chunk (2609.31342, 2608.24921).
- Add a read-path demand monitor and a coordination audit (2608.16044, 2610.24834).
- Sign or verify GraphRAG summaries and scores after the index build (2610.02373).
- Red-team injections through the retrieval channel (2610.19133).
- Raise the VLM page resolution and token budget, and add region OCR (2610.21318).
- Check embedder licenses (NV-Embed-v2 is NC) and GraphRAG indexing cost before adopting a paper recipe (2608.16096).
