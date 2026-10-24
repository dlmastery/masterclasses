# 05 — Multimodal RAG, Code RAG, Memory, CAG, Personalization, Streaming & On-Device RAG

Research date: 2026-10-23. Every fact below was checked against the primary source linked next to it, unless it is marked [UNVERIFIED]. Version numbers are given wherever the source states one.

---

## 1. Multimodal RAG: why text-only pipelines fail

**Problem.** Real corpora (PDF reports, slide decks, manuals, scanned forms) store much of their meaning in layout, tables, charts and figures. The classic pipeline (OCR, then text chunks, then text embeddings) loses that structure.

> "Modern document retrieval systems... mainly index documents using text extracted from page content, which is often a lengthy and brittle process." (paraphrase of the ColPali abstract, arXiv 2407.01449)

There are three architectural families, in order of increasing "visual nativeness":

1. **Parse-then-text (document understanding → text RAG).** Parse layout, tables and charts into Markdown or JSON, then do normal text RAG. Tool: **Docling** (IBM / docling-project). It handles table structure, reading order and layout analysis, and it converts bar, pie and line charts into tables or code with descriptions. It also runs VLM pipelines such as GraniteDocling via `docling --pipeline vlm --vlm-model granite_docling <source>`. Python 3.10+ is required (3.9 support was dropped in v2.70.0). Paper: *Docling Technical Report*, arXiv 2408.09869. https://github.com/docling-project/docling
2. **Caption / summarize-then-embed.** A VLM writes text descriptions of images and tables, the descriptions are embedded, and the raw image is returned to a multimodal LLM at answer time. This is the "multi-vector retriever" pattern.
3. **Embed the page image directly (visual retrieval).** **ColPali / ColQwen** use late interaction (multi-vector). Alternatively, use a single-vector natively multimodal embedder such as **Gemini Embedding 2**.

**Graph-based multimodal RAG.** *RAG-Anything: All-in-One RAG Framework* (Guo, Ren, et al., HKU, arXiv 2510.12323, Oct 14 2025) treats each image, table or equation as a knowledge entity. It builds a "dual graph" of cross-modal relations plus textual semantics and uses "cross-modal hybrid retrieval" (graph navigation plus semantic matching). The authors report that gains are largest on long documents. https://github.com/HKUDS/RAG-Anything

### Docling quickstart (README)
```python
from docling.document_converter import DocumentConverter

source = "https://arxiv.org/pdf/2408.09869"  # local path or URL
converter = DocumentConverter()
result = converter.convert(source)
print(result.document.export_to_markdown())
```
Source: https://github.com/docling-project/docling

---

## 2. ColPali and late-interaction visual retrieval

**Paper.** *ColPali: Efficient Document Retrieval with Vision Language Models*, by Manuel Faysse, Hugues Sibille, Tony Wu, Bilel Omrani, Gautier Viaud, Céline Hudelot and Pierre Colombo. arXiv 2407.01449 (v1 June 27 2024; v6 Feb 28 2025). **Published at ICLR 2025.** https://arxiv.org/abs/2407.01449

**Key ideas.**
- A VLM (originally PaliGemma) encodes each **page image** into **many patch-level vectors** (multi-vector). The query is encoded into token vectors.
- **Late interaction / MaxSim** (from ColBERT): for each query token, take the maximum similarity over all page patches, then sum across query tokens.
- **ViDoRe** (Visual Document Retrieval Benchmark) covers page-level retrieval across domains and languages. Follow-up: *ViDoRe Benchmark V2: Raising the Bar for Visual Retrieval* (Macé, Loison, Faysse, arXiv 2505.17166, 2025).
- The authors call the method simpler, faster and end-to-end trainable, and they release it under open licenses.

**Diagram in words (indexing).** PDF → render each page to an image → VLM encoder → about 1,000 patch embeddings × 128-d per page → store as a multi-vector index. No OCR and no chunking.
**Diagram in words (query).** Query text → token embeddings (e.g., 20 × 128) → MaxSim against every page → top-k page images → send those images plus the question to a multimodal LLM (Gemini, Claude, GPT) → answer.

