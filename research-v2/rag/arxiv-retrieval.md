# arXiv sweep: Retrieval (embeddings, late interaction, hybrid, rerankers, chunking, contextual retrieval, ANN, long-context vs RAG)

Window: papers submitted 2026-07-23 .. 2026-10-23. Sweep date: 2026-10-23.

## How this was gathered (read before using numbers)

- The arXiv API (export.arxiv.org) returned HTTP 429, because other agents share the quota. I used the arXiv advanced-search UI instead, with a submitted-date filter, across 8 queries: "late interaction", "reranking + retrieval", "chunking", "approximate nearest neighbor", "sparse + dense retrieval", "text embedding", "long-context + retrieval-augmented", "contextual chunk", and "embedding" in the title.
- For every paper below I read the arXiv HTML full text (arxiv.org/html/<id>) or the abstract page. A summarizing fetch tool did the reading, so I did not see the raw page myself. All numbers are as extracted. Before you put a number on a slide, check it against the paper's table. The links are given for this.
- None of these papers were in the older research (C:/Users/evija/googleadk2.0/research-rag cites no 2607–2610 IDs).
- Model names such as "Qwen3.5", "Qwen3.8-27B", "JEV-27B-VL", "gemini-embedding-2" and "Gemma-4" are written as the papers write them. I did not check that these models exist outside the papers.
- Where a paper has internal inconsistencies, I say so in its entry.

---

## Ranking (by practical impact for an engineer building RAG retrieval)

| # | arXiv | Short name | One-line "Monday" change |
|---|---|---|---|
| 1 | 2610.30612 | Fusion Tax | Do not turn on hybrid search by default. Measure the sparse–dense balance on 200–400 labeled queries, then pick RRF, dense-weighted interpolation, or dense-only. |
| 2 | 2610.24341 | WRRF intervals | If you fuse, tune one static weight w per corpus first. Only add per-query weighting when oracle headroom is large. |
| 3 | 2610.29722 | LASAGNA | Gains from separate RAG tricks do not add up (+47% predicted, +17% measured). Test each change inside your full stack, at your production corpus size. |
| 4 | 2610.10170 | Structure vs. contextualization | Split at real headings and prepend the heading path. This beat LLM-generated chunk context, and was cheaper. Do not route to a section first. |
| 5 | 2610.31019 | Chunk recomputation | For corpora that people edit, use recursive (boundary-aware) chunking, not fixed windows. It cuts re-embedding by 13–20 points. |
| 6 | 2610.26951 | Bottleneck is retrieval | Monitor "all evidence retrieved", not "any evidence retrieved". At k=10, any gold fact is found for 82% of queries but all gold facts for only 19%. |
| 7 | 2609.38473 | Rerank + late interaction | On scientific QA, ColBERT gave Hit@3 of 93% versus 46% for single-vector retrieval. Query rewriting without reranking hurt. |
| 8 | 2609.29455 | 33-retriever evaluation | Use GTE-large as a default dense model. Use SPLADE-v3 as the sparse model. Pick fusion partners by measured overlap on hard queries. |
| 9 | 2610.29523 | pplx-embed-v2-late | Index with a large model and query with a small model that shares its embedding space (9B index, 0.6B query). |
| 10 | 2610.27195 | UIBK-Embedding | One 179M model gives dense plus late-interaction scores in one PLAID index. No second index to keep in sync. |
| 11 | 2610.27273 | FLINT | A fixed V vectors per document and per query. The index is 5–9× smaller than ColBERTv2, at nearly equal nDCG on ModernBERT. |
| 12 | 2610.14196 | Linear correction | If you compress multi-vectors by pooling or pruning, train one d×d matrix on about 5k queries. It helped in 154 of 160 settings. |
| 13 | 2610.26313 | StrucChunk | For statutes and contracts, chunk on the Part > Chapter > Section tree and add a breadcrumb. Chunking gave 73–88% of the gain. |
| 14 | 2608.20845 | RAG deserves an index | Extract verified atomic claims at ingest. 85% accuracy at 2.2k reader tokens versus 72.5% at 16.3k for chunks. |
| 15 | 2610.13296 | PRIME | Deterministic TF-IDF metadata plus a heading tree matched structure-aware chunking with 45.8× less embedding compute. |
| 16 | 2610.28435 | VLM choice reranker | A general VLM asked one A–P choice question over the top 16 equals a dedicated 8B visual reranker. |
| 17 | 2610.20367 | SCOUT | Cascade: one vector per page for recall, then multi-vector MaxSim only on the top 25. 28.8× lower latency, index 104–337× smaller. |
| 18 | 2610.11553 | EVIE | Cluster page-patch vectors into 32–64 centroids. 3.81 GiB per million pages, against hundreds or thousands of GiB for full ColPali-style storage. |
| 19 | 2610.08463 | UNREAL | One frozen LLM selects evidence from a 21M-chunk corpus and from inside a long prompt. Long context and RAG become one mechanism. |
| 20 | 2610.02652 | RaBitQ-SSD | Billion-scale on one box: a RaBitQ code prefix in DRAM, the rest on SSD. 10B vectors at 3,000+ QPS (90% recall). |
| — | brief | EDAR (2609.35831), Lychee (2610.30697), GRIP (2610.30425), HNSW poisoning (2610.21464), SmallReason-ColBERT (2609.29652) | see the end |

---

## 1. The Fusion Tax: A Diagnostic Analysis of When Hybrid Retrieval Hurts
- **arXiv:** 2610.30612 (cs.IR). **Submitted:** 22 Oct 2026. Also in IEEE Access vol. 14, pp. 159620–159637.
- **Authors:** Aaditya Chauhan and Arun Agarwal (independent researchers, WA, USA).
- **Problem:** Hybrid (BM25 + dense, usually with RRF) is the default advice because it wins on average. Nobody measures how many single queries it makes worse.
- **Method (diagram):**
  1. Run BM25 (Anserini, k1=0.9, b=0.4) and dense (MiniLM, BGE-small/base/large, Qwen3-Embedding-0.6B) on 7 BEIR corpora.
  2. Fuse with RRF (k=60), min–max interpolation (α=0.7 on dense), or CombMNZ.
  3. For each query, compare the fused nDCG@10 with the better single retriever (oracle tax) and with dense-only (deployable tax).
  4. Sort queries into 4 quadrants (Both-Win, Dense-Only, Sparse-Only, Both-Fail) by which retriever has a relevant document in its top 10. Then try to predict fusion failure, and add a BGE-reranker-v2-m3 over the top 30.
