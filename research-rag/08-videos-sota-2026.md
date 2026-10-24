# 08 — RAG Frontier 2025-2026: Papers, Trends, Videos & Courses

Research date: 2026-10-23. Every item links to a primary source where one was found. Items marked **[UNVERIFIED]** could not be confirmed against a primary source in this pass.

---

## 1. The one-paragraph story (for the narrator)

From 2020 to 2023, RAG meant a fixed pipeline: chunk, embed, top-k, stuff into the prompt. Three things changed it in 2025-2026:
1. **Reasoning models learned to search.** RL-trained agents (Search-R1, OpenAI Deep Research) decide *when* and *what* to retrieve, in several rounds.
2. **Context windows grew to 1M-10M tokens** (Llama 4 Scout: 10M, April 2025). That revived the "RAG is dead" argument, but measurements of *context rot* showed that more tokens in the window does not mean better answers.
3. **Context engineering replaced prompt engineering** as the field's framing (Anthropic, Sep 2025; LangChain, Jul 2025). Retrieval became one tool among several for curating "the smallest possible set of high-signal tokens."

Graphs came back (HippoRAG 2, LazyGraphRAG), retrievers and rerankers began to reason (ReasonIR, Rank1), and test-time compute started being spent on retrieval (DRAG/IterDRAG, best-of-N on BrowseComp).

---

## 2. Key papers 2024-2026 (verified)

