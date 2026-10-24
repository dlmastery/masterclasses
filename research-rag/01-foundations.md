# 01 — RAG Foundations: Why RAG, Ingestion, Chunking, Embeddings, Vector Indexes, Metrics

Research date: 2026-10-23. Sources were fetched live on that date unless marked otherwise. [UNVERIFIED] means I could not confirm the item from a primary source. Leaderboard ranks change weekly, so check the live board before you put a rank on a slide.

---

## 1. Why RAG? The core argument

**The problem with parametric-only LLMs**
- Knowledge is frozen at the training cutoff, and updating it means retraining or fine-tuning.
- The model can't cite where an answer came from, which makes hallucination hard to audit.
- Private, proprietary or fast-changing data (tickets, contracts, inventory) was never in the training set.
- Access control can't be enforced per user inside model weights.

**The RAG answer:** keep knowledge in an external, swappable, permission-filterable index. At query time, retrieve the top-k relevant passages and condition generation on them. This gives you fresh data, citations, per-user ACL filtering, and much cheaper updates (re-index instead of retrain).

**Diagram in words (canonical two-phase pipeline):**
```
OFFLINE / INDEXING:  Sources -> Parse (layout, tables, OCR) -> Chunk -> (Contextualize) -> Embed -> Vector index (+ BM25 index, + metadata)
ONLINE / QUERY:      User query -> (rewrite) -> Embed query -> ANN search top-k (+ BM25, fuse) -> (rerank) -> Prompt = instructions + chunks + query -> LLM -> Answer + citations
```

---

## 2. The origin paper: Lewis et al. 2020

- **Title:** "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks". arXiv:2005.11401, submitted 22 May 2020 (v4: 12 Apr 2021). **NeurIPS 2020.** https://arxiv.org/abs/2005.11401
- **Authors:** Patrick Lewis, Ethan Perez, Aleksandra Piktus, Fabio Petroni, Vladimir Karpukhin, Naman Goyal, Heinrich Küttler, Mike Lewis, Wen-tau Yih, Tim Rocktäschel, Sebastian Riedel, Douwe Kiela (Facebook AI Research, UCL, NYU).
- **Architecture:** a DPR retriever (BERT bi-encoder, query encoder fine-tuned, document index frozen) plus a BART-large generator (~400M params). The index holds 21M Wikipedia passages of 100 words each, searched with MIPS through FAISS. The paper text gives the vectors as "728-dimensional"; DPR's BERT-base actually outputs 768 dims, so treat 728 as a probable typo. [paper-text detail]
- **Two variants:**
  - **RAG-Sequence:** the same retrieved document conditions the whole output sequence; probabilities are marginalized over the top-k documents.
  - **RAG-Token:** a different document can drive each generated token.
- **Quotable line (abstract):** the "non-parametric memory is a dense vector index of Wikipedia." The paper combines "pre-trained parametric and non-parametric memory."
- **Table 1, open-domain QA exact match (test)** (via ar5iv render of the paper):

| Model | NQ | TQA (Wiki split) | WebQ | CuratedTrec |
|---|---|---|---|---|
| T5-11B closed-book | 34.5 | 50.1 | 37.4 | – |
| T5-11B + SSM | 36.6 | 60.5 | 44.7 | – |
| REALM | 40.4 | – | 40.7 | 46.8 |
| DPR | 41.5 | – | 41.1 | 50.6 |
| **RAG-Token** | 44.1 | 66.1 | **45.5** | 50.0 |
| **RAG-Sequence** | **44.5** | **68.0** | 45.2 | **52.2** |

- **Teaching point:** a ~400M-parameter generator plus retrieval beats closed-book T5-11B, a model about 27x larger.
- **Jeopardy human eval (factuality):** RAG better 42.7%, BART better 7.1%, both good 11.7%.
- **Hot-swapping knowledge (key slide):** "we can update RAG's world knowledge by simply replacing its non-parametric memory." With the 2016 index, 70% of 2016 world-leader questions were answered correctly; with the 2018 index, 68% of 2018 questions. Mismatched index/year pairs fell to 12% and 4%.
- **Lineage:** DrQA (2017, retrieve-and-read), ORQA (2019), REALM (Guu et al., 2020, retrieval during pre-training), DPR (Karpukhin et al., 2020), then RAG (2020), then FiD, RETRO (2021), and today's prompt-stuffing RAG with frozen LLMs and agentic RAG.

