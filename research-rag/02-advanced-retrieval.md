# 02 — Advanced Retrieval: Hybrid, Sparse, Late-Interaction, Rerankers, Query Transforms, Contextual Retrieval, Long-Context vs RAG

Research date: 2026-10-23. Every item has been checked against a primary source unless it is marked [UNVERIFIED]. Versions are given where they matter.

---

## 0. The mental model: a retrieval funnel

```
query ──► [query transform] ──► [first stage: BM25 ‖ dense ‖ SPLADE] ──► fuse (RRF) ──► top-100/150
      ──► [rerank: cross-encoder / late-interaction / LLM] ──► top-5/20 ──► [order + compress] ──► LLM
                       ▲ metadata filters (self-query) apply inside the first stage
```
- **Recall** is decided at the first stage. Cheap, bi-encoder or inverted index, millions of docs.
- **Precision** is decided at the reranker. Expensive, sees query and doc together, about 100-1000 docs.
- **Use** is decided at context assembly. Position, distractors and length (lost-in-the-middle, context rot).

---

## 1. Hybrid search: BM25 + dense, fused with RRF

**Why hybrid.** Dense embeddings capture paraphrase ("car" ≈ "automobile"), but they miss exact tokens such as error codes, SKUs, names and rare acronyms. BM25 catches those exact tokens but misses synonyms. The two kinds of failure barely overlap, so combining them raises recall.

**Reciprocal Rank Fusion (primary source).**
- Paper: *"Reciprocal Rank Fusion outperforms Condorcet and individual Rank Learning Methods"*, G. V. Cormack, C. L. A. Clarke, S. Büttcher. SIGIR '09, Boston. http://cormack.uwaterloo.ca/cormacksigir09-rrf.pdf
- Formula: `RRFscore(d) = Σ_{r∈R} 1 / (k + r(d))`. The paper says "k = 60 was fixed during a pilot investigation and not altered during subsequent validation."
- Pilot table (MAP versus k): k=0 gives .2072, k=60 gives .2145, k=500 gives .2098. The curve is flat, so "the choice was not critical."
- Result: RRF "outperforms Condorcet, CombMNZ and the best system by 4% to 5% on average."
- Quotable: "RRF simply sorts the documents according to a naive scoring formula." It needs only ranks and ignores scores, so there is no score calibration problem between BM25 (unbounded) and cosine similarity (−1..1).

**Worked micro-example for a slide.** Doc A is rank 1 in BM25 and rank 3 in dense. Its score is 1/61 + 1/63 = 0.0323. Doc B is rank 2 in dense only, so its score is 1/62 = 0.0161. A wins.

**Score-based alternatives.**
- Weaviate: `relativeScoreFusion` (min-max normalise, then weight) has been the default since v1.24. `alpha` weights the two sides: 1 = pure vector, 0 = pure BM25, 0.5 = default. Docs: https://docs.weaviate.io/weaviate/concepts/search/hybrid-search
- Qdrant: DBSF (distribution-based score fusion) normalises each score list using mean ± 3σ and then sums. Added in v1.11.0.

