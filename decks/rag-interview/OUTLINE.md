# Interview drills: Retrieval-augmented generation, October 2026 - outline

Deck key: `rag-interview`. 28 slides, 6 chapters (opening + 5). Facts as of 2026-10-23. Follows engine/AUTHORING.md section 9.6: chapter openers, `.qa` slides with 3 Q&A pairs (each answer is its own step), one whiteboard (system-design prompt + animated reference architecture) and one debug-this slide (buggy code; the answer step highlights the bug with `data-focus`) per chapter.

Rules for authors: numbers and APIs come only from research-v2/rag (00-VERIFIED.md overrides). Label illustrative output and example latency budgets. Kicker for qa slides: `Interview`; whiteboard: `<span class="pill">Whiteboard</span> system design`; debug: `<span class="pill">Debug this</span> area`.

## Chapter 0: Opening  (tone: agent)

Scenario: The candidate's interview loop: one question, a strong answer with a number, the follow-up probe.

Research files:
- C:/Users/evija/googleadk2.0/research-v2/rag/00-VERIFIED.md
- C:/Users/evija/googleadk2.0/research-v2/rag/industry.md

### c00-01-opening.html - RAG interviews in 2026 test measurement, trade-offs and failure modes
- **id:** `rag-interview-c00-opening`
- **type:** opening
- **content:** Opening slide (.display). Display line: 'Interview drills: Retrieval-augmented generation'. Sub-line: 'October 2026'. Three count-up stats: 36 questions (12 Q&A slides x 3), 5 system-design whiteboards, 5 debug-this drills. A 4-item ul.ticks 'What the interviewer listens for': (1) you measure first (recall@k on a golden set, before any prompt change); (2) you name the trade-off with a number (latency, cost, recall); (3) you know how it fails in production (silent defaults, starved filters, judge NaNs); (4) you design under a budget (tokens, p95, memory). One .small line: chapters follow the pipeline - ingestion, indexes, retrieval quality, agentic and graph RAG, evaluation/security/production. Notes: tell students to answer aloud before each reveal; strong answers contain one mechanism, one number and one fix. Likely question: 'Are these real interview questions?' Answer: they match the trade-off, failure-mode and 'how would you build' questions that Google, Anthropic, OpenAI, Meta and startups ask AI engineers in 2026.
- **visual:** Bespoke Deck.register animation on the right half (700x520 SVG): the 'interview loop'. Four stations on a circle: Question (n-human violet), Mechanism (n-agent blue), Number (n-state green), Failure + fix (n-risk red). A token travels Question -> Mechanism -> Number -> Failure + fix -> back to Question on a deterministic 6 s gsap loop (killed in leave); each station pulses when the token arrives. Steps: (1) title + stats count up; (2) the ticks list staggers in, each tick lights the matching station; (3) the pipeline strip of five chapter chips (tool, state, agent, model, risk colours) draws left to right under the loop.

## Chapter 1: Foundations and ingestion  (tone: tool)

Scenario: Acme Insurance claims knowledge base: policy PDFs, an adjuster manual and a support FAQ that change every week.

Research files:
- C:/Users/evija/googleadk2.0/research-v2/rag/00-VERIFIED.md
- C:/Users/evija/googleadk2.0/research-v2/rag/lab-pipeline.md
- C:/Users/evija/googleadk2.0/research-v2/rag/lab-retrieval.md
- C:/Users/evija/googleadk2.0/research-v2/rag/gotchas.md
- C:/Users/evija/googleadk2.0/research-v2/rag/industry.md
- C:/Users/evija/googleadk2.0/research-v2/rag/arxiv-retrieval.md
- C:/Users/evija/googleadk2.0/archive/v1/rag/slides/c01-04-interview.html
- C:/Users/evija/googleadk2.0/archive/v1/rag/slides/c02-05-interview.html

### c01-01-chapter.html - Foundations and ingestion
- **id:** `rag-interview-c01-chapter`
- **type:** chapter
- **content:** Chapter opener (class 'slide chapter'). Chapter number 1. .display 'Foundations and ingestion'. One .lede: 'Most RAG failures start before the first query: in parsing, chunking and updates.' Three tags for the drills inside: 'When RAG', 'Chunking', 'Incremental ingest'. Notes: this chapter covers the screening questions; interviewers use them to see whether the candidate measures retrieval before tuning prompts.
- **visual:** Self-animating mini-diagram: a PDF page icon (n-tool) splits into 5 chunk bars (data-fx draw); each chunk drops into an index cylinder (n-state). One chunk turns red and is re-embedded (a hash label 'sha256 changed' flashes) while the others stay grey ('reused'). Deterministic 5 s gsap loop, killed in leave.