- **Key results:**
  - Interpolation beats dense-only on average on all 7 corpora, by +0.008 to +0.051 nDCG@10 (BGE-small). But it hurts 8.2–20.9% of queries against dense-only.
  - RRF is worse than dense-only on average on 5 of 7 corpora. It helps only on NFCorpus (+0.020) and TREC-COVID (+0.135). RRF hurts 15.3–32.9% of queries.
  - A bigger encoder does not remove the tax: Qwen3-Embedding still hurts 14–43% of queries. With SPLADE as the sparse side, the tax is 14–41%.
  - Failure is hard to predict: AUC is 0.63 within a corpus and 0.59 across corpora. A learned per-query router never beat static interpolation on held-out corpora.
  - 77 hurt queries lost all relevant documents from the top 10.
- **Monday takeaway:** Build a 200–400 query labeled sample from real traffic. Compute the four-quadrant split. Where dense clearly leads, use interpolation with α≈0.6–0.7. Where the two are balanced, use RRF, CombMNZ, or α≈0.5. Keep dense-only as an option. Use one static policy per corpus, not a per-query router. Run the check again when the corpus or the encoder changes.
- **Limitations:** First-stage retrieval only, with no answer generation. One reranker at depth 30. TREC-COVID has only 50 queries. Corpora with millions of documents were left out (CPU budget).
- **Slide idea:** "Hybrid wins on average and loses on one query in five." A bar chart shows the aggregate nDCG gain (small, green). Then each bar splits to show the % of queries hurt (red), animated per corpus. Last, a 2×2 quadrant grid fills with dots (one per query), and the off-diagonal cells pulse.
- **Code for the slide (plain Python, no library API assumed):**
  ```python
  # per-query fusion tax vs dense-only, given per-query nDCG@10 dicts
  hurt = [q for q in qids if ndcg_fused[q] < ndcg_dense[q] - 1e-9]
  print(f"aggregate gain: {mean(ndcg_fused.values()) - mean(ndcg_dense.values()):+.3f}")
  print(f"fusion tax: {len(hurt)/len(qids):.1%} of queries hurt")
  ```

## 2. Optimal Fusion Weights Form Intervals, Not Points: A Latency-Aware Study of Query-Adaptive WRRF
- **arXiv:** 2610.24341 (cs.IR). **Submitted:** 17 Oct 2026.
- **Authors:** Iris Ma (UC Irvine), with Zahra Shekarchi, Stuart Mcilroy, Mahtab Farrokh, Joel Stremmel (Thomson Reuters) and Fattane Zarrinkalam (Univ. of Guelph / Thomson Reuters).
- **Problem:** RRF gives every retriever the same weight for every query. Query-adaptive methods assume each query has one best weight.
- **Method (diagram):** WRRF score = w/(k + r_sparse) + (1−w)/(k + r_dense), with k=60. RRF is w=0.5. An oracle sweeps w from 0 to 1 in steps of 0.01 over the top 200, per query. The paper compares 8 predictors of w, in latency tiers:
  - T0: RRF
  - T1: mean weight, or ridge regression
  - T2: RoBERTa or ModernBERT-large with an interval loss
  - T3: DAT, or a few-shot LLM (Qwen3-32B, Ministral-3-14B)

  Data: MS MARCO, NQ, NFCorpus and ACORD, with BM25 or RM3 for sparse and MiniLM or Qwen3-Embedding-8B for dense.
- **Key results:**
  - The best w is almost never a single point: about 1% of queries on MS MARCO and NQ. Over 65% of queries have a contiguous interval of good weights.
  - 18–30% of queries have no w that puts a relevant document in the top 10. Fusion cannot fix them.
  - Oracle headroom over RRF: about 0.15–0.22 on MS MARCO and NQ, 0.05–0.09 on NFCorpus and ACORD.
  - 74 of 128 dynamic-method comparisons beat RRF after FDR correction. Only 46 of 128 beat a simple per-dataset mean weight.
  - Median recovery of the headroom is 12.2%. The best is 61.1% (few-shot Ministral on NQ).
  - Latency: RRF under 1 µs, linear model about 265 µs, small encoder 5–8 ms, LLM 205–225 ms.
- **Monday takeaway:** Compute (Oracle − RRF)/Oracle on a labeled sample. If it is low, use RRF or a tuned static w. If it is high and you have a GPU, a small encoder (T2) is the best value. An LLM weight predictor costs about 200 ms, and that time may serve a reranker better.
- **Limitations:** English only. LLM runs at temperature 0.1, so the numbers vary a little between runs.
- **Slide idea:** Plot nDCG against w for 3 example queries. The curves draw in and show flat plateaus (intervals) and a curve that stays at zero (unreachable). Then a latency ladder T0→T3 rises with an "is it worth it?" gauge.

## 3. Retrieval Augmented Generation Compositionality (LASAGNA)
- **arXiv:** 2610.29722 (cs.CL). **Submitted:** 21 Oct 2026.
- **Authors:** Ido Levy (IBM; Weizmann Institute), Segev Shlomov (IBM), Leshem Choshen (IBM; Weizmann).
- **Problem:** Papers test RAG techniques one at a time. Do the gains survive when you combine them? Do retrieval and faithfulness prefer the same choices? Do small-corpus results hold at scale?
- **Method (diagram):** An open-source framework, *lasagna*, with 8 pipeline dimensions:
  - embedder: BGE-M3, E5-large, MiniLM
  - chunker: fixed, semantic, sentence-window, hierarchical, structure-aware, recursive
  - index enrichment: RAPTOR, GraphRAG, contextual retrieval
  - retrieval: dense, BM25, SPLADE, RRF hybrid, graph
  - query augmentation: HyDE and similar
  - reranking: cross-encoder, MMR
  - context compression
  - agentic gates: CRAG, Self-RAG, Speculative RAG

  The study uses a D-optimal fractional factorial design over 5 BEIR sets and 3 QA sets in one shared corpus, scaled from about 5K to 200K documents. Cost: about $5,200 of compute and 310 hours.
- **Key results:**
  - The 3 largest single-component gains predicted +47% nDCG@10 together. The combined pipeline gave +17%.
  - Faithfulness gains carry over to the combined pipeline better than retrieval gains do.
  - The components that improve retrieval are different from those that improve faithfulness.
  - An agentic loop on top of a strong retrieval stack gave almost no faithfulness gain and hurt retrieval and latency.
  - GraphRAG alone did not change nDCG@10 and roughly doubled latency.
  - The design that wins at small scale is 13.7% behind at 200K documents. The ranking flips from about 25K documents.
  - Lighter pipelines kept similar quality at 10–20× lower latency on 100K–200K corpora.
- **Monday takeaway:** Do not stack blog-post tricks. Do an A/B test of each addition inside your full pipeline, at production corpus size. Track retrieval and faithfulness separately.
- **Limitations / inconsistencies:** The abstract says 450 configurations. The body describes 167 factorial runs plus 138 ablations. The abstract says 55K documents where the body says 5K. The query sets are small (93 retrieval, 56 generation). Faithfulness uses an LLM judge.
- **Slide idea:** "1 + 1 + 1 ≠ 3". Three green bars (+x% each) slide together into one stack labeled "predicted +47%". The stack then collapses to the measured +17%. Second build: a line chart of design A versus design B against corpus size, with the lines crossing at 25K.