---

## 3. Ingestion and parsing: garbage in, garbage out

Parsing quality is usually the biggest hidden lever. Tables, multi-column layouts, headers and footers, scanned pages and charts break naive `pdftotext`.

### 3.1 Docling (IBM Research to LF AI & Data)
- Repo: https://github.com/docling-project/docling. **MIT license** (individual models may carry their own licenses). Hosted by the **LF AI & Data Foundation**; started by IBM Research Zurich.
- Formats: PDF, DOCX, PPTX, XLSX, HTML, EPUB, images, audio, email, LaTeX, and more. Exports to Markdown, HTML, JSON (DoclingDocument).
- Features: layout and reading-order analysis, table structure recognition, code and formula handling, OCR, a VLM pipeline (**GraniteDocling**), local or air-gapped runs, an MCP server, and integrations with LangChain, LlamaIndex, CrewAI and Haystack.
- Requires Python 3.10+ (3.9 support was dropped in v2.70.0). Current exact version: [UNVERIFIED; check PyPI].
- Tech report: arXiv:2408.09869 ("Docling Technical Report", 2024).

```python
# Source: https://github.com/docling-project/docling (README quickstart)
from docling.document_converter import DocumentConverter

source = "https://arxiv.org/pdf/2408.09869"  # local path or URL
converter = DocumentConverter()
result = converter.convert(source)
print(result.document.export_to_markdown())
```
CLI: `docling https://arxiv.org/pdf/2206.01062` and, for the VLM pipeline, `docling --pipeline vlm --vlm-model granite_docling <url>`.

### 3.2 Unstructured
- Open source plus a hosted platform. Partitions documents into typed **elements** (`Title`, `NarrativeText`, `Table`, `ListItem`...), then chunks them along element boundaries.
- Chunking docs: https://docs.unstructured.io/open-source/core-functionality/chunking
  - Strategies (open source): `basic` and `by_title`. `by_title` closes a chunk at each `Title`, so a chunk never spans two sections.
  - Parameters: `max_characters` (hard max, default 500), `new_after_n_chars` (soft max), `overlap` (default 0), `overlap_all`, `combine_text_under_n_chars`, `multipage_sections`.
  - Tables are always isolated into their own chunks. The original elements are kept in `chunk.metadata.orig_elements`.
```python
# Source: https://docs.unstructured.io/open-source/core-functionality/chunking
from unstructured.partition.html import partition_html

chunks = partition_html(url=url, chunking_strategy="basic")
# or chunking_strategy="by_title", max_characters=1500, new_after_n_chars=1000
```

