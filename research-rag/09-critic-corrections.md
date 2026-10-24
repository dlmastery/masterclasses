# 09: Critic Pass. Corrections, Gaps and the 60-Slide Narrative Arc

Critic pass date: 2026-10-23. Inputs: files 01–08 in this folder (about 30k words). Every correction below was re-checked against a primary source today: PyPI JSON, the arXiv abs page or API, the GitHub API via `gh`, official docs, or an HTTP status check. Anything still unconfirmed is marked **[UNVERIFIED]**.

---

## 1. Contradictions between files, resolved

| # | Topic | File A says | File B says | Primary-source verdict (2026-10-23) |
|---|---|---|---|---|
| C1 | **Search-R1 headline gain** | 03: "+24% (Qwen2.5-7B), +20% (3B)" | 08: "v1/v3 +41%/+20%; v4/v5 +24%/+20%" | **Both are wrong.** v1 (12 Mar 2025) reports **+26% (Qwen2.5-7B), +21% (Qwen2.5-3B), +10% (LLaMA3.2-3B)**. v3, v4 and the current **v5 (5 Aug 2025)** all report **"41% (Qwen2.5-7B) and 20% (Qwen2.5-3B) over various RAG baselines"**. On the slide, use **+41% / +20% (arXiv 2503.09516v5)**. The arXiv page gives no venue. Cite COLM 2025 only from the repo README [UNVERIFIED on arXiv]. |
| C2 | **google-adk version** | 03: "2.12.0 on 2026-10-13" | 07: "2.13.0, 2026-10-23" | PyPI: **2.13.0 was released 2026-10-23**. 2.12.0 (10-13) is now the previous release. Use **2.13.0**. |
| C3 | **RAGAS repo location** | 06: `explodinggradients/ragas` | 07: moved to `vibrantlabsai/ragas` | `github.com/explodinggradients/ragas` returns **301 → github.com/vibrantlabsai/ragas** (16.1k stars). PyPI `ragas` **0.4.3 (2026-01-13)** is still the latest. Cite the new org and note the old URL redirects. |
| C4 | **Context Rot: shuffled vs coherent haystacks** | 02: "shuffled haystacks beat coherent ones" | 08: "coherent irrelevant text hurt more… verify" | The report says: *"Shuffling the haystack and removing local coherence consistently improves performance."* 02 is right. Canonical URL: **https://www.trychroma.com/research/context-rot** (`research.trychroma.com/...` 301-redirects there). Hong, Troynikov, Huber; 14 Jul 2025; 18 models. |
| C5 | **Claude prompt-cache minimum** | 02/06: "512–4,096, model-dependent" | 05: "Minimum 512 tokens on current models" | Docs table: **512** for Opus 5.5 / Sonnet 5.5 / Haiku 5.5 / Opus 5 (and others). **1,024** for Sonnet 4.5/4.6, Opus 4/4.1. **2,048** for Opus 4.7, Haiku 3.5. **4,096** for Opus 4.5/4.6 and **Haiku 4.5**. Prompts below the minimum are silently not cached ("no error is returned"). **Impact:** 02's Contextual-Retrieval snippet uses `claude-haiku-4-5`, so the cached document must be ≥4,096 tokens. Read multipliers: 0.1x default, **0.05x Opus/Sonnet 5.5**, 0.025x Fable/Mythos 5.1. |
| C6 | **Gemini File Search launch date** | 07: "~Nov 6 2025, blog URL [UNVERIFIED]" | 08: "launch date [UNVERIFIED]" | Official post: **"Introducing the File Search Tool in Gemini API", 6 Nov 2025**, https://blog.google/innovation-and-ai/technology/developers-tools/file-search-gemini-api/ (HTTP 200). Launch pricing was $0.15/1M indexing tokens (gemini-embedding-001), with free storage and free query embeddings. |
| C7 | **Advanced RAG codelab title** | 07: "Building a Google-quality Search System with Vertex AI" | 08: "Build a Google-quality RAG system with Vertex AI" | The page `<title>` reads **"Building a Google-quality Search System with Vertex AI"** (https://codelabs.developers.google.com/build-google-quality-rag). 07 is right. |
| C8 | **RAG Engine naming** | 03/07: ADK says "Knowledge Engine" | 07: "Cloud docs still say RAG Engine" | Release notes (22 Apr 2026): "Vertex AI RAG Engine" became **"RAG Engine"**, "Agent Engine is now **Agent Runtime**", and Vertex AI Search became **Agent Search**. "Knowledge Engine" appears **only in ADK docs** (page title "Knowledge Engine tool for ADK"). Use "RAG Engine" on slides, with a footnote "(ADK docs: Knowledge Engine)". |
| C9 | **Memory Bank doc URL** | 05 overview link `/agent-builder/agent-engine/memory-bank/overview` | 05 also uses `/gemini-enterprise-agent-platform/scale/memory-bank/...` | The old overview URL now redirects to the generic `/gemini-enterprise-agent-platform/scale` page. Cite **.../scale/memory-bank/generate-memories** (HTTP 200). |
| C10 | **Prompt-caching docs URL** | 02/06: `/docs/en/build-with-claude/prompt-caching` | 05: `/docs/en/docs/build-with-claude/...` | 05's URL redirects to the 02/06 form. Cite **https://platform.claude.com/docs/en/build-with-claude/prompt-caching**. |
| C11 | **OpenAI deep-research model in code** | 03 snippet: `model="o3-deep-research"` | 03 table: "shutdown 2026-07-23 → gpt-5.6-sol" | The docs confirm the shutdown date of **July 23, 2026** for both `o3-deep-research` and `o4-mini-deep-research`, with replacement **`gpt-5.6-sol`**. That date has passed, so **the snippet will not run today**. Change the model to `gpt-5.6-sol`. MCP still needs `search` + `fetch` and `require_approval: "never"`, and the limit is still 2 vector stores. |
| C12 | **"Knowledge Graphs for RAG" DLAI course** | 08: "[UNVERIFIED]" | — | It exists: **https://www.deeplearning.ai/short-courses/knowledge-graphs-rag/** (title "Knowledge Graphs for RAG"). |
| C13 | **Gemini Embedding 2 price** | 05: "$0.25/1M [UNVERIFIED]" | 01: Batch API at 50% | Pricing page: **$0.20 per 1M text tokens (standard), $0.10 (batch)**, free on the Free Tier. Image $0.45/1M ($0.00012/image), audio $6.50/1M, video $12.00/1M. |
| C14 | **Gemini Embedding 2 paper numbers** | 01: "~68–70 multilingual" | 05: "69.9 [UNVERIFIED]" | arXiv **2605.27295** (26 May 2026; Shanbhogue et al., 91 authors). The abstract reports **MSCOCO R@1 62.9, Vatex nDCG@10 68.8, MTEB Multilingual 69.9, MTEB Code 84.0**. These are now verified. |
| C15 | **Docling version** | 01/05: "[UNVERIFIED; check PyPI]" | — | PyPI **docling 2.142.1 (2026-10-23)**. |
| C16 | **ADK `google_search` sample model** | 03: `gemini-2.0-flash` | 07/08: `gemini-flash-latest` | Both are verbatim from adk.dev. The Python/Java examples use `gemini-2.0-flash` and the TS/Go examples use `gemini-flash-latest`. The docs say the tool "is only compatible with Gemini 2 models" and "can only be used by itself". On slides, use `gemini-flash-latest` for consistency. |
| C17 | **Cohere Rerank 5 / Embed 5** | 01/02: details from aggregators [UNVERIFIED] | — | **Cohere's own changelog** confirms: `rerank-v5.0-pro/fast` with 32k context, optional `relevant_spans` ("Context Focus") returning scored character spans, and calibrated scores. `embed-v5.0-pro/fast` with 128k context, MRL dims 256/512/768/1024/1536/2048, float/int8/binary output, and a shared Pro↔Fast space. **Release dates remain [UNVERIFIED]** because the changelog shows no dates. Cohere SDK `cohere` 7.3.0. |
| C18 | **open_deep_research status** | 03: "archived 2026-08-21" | — | `gh api`: `archived=true`, last push 2026-08-10. The exact archive date is [UNVERIFIED]. The successor `langchain-ai/deepagents` has 30.5k stars and PyPI `deepagents` 0.7.32. |
| C19 | **Langfuse `as_type="retriever"`** | 06: "[UNVERIFIED]" | — | Verified. The supported values are event, span, generation, agent, tool, chain, **retriever**, evaluator, embedding and guardrail (Python SDK ≥3.3.1). Langfuse is now 5.0.4. |
| C20 | **RedisVL docs version** | 06: links the `/redisvl/0.14.0/` docs | — | PyPI **redisvl 0.28.0 (2026-10-09)**. Link the unversioned page https://redis.io/docs/latest/develop/ai/redisvl/user_guide/llmcache/ instead (HTTP 200). |

### Smaller accuracy notes
- **Lewis et al. 2020** "728-dimensional" (01): this is a typo in the paper; DPR outputs 768 dimensions. Keep 01's caveat.
- **sentence-transformers**: v6.0.0 was released **2026-08-18** (adds `MultiVectorEncoder`), and the latest is **v6.2.0, 2026-10-21**. Files 02 and 05 agree, and PyPI confirms it.
- **MCP spec 2026-07-28** (03): confirmed against the official changelog. The previous revision is `2025-11-25`. Changes: stateless (no `initialize`), `server/discover` MUST, sessions/`Mcp-Session-Id` removed, `subscriptions/listen`, MRTR `InputRequiredResult`, Roots/Sampling/Logging deprecated, Tasks moved to an extension, and `ttlMs`/`cacheScope` on list results.
- **Gemini Deep Research agent IDs** (03): confirmed as `deep-research-preview-04-2026` and `deep-research-max-preview-04-2026`. Default tools are google_search, url_context and code_execution; `mcp_server` and `file_search` can be added.
- **Gemini implicit-cache minimums** (02/05): confirmed at 4,096 for Gemini 4 Argon, 3.8/3.6 Flash and 3.1 Pro Preview, and 2,048 for 2.5 Flash/Pro. Explicit caching is "not supported for Gemini 4 Argon and onward" and **not supported in the Interactions API**. The 02/05 `client.caches.create` snippets therefore need `generate_content`, not `interactions`. They are correct as written, but add a footnote.
- **Agent Starter Pack**: the README says it is now in **maintenance mode**. New projects should use **`agents-cli`** (`uvx google-agents-cli setup`, PyPI `google-agents-cli` 1.11.0, 2026-10-20). Its `agentic_rag` template supports Vertex AI Search / Vector Search datastores.
- **Codelab URLs**: all 19 Google codelab URLs in 07 returned HTTP 200 (a fake codelab slug returns 404, so a 200 is meaningful). The Firestore yoga codelab timed out once and returned 200 on retry.
- **Version table re-check (PyPI, today):** langchain 1.4.7, langgraph 1.2.16, llama-index-core 0.14.25, haystack-ai 3.4.1, dspy 3.4.1, graphrag 3.3.0, neo4j-graphrag 1.22.0, lightrag-hku **1.5.7** (fills 04's gap), mem0ai 2.2.1, graphiti-core 0.31.2, trulens 2.16.0, arize-phoenix 20.26.0, colpali-engine 0.3.18 (deprecated), google-genai 2.33.0, google-cloud-agentplatform 2.6.0, openai 3.37.0, voyageai 0.5.0, nemoguardrails 0.24.1, presidio-analyzer 2.2.364, pylate 1.6.0.

---

## 2. Gap research: topics a complete course still lacks

### G1. RAG vs fine-tuning, and RAFT (the "why not just fine-tune?" slide)
- *Fine-Tuning or Retrieval? Comparing Knowledge Injection in LLMs*, Ovadia et al., arXiv **2312.05934** (Dec 2023). Quote: "RAG consistently outperforms it [unsupervised fine-tuning], both for existing knowledge encountered during training and entirely new knowledge"; "LLMs struggle to learn new factual information through unsupervised fine-tuning."
- *RAFT: Adapting Language Model to Domain Specific RAG*, Tianjun Zhang et al., arXiv **2403.10131** (Mar 2024). The model is trained with a question, an oracle doc and **distractor documents**, and learns to "ignore those documents that don't help". It answers with verbatim citations plus chain-of-thought. Gains on PubMed, HotpotQA and Gorilla. Code: github.com/ShishirPatil/gorilla.
- **Flow in words (RAFT data):** for each Q, P% of examples contain the oracle doc plus k distractors, and (1−P)% contain distractors only. The target is a CoT that quotes `##begin_quote##…##end_quote##` from the oracle, followed by the answer.
- **Teaching line:** fine-tune for *form and skill* (format, reading discipline, domain jargon). Retrieve for *facts* (fresh, citable, ACL-filtered).

### G2. Embedding / retriever fine-tuning (domain adaptation)
Use this when MTEB-best models still miss on your jargon. Hard-negative contrastive fine-tuning with sentence-transformers:
```python
# Adapted from https://sbert.net/docs/sentence_transformer/training_overview.html (sentence-transformers v6.x)
from datasets import load_dataset
from sentence_transformers import SentenceTransformer, SentenceTransformerTrainer
from sentence_transformers.losses import MultipleNegativesRankingLoss

model = SentenceTransformer("google/embeddinggemma-300m")
train = load_dataset("sentence-transformers/natural-questions", split="train[:10000]")  # (anchor, positive)
loss = MultipleNegativesRankingLoss(model)          # in-batch negatives = InfoNCE
trainer = SentenceTransformerTrainer(model=model, train_dataset=train, loss=loss)
trainer.train()
model.save_pretrained("my-domain-embedder")
```
(The trainer and loss names are the standard v3+ API. Before shipping, confirm the dataset ID and column names on the docs page [UNVERIFIED for v6 specifics].) Jason Liu's course (08) presents synthetic-question generation as the way to create (anchor, positive) pairs.

### G3. Sufficient context and abstention (why RAG still hallucinates)
- *Sufficient Context: A New Lens on Retrieval Augmented Generation Systems*, Hailey Joren et al. (Google), arXiv **2411.06037** (Nov 2024; ICLR 2025 [venue UNVERIFIED on the arXiv API]).
- Finding: large models (Gemini 1.5 Pro, GPT-4o, Claude 3.5) "excel… when the context is sufficient, but often output incorrect answers instead of abstaining when the context is not". Smaller models (Mistral 3, Gemma 2) "hallucinate or abstain often, even with sufficient context."
- Fix: an autorater labels whether the context is sufficient, and that label drives **selective generation**, so the model abstains when the context is insufficient. This gives **+2–10%** correct answers among the cases where the model responds.
- **Slide:** a 2x2 grid of (sufficient vs not) × (correct / hallucinate / abstain). This explains why "retrieval recall high, still wrong" happens.

### G4. Citations and grounding as first-class APIs
**Anthropic Citations** (GA on all active models): https://platform.claude.com/docs/en/build-with-claude/citations
```python
# Adapted from the Citations docs (Messages API)
import anthropic
client = anthropic.Anthropic()
resp = client.messages.create(
    model="claude-opus-5-5", max_tokens=1024,
    messages=[{"role": "user", "content": [
        {"type": "document",
         "source": {"type": "text", "media_type": "text/plain",
                    "data": "The grass is green. The sky is blue."},
         "title": "My Document", "citations": {"enabled": True}},
        {"type": "text", "text": "What color is the grass and sky?"}]}])
for block in resp.content:
    for c in (getattr(block, "citations", None) or []):
        print(c.type, repr(c.cited_text))   # char_location / page_location / content_block_location
```
- Facts: `cited_text` "does not count toward output tokens". The API guarantees "valid pointers to the provided documents". Custom RAG results can be passed as **`search_result` blocks**. Citations **cannot be combined with structured outputs** (the API returns a 400).

**Gemini Grounding with Google Search** (https://ai.google.dev/gemini-api/docs/google-search):
```python
from google import genai
client = genai.Client()
interaction = client.interactions.create(
    model="gemini-3.8-flash", input="Who won the euro 2024?",
    tools=[{"type": "google_search"}])
print(interaction.output_text)   # text annotations carry url_citation {url,title,start_index,end_index}
```
- Pricing (Gemini 3+): billed **per search query** the model runs. The first **5,000/month** are free, then **$14 per 1,000**. Search suggestions (`search_suggestions` HTML) must be displayed.

### G5. Context compression (between rerank and generate)
- *LLMLingua* (Jiang et al., arXiv 2310.05736, EMNLP 2023) and *LongLLMLingua* (arXiv 2310.06839, **ACL 2024**). On NaturalQuestions, LongLLMLingua gives "up to **21.4%**" better performance "with around **4x fewer tokens**" (GPT-3.5-Turbo), a **94.0%** cost reduction on LooGLE, and **1.4x–2.6x** latency speedup at 2x–6x compression of ~10k-token prompts.
- *RECOMP* (Xu et al., arXiv 2310.04408): extractive and abstractive compressors, plus "selective augmentation" that can return an empty summary.
```python
# Adapted from https://github.com/microsoft/LLMLingua README (pip install llmlingua; PyPI 0.2.2)
from llmlingua import PromptCompressor
compressor = PromptCompressor()   # default small LM scorer
out = compressor.compress_prompt(retrieved_chunks, question=query, target_token=500)
prompt = out["compressed_prompt"]
```
[Exact default model and argument list UNVERIFIED for 0.2.2; check the README.]

### G6. RAG serving efficiency: KV-cache reuse and speculative RAG
- *CacheBlend* (Yao et al., arXiv 2405.16444): reuses precomputed KV caches of retrieved chunks *even when they are not the prefix* and recomputes a small subset of tokens. This gives **TTFT 2.2–3.3x lower** and **throughput 2.8–5x higher** at the same quality. Code: github.com/LMCache/LMCache.
- *RAGCache* (Jin et al., arXiv 2404.12457): multilevel KV caching for RAG.
- *Speculative RAG* (Wang et al., arXiv 2407.08223, **ICLR 2025**): a small specialist model drafts answers in parallel from document subsets, and a large model verifies them in one pass. Up to **+12.97% accuracy and −50.83% latency** on PubHealth.
- Teaching line: provider prompt caching (02/05) is the **prefix** case. CacheBlend handles the **non-prefix** chunk case that RAG actually produces.

### G7. Vectorless / reasoning-based retrieval (the 2026 counter-trend)
- **PageIndex** (VectifyAI, 39.6k stars): an LLM navigates a hierarchical **tree index** of each document (a table of contents built from layout) and reasons to the relevant section. There are no embeddings and no chunking. The project reports **98.7% on FinanceBench** against ~50% for vector RAG; this is a self-reported result. `pip install -U pageindex`.
```python
# From https://github.com/VectifyAI/PageIndex README
from pageindex import PageIndexClient
client = PageIndexClient(index="gpt-6-luna", chat="gpt-6-sol")
doc_id = client.submit_document("report.pdf")["doc_id"]
print(client.chat("What was the 2023 operating margin?", doc_id=doc_id))
```
- Put it on a slide with 05's "grep beats vectors in agent harnesses" (arXiv 2605.15184) and 08's just-in-time retrieval (Anthropic context engineering). The common thread is that the **agent's reasoning becomes the retriever**.

### G8. First-principles lexical retrieval (missing math)
None of the files writes out BM25. Add it:
`score(D,Q) = Σ_{q∈Q} IDF(q) · f(q,D)·(k1+1) / ( f(q,D) + k1·(1 − b + b·|D|/avgdl) )`, with k1≈1.2–2.0 and b≈0.75 (Robertson & Zaragoza, "The Probabilistic Relevance Framework: BM25 and Beyond", 2009). Also add the lineage papers with verified IDs: **DPR** arXiv 2004.04906 (EMNLP 2020); **REALM** 2002.08909 (Feb 2020); **FiD** 2007.01282 (Izacard & Grave, Jul 2020); **RETRO** 2112.04426 (DeepMind, Dec 2021), which uses a 2T-token database and matches GPT-3 "despite using 25x fewer parameters".

### G9. Hallucination datasets and detectors
- *RAGTruth* (Niu et al., arXiv **2401.00396**, Dec 2023): a word-level hallucination corpus for RAG outputs, used to train detectors. Pair it with HHEM-2.1-Open (06) as a cheap guardrail judge.

### G10. Other single-bullet gaps worth one line in the deck
- **M3-Embedding / BGE-M3** (arXiv 2402.03216): one model produces dense, sparse *and* multi-vector outputs. This is a neat bridge between §2 and §3 of 02.
- **Hierarchical chunking eval:** *HiChunk* (arXiv 2509.11552, Sep 2025).
- **New Google codelab (missing from 07):** **"Using Google Gemini File Search Tool for RAG"**, https://codelabs.developers.google.com/gemini-file-search-for-rag. Repo: github.com/derailed-dash/gemini-file-search-demo. It goes from a google-genai SDK agent to an ADK root agent with **RagAgent (File Search) + SearchAgent (Google Search) as Agent-as-a-Tool**. Google Search and File Search on the same request return **400 INVALID_ARGUMENT**, which is the same "use by itself" constraint as `VertexAiRagRetrieval`. Model in `.env`: `gemini-2.5-flash`.
- **DSPy for RAG** (Khattab et al., arXiv 2310.03714; `dspy` 3.4.1): compile and optimize RAG prompts against a metric (MIPROv2/GEPA). Use it as a bridge from eval to optimization.

---

## 3. Most important numbers: final "slide-safe" list

| Claim | Value to print | Source |
|---|---|---|
| RAG-Sequence vs T5-11B closed-book, NQ EM | 44.5 vs 34.5 | arXiv 2005.11401 |
| Contextual Retrieval failure rate | 5.7 → 3.7 → 2.9 → 1.9% (−35/−49/−67%); top-150 → rerank (Cohere) → top-20; $1.02/M doc tokens | anthropic.com/news/contextual-retrieval (19 Sep 2024) |
| "Stuff it" threshold | < 200,000 tokens (~500 pages) | same |
| Lost in the Middle | GPT-3.5 mid-position 53.8%/50.5% < closed-book 56.1% | arXiv 2307.03172 |
| Context Rot | 18 models; shuffled > coherent; ~300-token focused > ~113k full | trychroma.com/research/context-rot |
| Search-R1 | +41% (7B), +20% (3B) [v5] | arXiv 2503.09516v5 |
| BrowseComp | 1,266 Qs; GPT-4o 0.6%, +browsing 1.9%, o1 9.9%, Deep Research 51.5%; humans 29.2% | arXiv 2504.12516 |
| Anthropic multi-agent | +90.2% vs single Opus 4; tokens explain 80% of variance; 4x / 15x tokens | anthropic.com/engineering/multi-agent-research-system |
| GraphRAG vs vector | 72–83% comprehensiveness win; C0 >97% fewer tokens | arXiv 2404.16130 |
| LazyGraphRAG | index cost 0.1% of GraphRAG; >700x cheaper query at comparable quality | MSR blog 25 Nov 2024 |
| HippoRAG 2 | 59.8 avg F1 vs 57.0 NV-Embed-v2 | arXiv 2502.14802 |
| BIRD / Spider 2.0 | top 82.95 vs human 92.96; Spider 2.0 o1-preview 21.3% | bird-bench.github.io; arXiv 2411.07763 |
| PoisonedRAG | 90% ASR with 5 texts per target | arXiv 2402.07867 |
| CaMeL | 77% AgentDojo tasks with provable security vs 84% undefended | arXiv 2503.18813 |
| Gemini Embedding 2 | 8,192 tok; 128–3072 dims; $0.20/M text | ai.google.dev model + pricing pages |
| MCP spec | 2026-07-28 (stateless) | modelcontextprotocol.io changelog |

---

## 4. Recommended 60-slide narrative arc (first principles → state of the art, Oct 2026)

**Section A. Why retrieval? (slides 1–6)**
1. Title: "RAG from first principles to agentic search (Oct 2026)". Show a timeline teaser from 2020 to 2026.
2. The frozen-brain problem: training cutoff, no citations, no private data, no ACLs.
3. Parametric vs non-parametric memory. Lewis 2020 quote "dense vector index of Wikipedia".
4. Lewis et al. 2020 architecture: DPR + BART, RAG-Sequence vs RAG-Token, 44.5 vs 34.5 EM.
5. Hot-swapping knowledge: 2016 → 2018 index (70% / 68% vs 12% / 4%).
6. RAG vs fine-tuning vs long context. Ovadia 2023 and RAFT (G1) set up the course's central trade-off.

**Section B. Lexical and dense retrieval foundations (slides 7–13)**
7. Lineage: TF-IDF → BM25 → DrQA → DPR → REALM → FiD → RETRO (G8).
8. BM25 formula, animated with k1 saturation and b length normalization.
9. Embeddings: contrastive training (InfoNCE), cosine/dot, asymmetric query/doc prompts.
10. 2026 embedding landscape: Gemini Embedding 2 (multimodal, $0.20/M), Qwen3-8B (open), Voyage 4, Cohere Embed 5, OpenAI 3-large. "MTEB sub-boards differ."
11. Matryoshka + quantization storage math: 123 GB → 0.96 GB.
12. ANN indexes: HNSW layers animation, IVF/PQ, DiskANN, ScaNN/SOAR, and the trade-off triangle.
13. Retrieval metrics: Recall@k, MRR, nDCG@10, plus Anthropic's "failure-rate" framing.

**Section C. Building the pipeline (slides 14–20)**
14. The canonical two-phase pipeline (offline index / online query) as the course's map.
15. Parsing: "garbage in". Docling 2.142, Unstructured, LlamaParse tiers, Gemini native PDF.
16. Chunking spectrum, ending on the Chroma eval table (recursive ~200 tokens, no overlap).
17. Late chunking vs Contextual Retrieval (0.708 → 0.825; 5.7 → 1.9%).
18. Parent-child / sentence-window / small-to-big.
19. Prompt assembly with citations: Anthropic Citations API and Gemini `url_citation` (G4).
20. Live demo: a minimal RAG in about 25 lines (Gemini File Search, 4 steps).

**Section D. Advanced retrieval (slides 21–28)**
21. Two retrievers, two blind spots: hybrid BM25 + dense.
22. RRF in 30 seconds (k=60, worked example, Qdrant code).
23. Learned sparse (SPLADE) and BGE-M3's dense + sparse + multi-vector in one model.
24. The interaction spectrum: bi-encoder → ColBERT MaxSim → cross-encoder.
25. Rerankers in 2026: Cohere Rerank 5 `relevant_spans`, Voyage rerank-3, Jina v3 listwise, Rank1 reasoning.
26. Query transforms zoo (multi-query, RAG-Fusion, HyDE, step-back, decomposition) plus the "measure end-to-end" caution (arXiv 2603.02153).
27. Metadata filtering and self-query. ACL filters are deterministic and server-side.
28. Context compression and ordering: LongLLMLingua 4x fewer tokens, lost-in-the-middle reorder (G5).

**Section E. Long context, caching and context engineering (slides 29–33)**
29. Lost in the Middle and Context Rot (shuffled > coherent; 300 tokens > 113k).
30. Self-Route / LaRA: "no silver bullet".
31. CAG and prompt caching economics (1.25x/2x write, 0.1x/0.05x read; Gemini implicit 4,096 minimum).
32. KV reuse beyond prefixes: CacheBlend and Speculative RAG (G6).
33. Context engineering: Write / Select / Compress / Isolate. RAG = Select.

**Section F. Structured and graph RAG (slides 34–40)**
34. Where vector RAG breaks: global and multi-hop questions.
35. GraphRAG indexing in 6 phases and the 4 query modes (global, local, DRIFT, basic).
36. LazyGraphRAG and LightRAG: cost curves (0.1%, >700x, incremental union).
37. HippoRAG 2 (PPR as memory) vs RAPTOR (summary tree).
38. The metric trap: LLM-judge win rate vs F1 (LightRAG ~50% vs 6.6).
39. Text-to-SQL is RAG over schema (BIRD 82.95 vs 92.96; Spider 2.0 21.3%). Neo4j Text2Cypher.
40. Vectorless reasoning retrieval: PageIndex tree search and grep-based agents (G7).

**Section G. Multimodal, code, memory (slides 41–46)**
41. "Your PDF is a picture": ColPali/ColQwen MaxSim heatmap, ViDoRe ladder 81.3 → 90.9, and the move to ST v6 `MultiVectorEncoder`.
42. Single-vector (Gemini Embedding 2) vs multi-vector storage trade-off (7.5 MB vs 311.5 MB).
43. Video and audio RAG: clip → embed or caption → timestamp citations (VideoRAG).
44. Code RAG: Cursor Merkle tree (4.03 h → 21 s), cAST chunking, grep vs vectors.
45. Agent memory: Letta / Mem0 / Zep-Graphiti / Memory Bank lifecycle, plus Graphiti time-travel.
46. Freshness: streaming / incremental indexing (Pathway, LangChain `index()` cleanup modes) and on-device (EmbeddingGemma 308M).

**Section H. Agentic RAG (slides 47–53)**
47. From pipeline to policy: classic vs agentic loop diagram.
48. Taxonomy (arXiv 2501.09136 v4): patterns, workflows, architectures.
49. Router and Adaptive-RAG; Self-RAG reflection tokens vs CRAG traffic light.
50. IRCoT / FLARE / DRAGIN: retrieval that is triggered during generation.
51. Build it: a LangGraph retrieve → grade → rewrite loop, and ADK `SequentialAgent[LoopAgent]` with sub-agents via AgentTool (google-adk 2.13.0).
52. MCP as the universal retrieval port (spec 2026-07-28, `search`/`fetch`, stateless).
53. Deep research systems: Gemini Deep Research agents, OpenAI (`gpt-5.6-sol`; o3-deep-research shut down 23 Jul 2026), Anthropic multi-agent (+90.2%, 15x tokens).

**Section I. Frontier: RL and test-time compute (slides 54–55)**
54. RL-trained searchers: Search-R1 rollout with masked `<information>` (+41%/+20%), R1-Searcher, DeepResearcher, ReasonIR.
55. Spending compute on retrieval: DRAG/IterDRAG near-linear scaling, best-of-N on BrowseComp, parallel subagents. BrowseComp bars (1.9% → 51.5%).

**Section J. Evaluate, operate, secure (slides 56–60)**
56. The RAG triad, sufficient context (G3), and RAGAS 0.4 collections / TruLens / ARES PPI.
57. Benchmark timeline: HotpotQA → KILT → BEIR → MMTEB → FRAMES → BrowseComp. Build a private golden set.
58. Observability and cost: OTel trace anatomy (Langfuse `as_type="retriever"`, Phoenix), semantic cache with tenant partitioning.
59. Threat model: indirect injection, PoisonedRAG 90%, ACL-aware retrieval, PII (Presidio), and defenses (Spotlighting, CaMeL 77/84).
60. Decision tree recap ("which RAG for which problem?") and where to learn next (RAG From Scratch, DLAI RAG + Knowledge Graphs for RAG + Agentic RAG, Hamel series, Google codelabs).

---

## 5. Slide ideas (from this critic pass)

1. **"Same paper, three numbers"**: Search-R1 v1 (+26%) → v3–v5 (+41%) shown as version cards flipping. A lesson in citing arXiv versions. Visual: card flip animation.
2. **"Sufficient context 2x2"** (G3): quadrants of sufficient/insufficient × answered/abstained, with dots that animate from "hallucinated" to "abstained" when selective generation turns on.
3. **"RAG vs fine-tune vs RAFT"**: three lanes. RAFT training example with oracle plus distractor docs, where distractors fade as the model learns to quote `##begin_quote##`.
4. **"Citations are an API now"**: a response with highlighted spans linked by lines to document char ranges (Anthropic `char_location`) and web `url_citation` (Gemini). Callout: "cited_text costs 0 output tokens".
5. **"Compress before you generate"**: a 10k-token context bar shrinking 4x (LongLLMLingua) with an accuracy needle *rising* (+21.4%).
6. **"Prefix vs non-prefix caching"**: stacked KV blocks. Provider prompt cache reuses only the prefix, while CacheBlend reuses every chunk block and recomputes a thin stripe (TTFT 2.2–3.3x).
7. **"Vectorless RAG"**: a document's table-of-contents tree where an LLM cursor descends branch by branch (PageIndex), contrasted with a cloud of embedding points.
8. **"Rename map 2026 (verified)"**: Vertex AI → Gemini Enterprise Agent Platform (22 Apr 2026); Vertex AI RAG Engine → RAG Engine (ADK: "Knowledge Engine"); Agent Engine → Agent Runtime; Vertex AI Search → Agent Search; explodinggradients/ragas → vibrantlabsai/ragas; Agent Starter Pack → agents-cli.
9. **"Deprecation watch"**: a strip of struck-through items (o3-deep-research shut down 23 Jul 2026; colpali-engine deprecated; ragas legacy metrics removed in v1.0; Gemini explicit caching unsupported on Gemini 4 Argon / Interactions API). Footer: "pin your SDK versions".

---

## Sources checked in this pass
- arXiv: 2503.09516 (v1, v3, v4, v5), 2605.27295, 2411.06037, 2403.10131, 2312.05934, 2310.05736, 2310.06839, 2310.04408, 2405.16444, 2404.12457, 2407.08223, 2401.00396, 2402.03216, 2509.11552, 2004.04906, 2002.08909, 2007.01282, 2112.04426, 2310.03714 (via export.arxiv.org API)
- https://www.trychroma.com/research/context-rot
- https://platform.claude.com/docs/en/build-with-claude/prompt-caching · https://platform.claude.com/docs/en/build-with-claude/citations
- https://ai.google.dev/gemini-api/docs/caching · /docs/pricing · /docs/models/gemini-embedding-2 · /docs/google-search · /docs/interactions/deep-research
- https://blog.google/innovation-and-ai/technology/developers-tools/file-search-gemini-api/
- https://modelcontextprotocol.io/specification/latest/changelog
- https://developers.openai.com/api/docs/guides/deep-research
- https://docs.cohere.com/changelog
- https://www.anthropic.com/news/contextual-retrieval
- https://adk.dev/integrations/knowledge-engine/ · https://adk.dev/integrations/google-search/
- https://docs.cloud.google.com/gemini-enterprise-agent-platform/release-notes
- https://codelabs.developers.google.com/gemini-file-search-for-rag · https://github.com/GoogleCloudPlatform/agent-starter-pack · https://github.com/VectifyAI/PageIndex
- https://langfuse.com/docs/observability/features/observation-types
- PyPI JSON API for all package versions; `gh api repos/...` for repo status and stars; curl HTTP status for all 19 codelab URLs in 07