## 4. Does Document Structure Help Dense Retrieval? A Placebo-Controlled Ablation of Four Mechanisms Across Two Corpora
- **arXiv:** 2610.10170 (cs.IR). **Submitted:** 7 Oct 2026.
- **Authors:** Andrey Kuehlkamp, Priscila Correa Saboia Moreira, Samuel Rund (Center for Research Computing, Univ. of Notre Dame).
- **Problem:** Do structure-aligned chunks, LLM-generated chunk context (Anthropic-style contextual retrieval), heading-path prefixes, and hierarchical routing actually help? Or does any prefix just move the embedding?
- **Method (diagram):** 11 arms with size-matched chunks:
  - A0: fixed windows
  - A1: fixed windows + LLM context (contextual retrieval)
  - A2: structure-aligned chunks
  - A3: A2 + real heading path
  - P (placebo): shuffled heading paths taken from other documents
  - A4: route to a section first, then rank chunks
  - G2–G4: gold (author-written) structure

  Embedders: bge-small and bge-large. Optional reranker: bge-reranker-v2-m3 over the top 50. Structure is induced by Gemma-4-26B-A4B. Metric: coverage-nDCG@10. Corpora: 200 Wikipedia featured articles and QASPER.
- **Key results (strong embedder, cov-nDCG@10):**
  - Structure + heading path minus LLM contextualization: +0.0218 (Wikipedia), +0.0115 (QASPER), both significant.
  - Real heading paths minus placebo: +0.0099 and +0.0161. The gain comes from the content of the prefix, not from adding tokens.
  - Section routing minus flat retrieval: −0.0326 and −0.0147. Routing hurts, because first-stage section recall is only 0.17–0.20 on QASPER.
  - Fixed windows to structure-aligned chunks (A0→A2): +0.041 and +0.019.
- **Monday takeaway:** Before you pay for an LLM call per chunk, cut at real headings and prepend "Doc title > H1 > H2". It is cheaper, and in this study it was better. Do not build "route to section, then search". Search all chunks flat.
- **Limitations:** The effects are small (+0.01 to +0.02, dz ≤ 0.11). Two English expository corpora. Retrieval only. One structure-induction model.
- **Slide idea:** A placebo-trial layout with 4 lanes (fixed, +LLM context, +real headings, +shuffled headings). The bars race. The shuffled-heading bar stops at the fixed-window level and gets a "placebo" stamp.

## 5. Chunk Recomputation under Real Document Revisions: Measuring Update Cost and Retrieval Quality of Fixed, Recursive, and Content-Defined Chunking
- **arXiv:** 2610.31019 (cs.CL). **Submitted:** 22 Oct 2026.
- **Authors:** Yuning Bian, Lele Xu, Yifan Yuan, et al. (Anhui University of Technology).
- **Problem:** Chunkers are judged on static corpora. In a knowledge base that people edit, a moved boundary forces re-embedding of text that did not change.
- **Method (diagram):** Replay 120 real adjacent Wikipedia revision pairs (62 Chinese, 58 English).
  1. Chunk both versions with fixed-size (≤304 tokens), recursive (400-token target), or content-defined chunking (CDC, "Steadlith", 176–352 tokens).
  2. Reuse an embedding only when the chunk input is byte-identical to the old version.
  3. Recompute fraction = re-embedded tokens / all new-version tokens.
  4. Measure evidence recall with BGE-M3 at a 2048-token context budget.
- **Key results:**
  - Recompute, Chinese: fixed 68.4%, recursive 55.7%, CDC 54.0%. English: fixed 57.4%, recursive 37.9%, CDC 42.8%.
  - Recall differs by under 2 points (95.0–98.3%).
  - Small English edits: fixed re-embeds 46% of tokens, recursive 25%.
  - A 1% insertion at the start of a document makes fixed-size chunking re-embed 100%.
  - CDC failed on 4 of 62 Chinese articles, because long runs of unsegmented Chinese exceeded its maximum.
- **Monday takeaway:** Hash each chunk (sha256 of its exact input) and re-embed only changed hashes. Choose recursive or boundary-aware chunking, not fixed windows, so edits do not shift every later boundary. Report "recompute %" next to recall when you pick a chunker.
- **Limitations:** One source (Wikipedia), 120 pairs, one encoder, stateless chunkers only. The recall intervals do not rule out small losses.
- **Slide idea:** Animated text strip: a sentence is inserted near the top. Fixed-window boundaries all shift right, and every chunk turns red ("re-embed"). Recursive boundaries stay anchored at paragraph breaks, and only one chunk turns red.
- **Code for the slide:**
  ```python
  import hashlib
  def key(chunk_text, model_id): return hashlib.sha256(f"{model_id}\x00{chunk_text}".encode()).hexdigest()
  to_embed = [c for c in new_chunks if key(c, MODEL) not in vector_cache]   # only changed chunks
  ```

## 6. The Bottleneck Is Retrieval, Not Reading: Diagnosing Evidence-Based Generation with RAG for Long Context Question Answering
- **arXiv:** 2610.26951. **Submitted:** 18 Oct 2026.
- **Authors:** Debopriyo Banerjee, Owais Aijaz, Ahmer Tabassum, Zhuohan Xie, Preslav Nakov, Veselin Stoyanov (MBZUAI).
- **Problem:** When RAG fails on a multi-part question, is the cause retrieval or reading? Chunking also removes document identity (author, title, section).
- **Method (diagram):** "Evidence-based generation": the model must return an answer plus line-level citations, scored as Ans+Evid. The paper compares long-context prompting (with the oracle evidence in the context) against open-corpus RAG over 256-token windows. 13 LLMs. Benchmarks: MultiHop-RAG with re-annotated evidence, QASPER-MP (multi-paper), a two-hop haystack, and NoLiMa with evidence labels (10K–1M characters).
- **Key results:**
  - MultiHop-RAG at k=10: any gold fact is retrieved for 82% of queries, all gold facts for only 19% (8% on inference queries).
  - Answer accuracy, RAG: 60% (GPT-5), 48% (Sonnet-4.5), 44% (Gemini-3-Fl). Long context with the oracle evidence: 86%, 82%, 78%. The two conditions do not use the same candidate pool.
  - RAG refuses 24–40% of answerable QASPER-MP queries, against 13–18% for long context.
  - Retrieved text for two-hop NoLiMa grows from about 1.9K characters (10K context) to over 202K (1M context).
