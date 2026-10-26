# 00-VERIFIED: verifier pass over research-v2/rag (2026-10-23)

Scope: all 9 files in this folder (4 lab files with 35 labs, 3 arXiv sweeps, gotchas.md, industry.md).

**Method**
- **Code labs.** I downloaded the **released** wheel or sdist of every package from files.pythonhosted.org, at the exact version pinned in the labs. I extracted each into its own folder and grep-checked every import path, class, function, parameter, default and quoted error string. FAISS C++ defaults and the pgvector README/CHANGELOG were read from GitHub at tags `v1.15.1` and `v0.8.7`. I installed nothing and ran nothing. **No lab was executed.** Only lab-retrieval Lab 1 (stdlib) was run, by its original author. All "Expected output" blocks are still illustrative.
- **arXiv.** One batched arXiv API call (`id_list=` with all 160 IDs found in the folder). All 160 exist. 148 have a v1 date inside 2026-07-23..2026-10-23. 12 are outside (listed below).
- **Numbers.** I checked 22 headline numbers against the arXiv abstracts and the package source. Every checked number matched (see §4).
- Each lab heading in the four lab files now carries a `> **VERIFIED against <pkg> <version> source**` line.

---

## 1. Corrections table (edits made directly in the files)

| # | File / location | Problem found | Fix applied |
|---|---|---|---|
| 1 | lab-retrieval.md, Lab 2 `bm25_search` | **Real bug.** Lab 3 `hybrid_search(depth=20)` calls `bm25_search(q, 20)` on an 18-chunk corpus. bm25s 0.3.15 `retrieve()` raises `ValueError: k of 20 is larger than the number of available scores, which is 18...` (`bm25s/__init__.py` L759-764). So Labs 3, 5, 6 and 7 crashed on their first query. | Added `k = min(k, len(IDS))` before `retriever.retrieve(...)`. |
| 2 | lab-retrieval.md, Lab 9 walk-through | `InMemoryVectorStore` default k was marked [UNVERIFIED]. | Verified as `similarity_search(self, query, k=4, ...)` (langchain-core 1.7.0 `vectorstores/in_memory.py` L404). Tag removed. |
| 3 | lab-eval-prod.md, "Also seen" list | "Consistency Is the Attack Surface..." was cited as **2610.24907**. That ID is "CAT-RAG" (secure code generation). | Changed to **2610.24834**, with a note. |
| 4 | arxiv-agentic.md #8 ReFind | v1 date given as 2026-08-16. The arXiv API says 2026-08-13. | Corrected. |
| 5 | arxiv-agentic.md #4 SCOUT (PayPal) | 2026-08-24, API says 2026-08-25. | Corrected. |
| 6 | arxiv-agentic.md #7 Airbnb skill | 2026-10-09, API says 2026-10-10 (lab-agentic already had 10-10). | Corrected. |
| 7 | arxiv-agentic.md #16 BRIDGE | 2026-09-28, API says 2026-09-29. | Corrected. |
| 8 | all lab files | No per-lab verification status. | 35 `VERIFIED against ...` lines added under the lab headings. |

**Checked and found correct, so no edit was needed:**
- **2608.17153.** lab-eval-prod quotes Leakage 0.235→0.140 and ASR 0.233→0.298. arxiv-eval-graph quotes Cordon 0.205→0.075 and detection 0.965→0.665. All six numbers are in the abstract. They are different metrics, so the two files do not contradict each other.
- **2610.31606.** "Accepted chunk targets 36→51" (lab-retrieval) and "evidence spans 25→37" (gotchas) are both in the abstract.
- **lab-eval-prod Lab 6** uses the legacy `metadata={"hnsw:space": "cosine"}`. Chroma 1.5.9 still honours it (`collection_configuration.py` L375, `models/CollectionCommon.py` L553). The current form is `configuration={"hnsw": {"space": "cosine"}}`. I noted this in the VERIFIED line.
- **2610.26951.** The "any 82% / all 19%" numbers in arxiv-retrieval come from the paper's full text. They are not in the abstract. arxiv-eval-graph correctly marks them [UNVERIFIED]. Quote the qualitative finding unless someone checks the table.

**Papers outside the window.** I removed nothing. Every file that cites these papers already labels them as background or "just outside the window". Do not put them on a "last 3 months" slide:

| ID | v1 date | Title | Where it is used |
|---|---|---|---|
| 2607.12188 | 2026-07-13 | Cost-Governed RAG | industry (marked "just outside") |
| 2607.16604 | 2026-07-18 | Controlled Evaluation of Graph and Multimodal Augmentation in RAG | arxiv-eval-graph (marked "outside") |
| 2607.16973 | 2026-07-18 | TurboVec (post-filter recall 0.09-0.19) | industry (marked; also cited in checklist #6) |
| 2605.15184 | 2026-05-14 | Is Grep All You Need? | industry (background) |
| 2603.02153 | 2026-03-02 | RAG-Fusion industry deployment | lab-retrieval, industry (background) |
| 2602.07309 | 2026-02-07 | Semantic Search At LinkedIn | industry (case study) |
| 2501.09136, 2410.05779, 2408.09869, 2404.17723, 2403.14720, 2401.15884 | 2024-2025 | Agentic RAG survey, LightRAG, Docling report, LinkedIn KG, Spotlighting, CRAG | foundational citations only |

---

## 2. Verified labs (file, lab, versions checked)

Every row means this: the imports, classes, functions, parameters and cited defaults match the released source. The code was not executed.

| File | Lab | Verified against | Notes |
|---|---|---|---|
| lab-pipeline.md | 1 Docling parse + HybridChunker | docling-slim 2.142.1, docling-core 2.104.0 | `do_ocr` default True; default tokenizer MiniLM; `convert(max_num_pages=...)` |
| lab-pipeline.md | 2 Unstructured `chunk_by_title` | unstructured 0.27.34 | Requires-Python `<3.14,>=3.11`; `chunking-tokens` extra exists |
| lab-pipeline.md | 3 Header-aware token splitting | langchain-text-splitters 1.1.3 | `from_huggingface_tokenizer(tokenizer, **kwargs)` |
| lab-pipeline.md | 4 Gemini embeddings | google-genai 2.33.0 | `gemini-embedding-2` content conversion (`models.py` ~L6105) confirmed |
| lab-pipeline.md | 5 sentence-transformers v6, MRL, int8 | sentence-transformers 6.2.0 | `get_embedding_dimension`, `quantize_embeddings` top-level |
| lab-pipeline.md | 6 FAISS Flat/HNSW/IVF + IDSelector | faiss-cpu 1.15.1 wheel + v1.15.1 headers | efConstruction 40, efSearch 16, nprobe 1, HNSW default L2; IndexIDMap auto-wraps a plain selector |
| lab-pipeline.md | 7 pgvector filtered HNSW | pgvector-python 0.5.1, pgvector 0.8.7 README | ef_search 40, dimension limits 2,000/4,000/64,000 |
| lab-pipeline.md | 8 Chroma HNSW config + filters | chromadb 1.5.9 | defaults ef_construction 100, max_neighbors 16, ef_search 100; `$contains` on list metadata |
| lab-pipeline.md | 9 Incremental content-hash ingest | docling-core 2.104.0, google-genai 2.33.0, chromadb 1.5.9 | `include=[]` passes validation |
| lab-retrieval.md | 1 Metrics harness | stdlib (executed by its author) | ranx snippet not checked |
| lab-retrieval.md | 2 BM25 (bm25s) | bm25s 0.3.15 | **fixed** (k cap) |
| lab-retrieval.md | 3 Dense + RRF | sentence-transformers 6.2.0 | works after fix 1 |
| lab-retrieval.md | 4 Qdrant native BM25 + RRF | qdrant-client 1.20.0 | `DEFAULT_RANKING_CONSTANT_K = 2`; local text-query errors verbatim |
| lab-retrieval.md | 5 CrossEncoder.rank | sentence-transformers 6.2.0 | |
| lab-retrieval.md | 6 Cohere v5 spans + Voyage | cohere 7.3.0, voyageai 0.5.0 | `rerank-3` appears on docs.voyageai.com/docs/reranker |
| lab-retrieval.md | 7 Gemini multi-query/HyDE | google-genai 2.33.0 | `ThinkingLevel` is case-insensitive |
| lab-retrieval.md | 8 Contextual Retrieval (Haiku 5.5) | anthropic 2.3.0 | `messages.create` has no `temperature`; `ANTHROPIC_API_VERSION = "2026-10-21"`; effort `low..max`; Haiku 5.5 $0.10/$0.50 and 512-token cache minimum (claude-api reference) |
| lab-retrieval.md | 9 ParentDocumentRetriever | langchain-classic 1.0.8, langchain-core 1.7.0 | |
| lab-agentic.md | 1 ADK Workflow router+verifier | google-adk 2.13.0 | `__all__ = Agent, Context, Event, Runner, Workflow`; `DEFAULT_MODEL = 'gemini-3.5-flash'` |
| lab-agentic.md | 2 ADK CRAG back-edge | google-adk 2.13.0 | cycle-validation error text verbatim |
| lab-agentic.md | 3 ADK KB + GoogleSearchAgentTool | google-adk 2.13.0 | `propagate_grounding_metadata=True` |
| lab-agentic.md | 4 LangGraph router+verifier | langgraph 1.2.17, langchain-google-genai 4.4.2 | default recursion limit `"10007"` |
| lab-agentic.md | 5 LangGraph CRAG | langgraph 1.2.17 | `.text` is a `str` subclass |
| lab-agentic.md | 6 Multi-hop register | langgraph 1.2.17 | `Send` at `types.py` L738 |
| lab-agentic.md | 7 LightRAG on Gemini | lightrag-hku 1.5.7 | `supports_asymmetric` auto-detected from a `context` parameter |
| lab-agentic.md | 8 File Search via Interactions | google-genai 2.33.0 | `FileCitation.start_index` "measured in bytes" |
| lab-eval-prod.md | 1 ragas F/CP/CR | ragas 0.4.3 | `max_tokens` default 1024; ascore argument orders confirmed |
| lab-eval-prod.md | 2 TestsetGenerator | ragas 0.4.3, langchain-google-genai 4.4.2 | RunConfig defaults 180/10/60/16/42 |
| lab-eval-prod.md | 3 Calibrated claim judge | google-genai 2.33.0 | |
| lab-eval-prod.md | 4 CI regression gate | ragas 0.4.3 | GitHub Actions tag versions not re-checked |
| lab-eval-prod.md | 5 Semantic cache | redisvl 0.28.0 | `distance_threshold` default 0.1 |
| lab-eval-prod.md | 6 ACL-aware Chroma | chromadb 1.5.9 | legacy `hnsw:space` still accepted |
| lab-eval-prod.md | 7 Injection pytest | google-genai 2.33.0 | |
| lab-eval-prod.md | 8 RAG Engine | google-cloud-agentplatform 2.6.0, google-genai 2.33.0 | `retrieve_contexts` takes `genai_types.VertexRagStore` (mixing the two type modules is correct) |
| lab-eval-prod.md | 9 File Search refunds | google-genai 2.33.0 | `CreateFileSearchStoreConfig.embedding_model` exists |

**Still unverified** (these were already marked in the files and are unchanged):
- Exact server error texts: Gemini 429, the 400 for File Search combined with Google Search, the Chroma Rust dimension error, and the HF gated-repo message.
- Whether File Search `metadata_filter` supports OR or list membership.
- The `gemini-3.5-flash` model status (ADK default).
- The 40 ms rerank latency placeholder.
- The ranx/numba wheel availability.
- Whether ADK propagates grounding metadata in `single_turn` sub-agent mode.

---

## 3. Confirmed arXiv papers (148, all in window; id, title, date from the arXiv API)

Some takeaways come from the folder's own summaries and were not re-read in full text. The numbers I spot-checked against abstracts are listed in §4.

The full table is appended at the end of this file (§6) so that this section stays readable.

---

## 4. Spot-checked numbers (22 checked, all match the source)

| # | Claim | Source check |
|---|---|---|
| 1 | Fusion Tax: best fusion is below dense-only on 8-21% of queries; RRF taxed when dense is stronger | 2610.30612 abstract |
| 2 | Chunk recompute on revisions: fixed 57-68%, recursive 38-56%, CDC 43-54%, recall within 2 pts | 2610.31019 abstract |
| 3 | Structure vs contextualization: +0.022/+0.012; placebo +0.010/+0.016; hierarchical -0.033/-0.015 | 2610.10170 abstract |
| 4 | LASAGNA +47% predicted vs +17% measured; 450 configurations | 2610.29722 abstract |
| 5 | Ingest-time claims 85.2% at 2.2k tokens vs 72.5% at 16.3k; ~21x tokens; 33.7x cheaper updates | 2608.20845 abstract |
| 6 | SAFE-QE 57.5 / 27.8 / 4.3 hallucinated terms per query | 2610.13810 abstract |
| 7 | HyPE up to +42 pts context precision, +45 pts claim recall | 2607.29402 abstract |
| 8 | BM25 overtakes the agent at ~10M tokens; agent uses 39x the query tokens; ~20-pt margin | 2607.26497 abstract |
| 9 | Airbnb skill: 99.2% / 83.3%, 1-2 engineer days, ~90 s vs ~8-9 s | 2610.14428 abstract |
| 10 | MisKnow FCAR 0% → 54.7% | 2607.20891 abstract (the 85.5% pre-synthesis figure is from full text) |
| 11 | PayPal SCOUT 140.2k → 1.3k tool tokens | 2608.23992 abstract |
| 12 | CiteShade 0.01 → 0.68; CLR 0.84 / 0.64 | 2609.15660 abstract |
| 13 | DeclineCraft: iterative RAG lowers CAR in 30/40 configurations; rewrite+rerank lowers it for all 12 | 2610.28340 abstract |
| 14 | Raw-RAG first in 6 of 7 settings, +0.13 to +5.53 | 2610.30755 abstract |
| 15 | Requirement register 382 → 234 (MiniLM) | 2610.21184 abstract |
| 16 | Canaries: 16.7% vs 98.1% violations at 97-98% accuracy | 2608.26385 abstract |
| 17 | AGO judge AUROC 0.603 vs 0.783; per-domain 0.62-0.88; unsafe promotion 22.2-35.1% vs 29.3-41.8% | 2610.01218 abstract |
| 18 | Mixed embedding index recovers 4.96 of 11.90 pts; retrieval causes 81% of the deficit | 2609.05339 abstract |
| 19 | Union of rewriters +12.5 HIT@10 (51.70 vs 39.22); router rewrites <40% of queries; AmbigNQ -2.4 | 2609.05637 abstract |
| 20 | Qdrant RRF k default = 2; LangGraph recursion default 10007; FAISS efSearch 16 / nprobe 1; pgvector ef_search 40 and 2,000-dim limit; Chroma ef 100/16/100 | package source (see §2) |
| 21 | Claude Haiku 5.5 $0.10/$0.50 per MTok; 512-token cache minimum (4,096 on Haiku 4.5); sampling parameters → 400 on API 2026-10-21; effort default `medium` | claude-api reference (cached 2026-10-06) + anthropic 2.3.0 source |
| 22 | Shopify judge kappa 0.02 → 0.61 ("near-human") | shopify.engineering page (fetched) |

---

## 5. The 25 strongest slide candidates (hands-on, code-first)

| # | Slide | Source lab | Why it is strong |
|---|---|---|---|
| 1 | "Measure first": 25-line recall/MRR/nDCG harness and the floor run | lab-retrieval L1 | the only executed code; every later lab plugs into it |
| 2 | The E-4012 BM25 bug (`\b\w\w+\b` drops "E") and the normalise fix | lab-retrieval L2 | one-line bug that every support corpus has |
| 3 | Hybrid in 10 lines (RRF) next to the Fusion Tax (8-21% of queries hurt) | lab-retrieval L3 + 2610.30612 | code plus a counter-intuitive 2026 result |
| 4 | Qdrant one-call hybrid: default k=2 vs paper k=60 | lab-retrieval L4 | a silent default |
| 5 | `CrossEncoder.rank` returns positions and raw logits; don't threshold at 0.5 | lab-retrieval L5 | two bugs in one call |
| 6 | Cohere v5 `relevant_spans` as free context compression | lab-retrieval L6 | new API, visible output |
| 7 | Contextual Retrieval on Claude Haiku 5.5 with caching; the cookbook breaks on SDK 2.x (temperature 400, thinking block first) | lab-retrieval L8 | live "sample rot" demo |
| 8 | Docling HybridChunker with the embedder's own tokenizer, plus page provenance | lab-pipeline L1 | parse-to-citation in one script |
| 9 | Naive vs structure-first chunking, plus the placebo-controlled heading study | lab-pipeline L3 + 2610.10170 | code with evidence |
| 10 | Gemini embeddings: normalise 001 below 3072 dims; 2 aggregates a list of strings into one vector | lab-pipeline L4 | two silent bugs |
| 11 | FAISS efSearch/nprobe recall-latency sweep against exact search | lab-pipeline L6 | the trade-off curve on one slide |
| 12 | pgvector filtered top-k returns 3 of 10 rows; `hnsw.iterative_scan` fixes it | lab-pipeline L7 | the most common pgvector surprise |
| 13 | Content-hash incremental ingest ("reused=37 embedded=5 deleted=4"), plus the 57-68% recompute paper | lab-pipeline L9 + 2610.31019 | the day-2 problem |
| 14 | ADK 2.x `Workflow`: router → retrieve → answer → verifier gate | lab-agentic L1 | new ADK graph API |
| 15 | CRAG as a routed back-edge with a hard `MAX_ATTEMPTS` | lab-agentic L2 | budget lives in code |
| 16 | LangGraph recursion limit is now 10007: set `recursion_limit` plus a counter | lab-agentic L4 | 2026 gotcha |
| 17 | Multi-hop requirement register (#1/#2 substitution, sufficiency gate) | lab-agentic L6 + 2610.21184 | paper idea → code |
| 18 | LightRAG `mix` mode and `aquery_data` refs; the official demo is broken | lab-agentic L7 | GraphRAG hands-on |
| 19 | File Search citations: offsets are BYTES, insert right-to-left | lab-agentic L8 / lab-eval-prod L9 | managed RAG plus a subtle bug |
| 20 | ragas Faithfulness / Context Precision / Context Recall: which team fixes what | lab-eval-prod L1 | failure attribution |
| 21 | Calibrate the judge: kappa plus unsupported-admit rate | lab-eval-prod L3 + 2610.01218 / 2610.20634 | "the judge is a model you ship" |
| 22 | CI regression gate with knowledge-gap canaries (wrong = -4) | lab-eval-prod L4 + 2608.26385 | release decision as code |
| 23 | ACL pre-filter vs post-filter starvation, plus the leak-test assertion | lab-eval-prod L6 | security you can test |
| 24 | Prompt-injection pytest suite (canary, egress allowlist, false-action check) | lab-eval-prod L7 | runnable red-team |
| 25 | RAG Engine: corpus → import (partial failures do not raise) → retrieve with distance → rerank → grounded answer | lab-eval-prod L8 | Google managed RAG end to end |

---

## 6. Confirmed arXiv table (148 papers)

| arXiv id | v1 date | Title | One-line takeaway |
|---|---|---|---|
| 2607.20891 | 2026-07-23 | Is Deep Research Reliable? Misleading Knowledge Induces False Conclusions | One misleading document raises deep-research false-conclusion adoption from 0% to 54.7%; verify evidence when it enters the research state. |
| 2607.22922 | 2026-07-24 | iFVS: Towards Instance-Optimized Filtered Vector Search | Quantized filtered vector search loses precision; instance-optimized filtered search (abstract-level only). |
| 2607.23121 | 2026-07-25 | SMART: LLM-Augmented Hybrid Retrieval for Dynamic Product Ads | Snap: gate the LLM query path to ~10% of users: -90% LLM cost, +27.6% CVR in a 2-week A/B. |
| 2607.24010 | 2026-07-27 | When Should Active RAG Retrieve? A Budget-Aware Evaluation of Utility, Calibration, and Cost | Retrieval harm is non-negligible; simple uncertainty/score triggers often rival learned "when to retrieve" routers. |
| 2607.24173 | 2026-07-27 | Simple and Fast Algorithm for Graph-based Filtered Approximate Nearest Neighbor Search (Full Version) | Graph-based filtered ANN is still active research; post-filtering is the baseline it improves on. |
| 2607.26497 | 2026-07-29 | BM25 Wins at Scale: A Scaling Study of Retrieval-Augmented Generation Paradigms | BM25 overtakes a file-system agent above ~10M corpus tokens (agent costs 39x query tokens); rank first, then let the agent reason. |
| 2607.29173 | 2026-07-31 | MERIT: Efficient In-Place Deletion for Dynamic Graph-Based Approximate Nearest Neighbor Indexes | MERIT: in-place HNSW/Vamana deletes 3-19x faster than prior methods (right-to-be-forgotten deletes). |
| 2607.29402 | 2026-07-31 | Bridging the Question-Answer Gap in Retrieval-Augmented Generation: Hypothetical Prompt Embeddings | HyPE: embed LLM-generated questions per chunk at index time: up to +42 pts context precision, +45 pts claim recall, no query-time LLM. |
| 2608.01255 | 2026-08-02 | RaG-Tree: Combining R-Tree and HNSW for Multi-Attribute Range Filtered Approximate Nearest Neighbor Search | RaG-Tree: R-tree + HNSW for multi-attribute range filters. |
| 2608.01913 | 2026-08-03 | Diagnosing Search Behavior and Failure Modes in Long-Horizon Search Agents | Cumulative gold recall predicts search-agent accuracy (r=0.99); 77.5-93.6% of episodes add no new evidence. |
| 2608.08237 | 2026-08-08 | SAGE: SLO-Aware Adaptive Retrieval for Production RAG Systems | SAGE: learned per-query k under a 5 s P95 SLO: 95% vs 30% compliance, -51% retrieval cost, -2 pts EM. |
| 2608.08389 | 2026-08-09 | Not Worth Another Token: Marginal Value Estimation for Efficient Deep Research Agents | Where you prune deep-research subqueries matters more than the scoring rule; up to -73% tokens. |
| 2608.10385 | 2026-08-11 | Persona Conditioning as an Assessor-Sensitivity Probe for LLM-Based IR Evaluation | LLM relevance judges shift strictness under persona framing; small judges amplify ranking instability. |
| 2608.11584 | 2026-08-12 | EnterpriseRAG: Benchmarking LLM Instruction Adherence and Robustness under Non-Ideal Enterprise Retrieval | EnterpriseRAG: 80% per-constraint satisfaction but only 26.8% of answers meet all constraints. |
| 2608.12888 | 2026-08-13 | When Your Agent Opens the Chat App: Agent-Controlled Search over Raw Chat Logs Rivals Structured Memory | ReFind: agent-controlled BM25 over raw chat turns beats structured memory (58.2 vs 53.2 on MemoryAgentBench). |
| 2608.16044 | 2026-08-17 | Coverage Is Not Containment: A Fundamental Limit of Admission-Time Defenses Against Coordinated Poisoning of Vector Retrieval | Ingestion-time filters cannot stop coordinated "cone" poisoning; a read-path demand monitor caught 100% at 1% FPR. |
| 2608.16096 | 2026-08-17 | The Commercial Tax: Rent-vs-Own Blind Spots in Multi-Hop Retrieval Benchmarks | NV-Embed-v2 behind top multi-hop results is CC-BY-NC; GraphRAG indexing dominates cost; check licenses. |
| 2608.17153 | 2026-08-17 | When Detection Does Not Guarantee Resistance: Reasoning and Poisoned Context in RAG | Detection is not resistance: reasoning cut Leakage 0.235->0.140 and Cordon 0.205->0.075 while ASR rose 0.233->0.298 (DeepSeek-V4-Flash). |
| 2608.17994 | 2026-08-18 | Judge, Retrieve, or Abstain: Uncertainty-Guarded LLM Judging with Provable Risk Guarantees | Calibrate LLM-judge thresholds so accepted-verdict FDR <= alpha (Clopper-Pearson); route the rest. |
| 2608.20317 | 2026-08-20 | Projecting BrowseComp-Plus onto ClimbMix: Toward More Realistic Corpora for Agentic Search | BrowseComp-Plus on a 553M-doc web corpus: evidence recall 84.3% -> 21.4%; small corpora overstate retrieval ease. |
| 2608.20627 | 2026-08-20 | When Failures Propagate: Causal Failure Attribution in Agentic Retrieval-Augmented Generation | Hop-1 retrieval faults surface as hop-3 wrong answers; post-hoc traces miss hop-2/3 faults; log per-hop evidence. |
| 2608.20685 | 2026-08-21 | Temporal Validity on Real Software Histories: Eliminating Stale-Fact Errors in Code-Assistant Memory over GitHub Fixes | RAG served superseded code facts 36-38% of the time; a supersession memory reached 0.91 vs 0.57-0.59. |
| 2608.20845 | 2026-08-21 | RAG Deserves an Index: Why Ingest-Time Compilation Beats Query-Time Interpretation | Ingest-time compiled claims: 85.2% correct at ~2.2k reader tokens vs 72.5% at 16.3k for best chunking; contextual-chunk hybrid+rerank ties at ~21x tokens. |
| 2608.22167 | 2026-08-23 | MCP-Universe RL: A Framework for Training MCP Tool-Use Agents via Reinforcement Learning | MCP-Universe RL: MCP servers as RL environments (no headline number in abstract). |
| 2608.23992 | 2026-08-25 | Hybrid Semantic Tool Discovery for Enterprise MCP Gateway: Architecture and Implementation | PayPal SCOUT: two MCP meta-tools (tool_search with BM25+dense RRF, execute_tool): tool tokens 140.2k -> 1.3k. |
| 2608.24921 | 2026-08-14 | post-graph-rag: A PostgreSQL-Native Bi-Temporal Graph RAG Engine with Temporal Grounding at Synthesis | post-graph-rag: one Postgres (pgvector + edge tables) with bi-temporal edges; temporal grounding 0.496 -> 0.881 (self-reported). |
| 2608.26385 | 2026-08-26 | Why RAGs Hallucinate: Penalty-Aware Evaluation of Retrieval-Augmented Generation Systems with Knowledge-Gap Canaries | Knowledge-gap canaries: answer accuracy 97-98% across systems but canary violations 16.7% vs 98.1%; score wrong = -4. |
| 2609.00364 | 2026-08-31 | Closed Forms and Synthetic Twins: Predicting Approximate Nearest Neighbor Recall from Embedding Statistics | ANN recall predictable from label-free embedding statistics; benchmark encoder + index together. |
| 2609.02143 | 2026-09-02 | A Power Law in Logarithm's Clothing: On the Scalability of Graph-Based Vector Search | Graph-search cost grows as N^c before slowing; re-tune efSearch when the corpus grows 10x. |
| 2609.03654 | 2026-09-03 | Enhancing Financial Question Answering: A Novel Benchmark Dataset of Banks' financial statements | Bank financial statements: contextual chunk enrichment + retrieval-tuned embedder raises NDCG@10 0.322 -> 0.710. |
| 2609.05339 | 2026-09-04 | Does Your Agent's Memory Survive a Model Upgrade? A Controlled Study of Memory Portability | A 50/50 mixed-embedding index recovers only 4.96 of the 11.90-point re-embed gain; isolate embedding versions. |
| 2609.05518 | 2026-08-31 | CrossModalQA: A Cross-modal and Multi-hop Benchmark for Multimodal Retrieval-augmented Generation | CrossModalQA: incomplete cross-modal retrieval can be worse than closed-book. |
| 2609.05637 | 2026-09-04 | Better Together: Complementary Query Rewriting Under a Strong RAG Baseline | One query rewriter is at best on par with a strong baseline; a union of rewriters gives +12.5 HIT@10; score-gated routing rewrites <40% of queries. |
| 2609.10239 | 2026-09-09 | LiteRAG: Cost-Efficient Graph-Based Retrieval-Augmented Generation | LiteRAG: LLM-free graph traversal with hub penalties: >100x lower latency, >99% lower cost than GraphRAG Global/DRIFT. |
| 2609.10750 | 2026-09-09 | When Synthetic Data Hurts: On Catastrophic Forgetting in Skill Retrieval for LLM Agents | Synthetic fine-tuning of a 34k-skill retriever causes forgetting; anchor regularisation/LwF/EWC fixes it. |
| 2609.11065 | 2026-09-10 | MOSAIC: Query-Aware Exploration Policy Adaptation for GraphRAG | MOSAIC: per-query GraphRAG traversal policy (depth, width, stop) chosen by an LLM analyzer; 81.9% fewer paths. |
| 2609.11646 | 2026-09-10 | Your Retriever Already Knows: Distribution-Shape QPP for RAG Retrieval Sufficiency | Score-distribution QPP predicts retrieval sufficiency at AUROC 0.856 in 2 ms (local LLM judge 0.649). |
| 2609.14245 | 2026-09-13 | The Attribution-Compression Frontier in Retrieval-Augmented Generation | After compression, citations scored 0.86 precision vs summaries but 0.12 vs source spans; cite raw chunks. |
| 2609.14412 | 2026-09-13 | Question's Gambit: The First Move Matters in Agentic Deep Search | Question's Gambit: clue decomposition -> per-clue retrieval -> union -> rerank as the first move: 83.1% -> 90.5% on BrowseComp-Plus. |
| 2609.14875 | 2026-09-14 | EviQE: Evidence Selection for LLM-Based Query Expansion | EviQE: pool docs from several reformulators, select evidence, expand once; more rounds can hurt. |
| 2609.15058 | 2026-09-14 | Fast Label-Filtering Approximate Nearest Neighbor Search via Progressive Label Set Stratification | Fast label-filtered ANN via progressive label-set stratification. |
| 2609.15143 | 2026-09-14 | Top-K Is Not a Budget for Hybrid Retrieval | Top-K is not a budget: budgeted exact RRF keeps 95-97.7% nDCG@20 with 66-99.5% fewer accesses. |
| 2609.15660 | 2026-09-14 | CiteShade: Citation Laundering in Multi-Source Retrieval-Augmented Generation and Its Counterfactual Defense | CiteShade: one attacker source raises wrong answers 0.01 -> 0.68 and launders the citation to a trusted source; use leave-one-source-out. |
| 2609.16073 | 2026-09-13 | The Immutable Past: Formalizing State Mutability and Conflict Resolution in Mutable RAG | "Semantic shadowing" in append-only mutable RAG memories; formalizes conflict resolution. |
| 2609.16175 | 2026-09-14 | BOA: Beamwidth Online Adaptation for Filtered-ANNS on a GPU | BOA: GPU filtered-ANN beamwidth adaptation, 7-12.5x throughput (secondary summary). |
| 2609.16268 | 2026-09-14 | Spurious Tool Use: When RL Agents Learn the Wrong Reason to Act | RL agents learn spurious cue->tool shortcuts (up to +39% spurious calls); reward tool necessity. |
| 2609.16453 | 2026-09-15 | Predicting Partial Answer Quality and Utility in Agentic Retrieval-Augmented Generation | Agentic RAG answer quality plateaus early; early stopping cut ~11% of iterations at ~98% quality. |
| 2609.18099 | 2026-09-16 | When Is Graph Structure Worth Its Cost? The Case for Structure Pricing in Retrieval-Augmented Generation | EffiRAG: use the graph to locate passages, answer from source text: beat LightRAG-hybrid on 93/120 at 57% lower cost. |
| 2609.19417 | 2026-09-16 | Less Is More: Graph-free Multimodal RAG via Multi-signal Late Fusion | TrioRAG: graph-free multimodal RAG with late fusion matches graph systems, 1.6-2.3x faster. |
| 2609.22247 | 2026-09-05 | CHART: A Harness-Rotation Curriculum for Harness-Robust Search Agents | CHART: RL-learned parallel search breaks when the system prompt changes; rotate harnesses during training. |
| 2609.22537 | 2026-09-18 | EvidenT: Building Trustworthy Enterprise Assistants through Evidence Groundedness and Traceability | EvidenT: deterministic lexical evidence alignment before generation: +29% gold-source hit rate, no citations to non-retrieved URLs. |
| 2609.23053 | 2026-09-19 | Attributable Post-Rationalization in RAG Citations: A Controlled Reproduction and an RLVR Comparison | Planting probe: about 1 in 7 RAG citations is post-rationalized; RLVR agents are no better than the base model. |
| 2609.24122 | 2026-09-21 | Re:CAP - Auditing Retrieval Coverage in Production RAG Pipelines | Re:CAP: reference-free retrieval-coverage audit recovers 9-29% of gold docs BM25 top-500 misses. |
| 2609.27213 | 2026-09-23 | BoundaryMORPH: Budgeted Reranking via Active Set Selection for Diffuse Retrieval | BoundaryMORPH: when the cross-encoder budget is below the context size, spend it on the top-k boundary. |
| 2609.29455 | 2026-09-24 | A Systematic Multi-Domain Evaluation of Document Retrievers | 33-retriever evaluation: GTE-large best quality per ms, SPLADE-v3 best sparse, NV-Embed-v2 best but slowest. |
| 2609.29652 | 2026-08-29 | SmallReason-ColBERT: An Ultra-Small Late-Interaction Retriever for Reasoning Intensive Retrieval | SmallReason-ColBERT: 32M late-interaction model near a 150M one on BRIGHT. |
| 2609.30906 | 2026-09-25 | ToolSearcher: Optimizing Tool Selection at Scale via Reinforcement Learning | ToolSearcher: RL-optimized tool selection at scale (title-level). |
| 2609.31342 | 2026-09-25 | Stale-Document Poisoning: When Outdated Retrieval Overrides Correct Model Answers | Stale-document poisoning: outdated docs flip 30% (Llama) / 37% (Qwen) of correct answers; store valid_from/valid_to. |
| 2609.31415 | 2026-09-25 | Evaluating the accuracy of KV cache reuse techniques | Current metrics artificially inflate reported KV-cache-reuse accuracy. |
| 2609.31660 | 2026-09-15 | Parser, Chunking, and Embedding Interactions in Retrieval-Augmented Generation over Indian Government Regulatory Documents | Parser x chunker x embedder interact significantly on Indian regulatory documents; no retriever family dominates. |
| 2609.32699 | 2026-09-26 | RandSlot: Learning Compact Visual Document Representations with Random Soft Tokens | RandSlot: compact visual-document vectors via random soft tokens. |
| 2609.33778 | 2026-09-27 | Evidence-Inference Reconstruction: When The Evidence Is Recalled But The Reasoning Goes Wrong | Evidence recalled but reasoning wrong: separate retrieval from inference failures. |
| 2609.34179 | 2026-09-28 | RAGWarrant: Evidence-Preserving Governance for RAG Policy Promotion Under Quality, Cost, Latency, and Risk Constraints | RAGWarrant: release outcomes PROMOTE/BLOCK/REJECT/INCONCLUSIVE with quality and cost/latency/risk gates. |
| 2609.35155 | 2026-09-28 | Right Facts, Wrong Rule: Scope-Transfer Poisoning of Retrieval-Augmented Generation | Scope-transfer poisoning: correct facts, wrong scope; an applicability audit cuts target error 70.8% -> 16.4%. |
| 2609.35774 | 2026-07-29 | Post-Generation Verification Dominates Retrieval Optimization: A 2^4 Factorial Ablation of RAG Pipeline Features | 2^4 factorial: a post-generation completeness check (d=+0.48) beats agentic search tweaks. |
| 2609.35782 | 2026-08-06 | Financial Evidence Crowding: Diagnosing and Mitigating Constraint-Induced Displacement in Retrieval-Augmented Generation | Financial evidence crowding: off-scope passages take top-k; a gated reranker raises inclusion 0.757 -> 0.902. |
| 2609.35831 | 2026-09-23 | Beyond the Context Window: An Adaptive Entropy-Based Routing Framework for Hybrid Retrieval and Long-Context Language Models | EDAR: entropy-gated escalation from RAG to long context: 97.4% of LC accuracy, 70.7% fewer tokens (no code; treat as pattern). |
| 2609.36344 | 2026-09-28 | DeepRewind: Predicting and Repairing Premature Commitments in Deep Research Agents | DeepRewind: commitment gate + rollback: premature commitments -59.1% vs Open Deep Research. |
| 2609.36505 | 2026-09-29 | BRIDGE: Bilevel Retrieval-Credit-Aware Agentic Reinforcement Learning | BRIDGE: adapt the retriever before the policy when co-training search agents (+9.6 EM multi-hop at 3B). |
| 2609.36700 | 2026-09-29 | Lost in Conversation or Lost in Translation? Diagnosing Multi-Turn Degradation in RAG | Multi-turn sharded queries: up to 21% relative drop; consolidate constraints into one standalone query. |
| 2609.37225 | 2026-09-29 | ResComEmb: Effective and Efficient Multimodal Embedding via Residual Homogeneity Compression | ResComEmb: multimodal embeddings with fewer visual tokens. |
| 2609.37469 | 2026-09-27 | Relevance Is Not Sufficient Evidence: Detecting Evidence Gaps Before Generation in RAG | RINSE: even when told to abstain, generators answer 40.0-99.3% of insufficient-evidence questions; a pre-generation sufficiency check helps. |
| 2609.37911 | 2026-09-29 | Generated Query Expansion Still Helps Strong Sparse Retrieval: A Controlled Study with SPLADE-v3 | Generated query expansion still helps SPLADE-v3 if the original query keeps >=30% weight. |
| 2609.38473 | 2026-09-29 | Re-ranking and Late Interaction Drive Retrieval Quality: A Controlled Comparison of RAG Strategies for Scientific Question Answering | Scientific QA: ColBERTv2 Hit@3 ~93% vs ~46% single-vector; rewriting without reranking hurt (encoder confound). |
| 2609.39912 | 2026-09-30 | TRACE: Trajectory Selection for Parallel Scaling of Search Agents | TRACE: pick among parallel rollouts by evidence overlap: 8 rollouts ~ majority vote over 64. |
| 2610.00406 | 2026-09-30 | LLM-as-a-Judge for Low-Resource Languages: Adapting Ragas and Comparative Ranking for Romanian | Ragas for Romanian: granular decomposition gives 96% human alignment on faithfulness. |
| 2610.01218 | 2026-10-01 | AGO AI Quality Gate: Evidence-First Release Decisions for Retrieval-Augmented Generation | AGO quality gate: cheap judge AUROC 0.603 vs gpt-4o 0.783 (per-domain 0.62-0.88); validate the judge first. |
| 2610.01324 | 2026-10-01 | Evaluating Biomedical Reranking for LLM-Based Question Answering over Longitudinal Clinical Notes | Clinical notes: reranking lifts Hit@10 46.6% -> 60.6% but answer correctness only 44.8% -> 48.6%. |
| 2610.01871 | 2026-10-01 | Walking the Embedding Space: Datastore Extraction from Multimodal RAG | Black-box extraction of images from multimodal RAG: 2,500 queries reconstruct up to 611 radiology images. |
| 2610.02373 | 2026-10-01 | Hop-Decayed Influence: New Vulnerabilities of Structural Auxiliary Indexing in GraphRAG Pipelines with LLM | GraphRAG community summaries are an attack surface: 88-94% ASR modifying 0.016% of auxiliary structures. |
| 2610.02652 | 2026-10-02 | RaBitQ-SSD: Split Codes and Pipelined I/O for SSD-Resident Vector Search | RaBitQ-SSD: IVF + split RaBitQ codes, 10B vectors at ~3,200 QPS (90% recall) on one server. |
| 2610.03651 | 2026-10-02 | MRVQ: One Resident Index for Dimension- and Rate-Elastic Vector Search | MRVQ: one residual-quantized index serves all (dimension, bit-rate) pairs at 17.8-22x less RAM; a memory, not quality, win. |
| 2610.04691 | 2026-10-03 | RAGStress: A controlled benchmark for evaluating retrieval-augmented generation under knowledge-base degradation | RAGStress: benchmark for RAG under knowledge-base degradation (title-level). |
| 2610.05034 | 2026-10-04 | Agentic RAG Evaluation: Budget Allocation Across Questions, Trajectories, and Reads | Agentic RAG eval budgets: temperature 0 cut answer disagreement 14.3% -> 3.4%; more questions beat more trajectories. |
| 2610.05099 | 2026-10-04 | Small Agents with Semantic Search: Efficient Multilingual Code Localization | ColGREP: late-interaction semantic search tool for code-localization agents, -44.1% CPU latency. |
| 2610.05826 | 2026-10-05 | Bounded Provisional Visibility: Controlling Poisoning Exposure in Continuously Ingested RAG Vector Stores | Bounded provisional visibility: hide unvetted new items after a deadline: median poisoned retrievals 34 -> 7. |
| 2610.07091 | 2026-10-05 | Smart Content Ingestion for Generative AI Workloads | Production ingestion: structure-aware parent-child chunker reaches hit@1 68.6%, hit@10 92.8%, MRR 0.77. |
| 2610.07960 | 2026-10-06 | From Delivery to Stateful Exploration: Rethinking the Index for Agentic Search | IndexAct: return candidate-set handles and counts, not passages: 73.5% vs 62.7% (Pi-Serini) on BrowseComp-Plus. |
| 2610.08452 | 2026-10-06 | Agentic AutoRAG: RAG Pipeline Optimization through Reasoning-Driven Agents | Agentic AutoRAG: reasoning agents optimize RAG pipelines (title-level). |
| 2610.08463 | 2026-10-06 | UNREAL: Unifying Retrieval and Long-Context with a Single Model | UNREAL: one frozen LLM selects evidence from a 21M-chunk index and inside long prompts. |
| 2610.08571 | 2026-10-06 | RAG-PIBench: A Leakage-Aware Benchmark for Prompt-Injection Detection in Trustworthy RAG Systems | RAG-PIBench: DistilBERT F1 0.896; TF-IDF + SVM/LR competitive for injection detection. |
| 2610.10170 | 2026-10-07 | Does Document Structure Help Dense Retrieval? A Placebo-Controlled Ablation of Four Mechanisms Across Two Corpora | Real heading paths beat LLM-contextualized fixed windows (+0.022/+0.012) and a shuffled placebo; two-stage section routing hurts. |
| 2610.11553 | 2026-10-08 | EVIE: Evidence-Vector-Informed Embeddings for Visual Document Retrieval | EVIE: cluster page-patch vectors to 32-64 centroids: ~3.8 GiB per million pages. |
| 2610.13157 | 2026-10-09 | SOAR: Source-Aware Reinforcement Learning with Precise Credit Assignment for Search Agents | SOAR: separate doc vs memory evidence streams with a source-consistency reward: fabrication -74.8%. |
| 2610.13296 | 2026-10-09 | PRIME: Pre-Retrieval Index Modeling Enhancement for Structured Document Retrieval-Real | PRIME: TF-IDF metadata + heading tree matches structure-aware chunking with 45.8x less embedding compute; LLM rewriting lost evidence. |
| 2610.13810 | 2026-10-09 | Tracing and Taming Hallucinated Terms via Subsequence-Association Filtering and Breadth-Aware Selection for LLM Query Expansion | SAFE-QE: HyDE injects 57.5 unsupported terms/query, Query2doc 27.8, SAFE-QE 4.3 at equal nDCG@10. |
| 2610.14196 | 2026-10-09 | Simple Linear Corrections for Compression in Late Interaction | One learned d x d matrix fixes pooled/pruned multi-vector compression in 154/160 settings. |
| 2610.14428 | 2026-10-10 | Frustratingly Easy Agentic RAG via Portable Skills: A Case Study in Customer Support | Airbnb: SKILL.md + one hybrid search tool + LLM-written wiki index: 99.2% procedural equivalence, ~90 s vs ~8-9 s. |
| 2610.14816 | 2026-10-10 | Data Curation and Model Souping: Unlocking Qwen3-0.6B for MS MARCO Passage Ranking | Qwen3-0.6B reranker reaches strong MS MARCO results via data curation, hard negatives and model souping. |
| 2610.15130 | 2026-10-10 | Recall-Bounded Staleness for Filtered Multi-Tenant ANN Graph Indexes under Concurrent Updates | Multi-tenant filtered ANN recall loss = staleness + filtered navigability; bigger merge batches make staleness worse. |
| 2610.15642 | 2026-10-11 | Recall What Is Missing: Composing Evidence from Long-Term Agent Memory | MemPursuit: residual-based evidence composition for agent memory: +7.2 pts LoCoMo at Top-10, 32.9x faster than BGE-v2-m3 reranking. |
| 2610.16998 | 2026-10-12 | Glasseek: A Transparent Recipe for Training and Trustworthy Evaluation of DeepSearch Agents | Glasseek: benchmark leakage inflates deep-search scores (-5.1 pts when blocked); report closed-book baselines. |
| 2610.17627 | 2026-10-13 | AiSAQ-in-Filtering for DRAM-free Filtered Information Retrieval | AiSAQ filtering: DRAM-free filtered vector search. |
| 2610.17742 | 2026-10-13 | Geometric Structure Predicts Per-Example Neighborhood Loss Under PCA Truncation | PCA truncation: mean quality hides large per-example neighbor loss; test truncation on hard queries. |
| 2610.18442 | 2026-10-13 | Copying Is Not Grounding: Training Faithful Long-Form RAG with Authored-Sentence Credit | Faithfulness metrics get gamed by copying; credit only authored, supported sentences. |
| 2610.18925 | 2026-10-13 | CacheSmith: Accurate RAG Serving under Latency SLOs with Adaptive KV Reuse | CacheSmith: adaptive KV reuse under latency SLOs: up to +27.5% quality-gated SLO attainment. |
| 2610.19133 | 2026-10-13 | TRACER: Trace-Regularized Training Against Indirect Prompt Injection | TRACER: same injection succeeds 18% via chat but 53% via retrieved context; channel-aware training cuts RAG ASR 65.5% -> 6.1%. |
| 2610.19836 | 2026-10-14 | EGCForest: Structured Agent Memory Organization for Enterprise Group Chats | EGCForest: enterprise group-chat memory as Channel/Actor/Artifact forests. |
| 2610.20367 | 2026-10-14 | Cascaded Retrieval with Cross-Modal Query Refinement for Efficient Visual Document Search | SCOUT (visual): single-vector recall then multi-vector rerank of top 25: 28.8x lower latency, 104-337x smaller index. |
| 2610.20634 | 2026-09-30 | Jev-as-a-Judge for RAG Claim Verification: Confidence-Gated Cascading Between a Non-Generative Verifier and a Frontier LLM | Jev-as-a-Judge: equal accuracy but 23.2% vs 14.1% unsupported-claim admits; score guards on admit rate. |
| 2610.21184 | 2026-10-15 | Beyond Retrieval Failure: Understanding Why LLMs Miss Evidence in Multi-Hop RAG | Requirement register cuts wrong answers with unretrieved evidence 382 -> 234 on MuSiQue; bottleneck moves to sufficiency checking. |
| 2610.21318 | 2026-10-15 | Loud and Clear: Making Visual Evidence Count in Multimodal Document RAG | Loud and Clear: raise VLM page token budget and add region OCR: +8.88 / +3.09 / +4.22 over ColQwen3. |
| 2610.21464 | 2026-10-15 | Poisoning the Neighborhood: A Topology-Aware Topic-Level Attack on Large-Scale HNSW-based RAG Systems | HNSW-aware poisoning: >72% retrieval success, ~31% ASR on 2M docs; existing defenses fail. |
| 2610.21512 | 2026-10-15 | QREF: Improving DeepSearch Agents by Aligning Search with Reasoning via Query Refinement and Evidence Filtering | QREF: plug-in query refiner + evidence filter for deep-search agents, no policy retraining. |
| 2610.22297 | 2026-10-15 | Private Retrieval Augmented Generation via Random Projection | One shared random projection on query and doc embeddings resists extraction better than DP baselines. |
| 2610.22331 | 2026-10-15 | KnowGPO: Knowledge-Grouped Policy Optimization for Search Agents | KnowGPO: group RL rollouts by acquired knowledge state; +3.8-4.2 points over GRPO-family baselines. |
| 2610.22615 | 2026-10-15 | When Does Uncertainty Measure RAG Hallucination Risk? | Perplexity flags unsupported edits at 0.81-0.91 AUROC only when evidence constrains the answer. |
| 2610.22652 | 2026-10-15 | Evidence-Gated Bilingual RAG for Reliable Consumer Banking Search | Banking search: Answer / Related-Mismatch / No-Answer gate + hybrid + CE: Top-1 50.48% -> 79.05% (n=210, preliminary). |
| 2610.23148 | 2026-10-16 | Grounded Credit Assignment in Reinforcement Learning for Multi-Turn Search Agents | Search-R1 raises EM while the evidence-supported share of correct answers falls 84.0% -> 42.9% (Bamboogle); GCA fixes it. |
| 2610.24341 | 2026-10-17 | Optimal Fusion Weights Form Intervals, Not Points: A Latency-Aware Study of Query-Adaptive WRRF | Optimal WRRF fusion weights are intervals; 74/128 dynamic methods beat RRF; tune one static weight first. |
| 2610.24478 | 2026-10-17 | Beyond Recall Saturation: Scaling Hard-Negative Reranker Training for Industrial Legal Retrieval | Scaling hard-negative reranker training for industrial legal retrieval. |
| 2610.24659 | 2026-10-17 | RAGit: Turning Document Preprocessing into an Experimental Variable for RAG | RAGit: workbench treating parser x chunker x index as experimental variables. |
| 2610.24834 | 2026-10-17 | Consistency Is the Attack Surface: Detecting Coordinated Retrieval Poisoning with Embedding Geometry | CoordGuard: coordinated poison forms a dense query-anchored cluster in top-k; filtering cuts ASR_exp to 0.167. |
| 2610.24854 | 2026-10-17 | Learning to Program Retrievals: Composing Search Primitives via Reinforcement Learning | RPL (Meta): agent writes retrieval programs over sparse/dense/fuse/dedup/rerank primitives: +11.5% EM at 4B. |
| 2610.24907 | 2026-10-17 | CAT-RAG: Improving Secure Code Generation with Category-Aware Agentic Retrieval | CAT-RAG: category-aware agentic retrieval for secure code generation (only appears via a citation correction). |
| 2610.25269 | 2026-10-18 | EG-GRPO: Evidence-Guided Step-level Credit Assignment for Deep Search Agents | EG-GRPO: first-citation evidence as step reward (w=0.5): GAIA 34.8 -> 45.9 at 4B. |
| 2610.25779 | 2026-10-19 | OpenSaC: A Python Library for Search as Code in Deep Research Agents | OpenSaC: search-as-code SDK: BrowseComp 82.25% -> 85.21% with -37.8% tokens. |
| 2610.25937 | 2026-10-19 | RAGLeak: Supply-Chain Privacy Backdoors in Retrieval-Augmented Generation | RAGLeak: supply-chain privacy backdoors in RAG (title-level). |
| 2610.26260 | 2026-10-19 | Preference Is Not Position: Evaluating Reranking on NevIR in Fixed Hybrid Candidate Pools | NevIR: a ranker can improve pairwise preference (56.62% vs 52.30%) while cutting MRR 0.5764 -> 0.3055. |
| 2610.26313 | 2026-10-19 | StrucChunk: Structure-Aware Retrieval for Legal Document RAG | StrucChunk: section-tree chunking + breadcrumb: legal Recall@5 0.557 -> 0.804; boundary precision 100% vs 7.7%. |
| 2610.26951 | 2026-10-18 | The Bottleneck Is Retrieval, Not Reading: Diagnosing Evidence-Based Generation with RAG for Long Context Question Answering | Similarity retrieval finds any relevant chunk far more reliably than all required chunks; chunking drops document identity. |
| 2610.27195 | 2026-10-19 | UIBK-Embedding: Effective Text Retrieval by Unifying Dense and Late-Interaction Retrieval | UIBK-Embedding: one 179M model gives dense + late-interaction scores in one PLAID index (BEIR 59.79). |
| 2610.27273 | 2026-10-19 | FLINT: Fixed-budget Late Interaction | FLINT: fixed V vectors per doc/query; index 5.3-9.3x smaller than ColBERTv2 at near-equal nDCG. |
| 2610.28340 | 2026-10-20 | DeclineCraft: A RAG Abstention Benchmark for Jointly Measuring Combined Retrieval and Parametric Knowledge | DeclineCraft: iterative RAG lowers correct abstention in 30/40 configs; rewrite+rerank lowers it for all 12 models. |
| 2610.28364 | 2026-10-20 | Context-Aware Prompt Injection Detection via Small Language Models in RAG Pipelines: nokast-secureRAG | nokast-secureRAG: 0.994 recall in-distribution but near zero on PoisonedRAG; detectors miss fluent fact-poisoning. |
| 2610.28435 | 2026-10-20 | Multimodal Reranking Is a System One Decision | A general VLM's A-P choice logits over top 16 match a dedicated 8B visual reranker. |
| 2610.29250 | 2026-10-21 | Let Agents Design How They Search: Automatic Interface Optimization for Agentic Search | SearchWeaver: agents redesign corpus artifacts/tools/instructions: BrowseComp-Plus 71.6 -> 78.4%. |
| 2610.29523 | 2026-10-21 | pplx-embed-v2-late Technical Report | pplx-embed-v2-late: 9B index / 0.6B query encoders share one space (asymmetric serving). |
| 2610.29722 | 2026-10-21 | Retrieval Augmented Generation Compositionality | LASAGNA: three techniques predicted +47% combined deliver +17%; best design changes with corpus size. |
| 2610.30193 | 2026-10-21 | Protection Is Not One Event: A Survey of RAG Protection Research by Measured Endpoint | Survey of 118 RAG-protection papers: an 8-gram guard stops verbatim copying, yet a 3-query attacker recovers 48.3% of hidden facts. |
| 2610.30425 | 2026-10-21 | Getting a GRIP on Graph-Based Search for Learned Sparse Retrieval | GRIP: graph index for SPLADE vectors, 2.5x lower latency than Seismic, ~2x larger index. |
| 2610.30435 | 2026-10-21 | Self-Assessment Reinforcement Learning for Search-State Awareness in Retrieval-Augmented Large Language Models | SARL: RL-trained self-assessment of search state: +24.3% relative over strongest baseline. |
| 2610.30485 | 2026-10-21 | Why Bother Me Again? Benchmarking Personal Agent Memory for Interaction Preferences | MemPABench: retrieval memory (Mem0, MemOS, simple RAG) did not beat no-memory on interaction preferences. |
| 2610.30612 | 2026-10-22 | The Fusion Tax: A Diagnostic Analysis of When Hybrid Retrieval Hurts | Fusion Tax: best fusion still ranks relevant docs below dense-only on 8-21% of queries; RRF beats dense-only only when retrievers are balanced. |
| 2610.30697 | 2026-10-22 | Lychee: Certified Screening of Inverted Lists for High-Recall Vector Search | Lychee: certified GPU IVF screening, 9.7-117x faster than cuVS IVF-Flat at very high recall. |
| 2610.30755 | 2026-10-22 | Is Complex Agentic Memory Always Needed? Naive RAG Is Stronger Than We Thought | Raw-RAG (dense + rerank over raw history) ranks first in 6 of 7 memory-benchmark settings. |
| 2610.31019 | 2026-10-22 | Chunk Recomputation under Real Document Revisions: Measuring Update Cost and Retrieval Quality of Fixed, Recursive, and Content-Defined Chunking | On real revisions fixed-size chunking re-embeds 57-68%, recursive 38-56%, CDC 43-54%, with <2 pts recall difference. |
| 2610.31606 | 2026-10-22 | How Ground Truth Shapes Retrieval Scores: Evidence-Aware Evaluation of a Retrieval-Augmented Generation System for Breast Lesions | Evidence-span relabelling raised accepted chunk targets 36 -> 51 (spans 25 -> 37) without changing rankings. |