**Model scores on ViDoRe (nDCG@5 avg, from colpali README, Oct 2026).**
| Model | ViDoRe |
|---|---|
| vidore/colpali (original) | 81.3 |
| vidore/colpali-v1.3 | 84.8 |
| vidore/colqwen2-v1.0 | 89.3 |
| vidore/colqwen2.5-v0.2 | 89.4 |
| TomoroAI/tomoro-colqwen3-embed-4b | 90.6 |
| athrael-soju/colqwen3.5-4.5B-v3 | 90.9 |
| vidore/colSmol-256M (tiny) | 80.1 |

**Important 2026 update.** The `colpali-engine` README now says the package is **deprecated**. It recommends **Sentence Transformers v6 `MultiVectorEncoder`** for new projects. Install with `pip install colpali-engine`. Use tag v0.1.1 to reproduce the paper results.

### Legacy colpali-engine code (README)
```python
import torch
from colpali_engine.models import ColQwen2, ColQwen2Processor

model_name = "vidore/colqwen2-v1.0"
model = ColQwen2.from_pretrained(model_name, torch_dtype=torch.bfloat16,
                                 device_map="cuda:0").eval()
processor = ColQwen2Processor.from_pretrained(model_name)

batch_images = processor.process_images(images).to(model.device)
batch_queries = processor.process_queries(queries).to(model.device)
with torch.no_grad():
    image_embeddings = model(**batch_images)
    query_embeddings = model(**batch_queries)
scores = processor.score_multi_vector(query_embeddings, image_embeddings)
```
Source: https://github.com/illuin-tech/colpali

### Modern way: Sentence Transformers v6 (blog Aug 18 2026)
```python
# pip install -U "sentence-transformers[image]"
from sentence_transformers import MultiVectorEncoder

model = MultiVectorEncoder("vidore/colqwen2.5-v0.2")
queries = ["Total outlay is maximum in which year?"]
images = [
    "https://huggingface.co/datasets/sentence-transformers/example-documents/resolve/main/doc1.jpg",
    "https://huggingface.co/datasets/sentence-transformers/example-documents/resolve/main/doc2.jpg",
]
query_embeddings = model.encode_query(queries)
document_embeddings = model.encode_document(images)
scores = model.similarity(query_embeddings, document_embeddings)  # MaxSim
```
Source: *Multi-Vector (Late Interaction) Embedding Models with Sentence Transformers*, https://huggingface.co/blog/multi-vector-encoder. v6.0.0 is a major release that requires transformers v5 and scores in float32. It also loads PyLate and Stanford ColBERT checkpoints.

**Cost of multi-vector (teach this trade-off).** The same blog measured 4,874 Natural Questions passages:
- Dense MiniLM (384-d): **7.5 MB**
- Dense gte-modernbert (768-d): **15.0 MB**
- Multi-vector LateOn (608,414 vectors × 128): **311.5 MB** float32. This drops to **92 MB** with a fast-plaid index and to **78.8 MB** with token pooling `pool_factor=4`.
> Quotable (paraphrase): multi-vector "often beats comparable dense models but is not universally better."

---

## 3. Natively multimodal single-vector embeddings: Gemini Embedding 2

- **Model code:** `gemini-embedding-2` (stable; "Latest update April 2026"). Inputs: **text, image, video, audio, PDF** in **one embedding space**, across 100+ languages. https://ai.google.dev/gemini-api/docs/models/gemini-embedding-2
- **Limits (Google launch blog):** 8,192 input tokens; up to 6 images per request (PNG/JPEG); video up to 120 s (MP4/MOV); audio embedded directly without transcription; PDF up to 6 pages; interleaved inputs (image plus text) allowed. https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-embedding-2/
- **Output dims:** 128 to 3072 (default 3072) through Matryoshka (MRL). Recommended values are 768, 1536 and 3072.
- **Gotcha:** `task_type` is **not supported** on gemini-embedding-2. Put the task into the text instead (`"task: search result | query: ..."`). Its vectors are **incompatible** with `gemini-embedding-001`, so you must re-embed.
- **Paper:** *Gemini Embedding 2: A Native Multimodal Embedding Model from Gemini*, arXiv 2605.27295. It reports MSCOCO R@1 62.9, Vatex NDCG@10 68.8, MTEB multilingual 69.9 and MTEB Code 84.0 (taken from search-result summary; [UNVERIFIED] against the PDF tables).
- Pricing of $0.25 per 1M tokens: [UNVERIFIED].