- **Monday takeaway:** Add a "complete-evidence recall" metric: did you retrieve all needed chunks? Put document metadata (title, author, section) into each chunk. Decompose multi-part queries before retrieval. Ask for line citations so you can see grounding failures.
- **Limitations:** Mostly synthetic or semi-synthetic benchmarks. The long-context and RAG comparison is not matched on candidate pool. Line-level, not span-level, evidence.
- **Slide idea:** Two gauges side by side: "any relevant chunk: 82%" fills fast, "all relevant chunks: 19%" fills slowly and stops low. Then a multi-hop question splits into 3 evidence pieces and only 1 lights up in the top 10.

## 7. Re-ranking and Late Interaction Drive Retrieval Quality: A Controlled Comparison of RAG Strategies for Scientific Question Answering
- **arXiv:** 2609.38473 (cs.IR). **Submitted:** 29 Sep 2026.
- **Authors:** Bhagyesh Rathi, Eshan Chawla, William B. Andreopoulos (San José State University).
- **Problem:** Which RAG retrieval strategy matters on a large real corpus, with the generator held fixed?
- **Method (diagram):** 463,971 arXiv papers (2024–25). Generator: Llama-3.1-8B (4-bit). Six pipelines:
  1. Classic: SPECTER2 + Chroma, top 3
  2. Query rephrase
  3. Rephrase + listwise LLM rerank of the top 10
  4. RRF over 3 sub-queries
  5. Agentic tool call (at most 1 search)
  6. ColBERTv2 with a PLAID index

  Evaluation: an LLM judge (1–5) plus gold-paper Hit@3, on a released set of 19,484 synthetic questions.
- **Key results (judge score; Hit@3 problem / method queries):**
  - Classic: 3.60; 46.3% / 46.8%
  - Rephrase: 3.62; 39.7% / 45.9%
  - Rephrase + rerank: 3.77; 47.5% / 52.8%
  - Fusion: 3.55; 38.6% / 44.2%
  - Tool call: 3.54; 45.7% / 48.5%
  - ColBERT: 3.94; 92.8% / 94.8%
  - Fusion and agentic tool calling were significantly worse than Classic.
- **Monday takeaway:** If your corpus is scientific or technical, try a late-interaction retriever before you build query rewriting or agent loops. Never ship query rewriting without a reranker after it.
- **Limitations:** ColBERT also changes the encoder, so the gain cannot be credited to late interaction alone. Synthetic queries were generated from abstracts by the same model family. Zero scores were excluded from the means. No latency or cost data.
- **Data / code:** Kaggle dataset `bhagyeshrathi/synthetic-problem-query-and-method-query-dataset`; github.com/bhagyeshrathi07/rag_eval
- **Slide idea:** Six lanes race on Hit@3. Five lanes stop at about 45%. The ColBERT lane runs to 93%. A footnote flags the encoder confound.

## 8. A Systematic Multi-Domain Evaluation of Document Retrievers
- **arXiv:** 2609.29455 (cs.IR). **Submitted:** 24 Sep 2026.
- **Authors:** Valentin Velev, Andreas Spitz (Univ. of Konstanz).
- **Problem:** Leaderboard numbers come from different setups. What works out of the box, and at what latency?
- **Method:** 33 retrievers:
  - BM25
  - 4 learned sparse (incl. SPLADE-v3)
  - 16 encoder dense (incl. ColBERTv2, GTE, BGE, Jina v3)
  - 2 encoder-decoder
  - 7 decoder-only (incl. Qwen3-Embedding-0.6B, NV-Embed-v2, EmbeddingGemma, GritLM)
  - 3 expansion methods (docT5query, query2doc, HyDE)

  Datasets: MS MARCO, TREC-DL 19/20, 14 BEIR sets, LoTTE, InstructIR, FollowIR. Uniform compute budget.
- **Key results:**
  - NV-Embed-v2 is best on TREC-DL19 (0.753), TREC-DL20 (0.765), BEIR (0.612) and LoTTE (0.876 S@5), at about 1,292 ms per query on DL19.
  - SPLADE-v3 is best on MS MARCO (MRR@10 0.403) and scores 0.725 on DL19 at about 126 ms.
  - GTE-large is second on BEIR (0.587) at about 37 ms.
  - BM25 is the fastest (about 28 ms) and beats several neural models.
  - 22 of 33 retrievers have negative pp-MRR on FollowIR: they do not follow instructions.
  - About 70% of published numbers reproduced within 2 SE.
- **Monday takeaway:** Default dense model: GTE-large-class, for the best quality per millisecond. Sparse leg: SPLADE-v3. Choose hybrid partners by low overlap on your hard queries, not by "different architecture". Do not assume instruction prompts work.
- **Limitations:** No BGE-M3, E5-mistral or Qwen3-Embedding-8B. English only. Small cutoffs, so these results do not show first-stage recall for reranking.
- **Slide idea:** A scatter of nDCG against latency (log x) with 33 dots appearing by family color. A Pareto frontier line draws through GTE, SPLADE-v3 and NV-Embed-v2.

## 9. pplx-embed-v2-late Technical Report
- **arXiv:** 2610.29523 (cs.IR). **Submitted:** 21 Oct 2026.
- **Authors:** Markus Krimmel, Louis Milliken (equal contribution), …, Bo Wang (Perplexity AI).
- **Problem:** Production-grade multilingual, multimodal late-interaction models at two cost points.
- **Method (diagram):**
  1. Teacher: 18B (Qwen3.5-27B with its last 20 layers pruned), bidirectional attention, 128-dimensional token vectors, MaxSim. Trained with InfoNCE at batch 16,384 on 186M pairs (56.5% text-text, 30.9% text-image, 12.6% text-visual-document), then on triplets with hard negatives.
  2. Students: 9B and 0.6B, distilled to match the teacher's token embeddings with an L2 loss.
  3. Result: all three models share one embedding space, so you can index with 9B and query with 0.6B.
- **Key results:**
  - Internal 72-task domain text benchmark, nDCG@10: 9B 81.3, 0.6B 78.0. Comparisons: nemotron-3-embed-8b 79.7, voyage-4-nano 74.6.
  - ViDoRe-V3 (text/Markdown): 9B 64.7.
  - ViDoRe-V3 (image): 9B 65.2, against EVIE-8B 66.4.
  - MIRACL-Vision: 9B 75.7, against gemini-embedding-2 77.5.
  - BrowseComp+ agent accuracy: 64.0%, +4.9 pp over Reason-ModernColBERT.
  - Asymmetric 0.6B query against a 9B index: +1.6 pp over 0.6B→0.6B.
- **Monday takeaway:** Look at asymmetric serving: an expensive document encoder offline, and a cheap query encoder online in the same space. This cuts query-time latency without re-indexing.
- **Limitations:** The main benchmark is internal and its tasks are not disclosed. Storage cost is not quantified. The weight license is not stated in the paper (HF collection perplexity-ai/pplx-embed-v2). No limitations section.
- **Slide idea:** A big "18B teacher" box distills two arrows into 9B and 0.6B boxes. All three map into the same 2-D embedding cloud. Then a document goes in via 9B and a query comes in via 0.6B, and they meet in the same space.

