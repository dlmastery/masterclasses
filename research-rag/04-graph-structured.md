# 04 — Graph & Structured RAG (GraphRAG, LightRAG, HippoRAG 2, RAPTOR, KG-RAG/Neo4j, Text-to-SQL, Hybrid, "DRAG" disambiguation)

Researched 2026-10-23. All facts below were checked against primary sources (arXiv, official docs, GitHub, PyPI, Microsoft Research blog) unless marked [UNVERIFIED].

---

## 0. Why structure? (the one-sentence motivation)

Vector RAG retrieves the *k chunks most similar to the query*. It fails on two question shapes:
1. **Global / sensemaking** questions ("What are the main themes across this 1M-token corpus?"): no single chunk holds the answer.
2. **Multi-hop / associative** questions ("Which Stanford professor's student founded the company that acquired X?"): the answer is spread across chunks that don't look like the query.

Structured RAG adds an explicit index structure (entity graph, community hierarchy, summary tree, relational schema) so retrieval can aggregate or traverse.

> "Is GraphRAG really effective, and in which scenarios do graph structures provide measurable benefits for RAG systems?" — Xiang et al., *When to use Graphs in RAG*, ICLR 2026 (arXiv 2506.05690). Recent studies "report that GraphRAG frequently underperforms vanilla RAG on many real-world tasks."

---

## 1. Microsoft GraphRAG

**Paper:** "From Local to Global: A Graph RAG Approach to Query-Focused Summarization", Edge, Trinh, Cheng, Bradley, Chao, Mody, Truitt, Metropolitansky, Ness, Larson. arXiv 2404.16130, v1 24 Apr 2024, v2 19 Feb 2025. https://arxiv.org/abs/2404.16130
**Repo:** https://github.com/microsoft/graphrag — docs https://microsoft.github.io/graphrag
**Version:** `graphrag` **3.3.0** on PyPI (released 2026-10-08; 3.2.0 on 2026-09-23). https://pypi.org/project/graphrag/ . Requires Python 3.10–3.12.
**Status:** README: "This project is largely in maintenance mode, and won't be accepting new PRs or implementing new features." Also: "Always run `graphrag init --root [path] --force` between minor version bumps."

### 1.1 Indexing dataflow (official "Default Dataflow" doc)
https://microsoft.github.io/graphrag/index/default_dataflow/
1. **Compose TextUnits** — chunk documents (default chunk size 1200 tokens in current docs; the paper used 600 tokens / 100 overlap).
2. **Document Processing** — link docs to text units -> Documents table.
3. **Graph Extraction** — LLM extracts entities + relationships (or NLP-based with *FastGraphRAG*), then **summarizes** each entity/relationship description across all mentions; optional **claim extraction** (off by default) -> Covariates.
4. **Graph Augmentation** — **Hierarchical Leiden** community detection -> Entities, Relationships, Communities tables.
5. **Community Summarization** — LLM writes a "community report" for every community at every level.
6. **Text Embedding** — embed text units, entity descriptions, community report content into a vector store.
Outputs are parquet files in `./output`.

Diagram in words: `Docs -> chunks -> (LLM) entities+edges -> merged graph -> Leiden: level0 (few big communities) ... level3 (many small) -> (LLM) report per community -> embeddings`.