```python
from google import genai
from google.genai import types

client = genai.Client()
with open("chart.png", "rb") as f:
    img = f.read()

result = client.models.embed_content(
    model="gemini-embedding-2",
    contents=[types.Part.from_bytes(data=img, mime_type="image/png")],
    config=types.EmbedContentConfig(output_dimensionality=768),
)
print(len(result.embeddings[0].values))  # 768
```
Source: https://ai.google.dev/gemini-api/docs/embeddings

**Single-vector vs multi-vector (slide table).** Gemini Embedding 2 gives one vector per item. It is cheap and fits any vector DB, and it is cross-modal (text↔video↔audio). ColPali gives about 1,000 vectors per page. It costs more storage, but its fine-grained token↔patch matching wins on dense document pages.

---

## 4. Video RAG

- *VideoRAG: Retrieval-Augmented Generation with Extreme Long-Context Videos*, by Xubin Ren, Lingrui Xu, Long Xia, Shuaiqiang Wang, Dawei Yin and Chao Huang (HKU and Baidu). arXiv 2502.01549, Feb 3 2025. https://arxiv.org/abs/2502.01549
  - It uses a dual channel: (a) **graph-based textual knowledge grounding** across videos (from ASR and captions), and (b) **multimodal context encoding** that keeps visual features.
  - **LongerVideos** benchmark: more than 160 videos, over 134 hours (lectures, documentaries, entertainment).
- Practical video RAG pipeline: split video into scenes or clips of 10–120 s → (i) embed clips directly with Gemini Embedding 2 (≤120 s per video input) and/or (ii) transcribe and caption each clip into text → index with timestamps → retrieve clips → pass the clip (or frames) to Gemini for the answer, citing timestamps.

---

## 5. Code RAG

**Why code is different.** Code has exact identifiers, structure (AST), cross-file dependencies, and constant change (staleness).

- **AST-aware chunking.** *cAST: Enhancing Code Retrieval-Augmented Generation with Structural Chunking via Abstract Syntax Tree*, by Yilin Zhang, Xinran Zhao, Zora Zhiruo Wang, Chenyang Yang, Jiayi Wei and Tongshuang Wu. arXiv 2506.15655 (June 2025; Findings of EMNLP 2025). It recursively splits large AST nodes and merges small siblings under a size budget. Results: **+4.3 Recall@5 on RepoEval** and **+2.67 Pass@1 on SWE-bench**. Code: https://github.com/yilinjz/astchunk
- **Cursor (industrial example).** *Securely indexing large codebases* by Jeremy Stribling, Cursor blog, **Jan 27 2026**. https://cursor.com/blog/secure-codebase-indexing
  - A **Merkle tree** of file hashes tells Cursor which files changed. For a 50,000-file workspace the hashes are about 3.2 MB.
  - Changed files are split into **syntactic chunks** and embedded asynchronously. Embeddings are **cached by chunk content**.
  - A **simhash** of the Merkle tree lets a new user's index be seeded from a teammate's. Clones average "92% similarity across users within an organization."
  - **Time-to-first-query:** median 7.87 s → 525 ms; p90 2.82 min → 1.87 s; p99 **4.03 hours → 21 s**.
  - Content proofs mean the server returns results only for files the client can prove it has.
- **Agentic search vs vector index (the 2025–26 debate).** Claude Code's team reportedly tried local vector DBs and found plain **glob + grep agentic search** performed better (second-hand reports via a Pragmatic Engineer interview; [UNVERIFIED] as an Anthropic publication). Controlled study: *Is Grep All You Need? How Agent Harnesses Reshape Agentic Search* (Sen, Kasturi, Lumer, Gulati, Subbiah; arXiv 2605.15184, May 14 2026). On a 116-question LongMemEval sample across Claude Code, Codex, Gemini CLI and a custom harness, "grep generally yields higher accuracy than vector retrieval," but results "depend strongly on which harness and tool-calling style is used." https://arxiv.org/abs/2605.15184
- **Teaching takeaway.** Code RAG in 2026 is **hybrid**: grep/ripgrep for exact identifiers, LSP/symbol graphs for precision, embeddings for "where is the auth logic?"-style conceptual queries, all orchestrated by an agent loop.

