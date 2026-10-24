# 07: RAG Platforms, Google Codelabs, Managed RAG and Frameworks (as of 2026-10-23)

> Research brief for the 60-slide RAG deck. Every API name and import path here was checked against a primary source in this session (Google docs and codelabs, OpenAI and Microsoft docs, AWS docs, PyPI JSON, GitHub API). Anything not confirmed is tagged **[UNVERIFIED]**.

---

## 0. Context you need first: the 2026 Google renames

- **Vertex AI became the "Gemini Enterprise Agent Platform"**, announced at Google Cloud Next on **2026-04-22**. The docs now live under `docs.cloud.google.com/gemini-enterprise-agent-platform/...`, and old `/vertex-ai/` links redirect. Source: https://docs.cloud.google.com/gemini-enterprise-agent-platform/release-notes
  - Vertex AI Studio became **Agent Studio**, and Agent Engine became **Agent Runtime** (secondary coverage: https://thenewstack.io/google-finally-builds-the-ai-and-agent-platform-its-been-describing-for-years/).
  - Codelab titles now read "...Gemini Enterprise Agent Platform (formerly Vertex AI)".
- **There is a new Python SDK for RAG Engine.** The package is `google-cloud-agentplatform` **2.6.0** (PyPI, 2026-10-20), imported as `import agentplatform`. It uses a client object: `client.rag.create_corpus`, `client.rag.import_files`, `client.rag.retrieve_contexts`. The older `vertexai.rag` / `vertexai.preview.rag` style (`rag.create_corpus`, `rag.retrieval_query`) still shows up on many pages, ADK samples among them. **Don't mix the two styles in one project.**
- **ADK docs** now call the RAG Engine integration "**Knowledge Engine**" (https://adk.dev/integrations/knowledge-engine/), but the setup link still uses the `rag-engine` slug. Treat a formal rename of RAG Engine as **[UNVERIFIED]**. Cloud docs still say "RAG Engine".
- **Vertex AI Search** appears in current RAG Engine docs as "**Agent Search**" ("Use Agent Search as a retrieval backend using RAG Engine": https://docs.cloud.google.com/vertex-ai/generative-ai/docs/rag-engine/use-vertexai-search).
- **GitHub moves** (from the API redirects): `google/adk-samples` now resolves to **google/adk-recipes**, `firebase/genkit` to **genkit-ai/genkit**, `googleapis/genai-toolbox` to **googleapis/mcp-toolbox** (MCP Toolbox for Databases), and `explodinggradients/ragas` to **vibrantlabsai/ragas**.

---

## 1. Google codelabs and tutorials on RAG (exact titles and URLs)

### 1.1 Vertex AI / Agent Platform RAG Engine (managed RAG on GCP)
| Title | URL | Notes |
|---|---|---|
| RAG quickstart (docs, not a codelab) | https://docs.cloud.google.com/gemini-enterprise-agent-platform/build/rag-engine/rag-quickstart | Canonical; new `agentplatform` client |
| Deploying a RAG Application with AlloyDB to Agent Engine (notebook) | https://github.com/GoogleCloudPlatform/generative-ai/blob/main/gemini/agent-engine/tutorial_alloydb_rag_agent.ipynb | GoogleCloudPlatform/generative-ai repo, 17.8k stars |

I found **no dedicated codelabs.developers.google.com codelab for RAG Engine itself**. The quickstart is the primary learning path.

**Key code** (verbatim from the quickstart, lightly trimmed). The model in the doc is `gemini-3.5-flash` and the embedding model is `text-embedding-005`.
```python
import agentplatform
from agentplatform import types
from google import genai
from google.genai import types as genai_types

client = agentplatform.Client(project=PROJECT_ID, location="us-east4")
emb = types.RagEmbeddingModelConfig(
    vertex_prediction_endpoint=types.RagEmbeddingModelConfigVertexPredictionEndpoint(
        endpoint="publishers/google/models/text-embedding-005"))
rag_corpus = client.rag.create_corpus(rag_corpus=types.RagCorpus(
    display_name="test_corpus",
    rag_vector_db_config=types.RagVectorDbConfig(rag_embedding_model_config=emb)))
client.rag.import_files(name=rag_corpus.name, import_config=types.ImportRagFilesConfig(
    gcs_source=genai_types.GcsSource(uris=["gs://my_bucket/my_files_dir/*"]),
    rag_file_transformation_config=types.RagFileTransformationConfig(
        rag_file_chunking_config=types.RagFileChunkingConfig(chunk_size=512, chunk_overlap=100))))
rag_tool = genai_types.Tool(retrieval=genai_types.Retrieval(
    vertex_rag_store=genai_types.VertexRagStore(
        rag_resources=[genai_types.VertexRagStoreRagResource(rag_corpus=rag_corpus.name)],
        rag_retrieval_config=genai_types.RagRetrievalConfig(top_k=3))))
genai_client = genai.Client(enterprise=True, project=PROJECT_ID, location="us-east4")
resp = genai_client.models.generate_content(model="gemini-3.5-flash",
    contents="What is RAG and why it is helpful?",
    config=genai_types.GenerateContentConfig(tools=[rag_tool]))
```
**Flow in words:** GCS or Drive files go to `import_files`, which parses, chunks (512/100) and embeds them (text-embedding-005) into a RagCorpus vector DB (managed Spanner-based by default; Pinecone, Vertex Vector Search and others can be plugged in). At query time, `retrieve_contexts` (top_k, `vector_distance_threshold`) runs on its own, or Gemini calls the Retrieval tool automatically inside `generate_content`.

RAG Engine first launched as "Vertex AI RAG Engine" (GA announcement blog, Jan 15 2025: https://www.infoworld.com/article/3804343/google-rolls-out-vertex-ai-rag-engine.html).

### 1.2 ADK + RAG (agentic RAG on Google)
| Title | URL |
|---|---|
| ADK docs: Knowledge Engine (Vertex AI RAG retrieval tool) | https://adk.dev/integrations/knowledge-engine/ |
| ADK sample "RAG" agent (google/adk-recipes, formerly adk-samples, 10.5k stars) | https://github.com/google/adk-recipes |
| Build a Sports Shop Agent AI Assistant with ADK, MCP Toolbox and AlloyDB | https://codelabs.developers.google.com/codelabs/sports-agent-adk-mcp-alloydb |
| Build a Patent Search App with AlloyDB, vector search, and Java Agent Development Kit | https://codelabs.developers.google.com/patent-search-java-adk |
| Installing and Setting-up Toolbox for your Generative AI & Agentic Applications on AlloyDB | https://codelabs.developers.google.com/genai-toolbox-for-alloydb |
| Advanced RAG Techniques (Production-Ready AI with Google Cloud path) | https://codelabs.developers.google.com/codelabs/production-ready-ai-with-gc/8-advanced-rag-methods/advanced-rag-methods |

**ADK RAG agent** (verbatim from adk.dev; `google-adk` is **2.13.0** on PyPI, released 2026-10-23):
```python
import os
from google.adk.agents import Agent
from google.adk.tools.retrieval.vertex_ai_rag_retrieval import VertexAiRagRetrieval
from vertexai.preview import rag

ask_vertex_retrieval = VertexAiRagRetrieval(
    name="retrieve_rag_documentation",
    description="Use this tool to retrieve documentation and reference materials for the question from the RAG corpus,",
    rag_resources=[rag.RagResource(rag_corpus=os.environ.get("RAG_CORPUS"))],
    similarity_top_k=10,
    vector_distance_threshold=0.6,
)
root_agent = Agent(
    model="gemini-flash-latest",
    name="ask_rag_agent",
    instruction="You are an expert RAG documentation assistant. Use the retrieve_rag_documentation tool ...",
    tools=[ask_vertex_retrieval],
)
```
**Gotcha** (from the docs): this built-in tool "can only be used *by itself*" within an agent instance. The workaround is to wrap it in a sub-agent and expose that via AgentTool. Agentic RAG pattern: the agent decides *whether and when* to call retrieval, can loop, and can combine retrieval with MCP Toolbox SQL tools.

### 1.3 AlloyDB AI (Postgres plus in-database embeddings, ScaNN, reranking)
The official index at https://docs.cloud.google.com/alloydb/docs/ai/alloydb-ai-use-cases lists these codelabs:
1. Build a patent search app using AlloyDB, vector search, and Gemini Enterprise Agent Platform (formerly Vertex AI): https://codelabs.developers.google.com/patent-search-alloydb-gemini
2. Getting started with Vector Embeddings with AlloyDB AI: https://codelabs.developers.google.com/alloydb-ai-embedding
3. AlloyDB AI Operators and Reranking: https://codelabs.developers.google.com/alloydb-ai-operators
4. Multimodal Embeddings in AlloyDB: https://codelabs.developers.google.com/alloydb-ai-mm-embeddings
5. Generate SQL using AlloyDB AI natural language: https://codelabs.developers.google.com/alloydb-ai-nl-sql
6. Building an LLM and RAG-based chat application using AlloyDB AI and LangChain: https://codelabs.developers.google.com/codelabs/genai-db-retrieval-app
7. Build an AI-powered outfit recommendation app with AlloyDB and serverless runtimes: https://codelabs.developers.google.com/smart-stylist-app
8. Part 1: Build a Smart Shopping Assistant with AlloyDB and AI Applications: https://codelabs.developers.google.com/smart-shop-agent-alloydb
9. Part 2: Deploy a Smart Shopping Assistant with AlloyDB and AI Applications: https://codelabs.developers.google.com/smart-shop-agent-vertexai
10. Toy Store Search App with Cloud Databases, Serverless Runtimes and Open Source Integrations: https://codelabs.developers.google.com/toy-store-app
11. Deploy AlloyDB Omni and local AI model on Kubernetes: https://codelabs.developers.google.com/alloydb-omni-gke-embeddings
12. Quality-controlled RAG / patent search recall: https://codelabs.developers.google.cn/patent-search-rag-recall (description: "Quality Controlled RAG with AlloyDB's latest Vector Search Features!")
- Plus the LangChain quickstart notebook: https://github.com/googleapis/langchain-google-alloydb-pg-python/blob/main/samples/langchain_quick_start.ipynb (`langchain-google-alloydb-pg` **0.15.0**)

**Key SQL** (verbatim from the patent-search codelab). RAG retrieval runs *inside the database*:
```sql
CREATE EXTENSION vector;
CREATE EXTENSION google_ml_integration;
UPDATE patents_data SET abstract_embeddings = embedding('gemini-embedding-001', abstract);
SELECT id || ' - ' || title AS literature FROM patents_data
ORDER BY abstract_embeddings <=> embedding('gemini-embedding-001',
  'A new Natural Language Processing related Machine Learning Model')::vector
LIMIT 10;
```
(`<=>` is pgvector's cosine-distance operator. The codelab's Java code has a typo, `'tgemini-embedding-001'`, which is worth pointing out in a live demo.)

### 1.4 Cloud SQL for PostgreSQL / MySQL + pgvector
| Title | URL |
|---|---|
| Advanced RAG Techniques | https://codelabs.developers.google.com/codelabs/production-ready-ai-with-gc/8-advanced-rag-methods/advanced-rag-methods |
| Building an LLM and RAG-based chat application using Cloud SQL databases and LangChain | https://codelabs.developers.google.com/codelabs/cloud-db-retrieval-app |
| Repo: genai-databases-retrieval-app ("Cymbal Air" assistant) | https://github.com/GoogleCloudPlatform/genai-databases-retrieval-app |

"Advanced RAG Techniques" covers Character, Recursive and Token splitters, pgvector on Cloud SQL, reranking with `VertexAIRank` (`langchain_google_community.vertex_rank`) inside a `ContextualCompressionRetriever` (fetch 10, keep 3), and **HyDE** plus **step-back prompting**. Embeddings come from `VertexAIEmbeddings(model_name="gemini-embedding-001", ...)`. The sample corpus is Harry Potter (`rag_harry_potter_db`).
```python
# Adapted from "Advanced RAG Techniques" codelab
from langchain_google_community.vertex_rank import VertexAIRank
from langchain.retrievers import ContextualCompressionRetriever  # [UNVERIFIED path in LangChain 1.x; moved to langchain_classic]
reranker = VertexAIRank(project_id=PROJECT_ID, location_id="global",
                        ranking_config="default_ranking_config", top_n=3)
base = vectorstore.as_retriever(search_kwargs={"k": 10})
compression_retriever = ContextualCompressionRetriever(
    base_compressor=reranker, base_retriever=base)

def generate_hyde_doc(query, llm):
    prompt = PromptTemplate.from_template(
        "Write a concise, hypothetical answer to the question.\nQuestion: {q}")
    return (prompt | llm).invoke({"q": query}).content   # embed THIS, not the query
```
"Cymbal Air" architecture: a retrieval service on Cloud Run sits in front of Cloud SQL (Postgres 15 + pgvector, or MySQL 8.0.36 with the `cloudsql_vector` flag), and the chat app runs on a Compute Engine VM. Package: `langchain-google-cloud-sql-pg` **0.15.0**.

### 1.5 BigQuery vector search (RAG in pure SQL)
| Title | URL |
|---|---|
| Perform semantic search and retrieval-augmented generation (BigQuery docs tutorial) | https://docs.cloud.google.com/bigquery/docs/text-embedding-semantic-search |
| Create a RAG Application with BigQuery (Skills Boost lab GSP1289) | https://www.skills.google/catalog_lab/31904 [UNVERIFIED mapping of ID to GSP1289] |
| Coursera: Create Embeddings, Vector Search, and RAG with BigQuery | https://www.coursera.org/learn/create-embeddings-vector-search-and-rag-with-bigquery [UNVERIFIED canonical URL] |
| Blog: Introducing vector search in BigQuery (2024) | https://cloud.google.com/blog/products/data-analytics/introducing-new-vector-search-capabilities-in-bigquery |

I found no codelabs.developers.google.com page; the docs tutorial is canonical. **Note the naming:** current docs use `AI.GENERATE_EMBEDDING` and `AI.GENERATE_TEXT`, while older labs use `ML.GENERATE_EMBEDDING` and `ML.GENERATE_TEXT`.
```sql
CREATE OR REPLACE MODEL `bqml_tutorial.embedding_model`
  REMOTE WITH CONNECTION DEFAULT OPTIONS (ENDPOINT = 'text-embedding-005');
CREATE OR REPLACE VECTOR INDEX my_index ON `bqml_tutorial.embeddings`(embedding)
  OPTIONS(index_type='IVF', distance_type='COSINE', ivf_options='{"num_lists":500}');
SELECT result AS generated FROM AI.GENERATE_TEXT(MODEL `bqml_tutorial.text_model`,  -- gemini-2.5-flash
 (SELECT CONCAT('Propose project ideas to improve password security using: ',
   STRING_AGG(FORMAT("title: %s, abstract: %s", base.title, base.abstract), ',\n')) AS prompt
  FROM VECTOR_SEARCH(TABLE `bqml_tutorial.embeddings`, 'embedding',
    (SELECT embedding, content AS query FROM AI.GENERATE_EMBEDDING(
       MODEL `bqml_tutorial.embedding_model`, (SELECT 'improving password security' AS content))),
    top_k => 5, options => '{"fraction_lists_to_search": 0.01}')),
 STRUCT(600 AS max_output_tokens));
```
Dataset: `patents-public-data.google_patents_research.publications`. The whole retrieve, augment and generate loop runs in one SQL statement, which makes a strong slide.

### 1.6 Vertex AI Search (now "Agent Search")
| Title | URL |
|---|---|
| Building a Google-quality Search System with Vertex AI | https://codelabs.developers.google.com/build-google-quality-rag |
| Demo repo | https://github.com/kkrishnan90/vertex-ai-search-agent-builder-demo |

Flow: a GCS bucket holds JSONL metadata, which feeds an Agent Builder **data store** (parser options: digital, OCR or layout, plus advanced chunking). That data store backs a **Search app** (Enterprise edition + Advanced LLM features). The React and Python app is deployed to Cloud Run. This is "RAG as a product": ingestion, chunking, ranking and grounded answers are all managed.

### 1.7 Firestore vector search
| Title | URL |
|---|---|
| Codelab - Build a contextual Yoga Poses recommender app with Firestore, Vector Search, Langchain and Gemini (Python version) | https://codelabs.developers.google.com/yoga-pose-firestore-vectorsearch-python |
| Build gen AI features powered by your data with Genkit (Firebase codelab, TypeScript) | https://firebase.google.com/codelabs/ai-genkit-rag (repo: FirebaseExtended/codelab-ai-genkit-rag) |

```python
# Yoga codelab (langchain-google-firestore 0.5.0; embedding model text-embedding-004)
vector_store = FirestoreVectorStore.from_documents(
    client=firestore.Client(project=PROJECT, database=DB),
    collection="poses", documents=documents, embedding=VertexAIEmbeddings(
        model_name="text-embedding-004", project=PROJECT, location=LOC))
results = FirestoreVectorStore(client=client, collection="poses",
    embedding_service=embedding).similarity_search(query=q, k=3, include_metadata=True)
```
Index: `gcloud firestore indexes composite create --collection-group=poses --query-scope=COLLECTION --field-config=vector-config='{"dimension":"768","flat": "{}"}',field-path=embedding`

### 1.8 Genkit (Firebase / Google OSS framework)
The "Compass" travel app codelab (above) uses `defineFirestoreRetriever(ai, { name:'placesRetriever', collection:'places', contentField:'knownFor', vectorField:'embedding', embedder: vertexAI.embedder('text-embedding-005',{outputDimensionality:768}), distanceMeasure:'COSINE' })` and then `ai.retrieve({ retriever: placesRetriever, query, options:{limit:4} })`. Node 20+. Repo: **genkit-ai/genkit** (6.5k stars). The Python `genkit` package is **0.12.0** (2026-09-24).

### 1.9 Gemini API File Search (developer-tier managed RAG)
- **Docs:** https://ai.google.dev/gemini-api/docs/file-search
- **Launch:** announced on the Google developers blog around **Nov 6, 2025** as "a fully managed RAG system built directly into the Gemini API". Original blog URL **[UNVERIFIED]** (the text is reproduced at https://gilbane.com/2025/11/06/). Coverage: https://venturebeat.com/ai/why-googles-file-search-could-displace-diy-rag-stacks-in-the-enterprise
- **Pricing:** storage and query-time embeddings are **free**. Indexing is billed at embeddings rates (launch figure: **$0.15 per 1M tokens**, gemini-embedding-001). Retrieved chunks are billed as normal context tokens.
- **Limits** (current docs): 100 MB per file. Project store size is Free 1 GB, Tier 1 10 GB, Tier 2 100 GB, Tier 3 1 TB. Keep each store under 20 GB for latency. Storage is about 3x the input size.
- **Embedding models:** default `gemini-embedding-001`. Images and multimodal need `models/gemini-embedding-2`.
- **Features:** `chunking_config.white_space_config` (`max_tokens_per_chunk`, `max_overlap_tokens`), `custom_metadata` plus `metadata_filter` (AIP-160 syntax, e.g. `'author="Robert Graves"'`), and `file_citation` annotations (`file_name`, `page_number`, ...).
- **Current SDK surface** (`google-genai` **2.33.0**) uses the **Interactions API**:
```python
from google import genai
import time
client = genai.Client()
store = client.file_search_stores.create(config={
    'display_name': 'my-store', 'embedding_model': 'models/gemini-embedding-2'})
op = client.file_search_stores.upload_to_file_search_store(
    file='sample.txt', file_search_store_name=store.name,
    config={'display_name': 'display-file-name'})
while not op.done:
    time.sleep(5); op = client.operations.get(op)
interaction = client.interactions.create(
    model="gemini-3.8-flash", input="Can you tell me about ...",
    tools=[{"type": "file_search", "file_search_store_names": [store.name]}])
for step in interaction.steps:
    if step.type == "model_output":
        for b in step.content:
            if b.type == "text":
                print(b.text, [a.file_name for a in (b.annotations or []) if a.type == "file_citation"])
```
Older docs and blogs use `models.generate_content(..., config=types.GenerateContentConfig(tools=[types.Tool(file_search=types.FileSearch(file_search_store_names=[...]))]))`. Supported models listed include Gemini 3.8 Flash, 3.6 Flash, 3.5 Flash-Lite, 3.1 Pro Preview and "Gemini 4 Argon".

---

## 2. Managed RAG across clouds (Oct 2026)

| Platform | Primitive | Key API | Notable 2026 facts |
|---|---|---|---|
| **Gemini File Search** | FileSearchStore | `file_search_stores.*` + `file_search` tool | Free storage and query embeddings; multimodal via gemini-embedding-2 |
| **Google RAG Engine** | RagCorpus | `agentplatform.Client().rag.*` | BYO vector DB; Agent Search backend; ADK tool |
| **OpenAI file_search** | Vector Store | `client.vector_stores.create`, `vector_stores.files.create`, `responses.create(tools=[{"type":"file_search",...}])` | Hosted semantic + keyword search; `max_num_results`, `filters`, `include=["file_search_call.results"]`; Assistants API successor is the Responses API |
| **Amazon Bedrock Knowledge Bases** | Knowledge base + data source | `bedrock-agent-runtime`: `retrieve`, `retrieve_and_generate`(`_stream`) | Rerankers via `rerankingConfiguration`; query decomposition; GraphRAG on Neptune Analytics; S3 Vectors store (GA Dec 2025 per secondary source) |
| **Azure AI Search agentic retrieval** | Knowledge base + knowledge sources | `POST .../knowledgebases/{name}/retrieve` or MCP endpoint | GA in REST `2026-04-01` (minimal, extractive); query planning, answer synthesis and reasoning effort `low`/`medium` in `2026-08-01-preview`; powers **Foundry IQ** |

**OpenAI** (https://developers.openai.com/api/docs/guides/tools-file-search; `openai` SDK **3.37.0**):
```python
from openai import OpenAI
client = OpenAI()
vs = client.vector_stores.create(name="knowledge_base")
f = client.files.create(file=open("deep_research_blog.pdf", "rb"), purpose="assistants")
client.vector_stores.files.create(vector_store_id=vs.id, file_id=f.id)
resp = client.responses.create(
    model="gpt-6-astra",   # model as shown in current docs [UNVERIFIED model name]
    input="What is deep research by OpenAI?",
    tools=[{"type": "file_search", "vector_store_ids": [vs.id], "max_num_results": 2,
            "filters": {"type": "in", "key": "category", "value": ["blog", "announcement"]}}],
    include=["file_search_call.results"])
```
**Bedrock** (field names from https://docs.aws.amazon.com/bedrock/latest/userguide/kb-test-retrieve-generate.html; snippet adapted):
```python
import boto3
rt = boto3.client("bedrock-agent-runtime")
r = rt.retrieve_and_generate(
    input={"text": "What is our refund policy?"},
    retrieveAndGenerateConfiguration={"type": "KNOWLEDGE_BASE",
      "knowledgeBaseConfiguration": {"knowledgeBaseId": KB_ID, "modelArn": MODEL_ARN,
        "retrievalConfiguration": {"vectorSearchConfiguration": {
            "numberOfResults": 10, "overrideSearchType": "HYBRID"}}}})
print(r["output"]["text"]); print(r["citations"])   # generatedResponsePart + retrievedReferences
```
**Azure agentic retrieval flow** (https://learn.microsoft.com/en-us/azure/search/agentic-retrieval-overview, updated 2026-09-16). The app calls the knowledge base `retrieve` with the query and chat history. An LLM plans subqueries (skipped at `minimal` effort). Subqueries run **in parallel** as keyword, vector or hybrid searches, each goes through **semantic reranking (L2)**, and the results merge into grounding content with references and an activity log. Query-planning models: gpt-4o, gpt-4.1 and gpt-5 series. Worked cost example from the docs: 2,000 agentic retrievals cost about **$4.32** in total ($3.30 reranking + $1.02 planning). Quotable line: agentic retrieval "adds latency compared to a single-query pipeline, but it handles query complexity that a single query can't."

---

## 3. Framework versions (PyPI, checked 2026-10-23)

| Package | Latest | Released | Notes |
|---|---|---|---|
| langchain | **1.4.7** | 2026-10-21 | 1.0 shipped Oct 2025 (with LangGraph 1.0); `create_agent` + middleware; legacy chains moved to `langchain-classic` |
| langchain-core | 1.7.0 | 2026-10-22 | |
| langgraph | **1.2.16** | 2026-10-16 | Agentic RAG graphs (retrieve, grade, rewrite, generate) |
| llama-index / -core | **0.14.25** | 2026-09-21 | Still 0.x; Workflows, LlamaParse / LlamaCloud |
| haystack-ai | **3.4.1** | 2026-10-21 | **Haystack 3.0** is out (the brief's "2.x" is outdated): Agent owns tool execution plus hooks, one Pipeline with async/`Pipeline.stream()`, `warm_up`/`close` lifecycle, ~30 components moved to core-integrations (https://haystack.deepset.ai/release-notes/3.0.0) |
| dspy | **3.4.1** | 2026-10-12 | DSPy 3 line (3.0 in Aug 2025 [UNVERIFIED exact date]); optimizers like GEPA/MIPROv2 for RAG programs |
| google-adk | **2.13.0** | 2026-10-23 | |
| google-genai | 2.33.0 | 2026-10-23 | File Search, Interactions API |
| google-cloud-agentplatform | 2.6.0 | 2026-10-20 | New RAG Engine client |
| google-cloud-aiplatform | 2.6.0 | 2026-10-20 | legacy `vertexai` SDK |
| langchain-google-vertexai | 3.2.5 | 2026-10-23 | |
| openai | 3.37.0 | 2026-10-22 | |
| ragas | 0.4.3 | 2026-01-13 | RAG eval (faithfulness, context precision/recall) |

---

## 4. Top RAG GitHub repos (stars via GitHub API, 2026-10-23)

| Repo | Stars | What it is |
|---|---|---|
| langgenius/dify | 159.4k | LLMOps platform with a visual RAG pipeline |
| open-webui/open-webui | 156.6k | Self-hosted chat UI with built-in RAG |
| langchain-ai/langchain | 148.3k | Framework |
| infiniflow/ragflow | 92.8k | Deep-document-understanding RAG engine |
| Mintplex-Labs/anything-llm | 67.5k | All-in-one desktop/doc RAG |
| run-llama/llama_index | 52.6k | Data framework for RAG |
| milvus-io/milvus | 46.5k | Vector DB |
| langchain-ai/langgraph | 43.8k | Agent graphs / agentic RAG |
| HKUDS/LightRAG | 40.3k | Graph-based lightweight RAG |
| VectifyAI/PageIndex | 39.6k | Vectorless, reasoning-based tree-index RAG |
| stanfordnlp/dspy | 38.8k | Programming, not prompting, LMs |
| microsoft/graphrag | 36.4k | GraphRAG (community summaries) |
| qdrant/qdrant | 35.2k | Vector DB |
| NirDiamant/RAG_Techniques | 30.0k | Notebook catalogue of 30+ RAG techniques |
| chroma-core/chroma | 29.6k | Embedded vector DB |
| deepset-ai/haystack | 26.8k | Pipeline framework |
| pgvector/pgvector | 23.5k | Postgres vector extension (used by AlloyDB / Cloud SQL) |
| google/adk-python | 22.0k | Google ADK |
| GoogleCloudPlatform/generative-ai | 17.8k | Official GCP notebooks (RAG Engine, Agent Engine) |
| googleapis/mcp-toolbox | 16.7k | MCP Toolbox for Databases (ex genai-toolbox) |
| vibrantlabsai/ragas | 16.1k | RAG evaluation |
| google/adk-recipes | 10.5k | ADK samples incl. RAG agent |
| genkit-ai/genkit | 6.5k | Genkit |

---

## 5. Real-world examples to cite
- **Cymbal Air** (Google sample airline assistant): RAG over Cloud SQL / AlloyDB flight and amenity tables, plus tool-calling for bookings (genai-databases-retrieval-app).
- **Patent search** (AlloyDB + `embedding()` + `<=>`): enterprise semantic search over public patents. BigQuery's tutorial uses the same public dataset.
- **Compass travel planner** (Genkit + Firestore): RAG grounding for itinerary generation.
- **Azure OpenAI Demo** (https://github.com/Azure-Samples/azure-search-openai-demo): updated to use agentic retrieval. **Foundry IQ** is Microsoft's managed "knowledge layer for agents".
- **Gemini File Search launch partner:** coverage cites Phaser Studio's "Beam" game-generation tool **[UNVERIFIED]**.

---

## 6. Quotable lines
- "File Search imports, chunks, and indexes your data to enable fast retrieval of relevant information based on a provided prompt." (Gemini API docs)
- "...a fully managed RAG system built directly into the Gemini API that abstracts away the retrieval pipeline." (Google developers blog, Nov 2025, via reprint)
- "Agentic retrieval is a multi-query pipeline designed for complex questions posed by users or agents in chat and copilot apps." (Microsoft Learn)
- The built-in RAG tool "can only be used by itself within an agent instance." (ADK docs; good lead-in to sub-agent patterns)
- "Write a concise, hypothetical answer to the question." (the entire HyDE prompt, Advanced RAG Techniques codelab)

---

## 7. Slide ideas (8)
1. **"Five places RAG can live on Google Cloud"**: a ladder diagram from SQL (BigQuery `VECTOR_SEARCH`) to DB (AlloyDB/Cloud SQL pgvector, Firestore), managed (RAG Engine, Agent Search), API (Gemini File Search) and agent (ADK). Animate each rung with "you manage / Google manages" shading.
2. **"RAG in one SQL statement"**: the BigQuery AI.GENERATE_TEXT(VECTOR_SEARCH(AI.GENERATE_EMBEDDING())) query, with nested boxes zooming outward (embed, then search, then generate).
3. **"`<=>`: the operator that does retrieval"**: the AlloyDB query with the operator highlighted, and a 2D embedding scatter where the 10 nearest points light up.
4. **"Managed RAG in 15 lines"**: Gemini File Search code side by side with OpenAI file_search, showing the same four steps (create store, upload, poll, query with tool). Highlight citations coming back.
5. **"From retrieval tool to agentic RAG"**: the ADK `VertexAiRagRetrieval` agent loop animation (user, agent decides, tool call, chunks, answer, maybe re-query), with the "can only be used by itself" constraint leading to a sub-agent wrapper.
6. **"Azure agentic retrieval pipeline"**: a fan-out diagram (query plan, 3 parallel subqueries, semantic rerank, merge), with a reasoning-effort dial (minimal/low/medium) and the $4.32 cost callout.
7. **"Advanced RAG upgrades in the codelab"**: a before/after triptych: splitter comparison, reranker (10 down to 3 funnel), HyDE (query becomes a hypothetical doc, which then gets embedded).
8. **"The 2026 managed-RAG comparison table"**: Gemini / RAG Engine / OpenAI / Bedrock / Azure across storage price, rerank, graph, filters and agentic features. Reveal row by row.
9. **"Framework landscape Oct 2026"**: a bubble chart of stars against version (LangChain 1.4, LangGraph 1.2, LlamaIndex 0.14, Haystack 3.4, DSPy 3.4), with a callout for "Haystack 3.0 is out".
10. **"Rename map 2026"**: an arrow graphic showing Vertex AI to Gemini Enterprise Agent Platform, Agent Engine to Agent Runtime, Vertex AI Search to Agent Search, adk-samples to adk-recipes, genai-toolbox to mcp-toolbox, so students can find old tutorials.

## 8. Open items / unverified
- Whether "RAG Engine" is officially renamed "Knowledge Engine" (only seen in ADK docs).
- The exact original URL of the Gemini File Search launch blog post.
- The `ContextualCompressionRetriever` import path under LangChain 1.x (likely `langchain_classic.retrievers`).
- OpenAI model ID `gpt-6-astra` comes from the docs sample; it was not separately verified.
- Bedrock S3 Vectors GA date (Dec 2025) comes from a secondary source.