**Code: Qdrant Query API, dense + sparse prefetch fused by RRF** (source: https://qdrant.tech/documentation/concepts/hybrid-queries/)
```python
from qdrant_client import QdrantClient, models
client = QdrantClient(url="http://localhost:6333")

results = client.query_points(
    collection_name="my_collection",
    prefetch=[
        models.Prefetch(query=models.SparseVector(indices=[1, 42], values=[0.22, 0.8]),
                        using="sparse", limit=20),
        models.Prefetch(query=[0.01, 0.45, 0.67], using="dense", limit=20),
    ],
    query=models.RrfQuery(rrf=models.Rrf(k=60)),   # k param since v1.16.0
    limit=10,
)
# Weighted RRF (v1.17.0+): models.Rrf(weights=[3.0, 1.0])
# DBSF:                    models.FusionQuery(fusion=models.Fusion.DBSF)
```
Gotcha from the docs: the prefetch `limit` must be ≥ the main `limit + offset`, otherwise the result can come back empty.

**Code: RRF from scratch (10 lines, for teaching)**
```python
def rrf(rankings: list[list[str]], k: int = 60) -> list[tuple[str, float]]:
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, doc_id in enumerate(ranking, start=1):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)

bm25 = ["A", "C", "D"]; dense = ["B", "D", "A"]
print(rrf([bm25, dense]))   # A and D rise because both lists agree on them
```

---

## 2. Learned sparse: SPLADE

- Paper: *"SPLADE: Sparse Lexical and Expansion Model for First Stage Ranking"*, T. Formal, B. Piwowarski, S. Clinchant. SIGIR '21 short paper. https://arxiv.org/abs/2107.05720
- Idea: a BERT MLM head projects each token onto the **whole vocabulary (30,522 dims)**. A log-saturation and a sparsity regulariser (FLOPS) keep only a few hundred non-zero weights. The result **expands** the text: a passage about "car" also gets weight on "vehicle" and "automobile". It is still an inverted-index vector, so it runs on Lucene/Elastic/OpenSearch/Qdrant sparse vectors.
- The paper's abstract: "explicit sparsity regularization and a log-saturation effect on term weights" give highly sparse representations. You trade effectiveness against efficiency by changing the regulariser.
- Why teach it: it sits between BM25 and dense. You get exact-match interpretability, because you can read the expansion terms, plus learned semantics.

**Code: Sentence Transformers `SparseEncoder`** (source: https://sbert.net/docs/sparse_encoder/usage/usage.html)
```python
from sentence_transformers import SparseEncoder

model = SparseEncoder("naver/splade-cocondenser-ensembledistil")
emb = model.encode(["The weather is lovely today.", "It's so sunny outside!",
                    "He drove to the stadium."])
print(emb.shape)                         # [3, 30522]  -> vocabulary-sized sparse vectors
print(model.similarity(emb, emb))
stats = SparseEncoder.sparsity(emb)
print(f"Sparsity: {stats['sparsity_ratio']:.2%}, active dims: {stats['active_dims']:.0f}")
```
Version note: `SparseEncoder` ships in sentence-transformers v5.x. v6.2.0 (21 Oct 2026) adds `SparseEncoder.merge` (GitHub releases page).

---

## 3. Late interaction: ColBERTv2

- Paper: *"ColBERTv2: Effective and Efficient Retrieval via Lightweight Late Interaction"*, K. Santhanam, O. Khattab, J. Saad-Falcon, C. Potts, M. Zaharia. NAACL 2022. https://arxiv.org/abs/2112.01488
- **Mechanism (diagram in words).** Each query token gets its own vector, and so does each doc token. For every query token, find the **max** cosine over all doc tokens (MaxSim), then **sum** across query tokens. That sum is the score. Docs are pre-encoded offline, which makes it "late" interaction. Bi-encoders give one vector per text (fast, lossy). Cross-encoders see full attention (accurate, slow). ColBERT sits in between.
- ColBERTv2 contributions: **residual compression** (centroid plus quantised residual) and **denoised supervision** (distillation from a cross-encoder). The footprint drops **6–10×** compared with ColBERTv1, and quality is state of the art both in-domain and out-of-domain (from the abstract).
- 2026 tooling:
  - **sentence-transformers v6.0.0 (18 Aug 2026)** adds `MultiVectorEncoder`, "a fourth model type alongside SentenceTransformer, CrossEncoder, and SparseEncoder". https://github.com/huggingface/sentence-transformers/releases
  - Qdrant supports native multivector fields (`using="colbert"`) and is commonly used for **reranking** dense-prefetched candidates.

**Code: MultiVectorEncoder** (source: sentence-transformers v6.0.0 release notes)
```python
from sentence_transformers import MultiVectorEncoder

model = MultiVectorEncoder("lightonai/LateOn")
q = model.encode_query(["Which planet is known as the Red Planet?"])
d = model.encode_document(["Mars, known for its reddish appearance, is often referred to as the Red Planet."])
scores = model.similarity(q, d)   # MaxSim
```
The model ID `lightonai/LateOn` comes from the release notes. I did not open its model card [UNVERIFIED details].

---

## 4. Visual late interaction: ColPali / ColQwen

- Paper: *"ColPali: Efficient Document Retrieval with Vision Language Models"*, M. Faysse, H. Sibille, T. Wu, B. Omrani, G. Viaud, C. Hudelot, P. Colombo. **ICLR 2025**. arXiv 2407.01449 (June 2024). https://arxiv.org/abs/2407.01449
- **Idea.** Skip OCR, layout parsing, chunking and captioning. Screenshot each PDF page and run it through a VLM (PaliGemma-3B = SigLIP-So400m + Gemma-2B). Every image patch becomes a 128-dim vector, and retrieval uses ColBERT MaxSim between query tokens and page patches. The abstract claims it "largely outperforms modern document retrieval pipelines while being drastically simpler, faster and end-to-end trainable." It also introduced the **ViDoRe** benchmark.
- HF blog (https://huggingface.co/blog/manu/colpali) says ColPali "outperforms all other evaluated systems, including baselines where a very strong proprietary Vision model (Claude Sonnet) is used to caption all visual elements."
- Model family (colpali README): `vidore/colpali-v1.3`, `vidore/colqwen2-v1.0`, `vidore/colqwen2.5-v0.2`, `vidore/colSmol-256M/500M`, plus third-party ColQwen3 checkpoints.
- **2026 status.** The README now says `colpali-engine` is **deprecated for new projects** and recommends **Sentence Transformers v6** (`MultiVectorEncoder` loads colpali models). https://github.com/illuin-tech/colpali
- Interpretability: query-token-to-patch similarity maps show *where* on the page the match occurred. This makes a great slide.

**Code: ColQwen2** (source: illuin-tech/colpali README)
```python
import torch
from colpali_engine.models import ColQwen2, ColQwen2Processor

model = ColQwen2.from_pretrained("vidore/colqwen2-v1.0", torch_dtype=torch.bfloat16,
                                 device_map="cuda:0").eval()
processor = ColQwen2Processor.from_pretrained("vidore/colqwen2-v1.0")

batch_images  = processor.process_images(page_images).to(model.device)   # list[PIL.Image]
batch_queries = processor.process_queries(["What was Q3 revenue by region?"]).to(model.device)
with torch.no_grad():
    img_emb = model(**batch_images)
    q_emb   = model(**batch_queries)
scores = processor.score_multi_vector(q_emb, img_emb)
```
Real-world uses: financial filings, slide decks, scanned manuals and insurance forms, where tables and charts carry the answer and OCR breaks them.

---

## 5. Rerankers

### 5.1 Cross-encoders (open)
A cross-encoder runs query and doc **together** through a transformer and outputs one relevance logit. You cannot precompute anything, so cost is O(N) forward passes per query. Use one to rerank the top 50–200 candidates.

**BGE** (BAAI): `BAAI/bge-reranker-v2-m3` (0.6B, multilingual). Larger LLM-based variants are `bge-reranker-v2-gemma` (gemma-2b) and `bge-reranker-v2-minicpm-layerwise` (selectable output layers 8–40). https://huggingface.co/BAAI/bge-reranker-v2-m3
```python
from FlagEmbedding import FlagReranker
reranker = FlagReranker('BAAI/bge-reranker-v2-m3', use_fp16=True)
scores = reranker.compute_score(
    [['what is panda?', 'hi'],
     ['what is panda?', 'The giant panda is a bear species endemic to China.']],
    normalize=True)          # sigmoid -> [0,1]
```

**Jina**: `jina-reranker-v3` has 0.6B parameters and is built on Qwen3-0.6B. It is a **listwise** reranker: up to 64 docs share one 131K context with causal attention. BEIR nDCG@10 is **61.94**. Paper published 29 Sep 2025. License is **CC BY-NC 4.0**. The model card recommends **jina-reranker-v3.5** for new projects. https://huggingface.co/jinaai/jina-reranker-v3

### 5.2 Hosted rerank APIs (state as of Oct 2026)
**Cohere.** Models: `rerank-v5.0-pro`, `rerank-v5.0-fast` (32k context, 100+ languages), `rerank-v4.0-pro/fast` (32k), and `rerank-v3.5` (4k). Rerank 5 adds **`relevant_spans`**, which returns the spans of each document that drove the score. Docs: https://docs.cohere.com/docs/rerank and https://docs.cohere.com/reference/rerank. Release date of Rerank 5: 21 Oct 2026 according to aggregators [UNVERIFIED against Cohere's own blog].
```python
import cohere
co = cohere.ClientV2()
resp = co.rerank(
    model="rerank-v5.0-pro",
    query="What is the capital of the United States?",
    documents=["Carson City is the capital city of Nevada.",
               "Washington, D.C. is the capital of the United States.",
               "Capital gains are profits from the sale of an asset."],
    top_n=2,
    relevant_spans={"mode": "enabled", "threshold": 0.1, "max_spans": 3},  # v5+
)
for r in resp.results:
    print(r.index, r.relevance_score)
```
**Voyage AI.** Current models are `rerank-3` and `rerank-3-lite` (32K tokens). Legacy models are `rerank-2.5/-lite` and `rerank-2/-lite`. Release date 2026-09-30 per OpenRouter listings. The claimed +2.14% over Cohere Rerank v4.0 Pro across 93 datasets is [UNVERIFIED, vendor claim via aggregator]. https://docs.voyageai.com/docs/reranker
```python
import voyageai
vo = voyageai.Client()            # VOYAGE_API_KEY
r = vo.rerank(query, documents, model="rerank-3", top_k=3)
for x in r.results:
    print(x.index, x.relevance_score, x.document[:60])
```

### 5.3 LLM rerankers
- *"Is ChatGPT Good at Search? Investigating Large Language Models as Re-Ranking Agents"* (RankGPT), Sun et al., **EMNLP 2023**. https://arxiv.org/abs/2304.09542. The LLM outputs a **permutation** of passage IDs (listwise), and a sliding window handles long lists. The abstract reports that "a distilled 440M model outperforms a 3B supervised model on the BEIR benchmark".
- Pointwise (score each doc 0–10) is simple and parallel. Listwise (rank them all) is better calibrated but sensitive to position. The 2025–26 trend is small **listwise** models (Jina v3) and **reasoning rerankers**. BRIGHT is the reasoning-intensive retrieval benchmark that vendors now cite.

### 5.4 Practical rules
- Retrieve wide, then rerank narrow. Anthropic's setup retrieves **150**, reranks, and keeps **20**.
- Reranking adds latency: one API round-trip, or one GPU forward pass per pair. Cap the candidate count, and keep doc length ≤ `max_tokens_per_doc` (Cohere default 4096).

---

## 6. Query transformations

| Technique | Source | One-line mechanism |
|---|---|---|
| **Multi-query** | LangChain `MultiQueryRetriever` | LLM writes N paraphrases, retrieve each, return the unique union |
| **RAG-Fusion** | Raudaschl (blog + https://github.com/Raudaschl/rag-fusion); Rackauckas, *"RAG-Fusion: a New Take on Retrieval-Augmented Generation"*, arXiv 2402.03367 (2024) | Multi-query + **RRF** (k=60) instead of a plain union |
| **HyDE** | Gao, Ma, Lin, Callan, *"Precise Zero-Shot Dense Retrieval without Relevance Labels"*, arXiv 2212.10496 (Dec 2022; ACL 2023) | LLM writes a *hypothetical answer document*, which is embedded *instead of the question*. The encoder's "dense bottleneck" filters out the hallucinated details |
| **Step-back** | Zheng et al. (Google DeepMind), *"Take a Step Back: Evoking Reasoning via Abstraction in LLMs"*, arXiv 2310.06117, ICLR 2024 | Ask a more general question first ("what principle governs X?"), retrieve for both. PaLM-2L gains: MMLU Physics +7%, Chemistry +11%, TimeQA +27%, MuSiQue +7% |
| **Decomposition** | Least-to-Most (Zhou et al., arXiv 2205.10625, 2022); Self-Ask (Press et al., arXiv 2210.03350, 2022) | Split a multi-hop question into sub-questions and answer them sequentially or in parallel. This is the seed of agentic RAG |

**Code: multi-query** (source: `langchain_classic/retrievers/multi_query.py`; langchain-classic 1.0.8 on PyPI)
```python
from langchain_classic.retrievers.multi_query import MultiQueryRetriever
from langchain_google_genai import ChatGoogleGenerativeAI   # any chat model works

mq = MultiQueryRetriever.from_llm(
    retriever=vectorstore.as_retriever(search_kwargs={"k": 5}),
    llm=ChatGoogleGenerativeAI(model="gemini-2.5-flash"),
    include_original=True,           # default False
)
docs = mq.invoke("How do I rotate API keys without downtime?")
```
The default prompt (verbatim from source) says: "generate 3 different versions of the given user question ... to help the user overcome some of the limitations of distance-based similarity search." Note: in LangChain 1.x these retrievers moved to `langchain_classic`. The older import was `langchain.retrievers.multi_query`.

**Code: HyDE in about 8 lines (framework-free)**
```python
def hyde_search(question, llm, embed, index, k=5):
    fake_doc = llm(f"Write a short passage that answers the question.\nQuestion: {question}\nPassage:")
    vec = embed(fake_doc)                 # embed the *answer-shaped* text
    return index.search(vec, k)           # real docs near the hypothetical one
```

**Evidence against overusing them (2026).** *"Scaling Retrieval Augmented Generation with RAG Fusion: Lessons from an Industry Deployment"*, Medrano, Verma, Chhabra, arXiv 2603.02153 (2 Mar 2026). Fusion raised raw recall, but "gains mostly disappear after re-ranking and context truncation". Hit@10 fell from 0.51 to 0.48 in some configurations. Quote: "retrieval-level improvements do not reliably translate into end-to-end gains." The teaching point: **measure end-to-end, not recall@k alone.**

---

## 7. Metadata filtering and self-query

- **Metadata filtering**: run structured predicates (`year >= 2024 AND dept = "legal" AND acl CONTAINS user`) together with the vector search. Pre-filtering (filter inside the ANN search) keeps `k` results. Post-filtering can return fewer than k. Every major vector DB supports payload/metadata filters: Qdrant `Filter`, Pinecone `filter`, Weaviate `Filter.by_property`, pgvector `WHERE`.
- **Security**: tenant and ACL filters must be applied **server-side and deterministically**. Never let an LLM decide them.
- **Self-query**: an LLM turns the natural-language request into `(semantic query, structured filter, limit)`. Example: "sci-fi movies rated above 8.5 from the 90s" becomes query="sci-fi", filter=`rating > 8.5 AND 1990 <= year < 2000`.

**Code** (source: `langchain_classic/retrievers/self_query/base.py`, `chains/query_constructor/schema.py`)
```python
from langchain_classic.retrievers.self_query.base import SelfQueryRetriever
from langchain_classic.chains.query_constructor.schema import AttributeInfo

fields = [
    AttributeInfo(name="genre",  description="Movie genre", type="string"),
    AttributeInfo(name="year",   description="Release year", type="integer"),
    AttributeInfo(name="rating", description="IMDb rating 1-10", type="float"),
]
retriever = SelfQueryRetriever.from_llm(
    llm, vectorstore, document_contents="Brief summary of a movie",
    metadata_field_info=fields, enable_limit=True)
retriever.invoke("two highly rated sci-fi films from the 1990s")
```
Internally, the LLM emits a `StructuredQuery`, and a per-vector-store `Visitor` translator converts it into native filter syntax.

---

## 8. Anthropic Contextual Retrieval (Sep 19, 2024): the numbers

Source: https://www.anthropic.com/news/contextual-retrieval (cookbook: github.com/anthropics/anthropic-cookbook, `skills/contextual-embeddings`).

- **Problem**: "traditional RAG solutions remove context when encoding information." A chunk like "The company's revenue grew by 3% over the previous quarter" does not say *which* company or *which* quarter.
- **Fix**: before indexing, have an LLM write **50–100 tokens of chunk-specific context** and prepend it to the chunk. The augmented text goes to **both** the embedding model (Contextual Embeddings) and the BM25 index (Contextual BM25).
- Prompt core (Claude 3 Haiku): the full doc goes in `<document>`, the chunk in `<chunk>`, followed by "Please give a short succinct context to situate this chunk within the overall document ... Answer only with the succinct context and nothing else."
- **Cost**: about **$1.02 per million document tokens**, one-time. That assumes 800-token chunks, 8k-token docs, 50 tokens of instructions and 100 tokens of context per chunk, and it relies on **prompt caching** so the doc is read once and cached for every chunk.

| Configuration (top-20 retrieval failure rate) | Failure rate | Reduction |
|---|---|---|
| Baseline (standard chunk embeddings; exact baseline config per blog appendix) | 5.7% | — |
| Contextual Embeddings | 3.7% | **−35%** |
| Contextual Embeddings + Contextual BM25 | 2.9% | **−49%** |
| + Reranking (retrieve 150 → keep 20) | 1.9% | **−67%** |

- Quote: "All these benefits stack."
- Quote/guideline: "If your knowledge base is smaller than 200,000 tokens", skip RAG and put it all in the prompt with caching. Latency drops by more than 2× and cost by up to 90%.

**Code sketch** (adapted from the blog prompt; Anthropic SDK)
```python
import anthropic
client = anthropic.Anthropic()

def situate(doc: str, chunk: str) -> str:
    msg = client.messages.create(
        model="claude-haiku-4-5", max_tokens=150,
        system=[{"type": "text", "text": f"<document>\n{doc}\n</document>",
                 "cache_control": {"type": "ephemeral"}}],          # doc cached across chunks
        messages=[{"role": "user", "content":
            f"Here is the chunk we want to situate within the whole document\n<chunk>\n{chunk}\n</chunk>\n"
            "Please give a short succinct context to situate this chunk within the overall document "
            "for the purposes of improving search retrieval of the chunk. "
            "Answer only with the succinct context and nothing else."}])
    return msg.content[0].text + "\n\n" + chunk     # index THIS for both dense and BM25
```
(The model ID here is illustrative. The blog used Claude 3 Haiku.)

---

## 9. Long context vs RAG (2024 → 2026)

- **Lost in the Middle**. *"Lost in the Middle: How Language Models Use Long Contexts"*, N. F. Liu, K. Lin, J. Hewitt, A. Paranjape, M. Bevilacqua, F. Petroni, P. Liang. TACL (accepted 2023; published 2024). https://arxiv.org/abs/2307.03172
  - "performance is often highest when relevant information occurs at the beginning or end of the input context". The curve is U-shaped.
  - Striking number: GPT-3.5-Turbo with 20 or 30 docs and the answer in the middle scored **53.8% / 50.5%**, *below* its **closed-book 56.1%**. Adding the documents made it worse than giving none.
  - Practical fix: put the best reranked chunks first and last (LangChain's `LongContextReorder` does this), and send fewer chunks.
- **Self-Route**. *"Retrieval Augmented Generation or Long-Context LLMs? A Comprehensive Study and Hybrid Approach"*, Z. Li, C. Li, M. Zhang, Q. Mei, M. Bendersky (Google DeepMind). EMNLP 2024 Industry. https://arxiv.org/abs/2407.16833. Long context "consistently outperforms RAG in terms of average performance" when resourced, but RAG is far cheaper. **Self-Route** lets the model decide whether RAG context is sufficient and falls back to long context only when it is not. Performance stays comparable at much lower cost.
- **LaRA**. *"LaRA: Benchmarking Retrieval-Augmented Generation and Long-Context LLMs – No Silver Bullet for LC or RAG Routing"*, Kuan Li et al. (Alibaba, Penn State). **ICML 2025**. arXiv 2502.09977. 2,326 cases and 11 LLMs. The best choice depends on model capability, context length, task type and retrieval characteristics.
- **Context Rot**. Chroma technical report, *"Context Rot: How Increasing Input Tokens Impacts LLM Performance"*, 14 Jul 2025. https://www.trychroma.com/research/context-rot. 18 models (Claude Opus 4/Sonnet 4…, o3/GPT-4.1…, Gemini 2.5 Pro/Flash, Qwen3).
  - Models "do not use their context uniformly"; "performance grows increasingly unreliable as input length grows."
  - LongMemEval: **~300-token focused prompts beat ~113k-token full prompts across every model family**.
  - "Even a single distractor reduces performance relative to the baseline."
  - Surprising: shuffled haystacks beat coherent ones.
- **Synthesis for 2026.** It is not "RAG vs long context" but **RAG *into* long context**. Retrieve and rerank to a focused set, then use the large window for breadth and caching. Under ~200k tokens and a static corpus, stuff the context and cache it. For large, dynamic or permissioned corpora, retrieve. For multi-hop work, go agentic (iterate).

---

## 10. Context caching: the enabler for "stuff it" and for Contextual Retrieval

**Anthropic prompt caching** (https://platform.claude.com/docs/en/build-with-claude/prompt-caching, read 2026-10-23)
- Cache write costs 1.25× base input (5-min TTL, the default) or 2× (1-hour TTL, `"ttl": "1h"`). Cache reads cost 0.1× base for most models, and less on the newest (0.05× on Opus/Sonnet 5.5).
- Up to **4 breakpoints** per request. **Automatic caching** works through a top-level `cache_control`. Minimum cacheable length is model-dependent: 512–4,096 tokens.
```python
resp = client.messages.create(
    model="claude-opus-5-5", max_tokens=1024,
    system=[{"type": "text", "text": BIG_KNOWLEDGE_BASE,
             "cache_control": {"type": "ephemeral", "ttl": "1h"}}],
    messages=[{"role": "user", "content": question}])
print(resp.usage.cache_read_input_tokens)
```

**Gemini context caching** (https://ai.google.dev/gemini-api/docs/caching and https://ai.google.dev/gemini-api/docs/generate-content/caching)
- **Implicit caching** is on by default for Gemini 2.5+. The minimum is 2,048 tokens for 2.5 Flash/Pro and 4,096 for 3.x/4. Check `usage_metadata` for cached tokens.
- **Explicit caching** (`client.caches.create`) uses the generateContent API v1beta and has a default TTL of **1 hour**. Storage is billed per TTL duration. The docs say it is **not supported on Gemini 4 Argon and later**, which use implicit caching only.
```python
from google import genai
from google.genai import types
client = genai.Client()
cache = client.caches.create(
    model="models/gemini-3.8-flash",
    config=types.CreateCachedContentConfig(
        display_name="handbook", system_instruction="Answer only from the handbook.",
        contents=[client.files.upload(file="handbook.pdf")], ttl="3600s"))
r = client.models.generate_content(model="models/gemini-3.8-flash",
        contents="What is the parental-leave policy?",
        config=types.GenerateContentConfig(cached_content=cache.name))
```
Model names are taken verbatim from the current Gemini docs page.

---

## 11. Real-world examples
- **Anthropic**: Contextual Retrieval with prompt caching, published with a cookbook. Its benchmark corpora were codebases, fiction, ArXiv papers and science papers [as described in the blog appendix; the domain list is UNVERIFIED in this pass].
- **Elastic / OpenSearch / Weaviate / Qdrant / Pinecone** all ship native hybrid + RRF. Elasticsearch has an `rrf` retriever [UNVERIFIED version].
- **Cohere Rerank** is available on AWS Marketplace/Bedrock and Azure. It is the typical drop-in "second stage" for enterprise search.
- **ColPali-style visual RAG** is used for PDFs that are mostly tables and charts, such as financial reports, slide decks and technical manuals. The ViDoRe benchmark covers these domains.
- **Industry caution**: the 2026 RAG-Fusion deployment paper (arXiv 2603.02153) found fusion added latency with no end-to-end gain once a reranker was present.

---

## 12. Quotable lines (with source)
- "RRF simply sorts the documents according to a naive scoring formula." — Cormack et al., SIGIR 2009
- "traditional RAG solutions remove context when encoding information." — Anthropic, Contextual Retrieval, 2024
- "All these benefits stack." — Anthropic, Contextual Retrieval
- "performance is often highest when relevant information occurs at the beginning or end of the input context" — Liu et al., Lost in the Middle
- "performance grows increasingly unreliable as input length grows." — Chroma, Context Rot, 2025
- "retrieval-level improvements do not reliably translate into end-to-end gains" — Medrano et al., 2026

---

## 13. Slide ideas (8)

1. **"Two retrievers, two blind spots"**: a Venn diagram of BM25 hits vs dense hits for 3 queries ("error E1023", "how to make the car faster", "Q3 revenue ACME"). Animate the union lighting up after hybrid.
2. **"RRF in 30 seconds"**: two ranked columns side by side. Animate each doc sliding into a fused column while its `1/(60+rank)` scores add up live. Show the k-insensitivity table (MAP .2072 → .2145 → .2098) as a tiny sparkline.
3. **"Sparse vs Dense vs Learned-sparse"**: three vector visualisations. A BM25 bag of exact words, a dense 768-d heatmap strip, and a SPLADE 30,522-d bar chart where expansion terms ("vehicle", "automobile") appear in a different colour.
4. **"The interaction spectrum"**: bi-encoder → ColBERT MaxSim → cross-encoder, with an attention-grid animation (no interaction / token-max / full attention) and a cost-vs-quality axis.
5. **"ColPali sees the page"**: a PDF page with a patch grid, a query, and a heatmap overlay of MaxSim per patch. Contrast it with the OCR → layout → chunk → embed pipeline shown crossed out.
6. **"The retrieval funnel"**: a funnel graphic with 1M docs → 150 (hybrid) → 20 (rerank) → 5 (in prompt), latency per stage on the side, and Cohere/Voyage/BGE/Jina logos at the rerank stage.
7. **"Query transforms zoo"**: a 5-card grid (Multi-query, RAG-Fusion, HyDE, Step-back, Decomposition), each with an input → LLM → output mini-flow. A footer callout says "measure end-to-end" (arXiv 2603.02153 Hit@10 0.51 → 0.48).
8. **"Contextual Retrieval, by the numbers"**: an animated bar chart of failure rate 5.7 → 3.7 → 2.9 → 1.9%, with a before/after chunk card ("revenue grew 3%" → "From ACME's Q2 2023 10-Q…"). Show the $1.02/M tokens badge.
9. **"Lost in the middle / context rot"**: a U-shaped accuracy curve over position with the closed-book 56.1% line crossing it. Then Chroma's "300 tokens beat 113k tokens" bar.
10. **"Long context or RAG? A 2026 decision tree"**: corpus < 200k and static → stuff + cache. Large, dynamic or ACL'd → hybrid + rerank. Multi-hop → agentic/Self-Route. Annotate it with the caching price multipliers (write 1.25×/2×, read 0.1×).

---

## Sources (primary)
- Cormack, Clarke, Büttcher, SIGIR 2009: http://cormack.uwaterloo.ca/cormacksigir09-rrf.pdf
- Qdrant hybrid queries: https://qdrant.tech/documentation/concepts/hybrid-queries/
- Weaviate hybrid search: https://docs.weaviate.io/weaviate/concepts/search/hybrid-search
- SPLADE: https://arxiv.org/abs/2107.05720 · SparseEncoder docs: https://sbert.net/docs/sparse_encoder/usage/usage.html
- ColBERTv2: https://arxiv.org/abs/2112.01488 · sentence-transformers releases: https://github.com/huggingface/sentence-transformers/releases
- ColPali: https://arxiv.org/abs/2407.01449 · https://github.com/illuin-tech/colpali · https://huggingface.co/blog/manu/colpali
- Cohere Rerank: https://docs.cohere.com/docs/rerank · https://docs.cohere.com/reference/rerank
- Voyage reranker: https://docs.voyageai.com/docs/reranker
- Jina reranker v3: https://huggingface.co/jinaai/jina-reranker-v3 · BGE: https://huggingface.co/BAAI/bge-reranker-v2-m3
- RankGPT: https://arxiv.org/abs/2304.09542
- HyDE: https://arxiv.org/abs/2212.10496 · Step-back: https://arxiv.org/abs/2310.06117 · RAG-Fusion: https://arxiv.org/abs/2402.03367, https://github.com/Raudaschl/rag-fusion · RAG-Fusion industry: https://arxiv.org/abs/2603.02153
- LangChain source: https://github.com/langchain-ai/langchain/tree/master/libs/langchain/langchain_classic/retrievers
- Anthropic Contextual Retrieval: https://www.anthropic.com/news/contextual-retrieval
- Lost in the Middle: https://arxiv.org/abs/2307.03172 · Self-Route: https://arxiv.org/abs/2407.16833 · LaRA: https://arxiv.org/abs/2502.09977 · Context Rot: https://www.trychroma.com/research/context-rot
- Anthropic prompt caching: https://platform.claude.com/docs/en/build-with-claude/prompt-caching · Gemini caching: https://ai.google.dev/gemini-api/docs/generate-content/caching