## 10. UIBK-Embedding: Effective Text Retrieval by Unifying Dense and Late-Interaction Retrieval
- **arXiv:** 2610.27195. **Submitted:** 19 Oct 2026.
- **Authors:** Abdelrahman Abdallah, Mohammed Ali, Adam Jatowt (Univ. of Innsbruck).
- **Problem:** A dense index plus a ColBERT index means two indexes and two pipelines.
- **Method (diagram):**
  - A ModernBERT-base trunk (18 shared layers) splits into two 4-layer heads.
  - The token head gives 128-dimensional vectors. The dense head uses latent-attention pooling and splits its vector into 3 "slot" vectors.
  - A tag coordinate (+ for tokens, − for slots) means tokens only match tokens and slots only match slots. So a plain MaxSim equals the token score plus 0.75 × the dense cosine.
  - The result runs in an unmodified PLAID index. The model is distilled from the mxbai-rerank-large-v2 cross-encoder.
- **Key results:**
  - BEIR nDCG@10: 59.79, against LateOn 57.22 (+2.57). It leads on all 15 datasets.
  - Decontaminated BEIR: 61.55 against 60.36. LIMIT-small R@2: 91.4 against 83.5 (GTE-ModernColBERT).
  - Cost on FiQA: index 580 MiB, against 574 MiB for LateOn and 743 MiB for the two-index hybrid. Search 7.8 ms per query, against 4.4 ms for LateOn.
- **Monday takeaway:** If you run dense + ColBERT side by side, one model can give you the fused score in one index. 179M parameters. Weights: huggingface.co/DataScience-UIBK/uibk-embedding-v1 [UNVERIFIED license, check the model card]. Code: github.com/DataScienceUIBK/uibk-embedding
- **Limitations:** English only. Fine-tuned on training splits of 5 BEIR sets, so it is partly in-domain. Search is slower than LateOn.
- **Slide idea:** Animation of the "tag trick": token vectors (blue, +) and slot vectors (orange, −). MaxSim arrows only connect within the same color, then the two scores add into one number.

## 11. FLINT: Fixed-budget Late Interaction
- **arXiv:** 2610.27273 (cs.IR). **Submitted:** 19 Oct 2026.
- **Authors:** Himank Handa (UIUC), Negar Arabzadeh, Matei Zaharia (UC Berkeley).
- **Problem:** ColBERT stores one vector per token. Index size and query cost grow with length. ConstBERT pools only documents, so long queries stay slow.
- **Method (diagram):** V learned latent vectors cross-attend over the token outputs (Perceiver-resampler style), followed by a feed-forward refinement. This happens on both the query and the document side, so each always gets exactly V vectors (16, 32 or 64) of 128 dimensions. Scoring is MaxSim over V×V pairs. Served with PLAID 2-bit residual compression. Code: github.com/hmk55555/FLINT. Weights: HF collection himankhanda/flint.
- **Key results:**
  - BEIR nDCG@10 (ModernBERT-large, V=32): FLINT 0.530, ColBERTv2 0.534, ConstBERT 0.518.
  - BEIR nDCG@10 (BERT): FLINT 0.452, ColBERTv2 0.502. A clear loss on the BERT backbone.
  - MS MARCO MRR@10 (ModernBERT, V=64): 0.405, against 0.366 for ColBERTv2.
  - End-to-end 1.5–2.8× faster than ConstBERT on long-query corpora. Index 5.3–9.3× smaller than ColBERTv2.
- **Monday takeaway:** For agentic or long queries (tool-generated queries are long), a fixed-budget multi-vector model keeps latency flat. It also gives predictable storage (V × 128 × bytes per document).
- **Limitations:** Trained on short MS MARCO queries only, so long-query results are zero-shot. Query and document budgets are tied. Absolute scores on complex-query sets are low.
- **Slide idea:** A ColBERT document shows 300 token dots, and its index bar is tall. FLINT shrinks it to 32 dots and the bar drops 6–9×. A query-length slider moves: ConstBERT latency rises, FLINT stays flat.

## 12. Simple Linear Corrections for Compression in Late Interaction
- **arXiv:** 2610.14196 (cs.IR). **Submitted:** 9 Oct 2026.
- **Authors:** Mihir Agarwal, Sabyasachi Basu, Viraj Agrawal (Microsoft Research India).
- **Problem:** Training-free multi-vector compression (pooling, pruning) loses quality at small vector budgets.
- **Method (diagram):** Keep the encoder and compressor frozen. Compressors tested: Ward clustering, k-means, farthest-point sampling, EigenLI.
  1. Learn one d×d matrix A (16,384 parameters at d=128), initialized to the identity.
  2. The score becomes qᵀ(AᵀA)c.
  3. Train A by distilling the uncompressed MaxSim softmax over candidate panels, on about 5k queries (Adam, learning rate 1e-3, 5 epochs).
  4. Apply A once, offline, to the stored vectors, so there is no per-query cost.
- **Key results:**
  - Improves in-domain BEIR in 154 of 160 settings. Median +10.2% Recall@10 for ColBERTv2, +8.6% for Jina v4.
  - MS MARCO with k=4 vectors: up to +21.8% (ColBERTv2) and +31.9% (Jina v4) Recall@10. ViDoRe v3: +1.0–10.2%.
  - Transfer from MS MARCO to BEIR is weaker: 49/80 settings for ColBERTv2, 70/80 for Jina v4.
- **Monday takeaway:** If you pool ColPali or ColBERT vectors to save storage, fit one 128×128 matrix on in-domain queries (synthetic ones work) and apply it to the stored vectors. Almost free.
- **Limitations:** It does not recover discarded information. It beats the uncompressed model in only 9 of 160 settings. No significance tests. No code link.
- **Slide idea:** Compressed vectors drift away from their originals (ghost arrows). A matrix "lens" A slides over them and the score bars snap back toward the uncompressed values.

## 13. StrucChunk: Structure-Aware Retrieval for Legal Document RAG
- **arXiv:** 2610.26313 (cs.AI). **Submitted:** 19 Oct 2026.
- **Authors:** Surya Deep Singh, Ashutosh Tripathi, Gaurav Deep Singh (independent researchers).
- **Method (diagram):**
  1. Parse PDFs (pdfplumber) into a Part → Chapter → Section → Subsection graph.
  2. Keep a section whole up to 1.5× the limit (max 512 tokens). Split larger ones at paragraph and sentence boundaries.
  3. Prepend a breadcrumb such as `[CrPC 1973 > Chapter XII > Section 167]`.
  4. Append up to 3 summaries of cross-referenced provisions (200 characters each), found by regex.
  5. Retrieve with BGE-M3 (FAISS) + BM25 (bm25s), fused by RRF k=60. No reranker.
