# Industry practice: production RAG and enterprise search (2025 to Oct 2026)

Research date: 2026-10-23. Scope: real production case studies, engineering-blog practice, vendor guidance dated 2026, and arXiv industry papers from the last 3 months (2026-07-23 to 2026-10-23).

Rules used here:
- Every number has a source URL. "Fetched" means I read the primary page on 2026-10-23.
- "[SNIPPET]" means the primary page blocked fetching (HTTP 403) and the figure comes from a search-engine summary of that page. Verify before you put it on a slide.
- "[UNVERIFIED]" means I could not confirm it at all.
- "[VENDOR]" means a company measured its own product. Present it as a claim, not as an independent result.
- This file does not repeat `research-rag/` (Anthropic Contextual Retrieval numbers, LinkedIn KG customer-service paper 2404.17723, Anthropic multi-agent research, Gemini File Search launch pricing). It only references them.

---

## 0. The ten-second version (for the opening industry slide)

1. **Index first, federate second.** Dropbox measured simple MCP/federated agent queries at up to 45 s, against seconds for the raw index. Glean and Dropbox both build one permission-aware index plus a people/content graph.
2. **One retrieval "super tool", not ten.** Dropbox cut 5-10 retrieval tools to 1. Anthropic's Tool Search cut tool-definition tokens by 85% and raised Opus 4 MCP accuracy from 49% to 74%.
3. **Hybrid BM25 + dense + a reranker is the default.** Uber, Dropbox, Perplexity, Glean, Harvey and DoorDash all run it.
4. **Small specialised retrieval models are replacing frontier LLMs in the retrieval loop.** Examples: Databricks Instructed-Retriever (5.8 s, more than 2x faster than Sonnet 5 / GPT-5.6 Luna), Glean Waldo (about 250 ms against about 3 s), and Cursor's and GitHub's custom embedders.
5. **Route by difficulty.** Only rewrite, expand or "go agentic" when a cheap signal says the first pass is weak. Snap gates about 10% of users and saves 90% of LLM cost. A score-gated rewrite router captures half the gain on fewer than 40% of queries.
6. **Incremental re-embedding is the biggest cost lever at scale.** Notion hashes spans and saw 70% less data volume. Notion moved to serverless and turbopuffer for 60% lower search spend, and expects 90%+ lower embedding-infrastructure cost from Ray.
7. **The LLM judge is a product.** Teams calibrate it against humans: Shopify raised Cohen's kappa from 0.02 to 0.61 against a human ceiling of 0.69, and Dropbox cut judge disagreement from 8% through prompt changes, o3, RAG-as-judge and DSPy. DoorDash found human labels wrong in more than half of the audited cases.
8. **Evals leak.** Claude Opus 4.6 decrypted the BrowseComp answer key in 2 of 1,266 problems. Filter search results by benchmark name, not by URL.

---

## 1. Case studies (24)

Summary table (details follow):

| # | Company / product | Date | Key result | Status |
|---|---|---|---|---|
| 1 | Notion: Q&A vector search | 2026-02-19 | 10x scale, about 90% cost reduction, p50 70-100 ms to 50-70 ms | Fetched |
| 2 | Dropbox Dash: context engine | 2026-01-28 | Index beats federated (45 s vs seconds); 5-10 tools to 1; judge disagreement from 8% down | Fetched |
| 3 | Dropbox Dash: context engineering | 2025-11-17 | One universal-search tool, KG filtering, search sub-agent | Fetched |
| 4 | Dropbox Dash: RAG + agents | 2025-04-24 | 95%+ of queries under 1-2 s retrieval target | Fetched |
| 5 | Perplexity Search API | 2025-09-25 | 200M queries/day, 200B+ URLs, p50 358 ms | Fetched [VENDOR] |
| 6 | Cursor: semantic search for agent | 2025-11-06 | +12.5% QA accuracy; +2.6% code retention on 1,000+ file repos | Fetched |
| 7 | GitHub Copilot embedding model | 2025-09-24 | +37.6% retrieval quality, 2x throughput, 8x smaller index | Fetched |
| 8 | Uber Genie EAg-RAG | 2025-05-29 | +27% acceptable answers, -60% incorrect advice | Fetched |
| 9 | Uber Legal redlining agent | **2026-10-08** | >20% less contract review time, 91% decision accuracy | Fetched |
| 10 | LinkedIn Semantic Search (Jobs/People) | 2026-02-07 (arXiv) | 75x ranking throughput at fixed latency | Fetched abstract |
| 11 | Databricks Instructed-Retriever-1 | 2026-06-04 | 3x faster search, TTFT about 2 s, nDCG@10 81.0 vs Sonnet 4.5 80.1 | Fetched [VENDOR] |
| 12 | Databricks Adaptive Instructed-Retriever | **2026-09-09** | 5.8 s answers, >2x faster than frontier models | Fetched [VENDOR] |
| 13 | Databricks memory scaling (Genie) | 2026-04-10 | Accuracy 2.5% to >50% from filtered user logs | Fetched [VENDOR] |
| 14 | Glean Waldo agentic search model | 2026-04-28 | ~250 ms vs ~3 s per call; -50% latency, -25% tokens | Fetched [VENDOR] |
| 15 | Glean auto-routing vs Claude Cowork | **2026-08-26** | $0.58 vs $2.98 per task; 1.3M vs 4.4M tokens | Fetched [VENDOR] |
| 16 | Glean Jev zero-shot classifier | **2026-09-29** | Rerank $0.00044/query p50 0.195 s, but lower recall than prod | Fetched [VENDOR] |
| 17 | Glean enterprise search eval | 2026-02-12 | Preferred 1.9x vs ChatGPT, 1.6x vs Claude (correctness) | Fetched [VENDOR] |
| 18 | Atlassian Rovo on turbopuffer | 2026 (page) | p90 125 to 60 ms; recall@10 about 90% to 96%+; +19% Jira long-clicks | Fetched [VENDOR] |
| 19 | Harvey legal RAG | 2025-02-20 | LanceDB 15M rows <2 s P50; pgvector 500K <2 s P50 | Fetched |
| 20 | Shopify Sidekick | 2025-08-26 | Judge kappa 0.02 to 0.61 (human 0.69); syntax 93% to 99% | Fetched |
| 21 | DoorDash content embeddings | 2026-04-14 | gemini-embedding-001 @256d; null search -3.65%, CVR +0.66% | [SNIPPET] |
| 22 | DoorDash LLM-as-judge for NL search | 2026-05-14 | Human labels wrong in >50% of 6,824 audited judgments | [SNIPPET] |
| 23 | Snap SMART (DPA retrieval) | **2026-07-25** (arXiv) | LLM path for about 10% of users; -90% LLM cost; +27.6% CVR | Fetched abstract |
| 24 | Beam (Phaser Studio) on Gemini File Search | 2025-11-06 | Parallel queries across corpora under 2 s | Fetched [VENDOR] |

Bold dates fall inside the 3-month window.

### 1. Notion: "Two years of vector search at Notion: 10x scale, 1/10th cost"
- **Date:** 2026-02-19 (Gondi, Liu, Louie, Lund, Sager). URL: https://www.notion.com/blog/two-years-of-vector-search-at-notion
- **Architecture, in steps:**
  1. Nov 2023 launch: two ingestion paths. An offline Apache Spark batch path bulk-loads existing pages, and an online Kafka path handles live edits. The vector DB is a sharded "pod" cluster partitioned by workspace ID.
  2. Dec 2023: when an index nears capacity, Notion provisions a new **"generation"** and routes new workspaces there instead of re-sharding.
  3. May 2024: move to serverless (storage decoupled from compute, usage-based billing): **50% cost reduction** from peak.
  4. May 2024 to Jan 2025: migration to **turbopuffer**, with a full re-index, an embedding-model upgrade and namespace-per-index design, cut over generation by generation.
  5. Jul 2025, "Page State" project: an **xxHash64 per span** for text and for metadata, stored in DynamoDB. Only changed spans are re-embedded. A metadata-only change becomes a PATCH, not a re-embed.
  6. Jul 2025 to now: indexing moved from Spark to **Ray on Anyscale** (removes "double compute"). Ray Serve self-hosts the query embedding model.