---

## 6. Conversational RAG and agent memory

**Conversational RAG basics.** Rewrite the follow-up into a standalone query using chat history ("what about its price?" → "what is the price of the Pixel 10?"), retrieve, then answer. Memory goes further: it **persists distilled facts across sessions**.

**Memory taxonomy (slide).** Short-term or working memory (the context window or session state) · episodic (past conversations) · semantic (extracted facts and preferences) · procedural (learned instructions). Operations: **extract → consolidate (add/update/delete/merge) → retrieve → inject**.

### Benchmarks
- **LongMemEval**: *LongMemEval: Benchmarking Chat Assistants on Long-Term Interactive Memory* (Di Wu, Hongwei Wang, Wenhao Yu, Yuwei Zhang, Kai-Wei Chang, Dong Yu; **ICLR 2025**; arXiv 2410.10813). 500 questions covering 5 abilities: information extraction, multi-session reasoning, temporal reasoning, knowledge updates and abstention. Commercial assistants and long-context LLMs show about a **30% accuracy drop** across sustained interactions. https://github.com/xiaowu0162/LongMemEval
- **LOCOMO** (long conversational memory) is used by Mem0. **DMR** (Deep Memory Retrieval) is from the MemGPT paper.

### MemGPT → Letta
- *MemGPT: Towards LLMs as Operating Systems* (Packer, Wooders, Lin, Fang, Patil, Stoica, Gonzalez; arXiv 2310.08560, Oct 2023). It introduced **"virtual context management"**, which pages data between the context window ("RAM") and external storage ("disk") the way an OS does. https://arxiv.org/abs/2310.08560
- **Letta** (the MemGPT team's company): "The platform for building stateful agents." **Memory blocks** = "core memory", which are labeled, size-limited sections that are always in context and that the agent edits itself. Archival memory and recall memory are separate searchable stores (described on a separate docs page; details [UNVERIFIED] here). Docs also mention "Memory & dreaming", MemFS and shared memory.
```python
from letta_client import Letta
import os

client = Letta(api_key=os.getenv("LETTA_API_KEY"))
agent_state = client.agents.create(
    memory_blocks=[
        {"label": "human", "value": "The human's name is Bob the Builder.", "limit": 5000},
        {"label": "persona", "value": "My name is Sam, the all-knowing sentient AI.", "limit": 5000},
    ],
    model="openai/gpt-4o-mini",
)
```
Source: https://docs.letta.com/guides/agents/memory-blocks

### Mem0
- Paper: *Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory* (Chhikara, Khant, Aryan, Singh, Yadav; arXiv 2504.19413, Apr 28 2025). On **LOCOMO**: **+26% relative LLM-as-a-Judge vs OpenAI memory**, **91% lower p95 latency** and **>90% token-cost savings vs full-context**. The graph variant (Mem0ᵍ) adds about 2% over base. https://arxiv.org/abs/2504.19413
- An LLM extracts candidate facts from each exchange. Each fact is compared with similar existing memories, and the system chooses ADD / UPDATE / DELETE / NOOP.
- Defaults: OpenAI LLM plus embedder, local Qdrant, SQLite history. Python ≥ 3.10. `pip install mem0ai`.
```python
from mem0 import Memory

m = Memory()
messages = [
    {"role": "user", "content": "Hi, I'm Alex. I love basketball and gaming."},
    {"role": "assistant", "content": "Hey Alex! I'll remember your interests."},
]
m.add(messages, user_id="alex")
results = m.search("What do you know about me?", filters={"user_id": "alex"})
print(results)  # {"results": [{"id", "memory", "score", "categories", ...}]}
```
Source: https://docs.mem0.ai/open-source/python-quickstart

### Zep / Graphiti (temporal knowledge-graph memory)
- Paper: *Zep: A Temporal Knowledge Graph Architecture for Agent Memory* (Rasmussen, Paliychuk, Beauvais, Ryan, Chalef; arXiv 2501.13956, Jan 20 2025). **DMR 94.8% vs MemGPT 93.4%**; LongMemEval accuracy gains of **up to 18.5%**; **90% lower response latency** vs baselines. https://arxiv.org/abs/2501.13956
- **Graphiti** (open-source engine, `pip install graphiti-core`): "explicit bi-temporal tracking with automatic fact invalidation." Quote: **"Facts have validity windows. When information changes, old facts are invalidated — not deleted."** Backends: Neo4j 5.26, FalkorDB 1.1.2, Amazon Neptune (+OpenSearch Serverless), and Kuzu 0.11.2 (deprecated). https://github.com/getzep/graphiti
```python
from graphiti_core import Graphiti
graphiti = Graphiti("bolt://localhost:7687", "neo4j", "password")
# then: await graphiti.add_episode(...); await graphiti.search("...")
# (method names per examples/quickstart; exact signature [UNVERIFIED])
```
- Worked example: "Alice works at Acme" (valid 2024-01 → 2026-03). The episode "Alice joined Google" invalidates the old edge but keeps it in history. Now "where did Alice work in 2025?" can still be answered.

### Vertex AI / Agent Platform Memory Bank + Google ADK
- Product naming in Oct 2026 docs: **"Agent Platform Memory Bank"** under **Gemini Enterprise Agent Platform** (formerly Vertex AI Agent Engine Memory Bank). It "lets you construct long-term memories from conversations between the user and your agent." Features: generate memories, ingest events, memory profiles, fetch, memory revisions, IAM Conditions. Compliance: VPC-SC, CMEK, data residency, HIPAA. https://docs.cloud.google.com/agent-builder/agent-engine/memory-bank/overview
- Gemini-based extraction and consolidation that resolves contradictions, run asynchronously (per a Google community guide; https://discuss.google.dev/t/how-to-build-ai-agents-with-long-term-memory-using-vertex-ai-memory-bank-adk/193013).
```python
# Generate memories (current SDK surface per docs)
events = [{"content": {"role": "user", "parts": [{"text": "I work with LLM agents!"}]}}]
client.memory_banks.memories.generate(
    name=memory_bank.name,
    direct_contents_source={"events": events},
    scope={"user_id": "123"},
    config={"wait_for_completion": True},
)
# Similarity retrieval
results = client.memory_banks.memories.retrieve(
    name=memory_bank.name,
    scope={"user_id": "123"},
    similarity_search_params={"search_query": "programming interests", "top_k": 3},
)
```
Sources: https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/memory-bank/generate-memories and …/fetch-memories. Note: older guides use `client.agent_engines.memories.generate(...)`. The method surface changed, so check your SDK version.

**ADK integration (adk.dev, formerly google.github.io/adk-docs):**
```python
from google import adk
from google.adk.agents import Agent
from google.adk.memory import VertexAiMemoryBankService
from google.adk.tools import preload_memory

memory_service = VertexAiMemoryBankService(
    project="PROJECT_ID", location="LOCATION", agent_engine_id="AGENT_ENGINE_ID")

async def auto_save(callback_context):
    await callback_context.add_session_to_memory()

agent = Agent(model=MODEL, name="Generic_QA_Agent",
              instruction="Answer the user's questions",
              tools=[preload_memory],          # or load_memory (agent decides)
              after_agent_callback=auto_save)
runner = adk.Runner(agent=agent, app_name="app",
                    session_service=session_service, memory_service=memory_service)
```
- `preload_memory` retrieves on every turn automatically, while `load_memory` is a tool the agent calls when needed. `InMemoryMemoryService()` is for prototyping. CLI: `adk web agents_dir --memory_service_uri="agentengine://1234567890"`. https://adk.dev/sessions/memory/

**Comparison slide.**
| System | Memory shape | Update model | Signature idea |
|---|---|---|---|
| Letta/MemGPT | in-context blocks + archival | agent self-edits via tools | LLM-as-OS paging |
| Mem0 | vector facts (+ optional graph) | LLM ADD/UPDATE/DELETE | production cost/latency |
| Zep/Graphiti | temporal KG | bi-temporal invalidation | "when was it true?" |
| Memory Bank | managed, scoped facts | Gemini extract + consolidate | managed GCP + ADK |

---

## 7. Cache-Augmented Generation (CAG) and prompt caching

- Paper: *Don't Do RAG: When Cache-Augmented Generation is All You Need for Knowledge Tasks* (Chan, Chen, Cheng, Huang; arXiv 2412.15605, Dec 20 2024, v2 Feb 2025). https://arxiv.org/abs/2412.15605
  > "CAG eliminates retrieval latency and minimizes retrieval errors while maintaining context relevance."
- How it works: preload the whole (small) knowledge base into a long-context LLM, **precompute and cache the KV state**, and answer queries against that cache. There is no retriever. This works only when the corpus fits in context.
- Anthropic's rule of thumb (*Introducing Contextual Retrieval*, Sep 19 2024): if the knowledge base is "smaller than 200,000 tokens (about 500 pages of material)", skip RAG and put it in the prompt with prompt caching, which cuts latency by more than 2x and costs by up to 90%. The same post: contextual embeddings cut top-20 retrieval failures by **35%**, adding contextual BM25 by **49%**, and adding reranking by **67%** (5.7% → 1.9%). https://www.anthropic.com/news/contextual-retrieval
- **Claude prompt caching (docs, Oct 2026):** 5-min write 1.25x, 1-hour write 2x, read 0.1x base (0.05x on Opus/Sonnet 5.5). Minimum 512 tokens on current models. Max 4 breakpoints. https://platform.claude.com/docs/en/docs/build-with-claude/prompt-caching
```python
response = client.messages.create(
    model="claude-opus-5-5", max_tokens=1024,
    cache_control={"type": "ephemeral"},      # automatic caching
    system=BIG_KNOWLEDGE_BASE_TEXT,
    messages=[{"role": "user", "content": "Question..."}],
)
print(response.usage.cache_read_input_tokens)
```
- **Gemini explicit context caching** (v1beta; the docs note it is not supported on Gemini 4 Argon and later, which rely on implicit caching. Implicit caching minimums: 4,096 tokens for Gemini 3.x, 2,048 for 2.5). https://ai.google.dev/gemini-api/docs/generate-content/caching
```python
cache = client.caches.create(
    model="gemini-3.8-flash",
    config=types.CreateCachedContentConfig(
        display_name="kb-cache",
        system_instruction="Answer only from the manual.",
        contents=[manual_file], ttl="3600s"))
resp = client.models.generate_content(
    model="gemini-3.8-flash", contents="How do I reset the device?",
    config=types.GenerateContentConfig(cached_content=cache.name))
```
- **Decision rule (slide):** corpus fits in context and changes rarely → CAG/caching. Corpus is large, changes often, or needs per-user ACLs → RAG. Hybrid: cache the stable "core" docs and retrieve the long tail.

---

## 8. Personalization

- *LaMP: When Large Language Models Meet Personalization* (Salemi, Mysore, Bendersky, Zamani; ACL 2024, arXiv 2304.11406). Seven tasks (3 classification, 4 generation). It retrieves items from the **user profile** (BM25, Contriever, recency) and compares in-prompt augmentation with Fusion-in-Decoder. Retrieval augmentation helps both zero-shot and fine-tuned LLMs. https://aclanthology.org/2024.acl-long.399
- Follow-up LaMP-QA (personalized long-form QA) reports up to 39% gains from personalized context (per search summary, [UNVERIFIED] exact figure).
- Pattern: user-scoped memory (Mem0 `user_id`, Memory Bank `scope={"user_id":...}`) + profile retrieval + preference injection into the system prompt. Risks: privacy, stale preferences (use temporal invalidation, as in Graphiti), and filter bubbles.

---

## 9. Real-time / streaming RAG

- Problem: batch re-indexing causes staleness (prices, tickets, news, logs).
- **Pathway** (Rust engine on Differential Dataflow; Python ≥3.10; BSL 1.1 license, which converts to Apache 2.0 after 4 years). It has an LLM xpack (parsers, splitters, embedders) and an **in-memory real-time vector index**, and it updates results "whenever new (or late...) data points come into the system". https://github.com/pathwaycom/pathway
- Flow in words: source connector (Kafka / Drive / S3 / SharePoint) → incremental parse/chunk → embed only the delta → upsert into a live index → query sees fresh data within seconds. Deletes propagate too.
- The same idea in code RAG is Cursor's Merkle diff, which re-embeds only changed chunks (section 5).
- Alternative: **agentic live retrieval**, where tools hit live APIs or search (Google Search grounding, SQL) instead of an index.

---

## 10. On-device RAG

- **Google AI Edge RAG SDK** (Android; part of MediaPipe GenAI). It provides the building blocks of a RAG pipeline (chunk, embed, vector store, retrieve) on top of the **LLM Inference API**, running "completely on-device". The quickstart uses **Gemma 3 1B** as a `.task` file. Flutter wrapper `ai_edge_rag` (Android API ≥24; Pixel 7+ recommended). https://developers.google.com/edge/mediapipe/solutions/genai/rag and https://developers.googleblog.com/en/google-ai-edge-small-language-models-multimodality-rag-function-calling/ (exact Kotlin class names [UNVERIFIED]; the Android guide page returned 404 on fetch).
- **EmbeddingGemma** (announced Sep 4 2025): **308M params**, 2K context, 768-d with MRL truncation to 512/256/128, 100+ languages, under 200 MB RAM quantized. It was the top open multilingual embedder under 500M on MTEB at launch. https://developers.googleblog.com/en/introducing-embeddinggemma/
```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("google/embeddinggemma-300m", truncate_dim=256)
q = model.encode_query("Which planet is known as the Red Planet?")
d = model.encode_document(["Mars is often referred to as the Red Planet.",
                           "Jupiter has a prominent red spot."])
print(model.similarity(q, d))
```
Source: https://huggingface.co/blog/embeddinggemma
- Why on-device: privacy (data never leaves the phone), offline use, zero per-query cost, low latency. Limits: small models, RAM and battery, and index size. Multi-vector is usually too heavy; colSmol-256M (80.1 ViDoRe) is the small visual option.

---

## 11. Real-world examples
- **Cursor**: Merkle-tree incremental code indexing plus simhash index reuse (Jan 2026 blog).
- **Claude Code**: grep/glob agentic search instead of a vector DB (reported).
- **Google ADK + Memory Bank**: managed long-term memory for agents on Gemini Enterprise Agent Platform.
- **Mem0, Letta, Zep**: memory layers used as drop-in services for agent frameworks.
- **Docling (IBM)**: open-source document parsing for enterprise RAG ingestion.

---

## Slide ideas (8)
1. **"Your PDF is a picture"**: animate a financial report page being OCR'd into broken text (red X on the table), then the same page going into ColPali as a patch grid (green check). Visual: side-by-side pipelines.
2. **Late interaction / MaxSim, explained**: a heat-map grid of query tokens × page patches. Animate the max per row, then sum to a score. Overlay the ViDoRe score ladder (81.3 → 90.9).
3. **Single-vector vs multi-vector trade-off**: bar chart of index size (7.5 MB vs 311.5 MB vs 92 MB PLAID vs 78.8 MB pooled) against an accuracy arrow.
4. **One space for everything (Gemini Embedding 2)**: text, image, video, audio and PDF icons flowing into one 3072-d point cloud, with an MRL slider shrinking dims to 768.
5. **Code RAG in 2026: grep + LSP + embeddings**: a three-lane diagram. Animate the Cursor Merkle tree with changed branches lighting up, and show the TTFQ stats 4.03 h → 21 s.
6. **Memory lifecycle**: extract → consolidate (ADD/UPDATE/DELETE) → retrieve → inject loop, with Mem0, Letta, Zep and Memory Bank logos placed at the stage they emphasize. Footer: the comparison table.
7. **Time-travel memory (Graphiti)**: a timeline with the edge "Alice@Acme" fading (invalidated, not deleted) as "Alice@Google" appears, with the quote.
8. **RAG vs CAG decision tree**: corpus <200k tokens and static → cache it. Large or dynamic or ACL'd → RAG. Animate cost bars for cache write 1.25x vs read 0.1x.
9. **Freshness: streaming RAG**: a Kafka stream feeding an incremental index. Animate only the delta chunks being re-embedded.
10. **RAG in your pocket**: phone mockup with EmbeddingGemma (308M, <200 MB) plus Gemma 3 1B plus SQLite vectors, and an "airplane mode" badge.