### 1.2 Query modes (CLI `graphrag query -m {local|global|drift|basic}`, default `global`)
https://microsoft.github.io/graphrag/cli/
- **Global search**: map-reduce over community reports at a chosen level (`--community-level`, default 2). Map: each report batch -> partial answer with rated points; Reduce: merge top-rated points into the answer. Good for "themes across the corpus".
- **Dynamic community selection** (`--dynamic-community-selection`): starts at the root, a small model (GPT-4o-mini) rates report relevance, prunes irrelevant subtrees; GPT-4o does the map-reduce. On 50 global AP-News questions: comparable quality, **77% average total token-cost reduction** vs static global search at level 1. Blog: "GraphRAG: Improving global search via dynamic community selection" (Nov 2024) https://www.microsoft.com/en-us/research/blog/graphrag-improving-global-search-via-dynamic-community-selection/ (77% figure taken from search excerpts of the post).
- **Local search**: embed query -> nearest entities -> fan out to their relationships, text units, covariates, community reports -> fill a context window. Good for "Who is X and how is X related to Y?"
- **DRIFT search** (Dynamic Reasoning and Inference with Flexible Traversal), developed with Uncharted Software. Blog: "Introducing DRIFT Search: Combining global and local search methods to improve quality and efficiency", 31 Oct 2024. https://www.microsoft.com/en-us/research/blog/introducing-drift-search-combining-global-and-local-search-methods-to-improve-quality-and-efficiency/
  - **Primer**: compare query to top-K semantically relevant community reports -> broad initial answer + follow-up questions (a "lighter global search").
  - **Follow-up**: each follow-up runs local search -> intermediate answers + more follow-ups (terminates after 2 iterations in the blog's setup).
  - **Output hierarchy**: "The final output is a hierarchical structure of questions and answers ranked by relevance" (docs https://microsoft.github.io/graphrag/query/drift_search/).
  - **Result**: on 5,000+ AP news articles, 50 local questions, LLM judge: DRIFT beat Local Search **78%** on comprehensiveness and **81%** on diversity.
- **Basic search**: plain vector RAG over text units (baseline).

### 1.3 Headline numbers from the paper (v2)
- Datasets: Podcast transcripts ~1M tokens (1,669 chunks x 600 tok); News ~1.7M tokens (3,197 chunks). Graphs: 8,564 nodes / 20,691 edges (Podcast); 15,754 / 19,520 (News).
- vs vector RAG ("SS"): comprehensiveness win rate **72–83%** (Podcast), **72–80%** (News); diversity **75–82%** / **62–71%**.
- Root-level communities (C0) use **"over 97% fewer tokens"** than source-text map-reduce (TS); 9x–43x fewer tokens per query; C0 still wins 72% comprehensiveness / 62% diversity vs SS.
- Context window used: 8k tokens.

### 1.4 Code (CLI, from official Getting Started)
Source: https://microsoft.github.io/graphrag/get_started/
```bash
python -m pip install graphrag            # 3.3.0 as of 2026-10
graphrag init                             # creates .env, settings.yaml, input/
curl https://www.gutenberg.org/cache/epub/24022/pg24022.txt -o ./input/book.txt
# put GRAPHRAG_API_KEY in .env
graphrag index                            # --method standard|fast|standard-update|fast-update
graphrag query "What are the top themes in this story?"                     # global (default)
graphrag query "Who is Scrooge and what are his main relationships?" --method local
graphrag query "How does Scrooge change, and why?" --method drift
```
Note `fast` index method = NLP (noun-phrase) extraction instead of LLM extraction — much cheaper, lower graph quality.

### 1.5 Cost reality
- Full GraphRAG indexing calls an LLM for every chunk (extraction + gleanings), every entity summary, and every community report: cost scales with corpus size, not query count. Microsoft's own LazyGraphRAG post positions full-GraphRAG indexing as ~1000x the cost of vector RAG indexing (inverse of the 0.1% figure below).
- Incremental updates: `standard-update` / `fast-update` methods exist; LightRAG authors estimate GraphRAG needs to regenerate community reports on update (~1,399 x 2 x 5,000 tokens on their Legal set) (arXiv 2410.05779).

---

## 2. LazyGraphRAG (Microsoft Research)

Blog: "LazyGraphRAG: Setting a new standard for quality and cost", Darren Edge, Ha Trinh, Jonathan Larson, **25 Nov 2024** (editor's note 6 Jun 2025). https://www.microsoft.com/en-us/research/blog/lazygraphrag-setting-a-new-standard-for-quality-and-cost/

- Quote: "a radically different approach to graph-enabled RAG that requires no prior summarization of the source data."
- **Indexing**: NLP noun-phrase extraction -> concept co-occurrence graph -> graph statistics build hierarchical communities. **No LLM at index time.** Indexing cost "identical to vector RAG and 0.1% of the costs of full GraphRAG."
- **Query** (defers LLM work to query time = "lazy"):
  1. LLM generates 3–5 subqueries, expands with matching concepts.
  2. Best-first: rank chunks by embedding similarity, rank communities by their top chunks.
  3. Breadth-first relevance testing: LLM relevance assessor tests chunks community-by-community; iterative deepening into sub-communities after z communities yield nothing.
  4. Stop when budget exhausted ("relevance test budget").
  5. Map: extract query-relevant claims from relevant chunks grouped by community; Reduce: rank claims into context; final answer.
- Quote: "Overall performance can be scaled via a single main parameter – the relevance test budget."
- **Benchmark**: 5,590 AP news articles; 100 synthetic queries (50 local, 50 global); LLM-judged comprehensiveness, diversity, empowerment; budgets Z100_Lite, Z500, Z1500 vs 8 baselines (GraphRAG C1, C2, C3_Dynamic, Local, DRIFT, SS_8K, SS_64K, RAPTOR).
  - Comparable quality to GraphRAG Global Search at **>700x lower query cost**.
  - At **4%** of GraphRAG global query cost, it "significantly outperforms all competing methods on both local and global queries."
  - Z100_Lite costs the same as SS_8K vector RAG.
- "ideal for one-off queries, exploratory analysis, and streaming data use cases."
- **Availability**: integrated in **Microsoft Discovery** (Azure agentic science platform) and Azure Local public preview. Open-source status of LazyGraphRAG itself in microsoft/graphrag: [UNVERIFIED] — the blog does not state it.

---

## 3. LightRAG (HKU Data Intelligence Lab)

**Paper:** "LightRAG: Simple and Fast Retrieval-Augmented Generation", Guo et al., arXiv **2410.05779** (Oct 2024), listed as **EMNLP 2025** in repo. https://arxiv.org/abs/2410.05779
**Repo:** https://github.com/HKUDS/LightRAG — `pip install lightrag-hku` (server: `pip install "lightrag-hku[api]"`). Version number not shown on README [UNVERIFIED exact version].

### 3.1 How it works
- **Graph-based text indexing**: R(.) LLM extracts entities/relations per chunk; P(.) LLM "profiling" writes key-value pairs (index key + summary) per node/edge; D(.) deduplicates identical entities/relations across chunks.
- **Dual-level retrieval**: LLM extracts **low-level keywords** (specific entities) and **high-level keywords** (themes). Low-level -> match entity nodes; high-level -> match relation edges/themes; then gather 1-hop neighbors + source chunks.
- **No community reports** -> **incremental update** is a graph union (no full rebuild).
- **Cost vs GraphRAG (paper, Legal dataset)**: GraphRAG global retrieval ~610 level-2 communities x 1,000 tokens = **610,000 tokens** and hundreds of calls; LightRAG "fewer than 100 tokens for keyword generation and retrieval" and "only a single API call."
- **Datasets (UltraDomain)**: Agriculture 2.0M tokens, CS 2.3M, Legal 5.1M, Mix 0.6M.
- **Win rates (README, LLM judge, overall)** LightRAG vs GraphRAG: Agriculture 54.8%, CS 52.0%, Legal 52.8%, Mix 49.6% (i.e. roughly parity); vs NaiveRAG 60–85%.
- **Query modes**: `naive`, `local`, `global`, `hybrid`, `mix` (default `mix` = graph + vector). (`bypass` exists in code [UNVERIFIED in README].)
- **Storage**: defaults JsonKV/NanoVectorDB/NetworkX (dev only); production PostgreSQL (all four storage types), MongoDB, OpenSearch (2026.03); Neo4j or Memgraph for graph; Milvus/Qdrant for vectors.
- **News**: 2026.05 RAG-Anything (multimodal: images, tables, equations; MinerU/Docling parsing) merged into LightRAG; 2026.05 four chunking strategies; 2025.11 RAGAS + Langfuse; 2025.08 reranker support + document deletion with KG regeneration.

### 3.2 Code (from `examples/lightrag_openai_demo.py`)
Source: https://github.com/HKUDS/LightRAG/blob/main/examples/lightrag_openai_demo.py
```python
import asyncio
from lightrag import LightRAG, QueryParam
from lightrag.llm.openai import gpt_4o_mini_complete, openai_embed

async def main():
    rag = LightRAG(
        working_dir="./rag_storage",
        embedding_func=openai_embed,
        llm_model_func=gpt_4o_mini_complete,
    )
    await rag.initialize_storages()          # auto-initializes pipeline_status
    with open("./book.txt", "r", encoding="utf-8") as f:
        await rag.ainsert(f.read())
    for mode in ["naive", "local", "global", "hybrid", "mix"]:
        print(mode, await rag.aquery(
            "What are the top themes in this story?",
            param=QueryParam(mode=mode)))
    await rag.finalize_storages()

asyncio.run(main())
```

---

## 4. HippoRAG and HippoRAG 2 (OSU NLP Group)

- **HippoRAG** (v1): "HippoRAG: Neurobiologically Inspired Long-Term Memory for Large Language Models", arXiv 2405.14831, **NeurIPS 2024**. Hippocampal indexing theory: LLM = neocortex, KG = hippocampal index, **Personalized PageRank (PPR)** = pattern completion.
- **HippoRAG 2**: "From RAG to Memory: Non-Parametric Continual Learning for Large Language Models", Bernal Jiménez Gutiérrez, Yiheng Shu, Weijian Qi, Sizhe Zhou, Yu Su. arXiv **2502.14802** (v1 20 Feb 2025, v2 19 Jun 2025), **ICML 2025**. https://arxiv.org/abs/2502.14802
- Repo: https://github.com/OSU-NLP-Group/HippoRAG — `pip install hipporag` (README references 2.0.0a5 for index upgrades). Also exposes an MCP `retrieve` tool.

### 4.1 Pipeline
Offline: LLM **OpenIE** -> (subject, relation, object) triples; phrases become nodes; **synonym edges** where embedding similarity > 0.8; **dense-sparse integration**: every passage is also a **passage node** linked by "contains" edges to its phrases.
Online:
1. **Query-to-triple**: embed query, retrieve top-5 triples.
2. **Recognition memory**: LLM filters irrelevant triples (fallback to dense retrieval if none survive).
3. **Seeds**: phrase nodes from kept triples + all passage nodes (passage reset weight = embedding sim x 0.05).
4. **PPR** over graph -> rank passages -> QA reader.

### 4.2 Results (Table 2; Llama-3.3-70B-Instruct reader/extractor, NV-Embed-v2 retriever; avg F1 over 7 datasets: NQ, PopQA, MuSiQue, 2Wiki, HotpotQA, LV-Eval, NarrativeQA)
| Method | Avg F1 |
|---|---|
| **HippoRAG 2** | **59.8** |
| NV-Embed-v2 (dense) | 57.0 |
| HippoRAG (v1) | 53.1 |
| GraphRAG | 49.6 |
| RAPTOR | 48.8 |
| LightRAG | 6.6 |
2Wiki: 71.0 vs 61.5 dense. Abstract: "7% improvement in associative memory tasks over the state-of-the-art embedding model." Teaching point: **many graph-RAG systems lose to a strong dense retriever on factual QA; HippoRAG 2 is designed not to.** (LightRAG's 6.6 reflects a QA-F1 evaluation it wasn't built for — benchmark choice matters.)

### 4.3 Code (README quick start)
Source: https://github.com/OSU-NLP-Group/HippoRAG
```python
from hipporag import HippoRAG

docs = ["George Rankin is a politician.",
        "Erik Hort's birthplace is Montebello.",
        "Montebello is a part of Rockland County."]
queries = ["What is George Rankin's occupation?",
           "What county is Erik Hort's birthplace a part of?"]

with HippoRAG(save_dir="outputs",
              llm_model_name="gpt-4o-mini",
              embedding_model_name="text-embedding-3-small") as hipporag:
    hipporag.index(docs=docs)
    results = hipporag.rag_qa(queries=queries)
```
(Extra docs/queries added for a multi-hop demo; constructor/method names verbatim from README.)

---

## 5. RAPTOR (Stanford)

**Paper:** "RAPTOR: Recursive Abstractive Processing for Tree-Organized Retrieval", Parth Sarthi, Salman Abdullah, Aditi Tuli, Shubh Khanna, Anna Goldie, Christopher D. Manning. arXiv **2401.18059** (31 Jan 2024); published at **ICLR 2024** [venue from memory — arXiv page doesn't state it; mark UNVERIFIED]. https://arxiv.org/abs/2401.18059
Repo: https://github.com/parthsarthi03/raptor

- **Build (bottom-up)**: chunk (~100 tokens) -> embed (SBERT) -> reduce dims with **UMAP** -> soft-cluster with **Gaussian Mixture Models** (BIC chooses #clusters) -> LLM summarizes each cluster (gpt-3.5-turbo in paper) -> re-embed summaries -> repeat until no further clustering. [Clustering details from paper body; not in README.]
- **Retrieve**: *tree traversal* (top-down, layer by layer) or *collapsed tree* (flatten all nodes, pick top by similarity until token budget) — collapsed tree performed better in the paper.
- **Result**: with GPT-4, "improve the best performance on the QuALITY benchmark by 20% in absolute accuracy." Also evaluated on NarrativeQA, QASPER.
- Contrast with GraphRAG: RAPTOR clusters **chunks by semantic similarity** (tree); GraphRAG clusters **entities by graph connectivity** (Leiden communities).

Code (README): https://github.com/parthsarthi03/raptor
```python
import os
os.environ["OPENAI_API_KEY"] = "your-openai-api-key"
from raptor import RetrievalAugmentation

RA = RetrievalAugmentation()
with open("sample.txt", "r") as f:
    RA.add_documents(f.read())
print(RA.answer_question(question="How did Cinderella reach her happy ending?"))
RA.save("demo/cinderella")
RA = RetrievalAugmentation(tree="demo/cinderella")   # reload the tree
```
Custom summarizer: subclass `BaseSummarizationModel`, implement `summarize(context, max_tokens=150)`.

---

## 6. KG-RAG with Neo4j (`neo4j-graphrag` Python package)

Package: `neo4j-graphrag` **1.22.0** (2026-10-01). https://pypi.org/project/neo4j-graphrag/ — docs https://neo4j.com/docs/neo4j-graphrag-python/current/
**Retrievers**: `VectorRetriever`, `VectorCypherRetriever`, `HybridRetriever`, `HybridCypherRetriever`, `Text2CypherRetriever`, `ToolsRetriever`, `WeaviateNeo4jRetriever`, `PineconeNeo4jRetriever`, `QdrantNeo4jRetriever`.

### 6.1 Build the KG — `SimpleKGPipeline`
Source: https://neo4j.com/docs/neo4j-graphrag-python/current/user_guide_kg_builder.html (paraphrased close to docs)
```python
from neo4j import GraphDatabase
from neo4j_graphrag.embeddings.openai import OpenAIEmbeddings
from neo4j_graphrag.experimental.pipeline.kg_builder import SimpleKGPipeline
from neo4j_graphrag.llm import OpenAILLM

driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
llm = OpenAILLM(model_name="gpt-4.1-mini", model_params={"temperature": 0})
kg_builder = SimpleKGPipeline(
    llm=llm, driver=driver, embedder=OpenAIEmbeddings(),
    from_file=True,          # from_pdf is deprecated
    schema="EXTRACTED",      # default: schema inferred from text
)
await kg_builder.run_async(file_path="my_document.pdf")
```

### 6.2 Hybrid KG + vector: `VectorCypherRetriever` (vector entry point, graph expansion)
Source: https://neo4j.com/docs/neo4j-graphrag-python/current/user_guide_rag.html
```python
from neo4j_graphrag.retrievers import VectorCypherRetriever
from neo4j_graphrag.generation import GraphRAG
from neo4j_graphrag.llm import OpenAILLM

retrieval_query = """
RETURN node.title AS title, node.plot AS plot,
       collect { MATCH (a:Actor)-[:ACTED_IN]->(node) RETURN a.name } AS actors
"""   # `node` and `score` come from the vector search step
retriever = VectorCypherRetriever(driver, index_name="movie-index",
                                  retrieval_query=retrieval_query, embedder=embedder)
rag = GraphRAG(retriever=retriever, llm=OpenAILLM(model_name="gpt-5"))
response = rag.search(query_text="Movies about time travel", retriever_config={"top_k": 5})
print(response.answer)
```

### 6.3 `Text2CypherRetriever` (LLM writes Cypher — the graph analogue of text-to-SQL)
```python
from neo4j_graphrag.retrievers import Text2CypherRetriever
neo4j_schema = """
Node properties: Person {name: STRING, born: INTEGER}; Movie {title: STRING, released: INTEGER}
Relationship types: (:Person)-[:ACTED_IN]->(:Movie), (:Person)-[:DIRECTED]->(:Movie)
"""
examples = ["USER INPUT: 'Who acted in The Matrix?' QUERY: MATCH (p:Person)-[:ACTED_IN]->"
            "(m:Movie {title: 'The Matrix'}) RETURN p.name"]
retriever = Text2CypherRetriever(driver=driver, llm=llm,
                                 neo4j_schema=neo4j_schema, examples=examples)
print(retriever.search(query_text="Which movies did Hugo Weaving star in?"))
```
Invalid generated Cypher raises `Text2CypherRetrievalError`.

DRIFT on Neo4j: "Implementing DRIFT search with Neo4j and LlamaIndex" (Tomaž Bratanič, Neo4j blog; self-described reverse-engineering) https://neo4j.com/blog/developer/drift-search-with-neo4j-and-llamaindex/

### 6.4 Real-world KG-RAG
- **LinkedIn customer service**: "Retrieval-Augmented Generation with Knowledge Graphs for Customer Service Question Answering", Xu et al., arXiv 2404.17723 (SIGIR 2024 industry, DOI 10.1145/3626772.3661370). Builds a KG from historical tickets (intra-ticket tree + inter-ticket links). **MRR +77.6%**, BLEU +0.32, **median per-issue resolution time -28.6%** after ~6 months deployed.
- **HybridRAG (finance)**: "HybridRAG: Integrating Knowledge Graphs and Vector Retrieval Augmented Generation for Efficient Information Extraction", Sarmah, Hall, Rao, Patel, Pasquali, Mehta, arXiv 2408.04948 (Aug 2024; BlackRock + NVIDIA authors [affiliations UNVERIFIED on arXiv page]). Earnings-call transcripts; HybridRAG beats both VectorRAG and GraphRAG alone on retrieval accuracy and answer generation.
- Other KG-reasoning lines worth one bullet: Think-on-Graph (arXiv 2307.07697, ICLR 2024) LLM-as-agent beam search over a KG; G-Retriever (arXiv 2402.07630, NeurIPS 2024) PCST subgraph retrieval + GNN [both UNVERIFIED this session].

---

## 7. Text-to-SQL RAG (structured data as the "graph")

Pattern: **retrieve schema, not documents.** Steps: (1) schema linking — retrieve relevant tables/columns via embeddings over DDL + column descriptions; (2) retrieve few-shot (question, SQL) pairs similar to the query; (3) LLM generates SQL; (4) execute; (5) self-correct on error (agent loop); (6) LLM verbalizes the result.

- **Benchmarks**
  - **BIRD**: "Can LLM Already Serve as a Database Interface? A BIg Bench for Large-Scale Database Grounded Text-to-SQLs", NeurIPS 2023 (Datasets & Benchmarks, vol. 36), arXiv 2305.03111. https://bird-bench.github.io/ — leaderboard (checked 2026-10-23), test execution accuracy: **GrainSQL 82.95** (2026-09-07), DataGallery-Text2SQL (Huawei) 82.39, SiriusAI-SQL (Tencent) 82.28, AskData + GPT-4o (AT&T) 81.95, Agentar-Scale-SQL (Ant Group) 81.67. **Human: 92.96.**
  - **Spider 2.0**: "Spider 2.0: Evaluating Language Models on Real-World Enterprise Text-to-SQL Workflows", Lei et al., **ICLR 2025 Oral**, arXiv 2411.07763. 632 enterprise workflow problems, databases often >1,000 columns (BigQuery, Snowflake). o1-preview code agent solves **21.3%** (v2; v1 reported 17.0%) vs 91.2% on Spider 1.0 and 73.0% on BIRD. Lesson: real enterprise schemas break naive text-to-SQL; retrieval over schema + docs is essential.
- **Vanna 2.0** (https://github.com/vanna-ai/vanna): "a complete rewrite focused on user-aware agents and production deployments" — `Agent`, `ToolRegistry`, `RunSqlTool`, `UserResolver`, row-level security; legacy 0.x `train(ddl=...)`/`ask()` RAG API wrapped via `LegacyVannaAdapter`.
- **LangChain SQL agent tutorial** (https://docs.langchain.com/oss/python/langchain/sql-agent): tools `sql_db_list_tables`, `sql_db_schema`, `sql_db_query`, `sql_db_query_checker` + `create_agent`:
```python
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent

model = init_chat_model("...")        # any chat model
tools = [sql_db_list_tables, sql_db_schema, sql_db_query, sql_db_query_checker]
system_prompt = """You are an agent designed to interact with a SQL database.
Given an input question, create a syntactically correct {dialect} query ...
Never query for all columns; return at most {top_k} results.""".format(dialect="sqlite", top_k=5)
agent = create_agent(model, tools, system_prompt=system_prompt)
stream = agent.stream_events({"messages": [{"role": "user", "content": question}]}, version="v3")
```
(Tool functions are `@tool`-decorated wrappers over `sqlite3` defined in the tutorial; prompt abbreviated.)

---

## 8. Hybrid KG + vector — the design space

| Pattern | Entry point | Expansion | Example |
|---|---|---|---|
| Vector -> graph expand | vector top-k chunks/entities | Cypher 1–2 hops | Neo4j `VectorCypherRetriever`, GraphRAG local search |
| Hybrid lexical+vector -> graph | BM25 + vector | Cypher | `HybridCypherRetriever` |
| Graph-seeded PPR | query->triples | PageRank diffusion | HippoRAG 2 |
| Keywords -> nodes+edges + vector | LLM keywords | 1-hop | LightRAG `mix` |
| Community summaries | community reports | map-reduce | GraphRAG global / DRIFT |
| Parallel fusion | vector ctx + KG ctx | concatenate | HybridRAG (2408.04948) |
| Agentic router | LLM picks tool | any of the above | Neo4j `ToolsRetriever`, agent with Text2Cypher + vector tools |

"Combining selection and integration strategies from both paradigms yields consistent performance gains." — Han et al., "RAG vs. GraphRAG: A Systematic Evaluation and Key Insights", arXiv 2502.11371 (v1 Feb 2025, v3 Mar 2026).

---

## 9. What "DRAG" means in RAG literature (disambiguation — there is no single "DRAG")

| Name | Expansion | Paper | Year/venue | Idea |
|---|---|---|---|---|
| **DRAG / IterDRAG** | **Demonstration-based RAG** / **Iterative demonstration-based RAG** | "Inference Scaling for Long-Context Retrieval Augmented Generation", Yue, Zhuang, Bai, Hui, Jagerman, Zeng, Qin, Wang, Wang, Bendersky (Google DeepMind/Google). arXiv 2410.04343 | ICLR 2025 | Scale inference compute: many retrieved docs + in-context demos (DRAG); IterDRAG "learns to decompose input queries into simpler sub-queries and answer them using interleaved retrieval." "Up to 58.9% gains" vs standard RAG; "nearly linear gains" with optimally allocated compute (RAG inference scaling laws). |
| **DRAG** | **Distilling RAG** for SLMs | "DRAG: Distilling RAG for SLMs from LLMs to Transfer Knowledge and Mitigate Hallucination via Evidence and Graph-based Distillation", Chen, Myrzakhan, Luo, Khan, Bsharat, Shen. arXiv 2506.01954, code github.com/VILA-Lab/DRAG | ACL 2025 Main | Teacher LLM produces ranked evidence + KG; small model distilled on it; beats MiniRAG by up to 27.7%. |
| **DRAG** | **Debate-Augmented RAG** | "Removal of Hallucination on Hallucination: Debate-Augmented RAG", Hu, Zhang, Jiang, Zhang, Wei, Li. arXiv 2505.18581 | ACL 2025 | Training-free multi-agent debate (proponent/opponent/judge) at retrieval and generation to stop "hallucination on hallucination". |
| **DRAG** | **Dynamic Retrieval-Augmented Generation** (entity-augmented) | "Dynamic Retrieval-Augmented Generation", Shapkin, Litvinov, Zharov, Bogomolov, Galimzyanov, Bryksin (JetBrains Research). arXiv 2312.08976 | arXiv, Dec 2023 | For code generation: compress retrieved entities into embeddings injected into the model instead of pasting text — removes context-length limits. |
| **(D)RAGged** | pun, not an acronym | "DRAGged into Conflicts: Detecting and Addressing Conflicting Sources in Search-Augmented LLMs", Cattan et al. (Google Research, Bar-Ilan). arXiv 2506.08500; dataset google-research-datasets/rag_conflicts | Jun 2025 | Taxonomy of knowledge-conflict types + CONFLICTS benchmark; prompting models to reason about conflicts improves answers. |
| "Dynamic RAG" (generic) | family name | e.g. FLARE, DRAGIN | — | Decide *when* and *what* to retrieve during generation. |

### DRAGIN
"DRAGIN: Dynamic Retrieval Augmented Generation based on the Real-time Information Needs of Large Language Models", Weihang Su, Yichen Tang, Qingyao Ai, Zhijing Wu, Yiqun Liu (Tsinghua). **ACL 2024** long (2024.acl-long.702, pp. 12991–13013); arXiv 2403.10081. https://aclanthology.org/2024.acl-long.702 — code https://github.com/oneal2000/DRAGIN
- **RIND (Real-time Information Needs Detection)**: decides *when* to retrieve — per generated token, combines uncertainty (entropy), token importance (attention it receives from later tokens), and semantic significance (stopword filter); trigger when score > threshold.
- **QFS (Query Formulation based on Self-attention)**: decides *what* to retrieve — picks the tokens across the **whole context** that the triggering token attends to most, rather than only the last sentence (the critique of FLARE / fixed-interval methods).
- Evaluated on 2WikiMultihopQA, HotpotQA, StrategyQA, IIRC (top 1000 questions each), Llama-2 7B/13B chat (+Vicuna [UNVERIFIED]); best on all 4 datasets vs non-retrieval, single-retrieval, fixed-length, fixed-sentence, token-level (FLARE-style) baselines. Needs white-box model access (attention + logits) — not usable with closed APIs.

---

## 10. Benchmarks & cost cheat sheet

| System | Index-time LLM cost | Query cost | Best at | Key number |
|---|---|---|---|---|
| Vector RAG | embeddings only | 1 LLM call | local facts | baseline |
| GraphRAG global | very high (extract + summarize + reports) | map-reduce over many reports | corpus-wide themes | 72–83% comprehensiveness win vs vector |
| GraphRAG + dynamic selection | same | -77% tokens | global | 77% |
| DRIFT | same as GraphRAG | primer + 2 rounds local | local w/ breadth | 78%/81% win vs local |
| LazyGraphRAG | = vector RAG (0.1% of GraphRAG) | budgeted (Z100–Z1500) | both, one-off/streaming | >700x cheaper than global at similar quality |
| LightRAG | high-ish (extract + profile), incremental | <100 tokens retrieval, 1 call | cheap updates | ~50% win vs GraphRAG |
| HippoRAG 2 | OpenIE triples (less than GraphRAG/RAPTOR/LightRAG per README) | embed + PPR + 1 filter call | multi-hop + factual | 59.8 avg F1 vs 57.0 dense |
| RAPTOR | cluster summaries per level | similarity over all levels | long single docs | +20 pts QuALITY w/ GPT-4 |
| Text-to-SQL | schema/doc embeddings | generate + execute + retry | aggregates over tables | BIRD 82.95 vs human 92.96; Spider 2.0 21.3% |

Caveat for students: most GraphRAG-family wins are **LLM-as-judge head-to-head** (comprehensiveness/diversity), while HippoRAG/GraphRAG-Bench use **exact-match/F1** — the same system can look great or terrible depending on metric (LightRAG ~50% win vs GraphRAG, but 6.6 F1 in HippoRAG 2's table).

---

## 11. Decision guide (quotable framing)
- Questions about **specific facts** -> strong dense/hybrid retrieval + reranker first.
- **Multi-hop entity chains** -> HippoRAG 2 or vector->Cypher expansion.
- **Whole-corpus sensemaking** -> GraphRAG global / LazyGraphRAG.
- **Corpus changes daily / budget-sensitive** -> LazyGraphRAG or LightRAG (incremental).
- **Long single documents (books, contracts)** -> RAPTOR tree.
- **Numbers live in tables** -> text-to-SQL agent; **relationships live in a graph DB** -> Text2Cypher.
- **Mixed** -> agentic router over tools (vector, graph, SQL).

---

## 12. Sources (exact titles + URLs)
- From Local to Global: A Graph RAG Approach to Query-Focused Summarization — https://arxiv.org/abs/2404.16130
- microsoft/graphrag — https://github.com/microsoft/graphrag ; docs https://microsoft.github.io/graphrag ; PyPI https://pypi.org/project/graphrag/
- Introducing DRIFT Search: Combining global and local search methods to improve quality and efficiency — https://www.microsoft.com/en-us/research/blog/introducing-drift-search-combining-global-and-local-search-methods-to-improve-quality-and-efficiency/
- GraphRAG: Improving global search via dynamic community selection — https://www.microsoft.com/en-us/research/blog/graphrag-improving-global-search-via-dynamic-community-selection/
- LazyGraphRAG: Setting a new standard for quality and cost — https://www.microsoft.com/en-us/research/blog/lazygraphrag-setting-a-new-standard-for-quality-and-cost/
- LightRAG: Simple and Fast Retrieval-Augmented Generation — https://arxiv.org/abs/2410.05779 ; https://github.com/HKUDS/LightRAG
- From RAG to Memory: Non-Parametric Continual Learning for Large Language Models — https://arxiv.org/abs/2502.14802 ; https://github.com/OSU-NLP-Group/HippoRAG
- HippoRAG: Neurobiologically Inspired Long-Term Memory for Large Language Models — https://arxiv.org/abs/2405.14831
- RAPTOR: Recursive Abstractive Processing for Tree-Organized Retrieval — https://arxiv.org/abs/2401.18059 ; https://github.com/parthsarthi03/raptor
- neo4j-graphrag-python docs — https://neo4j.com/docs/neo4j-graphrag-python/current/ ; https://pypi.org/project/neo4j-graphrag/
- Implementing DRIFT search with Neo4j and LlamaIndex — https://neo4j.com/blog/developer/drift-search-with-neo4j-and-llamaindex/
- Retrieval-Augmented Generation with Knowledge Graphs for Customer Service Question Answering — https://arxiv.org/abs/2404.17723
- HybridRAG: Integrating Knowledge Graphs and Vector Retrieval Augmented Generation for Efficient Information Extraction — https://arxiv.org/abs/2408.04948
- RAG vs. GraphRAG: A Systematic Evaluation and Key Insights — https://arxiv.org/abs/2502.11371
- When to use Graphs in RAG: A Comprehensive Analysis for Graph Retrieval-Augmented Generation (GraphRAG-Bench) — https://arxiv.org/abs/2506.05690
- BIRD benchmark — https://bird-bench.github.io/ ; Spider 2.0 — https://arxiv.org/abs/2411.07763
- Vanna — https://github.com/vanna-ai/vanna ; LangChain SQL agent — https://docs.langchain.com/oss/python/langchain/sql-agent
- Inference Scaling for Long-Context Retrieval Augmented Generation — https://arxiv.org/abs/2410.04343
- DRAG: Distilling RAG for SLMs from LLMs ... — https://arxiv.org/abs/2506.01954
- Removal of Hallucination on Hallucination: Debate-Augmented RAG — https://arxiv.org/abs/2505.18581
- Dynamic Retrieval-Augmented Generation — https://arxiv.org/abs/2312.08976
- DRAGged into Conflicts: Detecting and Addressing Conflicting Sources in Search-Augmented LLMs — https://arxiv.org/abs/2506.08500
- DRAGIN: Dynamic Retrieval Augmented Generation based on the Real-time Information Needs of Large Language Models — https://aclanthology.org/2024.acl-long.702 ; https://github.com/oneal2000/DRAGIN
- Videos: none verified this session [UNVERIFIED — search YouTube for "GraphRAG Microsoft Research Forum" before citing].

---

## 13. Slide ideas (8)
1. **"Where vector RAG breaks"** — two panels: global question (answer smeared across 1,000 chunks, heatmap lights up everywhere) vs multi-hop question (three chunks connected by dotted arrows, none similar to the query). Animate the top-k window missing them.
2. **"GraphRAG indexing in 6 phases"** — horizontal pipeline animation: doc -> chunks -> entity nodes pop out -> edges draw -> Leiden colors communities, zoom out to levels C0..C3 -> report cards stack -> embeddings. Cost counter ticking up at each LLM step.
3. **"Four ways to ask a graph"** — 2x2: Global (map-reduce over report cards), Local (entity starburst), DRIFT (primer -> branching follow-up tree with confidence glyphs), Basic (vector). Overlay win-rate badges (72–83%, 78%/81%).
4. **"Lazy beats eager"** — bar chart on log scale: indexing cost (GraphRAG 1000x vs Lazy = vector = 1x) and query cost (Global vs Lazy, >700x); slider animation for the relevance-test budget Z100 -> Z1500 raising quality.
5. **"Graph flavors side by side"** — table-morph slide: GraphRAG (communities), LightRAG (dual-level keywords + 1-hop, incremental union), HippoRAG 2 (PPR spreading activation animated as heat diffusing from seed nodes), RAPTOR (tree growing upward via UMAP+GMM clusters).
6. **"The metric trap"** — same systems, two scoreboards: LLM-judge win rate vs exact F1 (LightRAG ~50% vs 6.6 F1; HippoRAG 2 59.8 vs dense 57.0). Flip-card animation.
7. **"KG-RAG in production with Neo4j"** — live code split: SimpleKGPipeline builds graph (left), VectorCypherRetriever query + Text2Cypher (right); callout LinkedIn -28.6% resolution time.
8. **"Text-to-SQL is RAG over schema"** — flow: question -> retrieve tables/columns + few-shot SQL -> generate -> execute -> error loop -> answer. Gauge: BIRD 82.95 vs human 92.96; Spider 2.0 21.3% "enterprise reality check".
9. **"DRAG: five papers, one acronym"** — spinning acronym wheel resolving to Demonstration / Distilling / Debate / Dynamic (entity) / (D)RAGged conflicts, plus DRAGIN's RIND (when) + QFS (what) shown as attention heatmap over the context.
10. **"Which structure for which question?"** — decision tree from Section 11, ending in an agentic router icon that picks vector / graph / SQL tools.