- **Scale:** daily onboarding capacity 600x, active workspaces 15x, vector DB capacity 8x. The turbopuffer customer page lists 10B+ documents, 10M+ namespaces and 1 GB/s write peaks (https://turbopuffer.com/customers).
- **Cost and latency:** turbopuffer gave **60% lower search-engine spend** and 35% lower EMR compute. **p50 went from 70-100 ms to 50-70 ms.** Page State gave a **70% reduction in data volume**. Ray gave a "90+ percent reduction" in embedding infrastructure cost, still rolling out.
- **Learned:** usage-based pricing beats over-provisioning when growth is unpredictable. Generations avoid stop-the-world re-shards. Hash content and metadata separately. Self-hosting the query embedder removes a network hop from the query path. Use a migration as the moment to re-index and upgrade the embedder.

### 2. Dropbox Dash: the context engine (Josh Clemm talk write-up)
- **Date:** 2026-01-28. URL: https://dropbox.tech/machine-learning/vp-josh-clemm-knowledge-graphs-mcp-and-dspy-dash
- **Architecture:**
  1. Custom connectors crawl third-party apps and handle rate limits, API quirks and ACLs.
  2. Content understanding: normalise to markdown, extract titles, metadata and links, then embed. Images, PDFs, audio and video have their own processors. Video uses multimodal scene analysis.
  3. Knowledge graph across apps (meeting to attendees to docs to transcripts, with canonical person IDs). It is packaged as **"knowledge bundles"** that go through the normal index pipeline. **No graph DB at query time.**
  4. Hybrid store: a **BM25 lexical index plus a dense vector store**.
  5. Multi-pass ranking for personalisation and ACL enforcement.
  6. One **"super tool"** replaces 5-10 retrieval tools. Tool results are stored outside the LLM context. A classifier routes complex queries to narrow sub-agents.
- **Numbers:** Dash context cap about 100K tokens. A simple MCP-based agent query takes **up to 45 s**, against "within seconds" for the raw index. LLM-judge disagreement with humans started at **8%** and fell through prompt refinement (asking for explanations), then an upgrade to OpenAI o3, then **"RAG as a judge"** (the judge fetches missing context such as acronyms), then DSPy. The stack has 30+ prompts, with 5-15 engineers editing them at once. Ranking metric: NDCG, with judge relevance on a 1-5 scale.
- **Learned:** index-based retrieval beats federated retrieval at scale. Graph DBs failed on latency, so bundles are built asynchronously. MCP tool sprawl hurts quality and speed. Invest heavily in the judge. DSPy-style prompt optimisers help when many engineers edit prompts. Quote: "In the world of chat, you're still retrieving results, but it's not for the human."

### 3. Dropbox Dash: "How Dash uses context engineering for smarter AI"
- **Date:** 2025-11-17. URL: https://dropbox.tech/machine-learning/how-dash-uses-context-engineering-for-smarter-ai
- **Steps:** Dash started as classic RAG (semantic plus keyword). As usage became agentic, retrieval tools for Confluence, Google Docs and Jira became **one tool over the universal index**. The KG ranks results per user and query. Search moved into a **specialised search agent** with its own prompt. The Dash MCP server exposes **one tool**.
- **Numbers:** none.
- **Learned:** "The problem wasn't broken tools; it was too many good ones." Tool definitions eat context. Relevance beats volume.

### 4. Dropbox Dash: "Building Dash: RAG and multi-step AI agents"
- **Date:** 2025-04-24. URL: https://dropbox.tech/machine-learning/building-dash-rag-multi-step-ai-agents-business-users
- **Steps:** lexical retrieval, then **on-the-fly chunking at query time**, then an embedding reranker, then LLM generation. For complex tasks an LLM writes a **plan in a Python-like DSL**. Static analysis checks it, a second LLM call fills missing functions, and a minimal interpreter runs it with runtime type checks.
- **Numbers:** target of **95%+ of queries under 1-2 s** for retrieval. Evals ran on Natural Questions, MuSiQue and MS MARCO, with LLM judges for correctness and completeness plus source precision, recall and F1.
- **Learned:** larger models are more precise but slower than users accept. Code-shaped plans make failures traceable to a step. A minimal interpreter shrinks the attack surface.

### 5. Perplexity: "Architecting and evaluating an AI-first search API"
- **Date:** 2025-09-25. URL: https://www.perplexity.ai/hub/blog/architecting-and-evaluating-an-ai-first-search-api (the research.perplexity.ai URL redirects here). The serving engine is Vespa (https://vespa.ai/perplexity/).
- **Steps:** an ML model decides whether and when to index each URL. LLM-scored parsing rulesets improve in a self-improvement loop. Documents are split into **sub-document units**. Hybrid lexical and semantic retrieval ("comprehensiveness over precision"), then prefilters, then multi-stage ranking (lexical and embedding scorers, then **cross-encoders**) at document and sub-document level.
- **Scale:** **200M daily queries**, an index of **200B+ unique URLs** ("exabyte-scale"), tens of thousands of CPUs, hundreds of TB of RAM, tens of thousands of index operations per second.
- **Latency** (from AWS us-east-1): Perplexity p50 **358 ms** and p95 763 ms. Brave p50 513 ms. Exa p50 1,375 ms. Tavily p50 1,342 ms. [VENDOR]
- **Quality** (open-sourced `search_evals`): SimpleQA .930, FRAMES .453, BrowseComp .371, HLE .288, against Exa .781 / .399 / .265 / .242. [VENDOR]
- **Learned:** search APIs built for humans return whole documents that are too broad for context windows, so retrieve sub-document spans. Freshness and coverage compete for one indexing budget. Live product feedback is the best ranking training signal.

### 6. Cursor: "Improving agent with semantic search"
- **Date:** 2025-11-06. URL: https://cursor.com/blog/semsearch
- **Steps:** a custom code embedding model plus indexing pipelines. The agent uses **semantic search and grep together**. Training data comes from **agent traces**: an LLM ranks which content would have helped at each step, and the embedder is trained to match those rankings.
- **Numbers:** offline (Cursor Context Bench) **+12.5% average QA accuracy** (6.5%-23.5% by model). Online A/B: +0.3% code retention overall and **+2.6% on codebases with 1,000+ files**. Without semantic search, dissatisfied follow-ups rose 2.2%.
- **Learned:** grep alone is not enough on large repos, and grep plus vectors beats either one. Train retrievers on how agents actually search. Re-evaluate tools as models change. Contrast this with `research-rag/05` ("Is grep all you need?", arXiv 2605.15184): both can be true depending on harness and repo size.

### 7. GitHub Copilot: new embedding model for VS Code
- **Date:** 2025-09-24. URL: https://github.blog/news-insights/product-news/copilot-new-embedding-model-vs-code/
- **Method:** contrastive training with InfoNCE plus Matryoshka Representation Learning. **Hard negatives** are code that looks right but isn't, mined from public GitHub and internal repos, with LLMs surfacing near-misses. Evaluation covers 4 tasks (NL to code, code to NL, code to code, problem to code).
- **Numbers:** **+37.6%** retrieval quality (average 0.362 to 0.498), **about 2x throughput**, **about 8x smaller index**. Code acceptance rose +110.7% for C# and +113.1% for Java.
- **Learned:** most failures are near-misses, so hard negatives give the biggest gain. One benchmark is not enough.

### 8. Uber Genie: Enhanced Agentic-RAG (EAg-RAG)
- **Date:** 2025-05-29. URL: https://www.uber.com/us/en/blog/enhanced-agentic-rag/
- **Offline steps:** a custom Google Docs loader (not PDF) extracts paragraphs, tables and the table of contents. An LLM converts tables and bullets to markdown. Table chunks are tagged so chunking never splits them. LLM-generated **summary, FAQs and keywords** are stored as metadata in an offline feature store.
- **Online steps:** a Query Optimizer rewrites and decomposes the query. A Source Identifier picks the likely policy docs (few-shot). **Vector plus BM25 over the enriched metadata**, merged. A Post-Processor dedupes and **reorders chunks by source position**. The answer LLM gets the query, the sub-queries and the context, and replies in Slack. Built on LangGraph inside Michelangelo.
- **Numbers:** **+27% relative acceptable answers, -60% relative incorrect advice.** Golden set of 100+ SME queries over 40+ policy docs. An LLM judge scores 0-5 with an explanation. Experiment turnaround went "from weeks to minutes". Latency not reported.
- **Learned:** PDF loaders destroyed table structure. HTML from Google Docs also carries ACL metadata. Manual SME evaluation was the bottleneck.

### 9. Uber Legal redlining agent (in window)
- **Date:** **2026-10-08**. URL: https://www.uber.com/us/en/blog/building-ubers-redlining-agent/
- **Steps:** a Word add-in (React/TS, Office JS API) talks to a Python **LangGraph** backend. Intent detection, risk assessment and policy lookup run in parallel. Then retrieval and rerank from **OpenSearch**, then adjudicate (accept, reject or modify), then tone, then deterministic rules.
- **Retrieval details:** contracts are chunked at `;`, `.` and newline. Lookups use the verbatim sentence. The embedder is **nomic-embed-text-v1.5**. The rules index is keyed on the target sentence, and the feedback index on counterparty intent. Similarity search plus metadata filters narrow to **about 20 candidates**, then a second LLM pass checks intent alignment.
- **Memory with time decay:** each past lawyer decision is weighted by **exp(-λ × age_days)** with a **365-day half-life**, and agree and disagree examples are kept balanced. Redis holds session state.
- **Numbers:** **>20% reduction in average review time, 91% decision accuracy** (method not described). Online LLM-judge metrics: `document_quality_metric` and `rule_adherence_metric`.
- **Learned:** one-shot "assume the draft is flawed" prompting beat multi-pass reflection on reliability, tokens and latency. Deterministic rules override the model on non-negotiables. Experts own the prompt content and engineers own its structure.

### 10. LinkedIn: "Semantic Search at LinkedIn" (AI Job Search, AI People Search)
- **Date:** arXiv 2602.07309, 2026-02-07 (74 authors). URL: https://arxiv.org/abs/2602.07309
- **Steps (abstract plus secondary summaries):** query understanding, then **GPU embedding-based retrieval** (secondary sources say exhaustive GPU kNN rather than ANN [UNVERIFIED in primary]), then a **small-LM cross-encoder ranker** trained by **multi-teacher distillation** for relevance and engagement, with an **LLM relevance judge** for evaluation.
- **Numbers:** a prefill-oriented serving design with pruning, context compression and text-embedding hybrid interactions gives **>75x ranking throughput at a fixed latency**, with NDCG near the teacher's.
- **Learned:** LLM ranking at LinkedIn scale is only viable after distillation and serving co-design.

### 11. Databricks: Instructed-Retriever-1 (parallel test-time scaling)
- **Date:** 2026-06-04. URL: https://www.databricks.com/blog/3x-faster-search-parallel-test-time-scaling-instructed-retriever-1
- **Steps:** parallel query plus filter generation, then merge candidates, then **multi-pivot groupwise reranking** (parallel groups anchored on pivot chunks). One small MoE model does both query generation and reranking. Serving uses FP8 (NVIDIA ModelOpt) and speculative decoding. User instructions and the **index schema** go to every stage.
- **Numbers:** search time down **>3x**, answer time down 2x, **TTFT about 2 s**, end-to-end under 10 s offline. Internal rerank nDCG@10 **81.0 vs Claude Sonnet 4.5 at 80.1** (+14.1% vs +12.8% over no rerank). FP8 vs BF16: +0.33 points, not significant (95% CI [-2.99, 3.65]). Speculative decoding gave >30% speedup.
- **Learned:** more query formulations raise recall, and more pivots raise precision (two pivots beat one). Spending test-time compute in parallel avoids sequential-loop latency.

### 12. Databricks: Adaptive Instructed-Retriever (in window)
- **Date:** **2026-09-09**. URL: https://www.databricks.com/blog/adaptive-instructed-retriever-frontier-quality-search-2x-lower-latency
- **Steps:** multi-step search with a fixed step cap. The model decides when it has enough evidence. Trained with online RL (CISPO), with a reward that penalises extra steps that don't help. Data reuses IR-1 data plus synthetic multi-hop questions.
- **Numbers:** answers in **5.8 s, >2x faster than Claude Sonnet 5, DeepSeek-V4-Flash and GPT-5.6 Luna**, at comparable quality on 7 held-out benchmarks (quality appears only in charts). Example: Recall@10 1.00 in 2 steps, against Sonnet 5 in 3 steps and GPT-5.6 Luna in 4 steps.
- **Learned:** the step-penalty knob traces a quality-latency frontier of checkpoints. Every checkpoint beat the base model.
- Product: Agent Bricks Knowledge Assistant is built on this line (https://www.databricks.com/blog/agent-bricks-knowledge-assistant-now-generally-available-turning-enterprise-knowledge-answers). The original Instructed Retriever post claims ">70% over traditional RAG" (https://www.databricks.com/blog/instructed-retriever-unlocking-system-level-reasoning-search-agents). [VENDOR], and that post was not fetched.

### 13. Databricks: memory scaling for agents
- **Date:** 2026-04-10. URL: https://www.databricks.com/blog/memory-scaling-ai-agents
- **Setup:** Genie Spaces (text-to-SQL agents). Memory is fed with (a) labelled examples, (b) **historical user logs filtered by an LLM judge**, and (c) an organisational knowledge store built from DB metadata.
- **Numbers:** labelled examples took accuracy from near 0 to **70%** (about 5 points over the expert-instruction baseline), and steps fell from about 20 to about 5. Filtered user logs took accuracy from **2.5% to >50%**, passing the 33.0% baseline after 62 records. The knowledge store added about +10%.
- **Learned:** agents fail to query memory they don't know exists. Stale or wrong memories get reused. ACLs must survive distillation.

### 14. Glean Waldo: an agentic search model in front of the frontier LLM
- **Date:** 2026-04-28. URL: https://www.glean.com/blog/waldo-launch
- **Steps:** Waldo is based on **NVIDIA Nemotron 3 Nano (30B total, 3B active MoE)**. It plans and runs searches over Glean Search, people search and web search, decides when evidence is enough, then **hands off** to the frontier model with the context already in place. It is not a sub-agent, so there are no extra serial calls. Training: DPO on anonymised tool-use traces, then RL with a reward of termination plus recall/F1 against the docs production cited. LoRA via Thinking Machines' Tinker.
- **Numbers:** **about 250 ms per call vs about 3 s for GPT-5.4 medium.** In the harness: **about 50% lower latency and about 25% fewer tokens with no quality regression.** About half of queries stay on the fast path. [VENDOR]

### 15. Glean auto-routing vs Claude Cowork (in window)
- **Date:** **2026-08-26**. URL: https://www.glean.com/blog/go-glean-cowork
- **Setup:** 180+ synthetic enterprise tasks from Glean's own data, graded on a 5-point preference scale. Auto-routing picks 1 of 40+ models and the reasoning effort, with Waldo setting the effort.
- **Numbers:** **$0.58 vs $2.98 per task (-81%)**, **1.3M vs 4.4M tokens per task (-70%)**, Glean preferred 78%. A separate Pareto study over 1,000 tasks and 37 configs found that "there's no single 'best' model". Claude Opus 5 (high) scored 67 at $2.96 and GPT-5.6 Luna (xhigh) scored 55 at $0.08. [VENDOR]
- **Credited to:** indexing, keeping tool outputs in sandbox files rather than in context, and loading only the needed tools.

### 16. Glean Jev: zero-shot "typed decision" model (in window)
- **Date:** **2026-09-29**. URL: https://www.glean.com/blog/jev-zero-shot-classifier
- **Why it matters:** this is an honest negative result for reranking. On 4,855 queries, **Jev Recall@6 was 40.2% against 51.2% for the production ranker**. It cost **$0.00044/query at p50 0.195 s**, and it gave identical scores to about 37 of 41 candidates. It **won** on routing (Expert 3 precision 12.5% to 85.7%, median 8.1x faster) and on citation judging (**6.6 s and $0.014 vs 81-260 s and $0.03-$0.06** for GPT-5.6 Luna; more consistent across runs: 1 of 28 vs 5-7 of 28 verdict flips).
- **Learned:** fine-tuned classifiers still win on stable, high-volume tasks. Cheap zero-shot judges are best for citation checks and routing.

### 17. Glean: enterprise search evaluation 2026
- **Date:** 2026-02-12. URL: https://www.glean.com/blog/enterprise-search-evaluation-2026
- **Method:** about 280 queries from Glean's own deployment, matched to the customer query-class mix. Blind and randomised, positions swapped, citations shown to graders, pairwise 5-point scale.
- **Numbers:** on correctness, when graders had a preference, Glean was chosen **1.9x as often as ChatGPT Business and 1.6x as often as Claude Teams**. [VENDOR] ChatGPT lacked Jira and Salesforce connectors at the time.
- **Qualitative:** Claude went deep and sequential and could get stuck on one source (Slack). ChatGPT went broad and parallel but mixed up old and new documents. Both made extra tool calls to compensate for weak search tools.

### 18. Atlassian Rovo on turbopuffer
- **Date:** customer page, © 2026. URL: https://turbopuffer.com/customers/atlassian
- **Architecture:** **one namespace per customer** (isolation by default). Active namespaces are cached in SSD/RAM, and inactive ones sit in object storage with no idle compute. BYOC on AWS and GCP with CMEK.
- **Numbers:** billions of documents across millions of namespaces. **p90 went from 125 ms to 60 ms** (cached namespaces under 20 ms). **recall@10 went from about 90% to 96%+**, and the **Jira long-click rate rose 19%**. [VENDOR]
- **Other customers on the same page:** Linear (2B+ docs, 13 ms p50, 70% cost cut), Legora (2B+ docs, 100 ms p90, 98% recall@10), Superhuman (10B+ docs), Mem0 (400M+ memories, 97% recall@10). [VENDOR] https://turbopuffer.com/customers

### 19. Harvey: "Enterprise-grade RAG systems"
- **Date:** 2025-02-20. URL: https://www.harvey.ai/blog/enterprise-grade-rag-systems
- **Architecture:** three retrieval scopes: per-thread uploads (1-50 docs), Vault projects (1,000-10,000 docs), and third-party legal, regulatory and tax corpora across 45 countries. **LanceDB Enterprise** runs in production because storage can live in customer buckets inside a VPC. **Postgres + pgvector** serves prototyping and small public-data projects.
- **Numbers:** pgvector at 500K embeddings under 2 s P50. LanceDB at **15M rows with metadata filters under 2 s P50**. The PwC tax assistant was "91% preferred over off-the-shelf ChatGPT".
- **Learned:** treat embeddings with the same privacy standard as source text (they can be inverted). Dense retrieval misses rare identifiers such as case numbers. Legal content changes over time (amendments, overrulings), so retrieval must model it. Ingestion throughput matters as much as query latency.

### 20. Shopify Sidekick: production agentic systems
- **Date:** 2025-08-26. URL: https://shopify.engineering/building-production-ready-agentic-systems
- **Practice:** a tool-count ladder: 0-20 tools are fine, 20-50 blur, 50+ make the system hard to reason about. **Just-in-time instructions** are returned with tool results instead of growing the system prompt, which also protects prompt caches. **Ground-truth sets** are sampled from real conversations and labelled by at least 3 experts.
- **Numbers:** LLM-judge **Cohen's kappa rose from 0.02 to 0.61, against a human-human ceiling of 0.69**. Average judge correlation rose from 0.66 to 0.75, and syntax validation from about 93% to about 99%.
- **Validation trick:** randomly swap a human in for the judge. If reviewers can't tell which one is the judge, trust the judge.
- **Gotcha:** reward hacking. Example: `customer_tags CONTAINS 'enabled'` in place of `customer_account_status = 'ENABLED'`.

### 21. DoorDash: LLM-built content embeddings for search [SNIPPET]
- **Date:** 2026-04-14. URL: https://careersatdoordash.com/blog/doordash-llms-to-build-content-embeddings-for-search-and-recommendations/ (403 to fetcher)
- **Reported:** LLMs write merchant and item profiles, which are then embedded with **gemini-embedding-001 at 256 dimensions (MRL)**. `SEMANTIC_SIMILARITY` is used for entity-to-entity work and asymmetric `RETRIEVAL_QUERY`/`RETRIEVAL_DOCUMENT` for search. Item-level retrieval is followed by a fine-tuned Qwen 3 reranker. Queries are evaluated by nDCG@K, stratified head/torso/tail, with an LLM judge.
- **Numbers (via the ZenML summary):** null search rate -3.65%, CVR +0.66%, homepage order rate +2.4% from generated carousels. https://zenml.io/llmops-database/llm-powered-content-embeddings-for-multi-vertical-search-and-recommendations
- **Related, 2026-05-27:** LLMs run **offline** to generate carousel titles and intents, which are stored in Milvus. Serving does retrieval only, with **no LLM call in the request path** [SNIPPET].

### 22. DoorDash: LLM-as-a-judge for natural-language search [SNIPPET]
- **Date:** 2026-05-14. URL: https://careersatdoordash.com/blog/doordash-llm-as-a-judge-evaluating-natural-language-search/
- **Reported:** an audit of **6,824 query-store judgments found the human labels wrong in more than half of the reviewed cases**, concentrated at boundary relevance levels. The fix splits relevance into **independent binary facets** ("serves tacos?", "items under $12?") and calibrates the judge against **adjudicated** human consensus. **Per-facet NDCG** exposed failures on speed and geolocation that the aggregate score hid. About 40% of store results were duplicates across queries [SNIPPET].
- The 2024 Dasher-support RAG (guardrail plus judge; widely quoted as "-90% hallucinations, -99% severe compliance issues") is [SNIPPET]; the primary page returned 403: https://careersatdoordash.com/blog/large-language-modules-based-dasher-support-automation/

### 23. Snap: SMART, LLM-augmented hybrid retrieval for Dynamic Product Ads (in window)
- **Date:** arXiv **2607.23121, 2026-07-25**. URL: https://arxiv.org/abs/2607.23121
- **Finding:** controlled tests on millions of users found **rule-generated queries on BM25 best for retargeting** and **LLM-generated queries on dense ANN best for prospecting**. A light **quality gate** detects coverage gaps in the keyword results and sends **only about 10% of users** to the LLM path.
- **Numbers:** **90% lower LLM cost**. In a 2-week online A/B test, **+27.6% ad conversion rate** over a strong embedding baseline.

### 24. Beam (Phaser Studio) on Gemini API File Search
- **Date:** 2025-11-06 (launch post). URL: https://blog.google/innovation-and-ai/technology/developers-tools/file-search-gemini-api/
- **Reported:** thousands of searches daily over a growing library of game templates. File Search "routinely handles parallel queries across all corpora, combining results in under 2 seconds", against hours of manual cross-referencing before. [VENDOR]
- Google Cloud: I found **no 2026 Google Cloud customer case study with measured RAG Engine or Agent Search (formerly Vertex AI Search) metrics**. Say so honestly on the slide and use the doc-level guidance in section 4.

---

## 2. arXiv industry papers, last 3 months (2026-07-23 to 2026-10-23)

| arXiv | Date | Title | Industry takeaway (numbers from abstract) |
|---|---|---|---|
| 2607.23121 | 07-25 | SMART: LLM-Augmented Hybrid Retrieval for Dynamic Product Ads (Snap) | Gate the LLM path to about 10% of users: -90% LLM cost, +27.6% CVR in a 2-week A/B |
| 2608.08237 | 08-08 | SAGE: SLO-Aware Adaptive Retrieval for Production RAG Systems | Learned per-query k with no LLM call. Under a 5 s P95 SLO: compliance 95% vs 30% for static k=20, P95 -36%, retrieval cost -51%, -2 pts EM. Generalises across 4 LLM families |
| 2608.11584 | 08-12 | EnterpriseRAG: instruction adherence under non-ideal enterprise retrieval | LLMs meet 80% of individual constraints but only **26.8%** of responses meet all of them (a 57-point "orchestration gap"). 983 samples, 6 domains, 13 LLMs. Noise, knowledge gaps and factual conflicts break them |
| 2609.05637 | 09-04 | Better Together: Complementary Query Rewriting Under a Strong RAG Baseline (EMNLP 2026 Industry) | On a strong BGE + cross-encoder + MMR baseline, a single rewrite method is at best on par. **A union of methods gives +12.5 HIT@10** (51.70 vs 39.22) on 512K-doc EnterpriseRAG-Bench. A score-gated router captures +4.3 while rewriting **fewer than 40% of queries**. On AmbigNQ, fusion *hurts* (-2.4) |
| 2609.10750 | 09-09 | When Synthetic Data Hurts: Catastrophic Forgetting in Skill Retrieval (EMNLP 2026 Industry) | Production skill router over **34,396 skills**. Synthetic fine-tuning breaks OOD retrieval. Anchor regularisation, LwF or EWC fix it and add +13.98% in-distribution for a 0.6B Qwen retriever/reranker |
| 2609.15143 | 09-14 | Top-K Is Not a Budget for Hybrid Retrieval | Exact top-20 RRF has long-tailed access costs. Budgeted DiBud keeps 95-97.7% of nDCG@20 with 66-99.5% fewer accesses |
| 2609.22537 | 09-18 | EvidenT: Trustworthy Enterprise Assistants through Evidence Groundedness and Traceability (EMNLP 2026 Industry) | Deterministic lexical alignment of extracted evidence before generation: **+29% gold-source hit rate** on about 500 real enterprise queries, and zero citations to non-retrieved URLs |
| 2610.22297 | 10-15 | Private RAG via Random Projection | One shared random projection on query and doc embeddings resists extraction attacks better than DP baselines at higher quality (no numbers in the abstract) |

Just outside the window, but useful: 2607.12188 (07-13) Cost-Governed RAG, per-tenant cost attribution at 99.96% accuracy, 3.1-9.0x lower retrieval cost than managed vector DBs under stated assumptions. 2607.16973 (07-18) TurboVec: **post-filter tenant isolation drops Recall@10 to 0.09-0.19, against 0.86-0.93 for in-kernel allowlist filtering**. 2603.02153 (Mar 2026) RAG-Fusion in industry: fusion raised raw recall, but after rerank and truncation Hit@10 *fell* from 0.51 to 0.48.

---

## 3. Cost and latency reference card (all sourced)

| Item | Number | Source |
|---|---|---|
| Gemini File Search indexing | $0.15 / 1M tokens at launch (gemini-embedding-001). Storage and query embeddings free. Retrieved chunks billed as context | blog.google launch post; ai.google.dev/gemini-api/docs/file-search |
| Gemini File Search store size | Free 1 GB, Tier 1 10 GB, Tier 2 100 GB, Tier 3 1 TB. Store is about 3x input size. **Keep each store under 20 GB for latency.** Max file 100 MB | ai.google.dev/gemini-api/docs/file-search (fetched) |
| OpenAI vector store storage | First 1 GB free, then **$0.10/GB/day**. Max file 512 MB, 5M tokens per file. Default chunk 800 tokens with 400 overlap (100-4096 allowed) | developers.openai.com/api/docs/guides/retrieval (fetched) |
| OpenAI file_search per-call price | [UNVERIFIED]; not on the guide page | — |
| Vertex AI RAG Engine | Default parser and fixed-size chunking free. LLM parser, Document AI, embeddings and reranking billed by their own services. RagManagedDb is Spanner: Basic 100 PU, Scaled 1-10 nodes autoscaling | docs.cloud.google.com/.../rag-engine-billing (fetched) |
| Vertex ranking API vs LLM reranker | Ranking API under 100 ms. LLM reranker 1-2 s | docs.cloud.google.com/.../retrieval-and-ranking (fetched) |
| Google check-grounding API | Designed for under 500 ms. Up to 200 facts of 10k chars each. Answer up to 4,096 tokens. Default citationThreshold 0.6 | docs.cloud.google.com/generative-ai-app-builder/docs/check-grounding (fetched) |
| Azure agentic retrieval worked example | 2,000 retrievals × 3 subqueries × rerank 50 chunks of 500 tokens = $3.30 search + $1.02 planning = **$4.32** (gpt-4o-mini example rates) | learn.microsoft.com/azure/search/agentic-retrieval-overview (fetched, updated 2026-09-17) |
| Reranker throughput (H100, bf16) | Ettin-17M 7,517 pairs/s; Ettin-1B 928; mxbai-rerank-large-v2 387. CPU: 17M at 267 pairs/s, 1B at 2.1 | huggingface.co/blog/ettin-reranker (2026-05-19) |
| Glean per-task cost | $0.58 vs $2.98 (Claude Cowork), 1.3M vs 4.4M tokens | glean.com/blog/go-glean-cowork [VENDOR] |
| Cheap reranking floor | $0.00044/query at p50 195 ms (Jev), but lower recall than a trained ranker | glean.com/blog/jev-zero-shot-classifier |
| Vector DB latency at scale | Notion p50 50-70 ms; Atlassian p90 60 ms; Linear p50 13 ms | Notion blog; turbopuffer.com/customers |
| Web search API latency | Perplexity p50 358 ms / p95 763 ms; Exa p50 1,375 ms | perplexity.ai/hub/blog [VENDOR] |
| Retrieval latency target | 95%+ of queries under 1-2 s (Dropbox); TTFT about 2 s (Databricks IR-1); 5.8 s full answer (Adaptive IR) | Dropbox 2025-04; Databricks 2026-06, 2026-09 |
| Agentic overhead | MCP/federated agent query up to 45 s vs seconds for the index (Dropbox). Tool definitions: 58 tools about 55K tokens, worst seen 134K (Anthropic) | Dropbox 2026-01; anthropic.com/engineering/advanced-tool-use |

---

## 4. Vendor guidance dated 2025-2026 (what each vendor tells you to do)

### Google (Gemini API File Search; Gemini Enterprise Agent Platform RAG Engine; Agent Search)
- **File Search** (ai.google.dev/gemini-api/docs/file-search, fetched 2026-10-23). Supported models listed: Gemini 4 Argon, 3.8 Flash, 3.6 Flash, 3.5 Flash-Lite, 3.1 Pro Preview, 3.1 Flash-Lite, 3 Flash Preview. Guidance: keep stores under 20 GB. Use `metadata_filter` (AIP-160 syntax) to search subsets. Raw Files API uploads are deleted after 48 h, but imported store data persists. File Search **cannot be combined with Google Search grounding or URL Context in one request**, and is **not supported in the Live API**.
  ```python
  # Chunking control at upload (from the docs page)
  operation = client.file_search_stores.upload_to_file_search_store(
      file_search_store_name=file_search_store.name,
      file='sample.txt',
      config={'chunking_config': {'white_space_config': {
          'max_tokens_per_chunk': 200, 'max_overlap_tokens': 20}}})
  while not operation.done:
      time.sleep(5)
      operation = client.operations.get(operation)

  # Query with metadata filter (docs page uses the Interactions API)
  interaction = client.interactions.create(
      model="gemini-3.8-flash",
      input="Tell me about the book 'I, Claudius'",
      tools=[{"type": "file_search",
              "file_search_store_names": [file_search_store.name],
              "metadata_filter": 'author="Robert Graves"'}])
  # Citations: content.annotations[] with type == "file_citation"
  # (file_name, source, page_number, media_id, custom_metadata)
  ```
- **RAG Engine** (docs.cloud.google.com/vertex-ai/generative-ai/docs/rag-engine/rag-overview, updated 2026-10-22). It is now part of **Gemini Enterprise Agent Platform**. Vector backends: RagManagedDb, Agent Platform Vector Search 2.0 ("Agent Retrieval"), Vector Search, Feature Store, Weaviate, Pinecone, Agent Platform Search. **us-central1, us-east1, us-east4 and europe-west1 are now allowlist-only for new projects.** europe-west3 and europe-west4 are GA. VPC-SC and CMEK are supported. Data residency and AXT are not.
  ```python
  # Reranking options (docs page)
  config = rag.RagRetrievalConfig(top_k=10,
      ranking=rag.Ranking(rank_service=rag.RankService(model_name=RANKER_MODEL_NAME)))   # <100 ms
  config = rag.RagRetrievalConfig(top_k=10,
      ranking=rag.Ranking(llm_ranker=rag.LlmRanker(model_name=MODEL_NAME)))             # 1-2 s
  ```
- **Agent Search** (formerly Vertex AI Search, renamed 2026-04-22). Release notes: Gemini 3.5 Flash for answer generation (2026-08-13), which becomes the `stable` answer model on 2026-10-16. CMEK rotation GA and per-request `searchAddonSpec` to switch off paid add-ons (2026-09-14). https://docs.cloud.google.com/generative-ai-app-builder/docs/release-notes
- **Check grounding** as a post-generation gate: support score 0-1, claim-level scores (`enableClaimLevelScore`), and citations. Keep one claim per sentence. Offsets are UTF-8 bytes.

### OpenAI (Responses API `file_search`)
- Docs: https://developers.openai.com/api/docs/guides/tools-file-search and /guides/retrieval (fetched).
- Knobs: `max_num_results`, `include=["file_search_call.results"]` to see what was retrieved (off by default), attribute `filters` (eq, ne, gt, gte, lt, lte, in, nin, and, or), `ranking_options.ranker` (`auto` or `default-2024-08-21`), `score_threshold`, `hybrid_search` RRF weights (`embedding_weight`, `text_weight`), `rewrite_query=true`, and `expires_after` on vector stores.
- Gotcha: filename filtering only works on a **custom `filename` attribute you set yourself**, not on the uploaded file's name.
  ```python
  from openai import OpenAI
  client = OpenAI()
  response = client.responses.create(
      model="gpt-6-astra",   # model id as shown on the docs page, 2026-10-23
      input="What is deep research by OpenAI?",
      tools=[{"type": "file_search", "vector_store_ids": ["<vector_store_id>"]}],
      include=["file_search_call.results"])
  ```

### Anthropic
- **Tool Search Tool** (https://www.anthropic.com/engineering/advanced-tool-use, 2025-11-24). Mark tools `defer_loading: true` and add `tool_search_tool_regex_20251119` (a BM25 variant also exists). Result: about 85% fewer tool-definition tokens, and MCP accuracy 49% to 74% (Opus 4) and 79.5% to 88.1% (Opus 4.5). Use it when tool definitions exceed 10K tokens or there are 10+ tools. Keep the 3-5 most-used tools always loaded. This is retrieval applied to tools, which is the same lesson as Dropbox's "super tool".
- **Demystifying evals for AI agents** (2026-01-09, https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents). Start with **20-50 tasks drawn from real failures**. A good task is one where two experts would independently agree on pass or fail. Grade outcomes, not paths. Give LLM judges an "Unknown" option. Use **one judge per rubric dimension**. For research and search agents, combine **groundedness, coverage (key facts) and source-quality checks**. Use pass^k when consistency matters (75% per trial is about 42% pass^3). Read transcripts.
- **Eval awareness in BrowseComp** (2026-03-06, https://www.anthropic.com/engineering/eval-awareness-browsecomp). Opus 4.6 multi-agent identified the benchmark and decrypted the answer key in 2 of 1,266 problems. The unintended-solution rate was 0.24% single-agent vs **0.87% multi-agent**. URL blocklists failed. **Blocking any result that contains the benchmark name** worked best.
- Context engineering, just-in-time retrieval and Contextual Retrieval are already covered in `research-rag/02`, `/05` and `/08`.

### Microsoft (Azure AI Search agentic retrieval / Foundry IQ)
- Docs updated 2026-09-17 (https://learn.microsoft.com/en-us/azure/search/agentic-retrieval-overview). The pipeline is: LLM query planning, then parallel subqueries (keyword, vector or hybrid), then **semantic rerank per subquery**, then merge with references and an activity log. Use **GA `2026-04-01` for minimal/extractive retrieval**, and `2026-08-01-preview` for planning, answer synthesis and multi-turn.
- **`retrievalReasoningEffort`**: `minimal` (no LLM planning, all sources searched, extractive only), `low` (default, one planning pass), `medium` (a semantic classifier triggers **at most one** follow-up iteration), and **`auto`** (preview: a light first pass, escalating to medium only when grounding is insufficient). https://learn.microsoft.com/en-us/azure/search/agentic-retrieval-how-to-set-retrieval-reasoning-effort
  ```python
  # Per-request override (verbatim from MS Learn, 2026-08-17)
  request = KnowledgeBaseRetrievalRequest(
      messages=[KnowledgeBaseMessage(role="user",
          content=[KnowledgeBaseMessageTextContent(text="What is the return policy?")])],
      retrieval_reasoning_effort=KnowledgeRetrievalLowReasoningEffort(),
      output_mode=KnowledgeRetrievalOutputMode.ANSWER_SYNTHESIS)
  result = kb_client.retrieve(request)
  ```
- Cost tips from the docs: consolidate knowledge sources (less fan-out), lower the effort, and curate summaries and tables so fewer documents are needed.
- Microsoft blog claims [VENDOR; the pages are JS-rendered and I could not fetch the body, so figures come from the search summary]: knowledge bases raise evidence recall by "up to 54%" with about 34% token savings (https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/foundry-iq-improve-recall-by-up-to-54-with-knowledge-bases/4524852). `auto` effort "keeps most of the recall of the highest effort level with far fewer planning tokens" (https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/let-the-query-decide-introducing-auto-retrieval-reasoning-effort/4558943).

### Hugging Face (Sentence Transformers)
- **Ettin rerankers** (2026-05-19, https://huggingface.co/blog/ettin-reranker): six Apache-2.0 cross-encoders (17M to 1B, 8K context). The guidance is to **replace MiniLM rerankers with Ettin-17M/32M** for speed and quality, use 150M as the best model under 600M, and turn on bf16 plus Flash Attention 2. Ettin-32M scores NanoBEIR 0.6825 against MiniLM-L12 at 0.6369.
  ```python
  from sentence_transformers import CrossEncoder
  model = CrossEncoder("cross-encoder/ettin-reranker-32m-v1")
  ranked = model.rank(query, docs, top_k=5, return_documents=True)
  ```
- Sentence Transformers v5 adds sparse (SPLADE) encoders, and v6 adds `MultiVectorEncoder` (ColBERT/PyLate checkpoints), so hybrid and late interaction come from one library (huggingface.co/blog/multi-vector-encoder) [SNIPPET].

### Databricks
- Pass **user instructions and the index schema** into query generation and reranking (Instructed Retriever). Spend test-time compute **in parallel** (query variants plus groupwise rerank) before going sequential. Penalise unnecessary steps in RL. Treat memory as a scaling axis, with judge-filtered user logs as memory. Sources are in section 1, items 11-13.

---

## 5. How top teams evaluate (patterns from the case studies)

1. **Golden sets come from production, not imagination.** Shopify uses sampled merchant conversations labelled by at least 3 experts. Uber uses 100+ SME queries. Glean uses about 280 internal queries matched to customer query classes. Anthropic says to start with 20-50 tasks from real failures.
2. **Measure judge-human agreement, and quote the human ceiling.** Shopify: kappa 0.61 against a human 0.69. Dropbox: disagreement starting at 8%.
3. **Audit the humans too.** DoorDash: more than half of audited human labels were wrong. Use binary facets and adjudicated consensus.
4. **RAG-as-a-judge.** Give the judge retrieval so it can resolve acronyms and internal jargon (Dropbox).
5. **Split the metrics.** Per-facet NDCG (DoorDash), separate judges per dimension (Anthropic), and retrieval metrics (source precision, recall, F1) separate from answer metrics (Dropbox, Uber `document_quality_metric` vs `rule_adherence_metric`).
6. **Online A/B tests with behavioural metrics:** code retention and dissatisfied follow-ups (Cursor), long-clicks (Atlassian), CVR and null-search rate (DoorDash, Snap), and review time (Uber Legal).
7. **Blind, randomised pairwise preference with citations visible** for product comparisons (Glean).
8. **User simulators** replay real goals against candidate systems before launch (Shopify).
9. **Guard eval integrity:** block benchmark-name results and gate datasets behind authentication (Anthropic).
10. **Report holistic compliance, not per-constraint averages.** EnterpriseRAG: 80% per-constraint becomes 26.8% all-constraints.

---

## 6. Best-practices checklist (36 items, each with a source)

**Ingestion and indexing**
1. Parse from the most structured source available (HTML or Google Docs, not PDF) and convert tables to markdown with an LLM. Never split a table across chunks. — Uber EAg-RAG
2. Enrich every document with an LLM-written summary, FAQs and keywords, and index them for BM25 as well as vectors. — Uber EAg-RAG
3. Hash each span's text and metadata separately (xxHash64). Re-embed only changed text, and PATCH metadata-only changes. — Notion (-70% data volume)
4. Plan capacity in "generations" (new index for new tenants) instead of re-sharding live indexes. — Notion
5. Use one namespace per tenant or customer, and keep cold namespaces in object storage. — Atlassian/turbopuffer, Notion
6. Filter tenants **inside** the ANN kernel (allowlist), never by post-filtering top-k. — TurboVec 2607.16973 (Recall@10 0.86-0.93 vs 0.09-0.19)
7. Treat embeddings as sensitive as the source text. Host them in the customer's VPC or bucket when required. — Harvey
8. Precompute graph relationships into "knowledge bundles" at index time. Don't query a graph DB on the hot path. — Dropbox Dash
9. Make index coverage explicit and monitored, because "coverage gaps are silent". — Glean (2026-07-29)
10. Keep managed stores within vendor guidance: Gemini File Search under 20 GB per store, and use metadata filters to scope. — Google docs
11. Set `expires_after` on scratch vector stores so they stop billing. — OpenAI docs

**Retrieval and ranking**
12. Default to hybrid BM25 + dense with a cross-encoder reranker. Pure dense misses identifiers such as case numbers and error codes. — Harvey, Dropbox, Perplexity, Uber
13. Retrieve sub-document passages, not whole documents. — Perplexity, Glean token-efficiency post
14. Swap MiniLM rerankers for Ettin-17M/32M (faster and better). Use bf16 plus FlashAttention-2. — Hugging Face 2026-05
15. Pick the reranker by latency budget: ranking API under 100 ms, LLM reranker 1-2 s. — Google RAG Engine docs
16. After retrieval, dedupe chunks and reorder them by position in the source document before generation. — Uber EAg-RAG
17. Mine hard negatives (near-misses) when fine-tuning embedders, and evaluate on several benchmarks, not one. — GitHub Copilot
18. If you have agent traces, train the embedder on "what would have helped", as ranked by an LLM over the traces. — Cursor
19. Use MRL-truncated embeddings (for example 256 dimensions) and the correct asymmetric task types for query vs document. — DoorDash [SNIPPET]
20. Don't assume fixed top-k. Budget retrieval per query (learned k, or certified-prefix fusion). — SAGE 2608.08237, DiBud 2609.15143

**Query transformation and routing**
21. Gate expensive paths (rewrite, LLM queries, agentic loops) behind a cheap first-pass quality signal such as top-1 score or a coverage gap. — Better Together 2609.05637 (<40% rewritten), Snap SMART (10% of users)
22. If you rewrite, fuse **complementary** methods rather than one rewriter, and measure after reranking and truncation. — 2609.05637; 2603.02153
23. Use the vendor's adaptive effort mode (`auto`) rather than a fixed high effort for mixed workloads. — Microsoft Learn 2026-08
24. Put a small specialised search model in front of the frontier model and hand off context directly, not through a sub-agent. — Glean Waldo, Databricks IR
25. Route model and reasoning effort per task, because no single model dominates the cost-quality frontier. — Glean 2026-08-26

**Agents and context**
26. Expose one retrieval "super tool" over the index. Defer the rest with tool search. — Dropbox; Anthropic Tool Search
27. Keep tool outputs in files or sandbox state, not in the context window. — Dropbox, Glean
28. Return just-in-time instructions with tool results instead of growing the system prompt. — Shopify
29. Above about 20 tools, expect blurred boundaries. Above 50, re-architect. — Shopify
30. For non-negotiable rules, run deterministic rules that override the LLM, then verify with a final LLM check. — Uber Legal
31. Time-decay feedback memories (half-life, for example 365 days) and balance positive and negative examples. — Uber Legal
32. Ingest judge-filtered user logs as agent memory, and make sure the agent knows the memory exists. — Databricks memory scaling

**Evaluation, grounding and security**
33. Calibrate LLM judges against adjudicated humans, report kappa against the human ceiling, and re-calibrate after model changes. — Shopify, Dropbox, DoorDash
34. Verify evidence before generation (lexical alignment of extracted spans) and reject citations to non-retrieved sources. — EvidenT 2609.22537
35. Add a post-generation grounding gate with claim-level scores and a citation threshold (Google check-grounding, under 500 ms). — Google docs
36. Use pass^k for consistency, grade outcomes not paths, give the judge an "Unknown" option, and block benchmark-name results in web-enabled evals. — Anthropic (2026-01, 2026-03)
37. Track tokens per successful task, cost per completed workflow, and the worst 10% of runs (retry loops). — Glean token-efficiency post (2026-07-23)
38. Test under noisy retrieval, knowledge gaps and conflicting sources, and report the all-constraints pass rate. — EnterpriseRAG 2608.11584

---

## 7. What top teams do differently

| Typical team | Top team (evidence) |
|---|---|
| Federates live API/MCP calls at query time | Builds and pays for a **unified, permission-aware index plus graph**, then exposes it as one tool (Dropbox, Glean) |
| Uses a frontier LLM for every retrieval step | Trains **small retrieval-specialised models** (Waldo 3B-active, Instructed-Retriever, Cursor and GitHub embedders, LinkedIn distilled SLM ranker) and saves the frontier model for synthesis |
| Same pipeline for every query | **Adaptive compute**: gates, routers, `auto` effort, and RL step penalties (Snap, Databricks, Microsoft, SAGE) |
| Re-embeds everything on every change | **Diff-based incremental indexing** and usage-priced serverless vector stores (Notion) |
| Vibe checks or a "rate 0-10" judge | **Calibrated, decomposed judges** with human-ceiling reporting, RAG-as-judge and DSPy-optimised prompts (Shopify, Dropbox, DoorDash) |
| Offline metrics only | **Online A/B on behaviour** (retention, long-clicks, CVR, review time) (Cursor, Atlassian, Snap, Uber) |
| Off-the-shelf embedder forever | **Domain or agent-trace fine-tuning with hard negatives**, watching for catastrophic forgetting (GitHub, Cursor, 2609.10750) |
| Adds tools and instructions until it breaks | **Prunes tools**, defers loading, and uses JIT instructions (Shopify, Anthropic, Dropbox) |
| Trusts the LLM's citations | **Verifies evidence deterministically** and gates on grounding scores (EvidenT, Google check-grounding) |
| Optimises tokens per request | Optimises **cost per successful outcome**, including retries (Glean) |
| Moves LLMs into the request path | Runs LLMs **offline** to enrich content, and serves with retrieval only (DoorDash carousels [SNIPPET], Uber metadata enrichment) |

---

## 8. Gotchas and challenges seen in production

- **Rewriting does not stack on a strong baseline.** One rewriter is at best on par (2609.05637), and RAG-Fusion's recall gain vanished after rerank and truncation (2603.02153).
- **Fusion can hurt ambiguous queries:** -2.4 on AmbigNQ (2609.05637).
- **Post-filtering kills recall** in multi-tenant ANN: 0.09-0.19 Recall@10 (2607.16973).
- **Agents get "analysis paralysis"** with many similar tools (Dropbox). Selection errors are the top failure (Anthropic).
- **Zero-shot rerankers tie heavily.** Jev gave identical scores to about 37 of 41 candidates, so a tie-break by prior order is needed (Glean).
- **Synthetic fine-tuning data causes forgetting** on real or OOD queries (2609.10750).
- **Human labels are noisy at relevance boundaries** (DoorDash, >50% wrong in the audit).
- **Reward hacking in RL-tuned agents:** opt-out answers, tag misuse, hallucinated IDs (Shopify).
- **Benchmark contamination and eval awareness** in web-enabled agents, worse with multi-agent (Anthropic).
- **Region and allowlist changes in managed RAG:** four big GCP regions became allowlist-only for RAG Engine (Oct 2026 docs).
- **Managed tool exclusivity:** Gemini File Search can't be combined with Google Search grounding or URL Context in one call.
- **Graph DBs on the hot path** were too slow for Dropbox.
- **Multi-pass reflection loops** were less reliable and more expensive than one strong prompt (Uber Legal).

---

## 9. Illustrative code for the hands-on slides (my own code, built from the sourced patterns; not copied from any company)

```python
# (a) Score-gated query rewriting / LLM path (pattern from arXiv 2609.05637 and Snap SMART 2607.23121)
def retrieve(query, search, rewrite_fns, rerank, gate=0.55, k=10):
    base = rerank(query, search(query, k=50))[:k]          # strong baseline: hybrid + cross-encoder
    if base and base[0].score >= gate:                       # confident -> cheap path
        return base
    pool = {d.id: d for d in base}
    for fn in rewrite_fns:                                    # complementary rewriters (e.g., HyDE, decomposition)
        for q in fn(query):
            for d in search(q, k=50):
                pool.setdefault(d.id, d)
    return rerank(query, list(pool.values()))[:k]           # always rerank against the ORIGINAL query

# (b) Time-decayed feedback memory weights (Uber Legal: exp(-lambda*age), half-life 365 days)
import math, random
def decay_weight(age_days, half_life_days=365):
    lam = math.log(2) / half_life_days
    return math.exp(-lam * age_days)

def sample_feedback(examples, n=6):
    """examples: list of dicts with 'age_days' and 'label' in {'agree','disagree'}; balanced sample."""
    out = []
    for label in ("agree", "disagree"):
        pool = [e for e in examples if e["label"] == label]
        if pool:
            w = [decay_weight(e["age_days"]) for e in pool]
            out += random.choices(pool, weights=w, k=min(n // 2, len(pool)))
    return out

# (c) Notion-style incremental re-embedding decision (Notion used xxHash64 per span; hashlib used here to stay stdlib-only)
import hashlib
def h(s): return hashlib.blake2b(s.encode(), digest_size=8).hexdigest()
def plan_update(span, stored):   # stored: {"text_hash":..., "meta_hash":...} or None
    th, mh = h(span["text"]), h(repr(sorted(span["meta"].items())))
    if stored is None or stored["text_hash"] != th:
        return "EMBED_AND_UPSERT"
    if stored["meta_hash"] != mh:
        return "PATCH_METADATA_ONLY"
    return "SKIP"
```

---

## 10. Slide ideas from this file

1. **"Index vs federate"**: a stopwatch race. Federated MCP agent "up to 45 s" against index "seconds" (Dropbox).
2. **"Notion's cost curve"**: a step chart from pods to serverless (-50%) to turbopuffer (-60% search spend) to Page State (-70% data) to Ray (-90%+ embedding infra), with p50 70-100 ms falling to 50-70 ms.
3. **"Small model in front"**: Waldo 250 ms vs 3 s; Adaptive IR 5.8 s vs >2x slower frontier models.
4. **"Gate it"**: a funnel of 100% of users to 10% on the LLM path, -90% LLM cost, +27.6% CVR (Snap). A second bar shows rewrites on fewer than 40% of queries capturing half the gain (2609.05637).
5. **"Your judge is a model you ship"**: Shopify kappa 0.02 to 0.61 (human 0.69), and DoorDash's ">50% of human labels wrong".
6. **"80% vs 26.8%"**: the EnterpriseRAG orchestration gap.
7. **"The answer key was on HuggingFace"**: Anthropic's BrowseComp eval-awareness story.
8. **"Too many good tools"**: Shopify's 0-20, 20-50, 50+ tool ladder alongside Anthropic's 85% token cut.

---

## 11. Sources (all accessed 2026-10-23)

Company engineering:
- https://www.notion.com/blog/two-years-of-vector-search-at-notion
- https://dropbox.tech/machine-learning/vp-josh-clemm-knowledge-graphs-mcp-and-dspy-dash
- https://dropbox.tech/machine-learning/how-dash-uses-context-engineering-for-smarter-ai
- https://dropbox.tech/machine-learning/building-dash-rag-multi-step-ai-agents-business-users
- https://www.perplexity.ai/hub/blog/architecting-and-evaluating-an-ai-first-search-api
- https://vespa.ai/perplexity/
- https://cursor.com/blog/semsearch
- https://github.blog/news-insights/product-news/copilot-new-embedding-model-vs-code/
- https://www.uber.com/us/en/blog/enhanced-agentic-rag/
- https://www.uber.com/us/en/blog/building-ubers-redlining-agent/
- https://arxiv.org/abs/2602.07309 (LinkedIn)
- https://www.databricks.com/blog/3x-faster-search-parallel-test-time-scaling-instructed-retriever-1
- https://www.databricks.com/blog/adaptive-instructed-retriever-frontier-quality-search-2x-lower-latency
- https://www.databricks.com/blog/memory-scaling-ai-agents
- https://www.databricks.com/blog/instructed-retriever-unlocking-system-level-reasoning-search-agents (not fetched)
- https://www.glean.com/blog/waldo-launch
- https://www.glean.com/blog/go-glean-cowork
- https://www.glean.com/blog/jev-zero-shot-classifier
- https://www.glean.com/blog/enterprise-search-evaluation-2026
- https://www.glean.com/blog/enterprise-ai-indexing-context
- https://www.glean.com/blog/how-to-optimize-token-efficiency-in-agentic-systems
- https://turbopuffer.com/customers and https://turbopuffer.com/customers/atlassian
- https://www.harvey.ai/blog/enterprise-grade-rag-systems
- https://shopify.engineering/building-production-ready-agentic-systems
- https://careersatdoordash.com/blog/doordash-llms-to-build-content-embeddings-for-search-and-recommendations/ [403, SNIPPET]
- https://careersatdoordash.com/blog/doordash-llm-as-a-judge-evaluating-natural-language-search/ [403, SNIPPET]
- https://blog.google/innovation-and-ai/technology/developers-tools/file-search-gemini-api/

Vendor docs and guidance:
- https://ai.google.dev/gemini-api/docs/file-search
- https://docs.cloud.google.com/vertex-ai/generative-ai/docs/rag-engine/rag-overview
- https://docs.cloud.google.com/vertex-ai/generative-ai/docs/rag-engine/rag-engine-billing
- https://docs.cloud.google.com/vertex-ai/generative-ai/docs/rag-engine/retrieval-and-ranking
- https://docs.cloud.google.com/generative-ai-app-builder/docs/check-grounding
- https://docs.cloud.google.com/generative-ai-app-builder/docs/release-notes
- https://developers.openai.com/api/docs/guides/tools-file-search
- https://developers.openai.com/api/docs/guides/retrieval
- https://www.anthropic.com/engineering/advanced-tool-use
- https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents
- https://www.anthropic.com/engineering/eval-awareness-browsecomp
- https://learn.microsoft.com/en-us/azure/search/agentic-retrieval-overview
- https://learn.microsoft.com/en-us/azure/search/agentic-retrieval-how-to-set-retrieval-reasoning-effort
- https://huggingface.co/blog/ettin-reranker

arXiv (window 2026-07-23 to 2026-10-23): 2607.23121, 2608.08237, 2608.11584, 2609.05637, 2609.10750, 2609.15143, 2609.22537, 2610.22297. Near-window: 2607.12188, 2607.16973, 2603.02153.

Not found or not verified: OpenAI file_search per-call price; a 2026 Google Cloud customer story with measured RAG Engine or Agent Search metrics; JetBrains "RAG pipeline for semantic code search" (Sep 2026, https://blog.jetbrains.com/ai/2026/09/building-a-rag-pipeline-for-semantic-code-search-a-developer-diary-and-field-notes/, 403); Ramp NAICS RAG post body (https://engineering.ramp.com/industry_classification, empty to fetcher; the ZenML summary claims +60% retrieval accuracy, +5-15% final accuracy [UNVERIFIED]); body text of the Microsoft Foundry IQ blog posts.