### 3.3 LlamaParse (LlamaIndex)
- Docs: https://developers.llamaindex.ai/python/cloud/llamaparse/. "Parse" is a product on the LlamaParse platform. The v1 API is deprecated in favor of v2, which has a migration guide.
- **Tiers:** `fast` (text and spatial text only, no markdown), `cost_effective`, `agentic`, `agentic_plus` (hardest documents).
- The SDK still uses the LlamaCloud names (`from llama_cloud import LlamaCloud`, env var `LLAMA_CLOUD_API_KEY`).
```python
# Adapted from https://developers.llamaindex.ai/python/cloud/llamaparse/ (v2 API)
from llama_cloud import LlamaCloud

client = LlamaCloud()  # reads LLAMA_CLOUD_API_KEY
f = client.files.create(file=open("10k.pdf", "rb"), purpose="parse")
result = client.parsing.parse(
    file_id=f.id, tier="agentic", version="latest", expand=["markdown"],
)
print(result.markdown.pages[0].markdown)  # field path [UNVERIFIED]; check docs
```
(The step sequence of upload, `parsing.parse(tier=..., version="latest", expand=["markdown"])`, and printing the first page's markdown is from the docs. The exact argument and field names for `file_id` and the result are [UNVERIFIED].)

### 3.4 Gemini native document understanding ("parse with the LLM")
- Docs: https://ai.google.dev/gemini-api/docs/document-processing
- Limits: **1,000 pages per PDF**, **50 MB** per file, and each page counts as **258 tokens**. The Files API is free and keeps files for 48 h. Gemini 3 adds a `media_resolution` parameter.
- Two uses: (a) a VLM converts PDF pages to Markdown/JSON for chunking; (b) **skip chunking** for small corpora and put the whole PDF in context (long-context vs RAG trade-off slide).
```python
# Source: https://ai.google.dev/gemini-api/docs/document-processing (as fetched 2026-10-23;
# the page currently shows the Interactions API and the model id below)
from google import genai
import base64

client = genai.Client()
pdf_bytes = open("path/to/document.pdf", "rb").read()
interaction = client.interactions.create(
    model="gemini-3.8-flash",
    input=[
        {"type": "document", "data": base64.b64encode(pdf_bytes).decode("utf-8"),
         "mime_type": "application/pdf"},
        {"type": "text", "text": "Convert to Markdown; render tables as Markdown tables."},
    ],
)
print(interaction.output_text)
```
- Also relevant: **Gemini Embedding 2** embeds PDFs directly (up to 6 pages per request), which enables "no-parse" multimodal retrieval (see §5). ColPali-style visual retrieval goes in a later deck section.

**Practical rule:** use a cheap layout parser (Docling/Unstructured) for the bulk. Send hard pages (tables, charts, scans) to a VLM tier (LlamaParse agentic, GraniteDocling, Gemini).

---

## 4. Chunking

**Why chunk at all:** embedding models have input limits (2K–32K tokens), a single vector "averages away" detail when the text is long, the LLM context costs money, and retrieval precision needs passage-level granularity.

| Strategy | How | Pros | Cons |
|---|---|---|---|
| Fixed-size (token/char) | Every N tokens, overlap O | Trivial, fast | Cuts sentences, tables |
| Recursive | Split on `\n\n` → `\n` → `. ` → ` ` until ≤ N | Strong default | Ignores semantics |
| Structure-aware | Markdown/HTML headers, code AST, `by_title` | Respects document structure | Needs good parsing |
| Semantic | Embed sentences, break where adjacent similarity drops (percentile threshold) | Topic-coherent | Extra embedding cost; English-centric regex |
| LLM-based | LLM proposes boundaries | Highest recall in Chroma eval | Slow, costly |
| Late chunking | Embed the whole document with a long-context model, then mean-pool token spans per chunk | Chunks carry document context; no extra training | Needs a long-context embedder with token-level access |
| Contextual headers / Contextual Retrieval | Prepend doc title, section path, or an LLM-written 50–100-token context to each chunk before embedding and BM25 | Large retrieval gains | One LLM call per chunk (prompt caching makes it cheap) |
| Parent-child / small-to-big | Index small child chunks; return the larger parent (or a sentence window) to the LLM | Precise match plus rich context | More storage and bookkeeping |

### 4.1 Evidence: Chroma, "Evaluating Chunking Strategies for Retrieval" (Brandon Smith & Anton Troynikov, July 3 2024)
https://www.trychroma.com/research/evaluating-chunking. Token-level recall, precision and IoU; text-embedding-3-large; 5 retrieved chunks.

| Strategy | Size/overlap | Recall | Precision | IoU |
|---|---|---|---|---|
| RecursiveCharacterTextSplitter | 200/0 | 88.1 | 7.0 | 6.9 |
| RecursiveCharacterTextSplitter | 400/0 | 89.5 | 3.6 | 3.6 |
| ClusterSemanticChunker | 200/0 | 87.3 | **8.0** | **8.0** |
| ClusterSemanticChunker | 400/0 | 91.3 | 4.5 | 4.5 |
| LLMSemanticChunker (GPT-4o) | –/0 | **91.9** | 3.9 | 3.9 |

Quotes: strategy choice can swing "up to 9% in recall"; "default settings for certain popular chunking strategies can lead to relatively poor performance." Recursive splitting at about 200 tokens with no overlap is a strong baseline, and reducing overlap improves IoU.

### 4.2 Code
```python
# Recursive — https://docs.langchain.com/oss/python/integrations/splitters
from langchain_text_splitters import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=0)
texts = text_splitter.split_text(document)
```
```python
# Semantic + hierarchical (parent-child) + sentence-window —
# https://developers.llamaindex.ai/python/framework/module_guides/loading/node_parsers/modules/
from llama_index.core.node_parser import (
    SemanticSplitterNodeParser, HierarchicalNodeParser, SentenceWindowNodeParser)
from llama_index.embeddings.openai import OpenAIEmbedding

semantic = SemanticSplitterNodeParser(
    buffer_size=1, breakpoint_percentile_threshold=95, embed_model=OpenAIEmbedding())
hierarchical = HierarchicalNodeParser.from_defaults(chunk_sizes=[2048, 512, 128])
window = SentenceWindowNodeParser.from_defaults(
    window_size=3, window_metadata_key="window",
    original_text_metadata_key="original_sentence")
```
(Parent-child in LangChain is `ParentDocumentRetriever`; LlamaIndex pairs `HierarchicalNodeParser` with `AutoMergingRetriever`. Exact current import paths are [UNVERIFIED] for LangChain v1.)

### 4.3 Late chunking (Jina AI)
- Paper: "Late Chunking: Contextual Chunk Embeddings Using Long-Context Embedding Models", Günther, Mohr, Williams, Wang, Xiao. arXiv:2409.04701 (7 Sep 2024; v3 Jul 2025). https://arxiv.org/abs/2409.04701
- Blog: "Late Chunking in Long-Context Embedding Models" (Jina, 22 Aug 2024). https://jina.ai/news/late-chunking-in-long-context-embedding-models/
- **Flow in words:** naive chunking is chunk → transformer → pool, one chunk at a time. Late chunking runs the transformer over the whole document, then pools each chunk's token span. In the late version, the pronoun "Its" in a chunk knows it refers to Berlin.
- Berlin example (cosine similarity to "Berlin"): for "Its more than 3.85 million inhabitants…", naive scores **0.708** and late scores **0.825**. For "The city is also one of the states…", naive scores 0.753 and late 0.850.
- BEIR nDCG@10, naive → late: SciFact 64.20 → 66.10; NFCorpus 23.46 → 29.98; FiQA 33.25 → 33.84.
- Related product: Voyage `voyage-context-3` (contextualized chunk embeddings) [details UNVERIFIED in this pass].

### 4.4 Contextual Retrieval (Anthropic, Sep 19 2024)
https://www.anthropic.com/news/contextual-retrieval
- Claude 3 Haiku is given the whole document plus one chunk and writes a "short succinct context to situate this chunk within the overall document" (50–100 tokens). That context is prepended to the chunk before **both** embedding and BM25 indexing.
- Top-20 retrieval failure rate, baseline 5.7%:
  - Contextual Embeddings: **−35%** (3.7%)
  - plus Contextual BM25: **−49%** (2.9%)
  - plus reranking: **−67%** (1.9%)
- Cost: "$1.02 per million document tokens" one time, assuming 800-token chunks and 8K-token documents, with prompt caching.

---

## 5. Embeddings (state as of Oct 2026)

**Concept:** an encoder maps text (and now images, audio, video, PDFs) to a vector, and similar meanings land near each other. Similarity is measured as cosine, dot product on normalized vectors, or L2. Models are trained contrastively (InfoNCE with in-batch and hard negatives). Use **asymmetric** query/document prompts for retrieval.

### 5.1 The models

| Model (vendor) | Released | Dims (default / MRL options) | Max input | Modalities | Notes |
|---|---|---|---|---|---|
| `gemini-embedding-001` (Google) | paper Mar 2025 | 3072 / 128–3072 (rec. 768, 1536) | 2,048 tok | text | `task_type` param (RETRIEVAL_QUERY, RETRIEVAL_DOCUMENT, CODE_RETRIEVAL_QUERY, QUESTION_ANSWERING, FACT_VERIFICATION…). Paper: MTEB(Multilingual) task mean **68.32**, **+5.09** over the next model (multilingual-e5-large-instruct) |
| `gemini-embedding-2` (Google) | preview 10 Mar 2026; **GA ~late Apr 2026** | 3072 / 128–3072 (rec. 768, 1536) | 8,192 tok; 6 images; 120 s video; 180 s audio; 6-page PDF | **text, image, video, audio, PDF in one space** | No `task_type`; use prefixes like `task: question answering \| query: …`. **Not compatible with 001; you must re-embed.** Batch API at 50% of the price |
| `text-embedding-3-small` / `-large` (OpenAI) | Jan 2024 | 1536 / 3072, `dimensions` param | 8,192 tok | text | MTEB 62.3 / 64.6 (ada-002: 61.0). 62,500 / 9,615 pages per $. 3-large at 256 dims still beats ada-002 at 1536 dims. Now well below the top of the 2026 leaderboard |
| Voyage 4 family: `voyage-4-large`, `voyage-4`, `voyage-4-lite`, `voyage-code-4`, open-weight `voyage-4-nano` | blog 15 Jan 2026 | 1024 / 256, 512, 2048 | 32K tok | text | **Shared embedding space across the family** (index with large, query with lite). MoE (4-large). `output_dtype`: float, int8, uint8, binary, ubinary. Not on the public MTEB board |
| Cohere `embed-v4.0` | Apr 2025 [date UNVERIFIED] | 1536 / 256, 512, 1024 | **128K tok** | text, images, interleaved (PDF pages) | Matryoshka |
| Cohere Embed 5: `embed-v5.0-pro`, `embed-v5.0-fast` | **30 Sep 2026** (secondary sources) | 256–2048 | 128K | text, image, mixed | Pro and Fast share one space (index with Pro, query with Fast; ~1.6-pt loss reported). Float/int8/binary per docs. Vendor numbers [UNVERIFIED] |
| Qwen3-Embedding 0.6B / 4B / 8B (Alibaba, **Apache-2.0** open weights) | Jun 2025 (arXiv:2506.05176) | 1024 / 2560 / 4096, MRL | 32K | text (+ code) | 8B: MTEB Multilingual **70.58** (#1 as of 5 Jun 2025), MTEB Eng v2 **75.22**, C-MTEB 73.84. Matching Qwen3-Reranker models |

Sources: https://ai.google.dev/gemini-api/docs/embeddings · https://developers.googleblog.com/building-with-gemini-embedding-2/ · https://arxiv.org/abs/2503.07891 · https://developers.openai.com/api/docs/guides/embeddings · https://docs.voyageai.com/docs/embeddings · https://docs.cohere.com/docs/cohere-embed · https://github.com/QwenLM/Qwen3-Embedding

**Leaderboard caveat (for the slide):** the MTEB board (https://huggingface.co/spaces/mteb/leaderboard) has several sub-boards: Multilingual (MMTEB, 250+ languages), Eng v2, Code, and domain boards. Ranks differ between them, and some vendors (Voyage) don't submit. Secondary 2026 snapshots put gemini-embedding-001/2 and Qwen3-Embedding-8B at the top, and text-embedding-3-large far down the list [snapshot-dependent]. Teaching point: **evaluate on your own data.** MTEB retrieval is mostly nDCG@10 on BEIR-style sets.

**Real-world results (Google Dev Blog, 30 Apr 2026, vendor-reported):**
- Harvey (legal): +3% Recall@20.
- Supermemory: +40% Recall@1.
- Nuuly (URBN): Match@20 rose from 60% to ~87%.

### 5.2 Code
```python
# Gemini — https://ai.google.dev/gemini-api/docs/embeddings + Dev Blog (Apr 30 2026)
from google import genai

client = genai.Client()
q = client.models.embed_content(
    model="gemini-embedding-2",
    contents="task: question answering | query: What is late chunking?",
    config={"output_dimensionality": 768},   # MRL truncation
)
d = client.models.embed_content(
    model="gemini-embedding-2",
    contents="title: Late Chunking | text: Late chunking pools token embeddings...",
    config={"output_dimensionality": 768},
)
print(len(q.embeddings[0].values))
```
```python
# OpenAI — https://developers.openai.com/api/docs/guides/embeddings
from openai import OpenAI
client = OpenAI()
resp = client.embeddings.create(model="text-embedding-3-large",
                                input="Your text string goes here", dimensions=256)
vec = resp.data[0].embedding
```
```python
# Voyage — https://docs.voyageai.com/docs/embeddings
import voyageai
vo = voyageai.Client()  # VOYAGE_API_KEY
docs = vo.embed(texts, model="voyage-4-large", input_type="document").embeddings
qry  = vo.embed(["my question"], model="voyage-4-lite", input_type="query").embeddings  # shared space
```
```python
# Qwen3-Embedding (open weights) — adapted from https://github.com/QwenLM/Qwen3-Embedding
# requires transformers>=4.51.0, sentence-transformers>=2.7.0
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("Qwen/Qwen3-Embedding-0.6B")
q = model.encode(["What is the capital of China?"], prompt_name="query")
d = model.encode(["The capital of China is Beijing."])
print(model.similarity(q, d))
```

### 5.3 Matryoshka Representation Learning (MRL)
- "Matryoshka Representation Learning", Kusupati, Bhatt, Rege, Wallingford, Sinha, Ramanujan, Howard-Snyder, Chen, Kakade, Jain, Farhadi. arXiv:2205.13147 (May 2022), NeurIPS 2022. https://arxiv.org/abs/2205.13147
- **Idea:** train so that every prefix (the first 64, 128, 256 … dims) of the vector is itself a good embedding, with the loss summed over nested prefix sizes.
- Results: "up to **14x smaller** embedding size … at the same level of accuracy" on ImageNet-1K, and up to 14x real-world retrieval speed-ups.
- **In 2026 this is everywhere:** Gemini (128–3072), OpenAI `dimensions`, Voyage (256–2048), Cohere v4 (256–1536), Qwen3.
- **Pattern:** "funnel" or adaptive retrieval. Search with short vectors, then re-score candidates with full vectors. **Re-normalize after truncating** (OpenAI docs).
- **Storage math (slide):** 10M chunks × 3072 dims × 4 B (float32) = **~123 GB**. At 768 dims that drops to ~31 GB; with int8, ~7.7 GB; with binary (768 bits = 96 B), ~0.96 GB, about 128x smaller than float32-3072.

---

## 6. Vector indexes (ANN)

Exact k-NN is O(N·d) per query. ANN gives up a little recall for orders of magnitude more speed. Every index is a point on the **recall vs latency vs memory vs build-time** trade-off surface.

| Index | Core idea | Key knobs | Typical use |
|---|---|---|---|
| **Flat** | Brute force | – | <1M vectors, ground truth |
| **IVF** | k-means into `nlist` cells; search the `nprobe` nearest cells | nlist, nprobe | Large, memory-bound |
| **PQ** (Jégou, Douze, Schmid, *IEEE TPAMI* 2011) | Split a vector into M sub-vectors and quantize each to one of 2^nbits centroids. Code = M·nbits/8 bytes | M, nbits | Compression (e.g. 768-d float32 is 3,072 B; PQ96x8 is 96 B, 32x smaller) |
| **HNSW** (Malkov & Yashunin, arXiv:1603.09320, 2016; IEEE TPAMI 2018) | Multi-layer proximity graph. Each node's top layer is random with exponentially decaying probability; search is greedy from the top layer down; "logarithmic complexity scaling" | M, efConstruction, efSearch | Default in pgvector, Qdrant, Weaviate, Milvus, Elasticsearch/OpenSearch, FAISS |
| **DiskANN / Vamana** (Subramanya et al., NeurIPS 2019, Microsoft Research) | Flat graph with long-range edges; PQ codes in RAM, full vectors and graph on SSD | R, L, beam width | Billion scale on one node: SIFT1B on a 64 GB RAM workstation plus SSD, >5,000 QPS, <3 ms mean latency, 95%+ 1-recall@1 (16 cores). Used in Azure Cosmos DB, SQL Server 2025 [deployment list UNVERIFIED] |
| **ScaNN** (Google, open-sourced 2020) | Partitioning plus **anisotropic vector quantization** (minimizes inner-product error) plus re-scoring | leaves, reorder | Vertex AI Vector Search, **ScaNN for AlloyDB** |
| **SOAR** (Sun & Guo, NeurIPS 2023; blog 10 Apr 2024) | "Spilling with Orthogonality-Amplified Residuals": each vector is assigned to a second cluster whose residual is near-orthogonal to the first | – | glove-100: rivals needed >10x memory and 50x indexing time to match query speed |

Sources: https://github.com/facebookresearch/faiss/wiki/Faiss-indexes · https://arxiv.org/abs/1603.09320 · https://neurips.cc/virtual/2019/poster/14308 · https://research.google/blog/soar-new-algorithms-for-even-faster-vector-search-with-scann/

**FAISS bytes per vector:** Flat 4·d. IVFFlat 4·d + 8. IVFPQ ceil(M·nbits/8) + 8. HNSWFlat 4·d + M·2·4 (graph links).

```python
# FAISS IVF-PQ — adapted from https://github.com/facebookresearch/faiss/wiki/Faiss-indexes
import faiss, numpy as np
d, nlist, m = 768, 4096, 96                    # 96 sub-quantizers x 8 bits = 96 bytes/vector
quantizer = faiss.IndexFlatL2(d)
index = faiss.IndexIVFPQ(quantizer, d, nlist, m, 8)
index.train(xt)                                 # representative training sample
index.add(xb)
index.nprobe = 16                               # query-time recall/speed knob
D, I = index.search(xq, 10)

hnsw = faiss.IndexHNSWFlat(d, 32)               # M=32 neighbors
hnsw.hnsw.efSearch = 64
```

**HNSW search in words (animation script):** enter at the single top-layer node, greedily move to the neighbor closest to the query until there is no improvement, drop a layer, repeat, and on layer 0 run a beam search of width efSearch, then return the top-k. It works like an express highway, then local roads, then street level.

---

## 7. Metrics (retrieval and end-to-end)

**Retrieval (needs relevance labels):**
- **Recall@k:** the fraction of relevant items found in the top-k. This is the main RAG metric, because the LLM can only use what was retrieved.
- **Precision@k:** relevant items in the top-k divided by k.
- **MRR** (Mean Reciprocal Rank): the mean of 1/rank of the first relevant hit. XTREME-UP reports MRR@10.
- **nDCG@k:** graded relevance with a log2 position discount, normalized by the ideal ranking. **nDCG@10 is the MTEB/BEIR retrieval headline metric.**
- **Hit rate / Match@k:** whether any relevant item appears in the top-k. Nuuly's Match@20 is one example.
- **Token-level IoU / precision** (Chroma): penalizes retrieving redundant or irrelevant tokens.
- **ANN-specific:** recall@k against exact k-NN, QPS, p95/p99 latency, memory per vector, build time (ann-benchmarks, Big-ANN).

**Generation / end-to-end (often LLM-as-judge):** faithfulness/groundedness, answer relevance, context precision and context recall (RAGAS-style), citation accuracy, exact match / F1 (Lewis 2020 used EM). A full evaluation deck section comes later.

**Failure-rate framing (Anthropic):** 1 − recall@20. Stating the improvement as 5.7% → 1.9% failures makes the gain obvious to an audience.

---

## 8. Quotable lines

- "This shows we can update RAG's world knowledge by simply replacing its non-parametric memory." — Lewis et al., 2020 (arXiv:2005.11401)
- "…the non-parametric memory is a dense vector index of Wikipedia." — Lewis et al., 2020 abstract
- "default settings for certain popular chunking strategies can lead to relatively poor performance." — Chroma Research, 2024
- Contextual Retrieval reduced failed retrievals "by 49%", and "by 67%" with reranking. — Anthropic, Sep 2024
- MRL: "up to 14x smaller embedding size … at the same level of accuracy." — Kusupati et al., 2022
- HNSW: hierarchical search "allows a logarithmic complexity scaling." — Malkov & Yashunin

## 9. Real-world examples

- **Harvey** (legal AI) and **Supermemory**: Gemini Embedding 2 retrieval gains (Google Dev Blog, Apr 2026).
- **Nuuly / URBN**: multimodal product search with Gemini Embedding 2, Match@20 up from 60% to ~87%.
- **Google Cloud**: Vertex AI Vector Search and AlloyDB run ScaNN. **Microsoft**: DiskANN in Azure database services [specific products UNVERIFIED].
- **IBM**: Docling, donated to LF AI & Data, with GraniteDocling VLM.
- **Anthropic**: the Contextual Retrieval cookbook pattern.

---

## 10. Slide ideas (8)

1. **"The frozen-brain problem" → RAG.** Split screen: on the left, the LLM brain with a "cutoff" padlock; on the right, a library card catalog plugging in. Animate the 2016 → 2018 index swap with accuracy flipping 70% / 4% (Lewis hot-swap experiment).
2. **Lewis et al. 2020 architecture.** Animated flow: query → DPR query encoder → MIPS over 21M passages → top-k → BART. Toggle RAG-Sequence vs RAG-Token, with per-token document highlights shifting. Callout: 400M plus retrieval beats T5-11B (44.5 vs 34.5 EM on NQ).
3. **Parsing gallery: "garbage in, garbage out."** One ugly two-column PDF page with a table, shown through naive text extraction (scrambled), Docling Markdown (clean table), and a Gemini/LlamaParse agentic VLM. Reveal each with a wipe transition.
4. **The chunking spectrum.** One paragraph about Berlin cut by fixed, recursive, semantic (similarity-drop line chart with a 95th-percentile threshold), and parent-child (nested boxes). End on the Chroma table with recall/IoU bars.
5. **Late chunking vs contextual retrieval.** Two pipelines side by side. Late chunking: the whole document goes through the transformer and the pooling brackets come down afterwards. Contextual: an LLM sticky note is prepended to each chunk. Numbers: "Its…" 0.708 → 0.825; failure rate 5.7% → 2.9% → 1.9% as an animated bar.
6. **The embedding landscape in Oct 2026.** Scatter of quality vs price/dims, with logos (Gemini Embedding 2, Qwen3-8B open, Voyage 4, Cohere Embed 5, OpenAI 3-large) and modality badges. Footnote: "evaluate on your data; MTEB sub-boards differ."
7. **Matryoshka dolls.** A 3072-d vector bar that shrinks to 1536, 768 and 256 as dolls nest, with a storage counter for 10M chunks (123 GB → 31 GB → 7.7 GB int8 → 0.96 GB binary).
8. **How HNSW finds your neighbor.** A 3-layer graph animation with greedy hops descending layers. Then a mini-montage: IVF Voronoi cells lighting up `nprobe`; PQ splitting a vector into 8 sub-codes; DiskANN RAM vs SSD; ScaNN/SOAR "spill into a second cluster."
9. **Metrics cheat sheet.** One query, a ranked list of 10 results with relevant ones highlighted, computing Recall@5, Precision@5, MRR and nDCG@10 live as items are re-ordered.
10. **Index trade-off triangle.** Recall, latency and memory at the corners, with Flat, HNSW, IVF-PQ, DiskANN and ScaNN placed on it and a slider for efSearch/nprobe moving points along the frontier.

---

## Open items / [UNVERIFIED]

- Exact current Docling release number; LlamaParse v2 SDK argument names (`file_id`, result field path).
- Cohere Embed 5 details come from secondary press (30 Sep 2026), not Cohere's own blog. Embed v4 release date.
- Live MTEB ranks as of Oct 2026 (the leaderboard page is dynamic and was not machine-readable). Gemini Embedding 2 MTEB numbers vary across secondary sources (~68–70 multilingual).
- DiskANN production deployments list; LangChain v1 import path for `ParentDocumentRetriever`.
- The Gemini document-processing page currently shows `client.interactions.create(model="gemini-3.8-flash", …)`. Re-check the model id before the deck ships.