### c01-02-qa-when-rag.html - Choose RAG for facts, tuning for behaviour, and check recall first
- **id:** `rag-interview-c01-qa-when-rag`
- **type:** qa
- **content:** Three .qa pairs; each .a is its own data-step (1, 2, 3). Q1: 'When do you choose RAG over fine-tuning or one long prompt?' A1: RAG for fresh, private or permissioned facts and for citations: an update is a re-index, not a retrain. Fine-tune for behaviour, format and style. Use one long cached prompt when the corpus is small, static and has one permission level (Claude Haiku 5.5 caches prefixes from 512 tokens). Q2: 'Your RAG bot gives wrong answers. What do you check first?' A2: Recall@k on a labelled golden set. If the gold chunk is not in the top-k, the generator cannot fix it. Then separate retrieval failures from reasoning failures (arXiv 2609.33778). Measure 'all gold chunks found', not only hit@k: similarity retrieval finds any relevant chunk far more reliably than all required chunks (arXiv 2610.26951). Q3: 'Can an agent with grep and file tools replace the index?' A3: Not at scale. BM25 overtakes a file-system agent above about 10M corpus tokens, and the agent uses 39x the query tokens (arXiv 2607.26497). Dropbox measured federated MCP agent queries at up to 45 s against seconds for its index. Rank first, then let the agent reason. Cites: .cite.paper 2610.26951, 2607.26497; .cite.doc Dropbox 'VP Josh Clemm: knowledge graphs, MCP and DSPy in Dash' (https://dropbox.tech/machine-learning/vp-josh-clemm-knowledge-graphs-mcp-and-dspy-dash). Notes: Q1 is the most common screening question; analogy: fine-tuning teaches the doctor how to talk, retrieval hands the doctor today's lab results. Follow-up: 'How do you build the golden set?' Sample real user questions, label the chunk that answers each, keep it versioned.
- **visual:** Right column (40%): a small bespoke SVG per answer step. Step 1: a three-way decision tree (Facts? -> RAG; Behaviour? -> fine-tune; Small + static + one ACL? -> cached long prompt) draws itself. Step 2: a top-k list of 5 grey bars; the gold chunk (green) is missing, a red 'recall@5 = 0' badge pops, then a 'any vs all' pair of mini bars. Step 3: two lines drawn on a log x-axis (corpus tokens 1M..100M): agent accuracy line crosses below BM25 at ~10M; a '39x tokens' label counts up. Each step's figure gets data-step k data-until k+1 so one figure shows at a time.

### c01-03-qa-chunking.html - Chunking answers need an eval, a token budget and an update cost
- **id:** `rag-interview-c01-qa-chunking`
- **type:** qa
- **content:** Three .qa pairs, one step per answer. Q1: 'How do you choose a chunk size?' A1: Run an eval on a golden set, not a guess. Size chunks in the embedder's tokens. Keep real heading paths: they beat LLM-contextualised fixed windows (+0.022 / +0.012 cov-nDCG@10) and a shuffled-heading placebo, while naive two-stage hierarchical retrieval hurts (-0.033) (arXiv 2610.10170). Parser x chunker x embedder interact, so test them together (arXiv 2609.31660). Q2: 'Why can you afford Contextual Retrieval on every chunk, and how does it fail silently?' A2: Prompt caching. The whole document is the cached prefix and only the chunk changes after it. Claude Haiku 5.5 costs $0.10 / $0.50 per MTok. The cache minimum is 512 tokens (4,096 on Haiku 4.5); below it nothing is cached and no error is returned: cache_creation_input_tokens stays 0. Do it once at ingest and store the context. Q3: 'A one-line edit re-embeds half the document. Why, and what is the fix?' A3: Chunk-boundary drift. On real revisions, fixed-size chunking recomputes 57-68% of the embeddings, recursive 38-56% and content-defined 43-54%, with recall within 2 points (arXiv 2610.31019). Key chunks by sha256 of the text and embed only unseen hashes. Notion hashes each span and cut data volume by 70%. Cites: .cite.paper 2610.10170, 2610.31019; .cite.repo claude-cookbooks 'Enhancing RAG with Contextual Retrieval'; .cite.doc Notion 'Two years of vector search at Notion' (https://www.notion.com/blog/two-years-of-vector-search-at-notion). Notes: listen for 'measure', 'tokens not characters' and 'update cost'. Follow-up: 'How do you keep parent and child chunks in sync?' Re-chunk the document, delete old children by document id, upsert.
- **visual:** Bespoke SVG chunk animation (Deck.register): a document bar of 12 paragraphs. Step 1: heading bands (state green) appear and chunk boundaries snap to them. Step 2: a cache icon fills on chunk 1 ('cache write'), chunks 2..n show 'cache read' ticks; a red '511 tokens -> no cache' variant flashes. Step 3: one paragraph is edited; with fixed-size boundaries 7 of 12 chunks turn red (re-embed), then with hash-keyed recursive chunks only 1 chunk turns red. Counter shows 're-embedded: 7/12' then '1/12' (illustrative).

### c01-04-wb-ingestion.html - Whiteboard: ingest 2M changing policy PDFs with page citations
- **id:** `rag-interview-c01-wb-ingestion`
- **type:** whiteboard
- **content:** Kicker 'Whiteboard'. Prompt panel (k-human): 'Design ingestion for Acme Insurance: 2M policy PDFs (some scanned), about 1% change each day, answers must cite the page. Budget: re-embedding cost.' Step-by-step reference answer beside the diagram as a short ol.seq (one item per step): (1) Detect change: content hash per file and per span; skip unchanged (Notion: per-span hashes, 70% less data volume). (2) Parse with layout: Docling (do_ocr default True), keep page numbers as provenance; route scanned pages to OCR. (3) Chunk by structure, sized with the embedder's tokenizer (Docling HybridChunker). (4) Enrich once at write time: heading path or a cached LLM context per chunk; 'RAG Deserves an Index' compiled claims reached 85.2% at ~2.2k reader tokens vs 72.5% at 16.3k (arXiv 2608.20845). (5) Embed and upsert with metadata: doc_id, page, acl_groups, embedding_model, embedding_version. (6) Guard: hidden-text canary PDF and page-count conservation in CI (unstructured issue: invisible text becomes a prompt-injection path). Numbers strip: fixed-size re-embeds 57-68% per revision vs 38-56% recursive (2610.31019). Notes: the interviewer wants the day-2 problem (updates and deletes), not only the first load; follow-up: 'How do deletes work?' delete by doc_id, then rebuild or use in-place deletes.
- **visual:** Large animated reference architecture (diagram 900x560, Deck wires, 6 steps). Nodes: Bucket (n-tool, 'GCS / S3'), Change detector (n-state, 'sha256 per span'), Parser (n-tool, 'Docling + OCR'), Chunker (n-tool, 'HybridChunker'), Enricher (n-model, 'heading path / LLM ctx'), Embedder (n-model), Index (n-state, 'vectors + metadata'), CI guard (n-risk). Wires: bucket>detect@1:flow; detect>parse@2 [changed only]; parse>chunk@3; chunk>enrich@4; enrich>embed@5:flow{model}; embed>index@5:flow{state}; guard>parse@6:dash{risk} [canary PDF]. A ghost 'unchanged 99%' pill branches from the detector to the index at step 1 (dim). Each ol.seq item reveals with the same step number.

### c01-05-debug-truncation.html - Debug this: the appeal deadline is in the index but never retrieved
- **id:** `rag-interview-c01-debug-truncation`
- **type:** debug
- **content:** Kicker '<span class="pill">Debug this</span> ingestion'. Prompt line: 'Users ask for the appeal deadline. The rule is in chunk 12, but retrieval never returns it. Find the bug.' Code block (left, data-focus answer step). Step 1: show code and the symptom output pane ('the appeal rule sits at character 1,600 of chunk 12'). Step 2 (answer): data-focus on the splitter line and the encode line; .gotcha card: Symptom 'text in the tail of long chunks is unsearchable; no warning'; Cause 'Sentence Transformers truncates every input to max_seq_length (256 tokens for all-MiniLM-L6-v2). chunk_size=2000 counts characters, so most of each chunk is cut off before embedding'; Fix 'size chunks in model tokens and assert nothing is truncated'. Step 3: .code-wrap.good fix: splitter = RecursiveCharacterTextSplitter.from_huggingface_tokenizer(model.tokenizer, chunk_size=240, chunk_overlap=0) plus the assert from gotchas B1 (too_long = [i for i, c in enumerate(chunks) if len(model.tokenizer(c)['input_ids']) > model.max_seq_length]; assert not too_long). Source: sentence-transformers issue #4060 (open, 2026-09-21). Pins: sentence-transformers==6.2.0, langchain-text-splitters==1.1.3. Notes: log 'truncated %' at ingestion and keep it at 0.
- **visual:** Left: code block (.sm) with data-focus '2:6, 2:10' on the answer step. Right: bespoke SVG - chunk 12 drawn as a long bar of 2,000 characters; at step 2 a scissors line cuts it at the 256-token mark, the tail (containing the highlighted 'appeal within 60 days' text, illustrative) fades to grey with label 'never embedded'. Step 3: the bar splits into token-sized chunks that all fit under the 256 line, and a green 'truncated: 0%' counter appears.
- **code (buggy version shown on the slide):**

```python
# ingest_claims.py -- chunk the claims manual and embed it
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)

text = open("claims_manual.md", encoding="utf-8").read()
chunks = splitter.split_text(text)
vecs = model.encode(chunks, normalize_embeddings=True)
print(len(chunks), "chunks", vecs.shape)

q = model.encode("deadline to appeal a denied claim", normalize_embeddings=True)
top = (vecs @ q).argsort()[::-1][:5]
print("top-5 chunks:", top.tolist())   # chunk 12 is never in the list
```

## Chapter 2: Embeddings and vector indexes  (tone: state)

Scenario: Northwind support-ticket KB and Acme claims chunks in FAISS, pgvector and Chroma, with tenants and a model upgrade coming.

Research files:
- C:/Users/evija/googleadk2.0/research-v2/rag/00-VERIFIED.md
- C:/Users/evija/googleadk2.0/research-v2/rag/lab-pipeline.md
- C:/Users/evija/googleadk2.0/research-v2/rag/gotchas.md
- C:/Users/evija/googleadk2.0/research-v2/rag/industry.md
- C:/Users/evija/googleadk2.0/research-v2/rag/arxiv-retrieval.md
- C:/Users/evija/googleadk2.0/archive/v1/rag/slides/c03-05-interview.html

### c02-01-chapter.html - Embeddings and vector indexes
- **id:** `rag-interview-c02-chapter`
- **type:** chapter
- **content:** Chapter opener. Chapter number 2. .display 'Embeddings and vector indexes'. .lede: 'Index questions are memory arithmetic plus one recall check against exact search.' Tags: 'ANN parameters', 'Model migration', 'Filtered search'. Notes: interviewers expect back-of-envelope maths and the silent defaults.
- **visual:** Self-animating mini-diagram: 40 points (state green) appear in a 2-D space by index-based positions; a query point (human violet) drops in and an HNSW-style path hops across 4 nodes to its 3 nearest neighbours, which glow. Deterministic 6 s loop, killed in leave.

### c02-02-qa-ann.html - ANN design answers start with memory maths and end with recall
- **id:** `rag-interview-c02-qa-ann`
- **type:** qa
- **content:** Three .qa pairs, one step per answer. Q1: 'Design an index for 1B vectors on a tight memory budget.' A1: Compress first: cut dimensions with Matryoshka (MRL) truncation, then int8 or binary. Keep compressed codes in RAM and the graph or full vectors on SSD (DiskANN, IVF-PQ). RaBitQ-SSD served 10B vectors at about 3,200 QPS at 90% recall on one server (arXiv 2610.02652). Re-score the top candidates with full vectors and measure recall@k against exact search on a sample. Q2: 'What do HNSW M, efConstruction and efSearch change, and what are the defaults?' A2: M is graph degree (memory and recall). efConstruction is build quality (build time). efSearch is the query beam: more recall, more latency, set per query. Defaults differ: FAISS efConstruction 40 / efSearch 16 and IVF nprobe 1; pgvector ef_search 40; Chroma ef_construction 100 / max_neighbors 16 / ef_search 100. Re-tune when the corpus grows 10x: graph-search cost grows as a power of N (arXiv 2609.02143). Q3: 'Estimate RAM for 10M gemini-embedding-001 vectors, then cut it.' A3: 10M x 3,072 x 4 B = about 123 GB float32. 768 dims: about 31 GB; int8: about 7.7 GB; 768-bit binary: about 0.96 GB. Normalise 001 vectors yourself below 3,072 dims. Check hard queries: a good mean can hide large per-example neighbour loss (arXiv 2610.17742). Cites: .cite.paper 2610.02652, 2609.02143, 2610.17742; .cite.doc Gemini API 'Embeddings' (https://ai.google.dev/gemini-api/docs/embeddings). Notes: expected structure for Q1 = compress, memory-light index, re-score, prove with recall@k. Follow-up: 'Where does efSearch live in pgvector?' SET hnsw.ef_search per session or transaction.
- **visual:** Step 1: stacked bar memory waterfall (bespoke gsap): 123 GB -> 31 GB -> 7.7 GB -> 0.96 GB bars shrink in sequence with count-down numbers (this is the Q3 maths, shown under A1 as the compression path; label 'per 10M vectors'). Step 2: a small recall-vs-latency curve draws itself with three dots labelled efSearch 16 / 64 / 256 (shape illustrative, axes labelled 'illustrative'). Step 3: a defaults table (table.t, 3 rows FAISS / pgvector / Chroma) with the default cells flashing amber. One figure per step (data-until).

### c02-03-qa-migrate-filter.html - Model swaps and filters break vector search without an error
- **id:** `rag-interview-c02-qa-migrate-filter`
- **type:** qa
- **content:** Three .qa pairs, one step per answer. Q1: 'Can you query a gemini-embedding-001 index with gemini-embedding-2 vectors? How do you migrate?' A1: No. The two models make different vector spaces. Blue/green: build the new index side by side, dual-read on the golden set, switch in one step, keep the old one for rollback. A 50/50 mixed index recovered only 4.96 of the 11.90-point re-embed gain, and retrieval caused 81% of the deficit (arXiv 2609.05339). Store embedding_model and embedding_version per vector; assert one version per result set. Q2: 'A filtered top-10 in pgvector returns 3 rows. Why?' A2: The filter runs after the index scan. pgvector README: 'If a condition matches 10% of rows, with HNSW and the default hnsw.ef_search of 40, only 4 rows will match on average.' Fix: SET hnsw.iterative_scan = relaxed_order (0.8.0+) with hnsw.max_scan_tuples, or partial indexes / partitions per tenant. Test rowcount == LIMIT. Q3: 'Cosine and dot-product rankings disagree after you cut dimensions. Why?' A3: gemini-embedding-001 is not normalised below 3,072 dims (gemini-embedding-2 auto-normalises). FAISS METRIC_INNER_PRODUCT is cosine only for unit vectors: call faiss.normalize_L2 on data and queries. Assert unit norm at write time. Cites: .cite.paper 2609.05339; .cite.repo pgvector README 'Filtering' (https://github.com/pgvector/pgvector/blob/master/README.md#filtering); .cite.doc Faiss wiki 'MetricType and distances'. Notes: Q2 is the most common pgvector surprise; analogy for Q1: GPS coordinates from two map projections cannot be compared.
- **visual:** Bespoke SVG per step. Step 1: two coloured point clouds (v1 green, v2 blue) in separate spaces; a query from v2 lands in v1's space and picks wrong neighbours (red lines); then a blue/green switch toggle flips. Step 2: an ef_search beam of 40 candidates as dots; a filter mask removes 90%, leaving 4 green dots, then iterative_scan keeps scanning until 10 are found (counter 4 -> 10). Step 3: two vectors of different lengths with the same angle; dot-product ranking bar swaps order, normalisation fixes it.

### c02-04-wb-multitenant.html - Whiteboard: a vector store for 10,000 tenants with per-user ACLs
- **id:** `rag-interview-c02-wb-multitenant`
- **type:** whiteboard
- **content:** Prompt panel (k-human): 'Design the vector layer for a B2B SaaS: 10,000 tenants (a few huge, most tiny), per-user document permissions, and an embedding-model upgrade next quarter. No tenant may affect another tenant's recall.' Reference answer as ol.seq, one item per step: (1) Identity from the authenticated user's token (groups claim), never from the prompt. (2) Isolation: big tenants get their own partition or namespace; small tenants share an index with a tenant filter applied inside the search (pgvector README recommends partitions or separate tables for multitenancy). (3) ACL as group IDs in metadata, filtered inside the ANN and BM25 queries, before fusion and rerank; iterative scan so filtered queries still return k. (4) Versioning: embedding_version column / named vector; blue/green index per version (Notion cut over 'generation by generation' and used the migration to upgrade the embedder). (5) Tests in CI: rowcount == LIMIT for selective filters, leak test for every user x golden query, one embedding_version per result set. Numbers: Notion p50 70-100 ms -> 50-70 ms after turbopuffer, 60% lower search spend; mixed-version index recovers 4.96 of 11.90 points (2609.05339); multi-tenant filtered recall loss = staleness + filtered navigability (arXiv 2610.15130). Notes: red flags = service account identity, post-filter after ranking, one shared index for all tenants without partitions. Follow-up: 'What happens when a user leaves a group?' Store groups, not users, so membership changes need no re-index.
- **visual:** Large animated architecture (900x560, 5 steps). Nodes: User (n-human pill, 'OIDC token'), Auth (n-tool, 'groups claim'), Tenant router (n-agent), Partition A (n-state, 'big tenant'), Shared index (n-state, 'tenant + ACL filter'), Index v2 (n-state ghost, 'blue/green'), Leak test (n-risk). Wires: user>auth@1:flow{human}; auth>router@1 [groups]; router>partA@2; router>shared@2 [filter inside]; shared>v2@4:dash [dual-read]; leak>shared@5:dash{risk}. Step 3 animates a filter mask on the shared index node (dots inside it dim except allowed ones). Step 4 flips a toggle from v1 to v2.

### c02-05-debug-embed-batch.html - Debug this: four tickets embedded, one row in the index
- **id:** `rag-interview-c02-debug-embed-batch`
- **type:** debug
- **content:** Kicker '<span class="pill">Debug this</span> embeddings'. Prompt: 'The script indexes 4 tickets and prints indexed 1. No exception. Find the bug.' Step 1: code + output pane (output · illustrative: 'indexed 1'). Step 2 (answer): data-focus on contents=texts and on the zip loop. .gotcha: Symptom 'one vector comes back for a list of strings; zip() stops after the first pair, so 3 tickets are silently dropped'; Cause 'Gemini API docs: adding multiple inputs directly to contents produces one aggregated embedding for all inputs (gemini-embedding-2)'; Fix 'wrap each input in its own Content and assert len(embeddings) == len(inputs)'. Step 3: .code-wrap.good: contents=[types.Content(parts=[types.Part.from_text(text=t)]) for t in texts] and assert len(resp.embeddings) == len(texts); add zip(..., strict=True). Pins: google-genai==2.33.0, chromadb==1.5.9. Source: llama_index issue #21658 and Gemini API 'Embeddings'. Notes: one assert on vector count catches a whole class of bugs (also Qdrant upload_collection and add_texts(generator)).
- **visual:** Left: code (.sm) with data-focus on the answer step '2:17, 2:19'. Right: bespoke gsap animation - four ticket cards fly into an 'embed_content' box; step 1 shows one merged vector strip coming out; step 2 the zip arrow connects TKT-1042 to that vector and three cards fall off with a red 'dropped' label; step 3 four separate Content boxes go in and four vector strips come out, a green 'assert 4 == 4' badge pops.
- **code (buggy version shown on the slide):**

```python
# index_tickets.py -- embed resolved tickets into Chroma
import chromadb
from google import genai
from google.genai import types

client = genai.Client()                                   # reads GEMINI_API_KEY
col = chromadb.PersistentClient(path="kb").get_or_create_collection("tickets")
TICKETS = {
    "TKT-1042": "Login loop after Okta SSO: clear the stale session cookie.",
    "TKT-1077": "Claim PDF upload fails: files over 20 MB are rejected.",
    "TKT-1103": "Refund not received: refunds post 5-7 business days after approval.",
    "TKT-1150": "Duplicate premium charge: void the second authorization.",
}
ids, texts = list(TICKETS), list(TICKETS.values())
resp = client.models.embed_content(
    model="gemini-embedding-2",
    contents=texts,
    config=types.EmbedContentConfig(output_dimensionality=768))
for tid, emb in zip(ids, resp.embeddings):
    col.upsert(ids=[tid], embeddings=[emb.values], documents=[TICKETS[tid]])
print("indexed", col.count())
```

## Chapter 3: Retrieval quality: hybrid, rerank, rewrite  (tone: agent)

Scenario: Northwind outdoor-gear support search: error codes like 'E-4012', paraphrased complaints and a cross-encoder second stage.

Research files:
- C:/Users/evija/googleadk2.0/research-v2/rag/00-VERIFIED.md
- C:/Users/evija/googleadk2.0/research-v2/rag/lab-retrieval.md
- C:/Users/evija/googleadk2.0/research-v2/rag/arxiv-retrieval.md
- C:/Users/evija/googleadk2.0/research-v2/rag/gotchas.md
- C:/Users/evija/googleadk2.0/research-v2/rag/industry.md
- C:/Users/evija/googleadk2.0/archive/v1/rag/slides/c04-09-interview.html

### c03-01-chapter.html - Retrieval quality: hybrid, rerank, rewrite
- **id:** `rag-interview-c03-chapter`
- **type:** chapter
- **content:** Chapter opener. Chapter number 3. .display 'Retrieval quality'. .lede: 'Each stage can make single queries worse while the mean goes up. Strong answers say how they would see that.' Tags: 'Hybrid + RRF', 'Rerankers', 'Query rewriting', 'Sufficiency'. Notes: the most-asked RAG design area in 2026 interviews.
- **visual:** Self-animating funnel: 150 candidate dots (two colours: BM25 amber, dense green) pour into an RRF funnel, 30 come out, a cross-encoder gate reorders them, 8 reach an LLM node. Deterministic loop, killed in leave.

### c03-02-qa-hybrid.html - Hybrid search: fuse ranks, pin the defaults, watch the fusion tax
- **id:** `rag-interview-c03-qa-hybrid`
- **type:** qa
- **content:** Three .qa pairs, one step per answer. Q1: 'Why RRF instead of averaging BM25 and cosine scores?' A1: The scales differ: BM25 is unbounded and cosine is -1..1. RRF uses only ranks: score = sum of 1/(k + rank), k = 60 in the paper. When you can tune on labels, tune one static weight first: optimal weighted-RRF weights form intervals, and 74 of 128 dynamic methods beat plain RRF (arXiv 2610.24341). Q2: 'Can hybrid search be worse than dense alone?' A2: Yes. The Fusion Tax paper found the best fusion still ranks relevant documents below dense-only on 8-21% of queries; RRF wins only when the two retrievers are balanced (arXiv 2610.30612). Print the per-query 'got worse' list, not only the mean. Q3: 'You moved hybrid into Qdrant and BM25 into bm25s. Quality changed. What do you check?' A3: Silent defaults. Qdrant's DEFAULT_RANKING_CONSTANT_K is 2, not 60: pin it. The bm25s token pattern \b\w\w+\b drops the one-letter 'E' in 'E-4012': normalise codes the same way on corpus and query. Weaviate's hybrid alpha default depends on the client. Cites: .cite.paper 2610.30612, 2610.24341; .cite.repo xhluca/bm25s; .cite.doc Qdrant 'Hybrid queries'. Notes: Q2 is the 2026 counter-intuitive result; analogy: two judges with different scoring scales - compare their rankings, not their points.
- **visual:** Step 1: bespoke two-column rank animation: BM25 list and dense list, lines connect the same doc IDs, RRF scores count up beside each fused row (1/(60+r)). Step 2: a histogram of per-query delta (fusion minus dense) with a red tail labelled '8-21% of queries worse'. Step 3: three 'default' chips (Qdrant k=2, bm25s pattern, Weaviate alpha) flip from grey to amber; the 'E-4012' token splits into 'E' (crossed out) and '4012', then glues into 'E4012'.

### c03-03-qa-rerank.html - Rerankers reorder candidates; they cannot find what you missed
- **id:** `rag-interview-c03-qa-rerank`
- **type:** qa
- **content:** Three .qa pairs, one step per answer. Q1: 'You retrieve 150 and rerank to 20. What does it cost, and how do you cut it?' A1: One cross-encoder pass per pair. On an H100 (bf16) Ettin-17M scores 7,517 pairs/s and Ettin-1B 928; on CPU 267 vs 2.1. Google's ranking API runs under 100 ms; an LLM reranker takes 1-2 s. Cap candidates, rerank child chunks, and spend the budget on the top-k boundary when it is below the context size (BoundaryMORPH, arXiv 2609.27213). Q2: 'Reranking raised Hit@10 a lot, but answers barely improved. Why?' A2: On clinical notes, reranking lifted Hit@10 from 46.6% to 60.6% but answer correctness only from 44.8% to 48.6% (arXiv 2610.01324). A reranker cannot raise recall@N of its candidates, and the bottleneck may be reading or sufficiency. Measure answer quality per stage. Q3: 'A new ranker wins pairwise preference. Ship it?' A3: Not yet. On NevIR a ranker raised pairwise preference (56.62% vs 52.30%) while cutting MRR from 0.5764 to 0.3055 (arXiv 2610.26260). Zero-shot LLM rerankers also tie: Glean's Jev gave identical scores to about 37 of 41 candidates. Measure MRR and cost together. Cites: .cite.paper 2609.27213, 2610.01324, 2610.26260; .cite.doc Hugging Face 'Ettin reranker' blog (huggingface.co/blog/ettin-reranker). Notes: listen for 'count forward passes' in Q1.
- **visual:** Step 1: bespoke throughput race - two horizontal bars count up to 7,517 and 928 pairs/s, then a timer converts 150 pairs into milliseconds for each (150/7517 = 20 ms, 150/928 = 162 ms, labelled 'GPU, compute only'). Step 2: paired bars Hit@10 46.6 -> 60.6 vs correctness 44.8 -> 48.6 (data-fx bar, count-up). Step 3: two gauges: preference up (52.30 -> 56.62, green) while MRR drops (0.5764 -> 0.3055, red).

### c03-04-qa-rewrite-sufficiency.html - Rewrite or escalate only when a cheap signal says retrieval is weak
- **id:** `rag-interview-c03-qa-rewrite-sufficiency`
- **type:** qa
- **content:** Three .qa pairs, one step per answer. Q1: 'Should every query go through an LLM rewrite or HyDE?' A1: No. Under a strong baseline one rewriter is at best on par; a union of rewriters gave +12.5 HIT@10 (51.70 vs 39.22), and a score-gated router rewrites fewer than 40% of queries (arXiv 2609.05637). HyDE adds 57.5 unsupported terms per query, Query2doc 27.8, SAFE-QE 4.3 at equal nDCG@10 (arXiv 2610.13810). Snap routes about 10% of users to the LLM path: -90% LLM cost, +27.6% CVR. Q2: 'How do you know the evidence is sufficient before you generate?' A2: Gate before generation. Score-distribution QPP predicts sufficiency at AUROC 0.856 in 2 ms, against 0.649 for a local LLM judge (arXiv 2609.11646). Without a gate, generators answer 40.0-99.3% of insufficient-evidence questions even when told to abstain (arXiv 2609.37469). Q3: 'When do you escalate from RAG to the full long context?' A3: Only when uncertainty is high. Entropy-gated routing kept 97.4% of long-context accuracy with 70.7% fewer tokens (arXiv 2609.35831, a pattern without code). In multi-turn chat, merge the constraints into one standalone query first: sharded multi-turn queries lose up to 21% relative (arXiv 2609.36700). Cites: .cite.paper 2609.05637, 2610.13810, 2609.11646, 2607.23121. Notes: the theme is adaptive compute: cheap path first, escalate on a signal.
- **visual:** Bespoke router animation: a stream of 10 query tokens hits a 'score gate' diamond. Step 1: 4 of 10 go to the rewrite lane (amber), 6 go straight (green); counter 'rewritten 40%'. Step 2: a QPP score-distribution curve draws; a flat curve flags 'insufficient' (red) and stops before the LLM node, a peaked curve passes. Step 3: an escalation arrow from the RAG node to a wide 'long context' node lights only for the high-entropy token; token counter shows '-70.7% tokens'.

### c03-05-wb-support-search.html - Whiteboard: support search for error codes and paraphrases
- **id:** `rag-interview-c03-wb-support-search`
- **type:** whiteboard
- **content:** Prompt panel (k-human): 'Design retrieval for Northwind's support bot. Queries mix exact codes ("E-4012 at checkout") and paraphrases ("box came crushed"). Retrieval budget: p95 under 300 ms. Show how you would know it works.' Reference answer, ol.seq one item per step: (1) Normalise identifiers once, shared by corpus and query ('E-4012' -> 'E4012'). (2) BM25 and dense in parallel, depth 50 each, capped at corpus size. (3) Fuse with RRF, k pinned to 60, or one tuned static weight. (4) Rerank the top 30 with a small cross-encoder and keep 8 for the reader (child chunks, max_length 512). (5) Score-gated escape: QPP / top-score check; only weak queries get a multi-query rewrite. (6) Eval harness: recall@5, MRR, nDCG on a labelled set, plus the per-query 'got worse' list after each stage. Numbers: Ettin-17M 7,517 pairs/s (H100), Google ranking API under 100 ms, Atlassian Rovo p90 125 -> 60 ms on turbopuffer, Perplexity search p50 358 ms. Example span budget labelled 'example budget': normalise 1 ms, BM25 + dense 60 ms, RRF 1 ms, rerank 80 ms, slack for p95. Notes: the interviewer wants stage-by-stage measurement and a latency budget per span. Follow-up: 'Where do you put ACLs?' inside both retriever queries, before RRF.
- **visual:** Large animated architecture (920x560, 6 steps): Query (n-human pill), Normaliser (n-tool), BM25 (n-tool), Dense (n-state), RRF (n-agent), Cross-encoder (n-model), Gate (n-risk diamond-like round), Rewriter (n-model ghost), Reader LLM (n-model). Wires: q>norm@1:flow; norm>bm25@2; norm>dense@2; bm25>rrf@3 [top 50]; dense>rrf@3 [top 50]; rrf>ce@4 [top 30]; ce>llm@4 [keep 8]. Step 5 shows gate>rewriter:dash{risk} [weak only] looping back to norm. Step 6: a latency waterfall (bespoke SVG) draws under the diagram with the example budget spans filling left to right.

### c03-06-debug-rerank.html - Debug this: after reranking, recall falls to almost zero
- **id:** `rag-interview-c03-debug-rerank`
- **type:** debug
- **content:** Kicker '<span class="pill">Debug this</span> reranking'. Prompt: 'Hybrid alone gives R@5 = 0.93. With the reranker, almost nothing comes back and the rest is wrong. Two bugs.' Step 1: code + output pane (output · illustrative: '[3, 0]' then 'R@5=0.07'). Step 2 (answer 1): data-focus on the return line: corpus_id is the position in the list you passed (0-19), not your chunk ID; map back with cand_ids[h['corpus_id']]. Step 3 (answer 2): data-focus on 'h["score"] > 0.5': cross-encoder/ms-marco-MiniLM-L6-v2 sets an Identity activation, so rank() returns raw logits (about -11 to +11); a 0.5 threshold drops good results. Rank only, or pass activation_fn=torch.nn.Sigmoid() and tune the threshold on labels. Step 4: .code-wrap.good fixed return line: return [cand_ids[h['corpus_id']] for h in hits]. Pins: sentence-transformers==6.2.0. Source: research lab-retrieval Lab 5 (verified against the 6.2.0 source). Notes: the same position-index trap exists in the Cohere and Voyage rerank APIs (they return an index into your list).
- **visual:** Left: code with data-focus '2:11, 3:11' (both bugs on the same line; step 2 focus band labels 'corpus_id', step 3 band labels 'score'). Right: bespoke SVG - step 2: candidate list c11, c04, c31... with position numbers 0,1,2; arrows show the reranker returning '3' and the code storing 3 instead of 'c18'. Step 3: a logit axis from -11 to +11 with dots for the 5 hits (6.91, -2.48, -6.10, -9.73, -10.42, illustrative from the lab); a red line at 0.5 cuts all but one. Step 4: green fixed list.
- **code (buggy version shown on the slide):**

```python
# rerank.py -- hybrid top-20 -> cross-encoder -> top-5
from sentence_transformers import CrossEncoder
from kb import TEXT                    # chunk_id -> text
from lab3_hybrid import hybrid_search  # query -> ranked chunk_ids

reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L6-v2", max_length=512)

def rerank_search(query: str, candidates: int = 20, keep: int = 5) -> list[str]:
    cand_ids = hybrid_search(query)[:candidates]
    hits = reranker.rank(query, [TEXT[i] for i in cand_ids], top_k=keep)
    return [h["corpus_id"] for h in hits if h["score"] > 0.5]

print(rerank_search("zipper broke on my pack after 3 years"))
```

## Chapter 4: Agentic, graph and memory RAG  (tone: model)

Scenario: Acme Outfitters refund agent (router + retriever + verifier loop) and a deep-research feature for the claims team.

Research files:
- C:/Users/evija/googleadk2.0/research-v2/rag/00-VERIFIED.md
- C:/Users/evija/googleadk2.0/research-v2/rag/lab-agentic.md
- C:/Users/evija/googleadk2.0/research-v2/rag/arxiv-agentic.md
- C:/Users/evija/googleadk2.0/research-v2/rag/arxiv-eval-graph.md
- C:/Users/evija/googleadk2.0/research-v2/rag/industry.md
- C:/Users/evija/googleadk2.0/archive/v1/rag/slides/c05-07-interview.html
- C:/Users/evija/googleadk2.0/archive/v1/rag/slides/c06-06-interview.html
- C:/Users/evija/googleadk2.0/archive/v1/rag/slides/c07-06-interview.html
- C:/Users/evija/googleadk2.0/archive/v1/rag/slides/c08-05-interview.html

### c04-01-chapter.html - Agentic, graph and memory RAG
- **id:** `rag-interview-c04-chapter`
- **type:** chapter
- **content:** Chapter opener. Chapter number 4. .display 'Agentic, graph and memory RAG'. .lede: 'Loops, graphs and memories must beat the strong simple baseline, and their budgets live in code.' Tags: 'Routers', 'Stop conditions', 'GraphRAG cost', 'Temporal memory', 'Deep research'. Notes: interviewers probe whether the candidate defaults to agents or earns them.
- **visual:** Self-animating mini-graph: router (n-agent) -> retrieve (n-state) -> generate (n-model) -> verify (n-risk); a token loops verify -> generate twice, a counter 'tries 1/2, 2/2' increments, then the token exits to 'publish' or 'fallback'. Deterministic loop, killed in leave.

### c04-02-qa-agentic.html - Agentic RAG earns its latency only with routes, budgets and stops
- **id:** `rag-interview-c04-qa-agentic`
- **type:** qa
- **content:** Three .qa pairs, one step per answer. Q1: 'Design an assistant that sometimes needs SQL, sometimes documents and sometimes nothing.' A1: Put a constrained router first: an enum (vector | sql | web | none) with structured output, so it cannot invent a source. Simple uncertainty or score triggers often match learned 'when to retrieve' routers (arXiv 2607.24010). Evaluate routing accuracy apart from answer quality. Cost of going agentic: Airbnb's SKILL.md + one hybrid search tool reached 99.2% procedural equivalence but took about 90 s against 8-9 s for the fixed pipeline (arXiv 2610.14428). Q2: 'How do you stop an agentic RAG loop?' A2: Put the budget in code: a counter in state and a route on it, plus a fallback answer. LangGraph's default recursion limit is now 10007, so set recursion_limit too. Early stopping cut about 11% of iterations at about 98% quality (arXiv 2609.16453); in long-horizon search, 77.5-93.6% of episodes add no new evidence (arXiv 2608.01913). Q3: 'Self-RAG or CRAG with a closed API model?' A3: CRAG. It wraps any generator with a separate retrieval evaluator and a fallback search. Self-RAG needs a model fine-tuned to emit reflection tokens, which you cannot train into a hosted model. Watch abstention: iterative RAG lowered correct abstention in 30 of 40 configurations (arXiv 2610.28340). Cites: .cite.paper 2610.14428, 2609.16453, 2610.28340; .cite.doc LangGraph 'Build a custom RAG agent'. Notes: analogy for Q3: you can add a smoke detector to any house, but you cannot rewire a rented flat.
- **visual:** Step 1: router diamond fans to 4 lanes (vector, sql, web, none) with a structured-output JSON chip; a speed comparison bar '~90 s vs 8-9 s' animates. Step 2: a loop ring with a counter badge that increments 1, 2, 3 and then breaks to a 'fallback' node; a '10007' default label is crossed out and replaced by '25'. Step 3: two side-by-side boxes: CRAG (wrapper around a sealed model box, evaluator + fallback attached) vs Self-RAG (model box opened with reflection tokens [Retrieve] [ISREL] [ISSUP] inside, lock icon on the hosted model).

### c04-03-qa-graph-memory.html - Graphs and memory must beat a strong naive-RAG baseline first
- **id:** `rag-interview-c04-qa-graph-memory`
- **type:** qa
- **content:** Three .qa pairs, one step per answer. Q1: 'When is GraphRAG worth its indexing cost?' A1: For corpus-wide sensemaking over a stable corpus. Price the structure: using the graph only to locate passages and answering from source text beat LightRAG-hybrid on 93 of 120 comparisons at 57% lower cost (EffiRAG, arXiv 2609.18099). LLM-free traversal gave more than 100x lower latency and over 99% lower cost than GraphRAG Global/DRIFT (LiteRAG, arXiv 2609.10239). Community summaries are an attack surface: 88-94% attack success by modifying 0.016% of them (arXiv 2610.02373). Q2: 'The user says "I moved to Berlin." Design the memory update.' A2: Extract the fact, find conflicting memories in this user's scope, close the old one with valid_from / valid_to, and keep history. Plain RAG served superseded code facts 36-38% of the time; a supersession memory reached 0.91 vs 0.57-0.59 (arXiv 2608.20685). Stale documents flip 30% (Llama) / 37% (Qwen) of correct answers (arXiv 2609.31342). Q3: 'Do you need a complex agent-memory system?' A3: Build the simple baseline first. Dense + rerank over raw history ranked first in 6 of 7 memory-benchmark settings (arXiv 2610.30755). Agent-controlled BM25 over raw chat beat structured memory, 58.2 vs 53.2 (ReFind, arXiv 2608.12888). Cites: .cite.paper 2609.18099, 2608.20685, 2610.30755. Notes: Q2 checks user scoping and temporal invalidation, not overwrite.
- **visual:** Step 1: a small knowledge graph draws (nodes + edges); a query lights 3 nodes, then arrows drop from those nodes to raw passages (green) - 'locate with graph, answer from text'; a cost bar shrinks by 57%. Step 2: a timeline bar 'city': Paris (2019-2026, closes) -> Berlin (2026-), the old fact greys but stays; a query 'where did I live last year?' points to Paris. Step 3: a leaderboard bars animation: 'naive RAG (dense + rerank)' bar rises to rank 1 in 6 of 7 settings (six gold ticks, one grey).

### c04-04-wb-deep-research.html - Whiteboard: a deep-research feature with a fixed token budget
- **id:** `rag-interview-c04-wb-deep-research`
- **type:** whiteboard
- **content:** Prompt panel (k-human): 'Design a deep-research feature for Acme's claims team: one question in, a cited report out in under 10 minutes, with a hard token budget per request. One misleading source must not flip the conclusion.' Reference answer ol.seq, one item per step: (1) Brief: the planner writes a short plan the user can edit. (2) First move: split the question into clues, retrieve per clue, union, rerank (Question's Gambit: 83.1% -> 90.5% on BrowseComp-Plus, arXiv 2609.14412). (3) N capped sub-agents in parallel, each with a token budget and a stop rule; prune low-value subqueries (up to -73% tokens, arXiv 2608.08389). (4) Verify evidence when it enters the research state: one misleading document raised false-conclusion adoption from 0% to 54.7% (arXiv 2607.20891). (5) Compress each lane to a short note with source URLs; a supervisor checks for gaps; a commitment gate with rollback cut premature commitments 59.1% (DeepRewind, arXiv 2609.36344). (6) Writer cites raw chunks, then a citation check (cite raw spans: 0.86 vs 0.12 precision after compression, arXiv 2609.14245). Notes: listen for caps, compression with URLs, verification at entry and per-lane token tracing. Follow-up: 'How do you evaluate it?' closed-book baseline and leakage blocking (Glasseek: -5.1 points when leakage is blocked, arXiv 2610.16998).
- **visual:** Large animated architecture (920x580, 6 steps): User (n-human, 'editable brief'), Planner (n-model), Clue splitter (n-agent), Sub-agent x3 (n-agent, inside a g-agent group 'capped lanes'), Search tool (n-tool), Evidence gate (n-risk, 'verify on entry'), Notes store (n-state, 'notes + URLs'), Writer (n-model), Citation check (n-risk). Wires: user>plan@1:flow{human}; plan>clue@2; clue>sub1@3; sub1>gate@4:flow; gate>notes@5 [verified]; notes>writer@6; writer>cite@6. A token-budget meter (bespoke gsap bar) fills as lanes run and stops at the cap; a red 'misleading doc' card bounces off the evidence gate at step 4.

### c04-05-debug-loop.html - Debug this: one refund question burned thousands of LLM calls
- **id:** `rag-interview-c04-debug-loop`
- **type:** debug
- **content:** Kicker '<span class="pill">Debug this</span> agent loop'. Prompt: 'The refund graph worked in tests. In production one question ran for minutes and the bill spiked before a GraphRecursionError. Find the bug.' Step 1: code + output pane (output · illustrative: verify -> generate repeated, then 'GraphRecursionError: Recursion limit of 10007 reached without hitting a stop condition'). Step 2 (answer): data-focus on the conditional edge and on app.invoke: the verify -> generate edge has no counter and no fallback, generate never sees why the draft failed, so it fails the same way; LangGraph 1.2.17's default recursion limit is 10007, so the loop runs thousands of paid steps. Step 3: .code-wrap.good: add tries to State, increment it in generate, route 'generate' only if tries < 2 else 'fallback', pass the unsupported sentences back into the prompt, and invoke with {'recursion_limit': 25} as the safety net. Pins: langgraph==1.2.17, langchain-core==1.7.0, langchain-google-genai==4.4.2. Source: lab-agentic Lab 4 (verified). Notes: budgets live in code, not prompts; the recursion limit is the net, the counter is the guard.
- **visual:** Left: code (.xs) with data-focus '2:20, 2:22'. Right: bespoke gsap animation - a 3-node loop (generate n-model, verify n-risk) with a token circling; a step counter climbs 1, 2, 3 ... (counts up quickly to 10007 at step 2) and a cost meter fills red. Step 3: the fixed graph adds a 'fallback' node; the counter now shows tries 1/2, 2/2 and the token exits to fallback.
- **code (buggy version shown on the slide):**

```python
# refund_graph.py -- retrieve -> generate -> verify, regenerate until grounded
from typing import TypedDict
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langgraph.graph import StateGraph, START, END

llm = ChatGoogleGenerativeAI(model="gemini-3.8-flash")
store = InMemoryVectorStore.from_texts(["Sale items are final sale; exchange only, within 14 days."],
                                       GoogleGenerativeAIEmbeddings(model="gemini-embedding-001"))
class State(TypedDict, total=False):
    question: str; context: str; answer: str; grounded: bool

def retrieve(s): return {"context": "\n".join(d.page_content for d in store.similarity_search(s["question"], k=3))}
def generate(s): return {"answer": llm.invoke(f"Use ONLY:\n{s['context']}\nQ: {s['question']}").text}
def verify(s):   return {"grounded": "YES" in llm.invoke(f"Supported? YES/NO\n{s['context']}\n{s['answer']}").text}

g = StateGraph(State)
g.add_node(retrieve); g.add_node(generate); g.add_node(verify)
g.add_edge(START, "retrieve"); g.add_edge("retrieve", "generate"); g.add_edge("generate", "verify")
g.add_conditional_edges("verify", lambda s: END if s["grounded"] else "generate", [END, "generate"])
app = g.compile()
print(app.invoke({"question": "Can I get a refund on a sale jacket?"})["answer"])
```

## Chapter 5: Evaluation, security and production  (tone: risk)

Scenario: HelpDesk triage RAG shipping weekly behind a CI gate; Acme claims KB with per-group ACLs; a 50M-document enterprise deployment.

Research files:
- C:/Users/evija/googleadk2.0/research-v2/rag/00-VERIFIED.md
- C:/Users/evija/googleadk2.0/research-v2/rag/lab-eval-prod.md
- C:/Users/evija/googleadk2.0/research-v2/rag/arxiv-eval-graph.md
- C:/Users/evija/googleadk2.0/research-v2/rag/gotchas.md
- C:/Users/evija/googleadk2.0/research-v2/rag/industry.md
- C:/Users/evija/googleadk2.0/archive/v1/rag/slides/c09-06-interview.html
- C:/Users/evija/googleadk2.0/archive/v1/rag/slides/c10-05-interview.html

### c05-01-chapter.html - Evaluation, security and production
- **id:** `rag-interview-c05-chapter`
- **type:** chapter
- **content:** Chapter opener. Chapter number 5. .display 'Evaluation, security and production'. .lede: 'The judge is a model you ship, retrieved text is untrusted input, and every span has a latency budget.' Tags: 'Judges', 'Canaries', 'Injection', 'ACLs', 'Caching', 'Release gates'. Notes: senior interviews end here: how do you know it works, and how do you keep it safe and cheap.
- **visual:** Self-animating mini-diagram: a request token passes three gates in a row - shield (risk, 'ACL + injection'), gauge (state, 'eval gate'), stopwatch (tool, 'p95 budget'); each gate flashes green as the token passes; on every third loop the shield turns red and blocks a poisoned token. Deterministic loop, killed in leave.

### c05-02-qa-eval.html - Calibrate the judge and test what the bot should refuse
- **id:** `rag-interview-c05-qa-eval`
- **type:** qa
- **content:** Three .qa pairs, one step per answer. Q1: 'Faithfulness is 0.95, but users still complain. What is wrong?' A1: Faithfulness checks support, not usefulness or completeness. Measure answer relevance and retrieval recall@k on a golden set. Report all-constraint compliance: EnterpriseRAG found 80% per-constraint satisfaction but only 26.8% of answers met all constraints (arXiv 2608.11584). Copying can game faithfulness (arXiv 2610.18442). Q2: 'How do you trust an LLM judge?' A2: Calibrate it against humans and quote the human ceiling: Shopify raised Cohen's kappa from 0.02 to 0.61 against a human 0.69. A cheap judge scored AUROC 0.603 vs 0.783 for gpt-4o (AGO, arXiv 2610.01218). Gate on unsupported-claim admits: two judges with equal accuracy admitted 23.2% vs 14.1% (arXiv 2610.20634). Audit the humans too: DoorDash found more than half of audited labels wrong. Q3: 'All your candidate systems score 97-98% accuracy. Which test is missing?' A3: Knowledge-gap canaries: questions the KB cannot answer. At the same accuracy, canary violations ranged from 16.7% to 98.1%; score correct +1, wrong -4, abstain 0 (arXiv 2608.26385). Run eval at temperature 0 where the API allows it: disagreement fell from 14.3% to 3.4% (arXiv 2610.05034). Cites: .cite.paper 2608.26385, 2610.01218, 2610.20634; .cite.doc Shopify 'Building production-ready agentic systems' (https://shopify.engineering/building-production-ready-agentic-systems). Notes: analogy for Q2: calibrate a new thermometer against a reference before you trust it.
- **visual:** Step 1: three triad bars (faithfulness 0.95 green, answer relevance low amber, recall@5 low red) animate, then '80% per constraint -> 26.8% all' count-down. Step 2: a kappa gauge needle sweeps 0.02 -> 0.61 with a dashed 'human 0.69' mark. Step 3: bespoke scatter - systems as dots at accuracy 97-98% (x) spread vertically on canary violation 16.7%..98.1% (y); a '+1 / -4 / 0' scoring chip pops.

### c05-03-qa-security.html - Treat retrieved text as untrusted input with an identity attached
- **id:** `rag-interview-c05-qa-security`
- **type:** qa
- **content:** Three .qa pairs, one step per answer. Q1: 'Your agent reads email and can send email. How do you stop indirect prompt injection?' A1: Architecture, not only a better prompt. The same injection succeeded 18% via chat but 53% via retrieved context (TRACER, arXiv 2610.19133). Take the plan only from the user's request, mark retrieved text as data, give tools least privilege, ask a human before a send, allowlist egress, and run an injection pytest suite in CI. Detectors are not enough: one scored 0.994 recall in-distribution and near zero on PoisonedRAG (arXiv 2610.28364). Q2: 'Pre-filter or post-filter for ACLs?' A2: Pre-filter inside the ANN and BM25 queries, with the end user's identity, before fusion, rerank and cache. A post-filter starves top-k (in the Chroma lab the call-center user got [] although an FAQ was allowed) and leaks through counts. Add a CI leak test for every user x golden query. Q3: 'How do you defend a store that ingests new content all day against poisoning?' A3: Admission filters cannot stop coordinated poisoning; a read-path demand monitor caught 100% at 1% FPR (arXiv 2608.16044). Hide unvetted new items after a deadline: median poisoned retrievals 34 -> 7 (arXiv 2610.05826). One attacker source raised wrong answers 0.01 -> 0.68 and laundered the citation (CiteShade, arXiv 2609.15660): test leave-one-source-out. Cites: .cite.paper 2610.19133, 2608.16044, 2609.15660; .cite.doc OWASP LLM08 'Vector and embedding weaknesses'. Notes: Q2 red flags: service-account identity, filter after generation.
- **visual:** Step 1: two channels into a model node - chat (18%) and retrieved context (53%) - with attack-success bars counting up; a 'plan from user only' lock closes the retrieved channel's arrow into the planner. Step 2: bespoke ACL animation: top-3 global results (2 SIU red, 1 adjuster amber) get filtered after ranking -> empty list; then pre-filter inside search returns faq-01 (green). Step 3: a time axis of ingested items; unvetted items fade out after a deadline line; counter 'poisoned retrievals 34 -> 7'.

### c05-04-qa-production.html - Production answers name the cache risks, the bill and the gate
- **id:** `rag-interview-c05-qa-production`
- **type:** qa
- **content:** Three .qa pairs, one step per answer. Q1: 'What are the risks of a semantic cache?' A1: Three. Cross-tenant leakage: partition entries by tenant or user and filter on it. False hits: tune distance_threshold (RedisVL default 0.1) on labelled paraphrase and non-paraphrase pairs. Stale answers: set a TTL and invalidate by doc_id when a document changes. Apply the same ACL as retrieval. Q2: 'Build your own pipeline, or use Gemini File Search / RAG Engine?' A2: Managed for speed, citations and low ops: File Search indexing costs $0.15 per 1M tokens, storage and query embeddings are free; keep each store under 20 GB; 100 MB per file. It cannot be combined with Google Search grounding in one request, and citation offsets are bytes. Build DIY for custom chunking, hybrid weights, rerankers or ACL logic. Measure both on the same golden set. Q3: 'How do you decide to ship a pipeline change?' A3: A release gate in CI: deterministic recall@5 first, canary abstention with zero tolerance, faithfulness with a NaN-rate check, and a paired comparison against the baseline. Use explicit outcomes PROMOTE / BLOCK / REJECT / INCONCLUSIVE (RAGWarrant, arXiv 2609.34179). A beta-binomial gate cut unsafe promotions to 22.2-35.1% vs 29.3-41.8% for a naive gate (AGO, arXiv 2610.01218). Cites: .cite.doc Gemini API 'File search' (https://ai.google.dev/gemini-api/docs/file-search); .cite.repo redis/redis-vl-python; .cite.paper 2609.34179. Notes: Q2 tests judgment, not vendor loyalty.
- **visual:** Step 1: three cache-risk cards flip in sequence (leak, false hit, stale) each with a tiny icon animation: two tenant colours mixing then separating; a threshold slider moving from 0.1 to 0.08; a clock with TTL. Step 2: a two-column 'managed vs DIY' table.t with rows lighting one by one. Step 3: a gate animation: a PR token passes recall@5 (ok), canary (ok), faithfulness + NaN check (ok) and lands in PROMOTE; a second token lands in INCONCLUSIVE (grey).

### c05-05-wb-production.html - Whiteboard: RAG for 50M documents, p95 under 1 s, per-user ACLs
- **id:** `rag-interview-c05-wb-production`
- **type:** whiteboard
- **content:** Prompt panel (k-human): 'Design enterprise RAG over 50M documents from Drive, Jira and email. p95 time-to-first-token under 1 s, per-user permissions, nightly updates, and a weekly release cadence.' Reference answer ol.seq, one item per step: (1) One permission-aware index, not live federation (Dropbox: federated agent queries up to 45 s vs seconds). (2) Hybrid BM25 + ANN (HNSW or DiskANN, MRL 768 + int8), ACL pre-filter inside both queries with the end user's identity. (3) RRF, then a small fast reranker on the top 50-100. (4) Tenant-partitioned semantic cache in front; cache the static prompt prefix; stream tokens. (5) Incremental ingest by content hash; embedding_version per vector; blue/green for model upgrades. (6) Observability and release: per-span latency budget and traces, CI gate (recall@5, canaries, judge NaN rate), online A/B on behaviour (long-clicks, retention). Numbers: Notion p50 50-70 ms vector search; Atlassian p90 60 ms; Google ranking API under 100 ms; check-grounding designed for under 500 ms; Dropbox target 95%+ of queries under 1-2 s retrieval. Example budget labelled 'example budget': auth 20 ms, cache 10 ms, hybrid 120 ms, rerank 100 ms, prompt build 30 ms, model TTFT the rest. Notes: classic system-design question; a strong answer names the budget per span, the ACL inside the queries and a small reranker because it runs on every query. Follow-up: 'How do you migrate the embedding model with zero downtime?' blue/green with golden-set comparison.
- **visual:** Large animated architecture (940x540, 6 steps) plus a bespoke latency waterfall. Nodes: User (n-human pill), Auth (n-tool), Semantic cache (n-state), Hybrid retriever (n-agent, 'BM25 + ANN + ACL'), Reranker (n-model), Prompt + LLM (n-model, 'cached prefix, stream'), Index (n-state, '50M docs'), Ingest (n-tool, 'hash diff'), Eval gate (n-risk). Wires: user>auth@1:flow{human}; auth>cache@2 [miss]; cache>ret@2; ret>rr@3 [top 100]; rr>llm@4 [top 10]; ingest>index@5:dash; gate>llm@6:dash{risk}. Under the diagram, a waterfall SVG draws the example spans one by one, ending at a dashed 1 s line.

### c05-06-debug-eval-gate.html - Debug this: the judge broke and the faithfulness score went up
- **id:** `rag-interview-c05-debug-eval-gate`
- **type:** debug
- **content:** Kicker '<span class="pill">Debug this</span> eval gate'. Prompt: 'The judge hit a quota limit on a third of the rows. The gate printed a higher faithfulness than baseline and passed the PR. Find the bug.' Step 1: code + output pane (output · illustrative: 'faithfulness=0.962 base=0.910' and '41 of 120 rows were NaN' in .dim). Step 2 (answer): data-focus on the NaN filter and the mean: failed judge calls become NaN, the filter removes them from the denominator, so the score rises as more rows fail (the same effect as ragas evaluate() with raise_exceptions=False and nan-mean, gotchas F1). Step 3: .code-wrap.good: nan_rate = 1 - len(vals) / len(results); fail if nan_rate > 0.05; require len(rows) >= 50; for release gates count NaN as 0; add a canary-abstention check. Pins: ragas==0.4.3, openai==3.37.0. Source: lab-eval-prod Lab 4 (verified) and ragas issue #3028. Notes: report coverage next to every metric.
- **visual:** Left: code (.xs) with data-focus '2:16-17'. Right: bespoke gsap animation - 12 row tiles (green = scored, red = NaN); as more tiles turn red (4 of 12), the displayed mean counts UP (0.91 -> 0.96) while a 'coverage' gauge drops; step 3 the fixed gate shows coverage 66% < 95% -> BLOCK (red stamp).
- **code (buggy version shown on the slide):**

```python
# eval_gate.py -- block a PR when faithfulness drops
import asyncio, json, math, os, sys
from openai import AsyncOpenAI
from ragas.llms import llm_factory
from ragas.metrics.collections import Faithfulness

client = AsyncOpenAI(api_key=os.environ["GEMINI_API_KEY"],
                     base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
faith = Faithfulness(llm=llm_factory("gemini-3.8-flash", provider="openai", client=client, max_tokens=4096))
base = json.load(open("baseline.json"))                    # {"faithfulness": 0.91}
rows = [json.loads(line) for line in open("runs/candidate.jsonl", encoding="utf-8")]

async def main():
    results = await asyncio.gather(*(faith.ascore(user_input=r["question"], response=r["response"],
                                     retrieved_contexts=r["retrieved_contexts"]) for r in rows))
    vals = [x.value for x in results if not math.isnan(x.value)]
    score = sum(vals) / len(vals)
    print(f"faithfulness={score:.3f} base={base['faithfulness']:.3f}")
    sys.exit(0 if score >= base["faithfulness"] - 0.03 else 1)

asyncio.run(main())
```