- **Key results:**
  - Boundary precision 100% against 7.7% for recursive splitting.
  - LegalBench-RAG Char-Recall@8: 48.18% against 23.59%.
  - CrPC: R@5 0.557→0.804, R@1 0.214→0.627.
  - Thai NitiBench HR@5: 0.856 against 0.594 for naive chunking, but 0.861 for the existing hierarchy-aware baseline.
  - Chunking gave 88% (CrPC) and 73% (CPC) of the gain. On GDPR, hybrid hurt (−0.040), and dense-only was best (R@5 0.908).
- **Monday takeaway:** For structured legal or regulatory text, the chunker matters more than the retriever. Build a section tree with a breadcrumb. Note again (as in #1) that hybrid can hurt.
- **Limitations / inconsistencies:** Queries were AI-assisted with a single annotator, and the agreement figure in the paper is left as "X/100". Query totals do not reconcile (5,256 against about 6,009). Retrieval only. Code: github.com/SinghSuryaDeep/legal-rag-strucchunk-1
- **Slide idea:** A statute page is sliced by a fixed-window "saw" that cuts through a section. Then by StrucChunk, which follows the section borders, with breadcrumb tags flying onto each chunk.

## 14. RAG Deserves an Index: Why Ingest-Time Compilation Beats Query-Time Interpretation
- **arXiv:** 2608.20845 (cs.AI). **Submitted:** 21 Aug 2026.
- **Authors:** Kyle Wild (Endgame Labs; Musashino University), Yusuke Takahashi, Asako Uraki (Musashino University; AIx).
- **Method (diagram):** "Ingest-time semantic compilation" builds two layers:
  - Geometric: embeddings, updated incrementally.
  - Symbolic: atomic claims, each with attribution and a supporting quote. A validation gate drops any claim whose quote is not found byte-exactly in the source.

  Stored in PostgreSQL. At query time the reader gets claim + span + attribution, not raw chunks.
- **Key results:**
  - 500 interview transcripts, 499 questions: compiled claims gave 85.2% at about 2.2k reader tokens. The best chunking gave 72.5% at about 16.3k.
  - A contextualized-chunk stack (hybrid + RRF + cross-encoder) gave 88.0% at about 47.7k tokens. That is not significantly different (McNemar p=0.202), at about 21× the tokens.
  - Ingest cost: about $0.064 per document. Break-even at about 580 reads. Incremental updates were 33.7× cheaper than full re-decomposition (synthetic pilot).
- **Monday takeaway:** For high-read corpora, extract quote-verified claims at ingest and retrieve claims, not chunks. The quote-must-match gate is a cheap guard against hallucinated extraction.
- **Limitations:** One corpus type. The same model (Kimi K2.6) did extraction and grading. The advantage did not clearly hold when an agent did the retrieval.
- **Slide idea:** A transcript flows through a "compiler" box that emits claim cards, each with a highlighted source quote. Cards without a matching quote fall into a bin. A token meter at query time: 16.3k → 2.2k.

## 15. PRIME: Pre-Retrieval Index Modeling & Enhancement for Structured Document Retrieval
- **arXiv:** 2610.13296 (cs.IR). **Submitted:** 9 Oct 2026.
- **Authors:** Cheuk Hei Chung, Li Liu (HKUST Guangzhou).
- **Method (diagram):** Improve the corpus before indexing, without changing the retriever. Two tracks:
  - Deterministic: Metadata Synthesis (top 5 terms by TF-IDF, with positional decay and a heading bonus, plus an H2 heading tree). Then hierarchical retrieval: BM25 + BGE-small over metadata, fused by RRF, gives 30 documents. A MiniLM cross-encoder scores their H2 sections and keeps 5.
  - LLM: Semantic Restructuring rewrites each section in a compressed form.
- **Key results:**
  - Metadata matches structure-aware chunking on QASPER (overlapping CIs) with 45.8× less embedding compute and 22.4× fewer vectors.
  - Full deployment: +13.7% Answer-F1 (0.0842→0.0957).
  - But: on NFCorpus (no headings), metadata is 19.5% worse. Restructured text under a strong reranker is worse than raw chunks (0.325 against 0.391). Only 63.2% of gold evidence survives the rewrite.
- **Monday takeaway:** For long structured documents, a cheap document-level metadata index is a good first stage. Do not let an LLM rewrite your source text for indexing: about a third of the evidence was lost.
- **Slide idea:** Embedding-compute meter drains 45.8× slower. Then a red warning card: "LLM rewrite kept 63% of evidence".

## 16. Multimodal Reranking Is a System One Decision
- **arXiv:** 2610.28435 (cs.IR). **Submitted:** 20 Oct 2026.
- **Authors:** Zhuchenyang Liu, Yao Zhang, Yu Xiao.
- **Method (diagram):**
  1. The first stage (Qwen3-VL-Embedding-2B) returns the top 16.
  2. Put all 16 into one prompt, labeled A–P, and ask which one best matches the query.
  3. Take the next-token logits for the 16 label tokens and softmax them into a ranking. One forward pass, no decoding.
  4. Compared with a yes/no readout per candidate. The tuned variant, "JEV-27B-VL", adds a LoRA trained on text decisions only.
- **Key results:**
  - MMEB-V2 visual documents: zero-shot "Qwen3.8-27B" scores 84.79 nDCG@5, against 84.78 for the dedicated Qwen3-VL-Reranker-8B.
  - Image hit@1: the choice readout scores 76.76, the yes/no readout 69.50.
  - ViDoRe V3: 60.94 against 61.98 (Reranker-8B).
  - Latency: 3.97 s against 3.67 s, or about 1.5× once the reranker is batched.
  - Small Gemma-4 models (E2B, E4B) made results worse.
- **Monday takeaway:** If you already serve a large VLM, a listwise "pick one of A–P" logit readout can replace a separate visual reranker. Use the label-token logits, not generated text. Watch for position bias (order sensitivity).
- **Limitations:** The 27B zero-shot model is a newer and bigger generation than the rerankers it is compared with. At most 16 candidates. The ranking depends on candidate order.
- **Slide idea:** 16 page thumbnails labeled A–P feed into the VLM. A bar chart of logits over A–P grows and the thumbnails re-sort by height.

## 17. Cascaded Retrieval with Cross-Modal Query Refinement for Efficient Visual Document Search (SCOUT)
- **arXiv:** 2610.20367 (cs.CL). **Submitted:** 14 Oct 2026.
- **Authors:** Diana Turmakhan, Aseem Srivastava, Vivek Gupta, Iryna Gurevych, Thamar Solorio (MBZUAI, ASU, UKP Lab).
- **Method (diagram):**
  - Visual track: one vector per page (light VLM) gives the top K=25. Then ColEmbed-3B-v2 multi-vector MaxSim reranks those 25.
  - Semantic track: Gemini 2.5 Flash writes document and page summaries offline, embedded with Qwen3-Embedding, top T=20.
  - Cross-modal query refinement: scores from both tracks adjust the visual query vector before the final rescoring.
- **Key results:**
  - Latency 468 ms against 13,464 ms for full ColEmbed-3B-v2 (28.8× on average, up to 80.7×).
  - ViDoRe v3 NDCG@10: 61.31 against 58.99.
  - Active index 0.63 GB against 213.1 GB (104–337× smaller).
  - Without the reranker: −20.9%. Replacing the query refinement with RRF: −6.28%.
- **Monday takeaway:** Do not run ColPali-style MaxSim over the whole corpus. Use single-vector recall over all pages, then multi-vector rerank of the top 10–50. K=10 was already near the peak.
- **Slide idea:** A funnel animation: 1M pages → single-vector → 25 → MaxSim → 5. Latency counter: 13.4 s → 0.47 s.

## 18. EVIE: Evidence-Vector-Informed Embeddings for Visual Document Retrieval
- **arXiv:** 2610.11553. **Submitted:** 8 Oct 2026.
- **Authors:** Zifei Wang et al. (Tencent IMA Product Center; Tencent Youtu Lab).
- **Method (diagram):**
  1. A VLM judge (GLM-5V-Turbo) labels mined pages as full, partial or no evidence. Partial pages are removed from the negatives.
  2. An 8B teacher distills into a 4.5B student with Prefix-MRL: nested widths from 64 to 2048 dimensions.
  3. Hierarchical agglomerative compression clusters page tokens by meaning and grid position into K centroids, scored with single-stage MaxSim.
- **Key results (ViDoRe V3 nDCG@10):**
  - EVIE-8B: 66.75, against 65.32 for webAI-ColVec1.1-8b.
  - Compressed, d=64, K=64: 62.06 at 7.63 GiB per million pages. WeMM-9B (single-vector) scores 57.42 at the same 7.63 GiB.
  - Compressed, K=32: 59.58 at 3.81 GiB per million pages. Uncompressed multi-vector at 1024 tokens × 256 dims BF16 needs about 488 GiB.
- **Monday takeaway:** (1) When you mine hard negatives, drop "partially relevant" pages from the negatives. Do not train against them. (2) To budget visual-RAG storage, cluster patch vectors to 32–64 per page.
- **Limitations:** Labels depend on the judge (80.67% human agreement on partial pages). Changing the width requires re-clustering. The release status of the final weights is unclear (tencent/EVIE-Preview-4.5B is public).
- **Slide idea:** A page grid of 1024 patch dots merges into 32 colored clusters. A storage bar shrinks from 488 GiB to 3.8 GiB.

## 19. UNREAL: Unifying Retrieval and Long-Context with a Single Model
- **arXiv:** 2610.08463 (cs.CL). **Submitted:** 6 Oct 2026.
- **Authors:** Edan Kinderman, Elad Hoffer, Yochai Blau, Brian Chmiel, Ron Banner, Daniel Soudry, Boris Ginsburg (NVIDIA; Soudry also Technion).
- **Problem:** RAG and long-context are usually framed as competitors. Can one frozen LLM do both kinds of evidence selection?
- **Method (diagram):**
  1. Encode each chunk with the frozen LLM, take intermediate-layer token states, and mean-pool them to 7 vectors.
  2. Append 64 learned "retrieval tokens" (pooled to 4 groups) to the query. Add the top-5 BM25 chunks as initial context, and mix layers with learned weights.
  3. Score with MaxSim. Under 500K trainable parameters.
  4. The same selector treats a long prompt as a set of chunks and drops distractors before generation.
- **Key results:**
  - 21M-chunk Wikipedia index, complete-evidence R@10: HotpotQA 49.1→73.2%, 2Wiki 31.7→60.1%, MuSiQue 8.8→14.4%.
  - HotpotQA EM: 52.6 against 43.3 for LateOn + reranker.
  - NoLiMa at 128K: 1.0→24.83%. LV-Eval at 256K: F1 49.97→54.66.
  - Fewer FLOPs than full-context inference above about 18–32K tokens.
- **Monday takeaway:** The "long context or RAG?" question has a third answer: retrieval inside the long context. If you stuff more than about 32K tokens, add an evidence-selection pass that drops distractors. Measure complete-evidence recall (see #6).
- **Limitations:** Trained on Wikipedia QA only. Sparse-evidence tasks only. Multi-vector storage. Depends on a BM25 seed. No code link.
- **Slide idea:** One LLM box with two input doors: "21M-chunk corpus" and "128K prompt". The same retrieval-token probe lights up the evidence chunks in both, and the distractors fade.

## 20. RaBitQ-SSD: Split Codes and Pipelined I/O for SSD-Resident Vector Search
- **arXiv:** 2610.02652 (cs.DB). **Submitted:** 2 Oct 2026.
- **Authors:** Yuexuan Xu (NTU Singapore), Jianyang Gao (ETH Zurich), Michael Norris, …, Matthijs Douze (Meta), Cheng Long (NTU).
- **Method (diagram):** An IVF index with RaBitQ codes.
  - Split-RaBitQ: the first Dm bits of each code plus 3 factors stay in DRAM. The other bits and the re-ranking factors go to SSD.
  - The prefix gives an unbiased distance estimate with error O(1/√Dm). Candidates are ordered by lower bound and grouped into SSD pages.
  - Asynchronous reads run under an in-flight budget. Each page is re-checked against the current threshold before it is read, with an α-quantile drain at the end.
- **Key results:**
  - Up to 1.74× the throughput of graph baselines at 90% recall, and up to 3.8× fewer SSD page reads.
  - On-SSD index up to 7.0× smaller and 10× faster to build than DiskANN.
  - 10B vectors at about 3,210 QPS (90% recall) on one server with one SSD, about 545 GB resident index.
  - DRAM per point: Dm/8 + 12 bytes (108 bytes at 768 dimensions).
- **Monday takeaway:** If your vectors exceed RAM, IVF + RaBitQ with SSD tiering is now an alternative to DiskANN. Lower build cost, simple memory math. Graph indexes still win at 0.98 recall on most datasets. Code: github.com/VectorDB-NTU/RaBitQ-SSD
- **Slide idea:** A DRAM box holds short code prefixes and an SSD box holds the remainders. A query sweeps, candidates sort by lower bound, and only a few SSD pages light up and get fetched.

---

## Brief entries (relevant, lower immediate impact or narrower)

- **2609.35831: Beyond the Context Window: An Adaptive Entropy-Based Routing Framework for Hybrid Retrieval and Long-Context LMs (EDAR).** 23 Sep 2026. Olufadewa et al. (Univ. of Ibadan / ALPHA Centre).
  - Method: answer with RAG first. If the mean token entropy of the first 30 output tokens is above τ=1.2, throw that answer away and send the query to long context.
  - Results: 97.4% of long-context accuracy, 18.2% of queries escalated, 70.7% fewer tokens, latency 9.8 s against 48.5 s. Entropy correlates with hallucination at r=0.85.
  - Takeaway: a cheap logprob-based escalation gate.
  - Caveat: needs logprobs. Some infrastructure details read oddly, such as "PagedAttention v3" on H200. Treat it as a pattern, not a proven result. [UNVERIFIED: reproducibility; no code]
- **2610.30697: Lychee: Certified Screening of Inverted Lists for High-Recall Vector Search.** 22 Oct 2026. Dongfang Zhao (UW Tacoma).
  - Method: GPU IVF. Take exact distances to anchors (every 16th vector) as an upper bound. Use a tensor-core lower bound to skip vectors that cannot be in the top k.
  - Results: 9.7–117× faster than cuVS IVF-Flat at equal recall, 44.5× on BIGANN-1B at 0.9999 recall.
  - Use for: fraud, watchlist, or medical search where a miss is expensive. CAGRA is faster at recall ≤0.995. No code link.
- **2610.30425: Getting a GRIP on Graph-Based Search for Learned Sparse Retrieval.** 21 Oct 2026. Vihan Lakshman (MIT), Nardini (ISTI-CNR), Rulli (Linkup), Venturini (Pisa).
  - Method: a graph index for SPLADE vectors. Seed entry points from high-impact query terms, route over 8-bit top-R sketches, and build with sparse PiPNN.
  - Results: 2.5× lower latency than Seismic on MS MARCO v2 (138M) at 95% R@10. But the index is about 2× larger (140 GB against 73 GB) and the build is about 10× slower.
- **2610.21464: Poisoning the Neighborhood: A Topology-Aware Topic-Level Attack on Large-Scale HNSW-based RAG Systems.** 15 Oct 2026. Yufei Chen et al. (Xidian Univ.).
  - Point: earlier attacks assume exact kNN. On a 2M-document HNSW index, PoisonedRAG reaches only 0.4% retrieval success.
  - Method: a hub–satellite cluster of 40–60 injected documents.
  - Results: 72–74% retrieval success, 29–31% attack success.
  - Defenses: hubness detection flagged 0%. A reranker cut attack success by only 2.8–4.8 points.
  - Takeaway: ANN is not a defense. Control write access to the corpus and keep provenance.
- **2609.29652: SmallReason-ColBERT: An Ultra-Small Late-Interaction Retriever for Reasoning Intensive Retrieval.** 29 Aug 2026. Abdallah, Ali, Jatowt (Innsbruck). EMNLP 2026.
  - A 32M-parameter ColBERT with a learned per-query-token importance head.
  - BRIGHT nDCG@10 21.41, against 22.62 for the 150M Reason-ModernColBERT.
  - A good fit for on-device or edge reasoning retrieval. Code: github.com/DataScienceUIBK/SmallReason-ColBERT

Also seen, not detailed (check before use):
- 2610.24478: hard-negative reranker training for legal search.
- 2610.15642 (MemPursuit): reranking 32.9× faster than BGE-v2-m3.
- 2609.16175 (BOA): filtered ANN on GPU, 7–12.5× throughput.
- 2609.15058 (LSSG): label-filtered ANN.
- 2610.17627 (AiSAQ filtering): DRAM-free filtered search.
- 2609.37225 (ResComEmb): beats ColQwen2.5 with 37.5% of its visual tokens.
- 2609.32699 (RandSlot): compact visual-document vectors.
- 2610.05099 (ColGREP): semantic code search for small agents, 44.1% lower CPU latency.
- 2610.30755: naive RAG beats agentic memory in 6 of 7 settings (memory topic).
- 2609.03654: contextual chunk enrichment on bank financial statements, NDCG@10 0.322→0.710.

---

## Cross-paper trends (for a "what changed in 2026 H2" slide)

1. **"Measure per query, per corpus" replaces "always hybrid, always rerank".** Four independent studies (#1 Fusion Tax, #2 WRRF intervals, #3 LASAGNA, #13 StrucChunk on GDPR) show that a popular component helps on average and hurts many queries or whole corpora. Static per-corpus policies beat learned per-query routers (#1). Gains from separate components do not add up (+47% predicted, +17% measured). Lecture message: build a 200–400 query labeled set first. Every other choice depends on it.
2. **Structure beats LLM contextualization for chunking.** #4 (placebo-controlled), #13, #15 and #6 agree: cut at real headings, prepend a heading or breadcrumb path, and keep document identity in the chunk. LLM per-chunk context was worse than structure in #4, and statistically equal to compiled claims at 21× the tokens in #14. LLM rewriting of source text loses evidence (#15: 63% kept). Update cost matters too (#5): boundary-stable chunkers re-embed 13–20 points less.
3. **Late interaction becomes cheap enough to be the default.** Fixed budgets (#11 FLINT, V=32), centroid compression (#18 EVIE, 32 centroids per page; #12 linear correction), unified dense + multi-vector in one index (#10), asymmetric large/small encoders in one space (#9), and cascades (single-vector recall → MaxSim rerank, #17). The quality evidence (#7: Hit@3 93% against 46%) makes multi-vector the first upgrade to try.
4. **The reranker is becoming "any big model + a choice question".** A listwise A–P logit readout from a general VLM matches an 8B dedicated reranker (#16). LLM reranking after rewriting is the best single-vector pipeline (#7). But reranking does not fix fusion errors on every corpus (#1) and barely stops poisoning (2610.21464).
5. **Long context and RAG are converging.** Retrieval inside the long prompt (#19 UNREAL), entropy-gated escalation from RAG to long context (EDAR), and the finding that retrieval, not reading, is the bottleneck (#6: all-evidence recall 19%). Practical rule: track complete-evidence recall, and add evidence selection once the context goes above about 32K tokens.
6. **The ANN index layer is moving to SSD, GPU and certified high recall.** RaBitQ-SSD (10B vectors on one box), Lychee (certified 0.9999 recall on GPU), GRIP (graph search for SPLADE), and filtered-ANN work (BOA, LSSG, AiSAQ). For most RAG teams, the practical change is filtered search and SSD tiering, not a new algorithm.

## Verification notes / open items

- [UNVERIFIED] Exact numbers came through a summarizing fetch tool. Check each number against the paper's tables before the slide goes out.
- [UNVERIFIED] Configuration counts in LASAGNA (2610.29722) do not reconcile: 450 against 167+138. The smallest corpus is given as 5K or 55K.
- [UNVERIFIED] The StrucChunk (2610.26313) query totals do not reconcile, and its annotator agreement figure is left blank.
- [UNVERIFIED] EDAR (2609.35831): no code, and infrastructure descriptions that look unusual.
- [UNVERIFIED] Weight licenses: pplx-embed-v2-late (not stated in the paper), UIBK-Embedding (check the HF card), and EVIE final weights (release unclear).
- 2610.28435: the authors' affiliations were not extracted.