| Paper | arXiv / venue | Date | Key claim / number |
|---|---|---|---|
| **Search-R1: Training LLMs to Reason and Leverage Search Engines with Reinforcement Learning** (Bowen Jin et al., UIUC / UMass / Google Cloud AI Research) | [arXiv 2503.09516](https://arxiv.org/abs/2503.09516), COLM 2025 | Mar 2025 | RL with an outcome-only reward, plus masking of retrieved tokens. Gains over RAG baselines on 7 QA sets: **v1/v3 abstract reports +41% (Qwen2.5-7B) and +20% (3B); v4/v5 reports +24% and +20%.** Cite the version you use. Code: [github.com/PeterGriffinJin/Search-R1](https://github.com/PeterGriffinJin/Search-R1) (Apache-2.0; PPO, GRPO and REINFORCE; BM25, E5 dense or Google/Bing/Brave search). |
| **Inference Scaling for Long-Context Retrieval Augmented Generation** (Yue, Zhuang et al., Google DeepMind / UIUC / UMass) | [arXiv 2410.04343](https://arxiv.org/abs/2410.04343), ICLR 2025 | Oct 2024 (v2 Mar 2025) | DRAG (more documents plus in-context demos) and IterDRAG (decomposes the query into sub-queries with interleaved retrieval, Self-Ask style, at most 5 iterations). Reports a **near-linear** relationship between RAG performance and effective context length when compute is allocated well. Standard RAG plateaus early. |
| **From RAG to Memory: Non-Parametric Continual Learning for LLMs** (HippoRAG 2, Gutiérrez, Shu, Qi, Zhou, Su, OSU) | [arXiv 2502.14802](https://arxiv.org/abs/2502.14802), ICML 2025 | Feb 2025 | Personalized PageRank over a KG plus deeper passage integration. **+7% on associative-memory tasks** over a SOTA embedding model, without losing factual QA. Code: [github.com/OSU-NLP-Group/HippoRAG](https://github.com/OSU-NLP-Group/HippoRAG) |
| **ReasonIR: Training Retrievers for Reasoning Tasks** (Meta FAIR + UW) | [arXiv 2504.20595](https://arxiv.org/abs/2504.20595) | Apr 2025 | ReasonIR-8B (from Llama 3.1-8B) scores **29.9 nDCG@10 on BRIGHT without a reranker and 36.9 with one**. RAG gains of +6.4% on MMLU and +22.6% on GPQA over closed-book. |
| **Rank1: Test-Time Compute for Reranking in Information Retrieval** (Weller et al., JHU) | [arXiv 2502.18418](https://arxiv.org/abs/2502.18418), COLM 2025 | Feb 2025 | A reranker that "thinks", distilled from a reasoning model. Releases more than **600K reasoning traces** built from MS MARCO. |
| **BrowseComp: A Simple Yet Challenging Benchmark for Browsing Agents** (OpenAI) | [arXiv 2504.12516](https://arxiv.org/abs/2504.12516), [blog](https://openai.com/index/browsecomp/) | Apr 2025 | 1,266 questions (21 removed from the original 1,287). Accuracy: **GPT-4o 0.6%, GPT-4o + browsing 1.9%, o1 9.9%, Deep Research 51.5%**. Best-of-N over 64 samples adds **15-25%**. |
| **Agentic Retrieval-Augmented Generation: A Survey on Agentic RAG** (Singh, Ehtesham, Kumar, Khoei, Vasilakos) | [arXiv 2501.09136](https://arxiv.org/abs/2501.09136) | Jan 2025 (v4 Apr 2026) | Taxonomy by agent cardinality, control structure, autonomy and knowledge representation. Repo: [github.com/asinghcsu/AgenticRAG-Survey](https://github.com/asinghcsu/AgenticRAG-Survey) |
| **Towards Agentic RAG with Deep Reasoning: A Survey of RAG-Reasoning Systems in LLMs** | [arXiv 2507.09477](https://arxiv.org/abs/2507.09477) | Jul 2025 | Survey of how reasoning and retrieval combine; includes tables of search-RL methods. |
| **Deep Research: A Survey of Autonomous Research Agents** | [arXiv 2508.12752](https://arxiv.org/abs/2508.12752) | Aug 2025 | Survey of deep-research agents (contents not deeply verified). |
| **Data-Centric Perspectives on Agentic RAG: A Survey** | [ACL Findings 2026](https://preview.aclanthology.org/ingest-acl/2026.findings-acl.78/) | 2026 | Argues that the scarcity of agent trajectories is the bottleneck. |
| **Context Rot: How Increasing Input Tokens Impacts LLM Performance** (Kelly Hong, Anton Troynikov, Jeff Huber, Chroma) | [trychroma.com/research/context-rot](https://research.trychroma.com/context-rot) | 14 Jul 2025 | **18 LLMs** tested (GPT-4.1, Claude 4, Gemini 2.5, Qwen3). Performance degrades "in surprising and non-uniform ways" as input length grows, even on trivial tasks. Note: Chroma sells retrieval infrastructure. |
| **LazyGraphRAG** (Microsoft Research blog) | [blog](https://www.microsoft.com/en-us/research/blog/lazygraphrag-setting-a-new-standard-for-quality-and-cost/) | 25 Nov 2024; in Microsoft Discovery from Jun 2025 | No up-front LLM summarization of the graph. Reports quality comparable to GraphRAG Global Search at a fraction of the query cost. GraphRAG 1.0 shipped on 16 Dec 2024 ([post](https://www.microsoft.com/en-us/research/blog/moving-to-graphrag-1-0-streamlining-ergonomics-for-developers-and-users/)). |

Industry reports with hard numbers:
- **Anthropic, "How we built our multi-agent research system"** (13 Jun 2025): <https://www.anthropic.com/engineering/multi-agent-research-system>. Uses an orchestrator-worker pattern. The multi-agent setup (Opus 4 lead, Sonnet 4 subagents) "outperformed single-agent Claude Opus 4 by **90.2%**." "Token usage by itself explains **80%** of the variance" on BrowseComp, and three factors together explain 95%. Agents use about **4×** the tokens of chat; multi-agent systems use about **15×**.
- **Anthropic, "Introducing Contextual Retrieval"** (Sep 2024): <https://www.anthropic.com/news/contextual-retrieval>. Top-20 retrieval failure rate falls from 5.7% to 3.7% with contextual embeddings (−35%), to 2.9% when contextual BM25 is added (−49%), and to 1.9% with reranking (−67%). Figures were confirmed through several secondary sources and match Anthropic's post as I remember it; **[re-check exact wording on the primary page]**.

---

## 3. Trends, each explained as a step-by-step flow

### 3.1 Agentic search (retrieval as a tool the model calls)
**Flow:** User question → reasoning model thinks → emits `<search>query</search>` → environment runs the retriever → results are injected as `<information>…</information>` → model thinks again, possibly searching several more times → `<answer>…</answer>`. This is the Search-R1 rollout template from the arXiv 2503.09516 paper; the GitHub README does not show the tags. RL rewards only whether the final answer is correct (exact match). Retrieved tokens are **masked out of the loss**, so the model is never trained to "generate" evidence.

**Production equivalents:** OpenAI Deep Research (51.5% on BrowseComp), the Anthropic Research orchestrator with parallel subagents, and Gemini File Search used as a tool. Search-R1 was integrated into veRL (Jun 2025) and SkyRL (Jul 2025), and was featured in Thinking Machines' Tinker (Oct 2025), per the repo news.

Quote (OpenAI, BrowseComp blog): "browsing alone is not sufficient—models must also be capable of reasoning strategically, identifying relevant search paths, and interpreting retrieved content."

### 3.2 Reasoning plus retrieval inside the retriever
- **Reasoning retrievers:** ReasonIR-8B trains on synthetic queries that need reasoning to match, each paired with a hard negative. It sets SOTA on BRIGHT, the reasoning-intensive retrieval benchmark.
- **Reasoning rerankers:** Rank1 spends test-time tokens per (query, doc) pair.
- Orion Weller (Hamel series, part 3): retrievers can now follow instructions like "find documents about data privacy using metaphors."

### 3.3 Test-time compute for retrieval
Three levers, all verified:
1. **More documents plus demonstrations** (DRAG) and **iterative decomposition** (IterDRAG). Performance scales near-linearly with effective context when compute is allocated optimally (arXiv 2410.04343).
2. **Sampling and aggregation:** best-of-N over 64 samples raised BrowseComp scores by 15-25% (OpenAI).
3. **Parallel subagents**, which spend tokens across separate context windows. In Anthropic's analysis, token usage explains 80% of the performance variance.

Slide line: *"In 2026 you don't buy better retrieval only with a better embedding. You also buy it with inference compute."*

### 3.4 Context engineering (the 2025 reframe)
- **Anthropic, "Effective context engineering for AI agents"**, 29 Sep 2025, Applied AI team (Rajasekaran, Dixon, Ryan, Hadfield): <https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents>
  - Definition: "the set of strategies for curating and maintaining the optimal set of tokens (information) during LLM inference."
  - "good context engineering means finding the smallest possible set of high-signal tokens that maximize the likelihood of some desired outcome."
  - **Just-in-time retrieval:** agents keep "lightweight identifiers (file paths, stored queries, web links, etc.)" and load data at runtime through tools.
  - **Hybrid strategy:** some data is retrieved up front and the rest explored by the agent. It "might be better suited for contexts with less dynamic content, such as legal or finance work."
  - **Compaction**, **structured note-taking**, and **sub-agents** that return "a condensed, distilled summary of its work (often 1,000-2,000 tokens)."
- **LangChain, "Context Engineering for Agents"** (2 Jul 2025): <https://blog.langchain.com/context-engineering-for-agents/>. Four buckets: **Write, Select, Compress, Isolate**. Attributed to Lance Martin; the post's byline reads "LangChain Team" **[author attribution UNVERIFIED]**.
- Where RAG fits: RAG is the **Select** operation. The vector store becomes one of several context sources, alongside memory, tools, the file system and scratchpads.

### 3.5 "RAG is dead?" versus 1M-10M token contexts
- **Pro-long-context:** Llama 4 Scout, released 5 Apr 2025, claims a **10M-token** context. It was pre- and post-trained at 256K, and Meta says it "generalizes" beyond that, a claim still debated. Gemini models offer 1M+ tokens.
- **Counter-evidence:** Chroma's Context Rot study (18 models) found that distractors and haystack *structure* matter. Coherent irrelevant text hurt more than shuffled text (from secondary summaries; **verify in the report**). Long prompts also bring cost, latency and KV-cache memory.
- **Practitioner consensus:** Hamel Husain and Ben Clavié, "Stop Saying RAG Is Dead" (7-part series, 2025): <https://hamel.dev/notes/llm/rag/not_dead.html>. Naive single-vector search is dead; retrieval is not.
- **Synthesis for the slide:** long context and RAG are **complementary**. Retrieval selects, and the long window holds the selection plus reasoning traces. Cache-augmented generation (CAG) suits small, static corpora; RAG suits large, changing, permissioned corpora.

### 3.6 Knowledge-graph revival, done carefully
- GraphRAG 1.0 (Dec 2024) → LazyGraphRAG (cheap, built at query time) → in **Microsoft Discovery** (Azure) from Jun 2025. BenchmarkQED eval toolkit released 5 Jun 2025.
- HippoRAG 2 (ICML 2025) treats the graph as long-term *memory*, using PPR over a KG.
- Counterpoint, Jo Kristian Bergum (Hamel series, part 7): "You don't need a graph database for GraphRAG." and "sophistication isn't complexity."
- AI Engineer World's Fair 2026 ran a dedicated **Graphs track** (Graph RAG, ontology-driven retrieval) alongside a **Search & Retrieval track**.

### 3.7 Late interaction and multiple representations
- Antoine Chaffin (Hamel series, part 4): late-interaction (ColBERT-style) models keep "token-level detail instead of forcing everything into one conflicted representation"; "150M parameter models outperforming 7B parameter alternatives on reasoning tasks."
- Bryan Bischof and Ayush Chaurasia (part 5): "Stop searching for the perfect embedding. Build specialized representations and route intelligently."

### 3.8 Managed "RAG-as-a-tool" from cloud vendors
- **Gemini API File Search** (launched Nov 2025 per third-party coverage **[launch date UNVERIFIED]**). The service handles chunking, embedding and indexing. Storage and query-time embeddings are free; you pay embedding rates at indexing time, and retrieved tokens are billed as normal context. Docs: <https://ai.google.dev/gemini-api/docs/file-search>
- **Vertex AI RAG Engine** (GA blog 15 Jan 2025): <https://cloud.google.com/blog/products/ai-machine-learning/introducing-vertex-ai-rag-engine>. Supports Pinecone, Weaviate, Vertex AI Vector Search or RagManagedDb.
- **ADK `VertexAiRagRetrieval` tool**, which turns retrieval into a tool the agent decides to call (agentic RAG in about 20 lines).

---

## 4. Real code snippets

### 4.1 Agentic RAG with Google ADK plus Vertex AI RAG Engine
Source: "Knowledge Engine tool for ADK", <https://adk.dev/integrations/knowledge-engine/> (based on google/adk-samples `RAG/rag/agent.py`; older snapshots omit `vector_distance_threshold`).
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
    instruction=("You are an expert RAG documentation assistant. Use the "
                 "retrieve_rag_documentation tool to fetch relevant documentation and "
                 "reference materials, then answer the user's question based on them."),
    tools=[ask_vertex_retrieval],
)
```
Teaching point: the *model* decides whether to call retrieval, which makes this agentic RAG rather than a fixed pipeline.

### 4.2 Managed RAG with Gemini File Search (current docs, Oct 2026)
Source: <https://ai.google.dev/gemini-api/docs/file-search.md.txt>, `google-genai` SDK. The current docs use the new `client.interactions` API and model `gemini-3.8-flash`. Older tutorials from 2025 use `client.models.generate_content` with `gemini-2.5-flash`. **Pin your SDK version.**
```python
from google import genai
import time

client = genai.Client()
store = client.file_search_stores.create(
    config={'display_name': 'course-notes', 'embedding_model': 'models/gemini-embedding-2'})

op = client.file_search_stores.upload_to_file_search_store(
    file='sample.txt', file_search_store_name=store.name,
    config={'display_name': 'sample'})
while not op.done:
    time.sleep(5)
    op = client.operations.get(op)

interaction = client.interactions.create(
    model="gemini-3.8-flash",
    input="What does the document say about X?",
    tools=[{"type": "file_search", "file_search_store_names": [store.name]}],
)
for step in interaction.steps:
    if step.type == "model_output":
        for block in step.content:
            if block.type == "text":
                print(block.text)
                for a in (block.annotations or []):
                    if a.type == "file_citation":
                        print("  -", a.file_name, a.source)
```

### 4.3 Search-R1 (research code) quick start
Source: <https://github.com/PeterGriffinJin/Search-R1> README.
```bash
conda activate retriever
bash retrieval_launch.sh      # E5 dense retriever over Wikipedia
conda activate searchr1
python infer.py               # edit `question` on line 7
```

---

## 5. Videos and courses (title, channel, URL, takeaways)

### LangChain: "RAG From Scratch" (Lance Martin)
- Playlist: **RAG From Scratch**, LangChain YouTube channel. <https://www.youtube.com/playlist?list=PLfaIDFEXuae2LXbO1_PKyVJiQ23ZztA0x>
- Notebooks: <https://github.com/langchain-ai/rag-from-scratch> (`rag_from_scratch_1_to_4.ipynb` … `15_to_18.ipynb`)
- Single-video version: **"Learn RAG From Scratch – Python AI Tutorial from a LangChain Engineer"**, freeCodeCamp.org, 2h33m, 17 Apr 2024. <https://youtu.be/sVcwVQRHIc8>
- Takeaways: covers indexing, retrieval and generation, then query translation (Multi-Query, RAG-Fusion, Decomposition, Step-Back, HyDE), routing, query construction, RAPTOR and ColBERT indexing, CRAG and Adaptive RAG, and "Is RAG still relevant?". This is the best ladder for the deck's middle section.

### DeepLearning.AI
- **Retrieval Augmented Generation (RAG)**, a course taught by Zain Hasan, about 3 weeks at roughly 10 h/week, intermediate, on Coursera. <https://www.deeplearning.ai/courses/retrieval-augmented-generation-rag>. Covers Weaviate, Arize Phoenix monitoring, hybrid retrieval, context-window limits and latency/cost trade-offs.
- **Building Agentic RAG with LlamaIndex**, a short course taught by Jerry Liu (6 videos, 4 notebooks, about 44-54 min). <https://www.deeplearning.ai/short-courses/building-agentic-rag-with-llamaindex/>. Covers a router query engine, tool calling with inferred arguments, a multi-step research agent and a multi-document agent.
- **Knowledge Graphs for RAG** (with Neo4j): exists to my knowledge, but this search did not confirm it **[UNVERIFIED]**.

### AI Engineer World's Fair (channel: AI Engineer, youtube.com/@aiDotEngineer)
Jerry Liu (LlamaIndex), from <https://www.ai.engineer/speakers/jerry-liu>:
- **"RAG for VPs of AI"**, WF 2024, 26:51. <https://www.youtube.com/watch?v=KJsUHnwSvTY>
- **"The Future of Knowledge Assistants"**, 16:55. <https://www.youtube.com/watch?v=zeAyuLc_f3Q>
- **"Building AI Agents that actually automate Knowledge Work"**, WF 2025, 17:57. <https://www.youtube.com/watch?v=jVGCulhBRZI>. Argues for moving beyond RAG chatbots to "document toolboxes" covering parsing, permissions, indexing, search and document manipulation. Distinguishes *assistive* agents (chat) from *automation* agents (background), and covers VLM-based parsing with agentic validation and an Excel agent.
- **"Building the Document Context Layer for AI Agents"**, WF 2026, 21:03. <https://www.youtube.com/watch?v=RQi7x-navxU>
- **"Production-Ready RAG: Retrieval, Evaluation, and Failure Analysis"**, 18:35. <https://www.youtube.com/watch?v=TRjq7t2Ms5I>

WF 2026 (29 Jun-2 Jul, SF) Search & Retrieval and Graphs tracks, from <https://www.ai.engineer/worldsfair/2026/llms.md>:
- Yuval Belfer (AI21), "Stop Chunking Like It's 2022": no single chunk size fits all queries; multi-index approach, "up to 37% better recall" (AI21's own claim).
- Jeff Ng, "Building agents is trivial now, context is the next frontier".
- Luis Romero-Sevilla, "Extended Cache Augmented Generation (ECAG)".
- Abed Matini, "Framework-Free Hybrid RAG, Raw SQL RRF, and Live UI Telemetry".
- YouTube URLs for these individual talks: **[UNVERIFIED]**. Check the AI Engineer channel.

### Hamel Husain and Ben Clavié: "Stop Saying RAG Is Dead" (7 parts, 2025)
Index: <https://hamel.dev/notes/llm/rag/not_dead.html>
1. Ben Clavié, "I don't use RAG, I just retrieve documents"
2. Nandan Thakur, "Modern IR Evals for RAG": "Models that ace BEIR benchmarks often fail at real RAG tasks."
3. Orion Weller, "Optimizing Retrieval with Reasoning Models"
4. Antoine Chaffin, "Late Interaction Models for RAG"
5. Bryan Bischof and Ayush Chaurasia, "RAG with Multiple Representations"
6. Kelly Hong (Chroma), "Context Rot", 10 Sep 2025, <https://youtu.be/3s_N60u0jEY>: "Simply having the right information in the context is not enough."
7. Jo Kristian Bergum, "You Don't Need a Graph DB (Probably)"

### Jason Liu (jxnl, creator of Instructor)
- Course: **Systematically Improving RAG Applications** (Maven). <https://maven.com/applied-llms/rag-playbook>. Covers synthetic evals, query segmentation and clustering, embedding fine-tuning and reranking. The course page claims +20% from reranking and +14% from cross-encoders; these are marketing figures.
- Podcast: TWIML #709, **"Why Your RAG System Is Broken, and How to Fix It"**. <https://twimlai.com/go/709>
- Podcast: Vanishing Gradients Ep. 27, **"How to Build Terrible AI Systems"**. <https://vanishinggradients.fireside.fm/27>
- AI Engineer 2023 keynote "Pydantic is all you need": not RAG-specific; URL **[UNVERIFIED]**.
- Takeaway: treat RAG as a recommender system. Measure retrieval with recall on synthetic questions, segment queries to find the worst-performing clusters, and fix data before models.

### Google Cloud Tech and Google resources
- I could not confirm an official Google Cloud Tech YouTube video on RAG Engine or ADK RAG in this pass **[UNVERIFIED]**. Use these primary written sources instead:
  - Codelab: **"Build a Google-quality RAG system with Vertex AI"**, <https://codelabs.developers.google.com/build-google-quality-rag> (grounded, cited answers with Vertex AI Search).
  - Blog: "Introducing Vertex AI RAG Engine" (Jan 2025), <https://cloud.google.com/blog/products/ai-machine-learning/introducing-vertex-ai-rag-engine>
  - Repo: <https://github.com/google/adk-samples> (RAG agent sample)
  - Community: "10-Minute Agentic RAG with the New Vector Search 2.0 and ADK" (Google Cloud Community, Medium)

---

## 6. Real-world examples
- **OpenAI Deep Research**: an RL-trained browsing agent; 51.5% on BrowseComp versus 1.9% for GPT-4o with browsing.
- **Anthropic Claude Research**: orchestrator-worker multi-agent search; +90.2% on Anthropic's internal research eval.
- **Microsoft Discovery** (Azure): GraphRAG and LazyGraphRAG offered as a product.
- **LlamaIndex / LlamaCloud**: document parsing plus agentic "knowledge work" automation.
- **Google Gemini File Search / Vertex AI RAG Engine**: managed RAG offered as a tool.
- **Thinking Machines Tinker** featured Search-R1-style RL training (repo news, Oct 2025).

---

## 7. Quotable lines (with source)
- "good context engineering means finding the smallest possible set of high-signal tokens that maximize the likelihood of some desired outcome." (Anthropic, Sep 2025)
- "token usage by itself explains 80% of the variance" (Anthropic multi-agent research post, Jun 2025)
- "browsing alone is not sufficient" (OpenAI, BrowseComp, Apr 2025)
- "As you add more information, models become increasingly unreliable, even on simple tasks." (Kelly Hong, Context Rot talk, Sep 2025)
- "Stop searching for the perfect embedding." (Bischof and Chaurasia, Hamel series)
- "You don't need a graph database for GraphRAG." (Jo Kristian Bergum, Hamel series)
- "Models that ace BEIR benchmarks often fail at real RAG tasks." (Nandan Thakur, Hamel series)

---

## 8. Slide ideas (8)
1. **"RAG timeline 2020 → 2026"**: horizontal timeline that builds left to right (RAG 2020 → Self-RAG/CRAG 2023 → GraphRAG 2024 → Search-R1 / Deep Research / Context Rot 2025 → File Search, Document Context Layer 2026).
2. **"The pipeline becomes a loop"**: morph a linear chunk→embed→retrieve→generate pipeline into a circular think→search→read→think loop with `<search>`/`<information>` tags. Animate the masked retrieved tokens greying out.
3. **"BrowseComp bar chart"**: 0.6 / 1.9 / 9.9 / 51.5 bars growing one at a time; caption: "browsing alone is not sufficient."
4. **"Context rot curve"**: accuracy against input length for several models, falling non-uniformly; overlay a "10M tokens!" sticker that cracks.
5. **"Long context vs RAG decision matrix"**: 2×2 of corpus size (small/large) × volatility (static/changing): CAG / long context, RAG, hybrid, agentic RAG.
6. **"Context engineering: Write / Select / Compress / Isolate"**: four quadrants around a context-window box; RAG lights up in "Select," compaction in "Compress," subagents in "Isolate."
7. **"Spend compute on retrieval"**: three dials (more docs + demos, best-of-N, parallel subagents) feeding an accuracy gauge; cite DRAG near-linear scaling and the 80%-variance quote.
8. **"Graphs are back (carefully)"**: split screen with GraphRAG/HippoRAG PPR spreading across nodes on the left and Bergum's "you don't need a graph DB" on the right.
9. **"Live demo: agentic RAG in 20 lines"**: the ADK `VertexAiRagRetrieval` code, highlighting step by step how the model chooses the tool.
10. **"Where to learn next"**: a grid of video thumbnails (LangChain RAG From Scratch, DLAI, Jerry Liu WF 2025/2026, Hamel series, Jason Liu course) with QR codes.
