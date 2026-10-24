# 03 — Agentic RAG: from routers to RL-trained deep-research agents (state as of 2026-10-23)

> Research brief for the 60-slide RAG deck. Every paper title, ID and number below was checked against arXiv, the official docs or a GitHub repo on 2026-10-23, unless it is marked [UNVERIFIED].

---

## 1. Definition and the core shift

- **Classic ("naive") RAG** is a fixed pipeline: `query -> retrieve top-k -> stuff into prompt -> generate`. Retrieval happens once, whether or not it is needed, and nothing checks whether the retrieved context is any good.
- **Agentic RAG** puts an LLM agent *in control of* retrieval. At each step the agent decides **whether** to retrieve, **where** to retrieve from (vector DB, SQL, web, API, MCP server), **what** to query (rewrite or decompose the question), **whether the evidence is good enough** (grade it and reflect on it), and **when to stop**.
- Quotable line (survey abstract, arXiv 2501.09136): Agentic RAG works by *"embedding autonomous AI agents into the RAG pipeline."*
- Quotable line (Anthropic, *How we built our multi-agent research system*, 2025-06-13): *"The essence of search is compression: distilling insights from a vast corpus."* https://www.anthropic.com/engineering/multi-agent-research-system

**Diagram in words: classic RAG compared with agentic RAG**
```
Classic:  Q ──► Retriever ──► top-k ──► LLM ──► A            (one straight pass)

Agentic:  Q ──► [Agent: think] ──► need info? ──no──► A
                     ▲                 │yes
                     │                 ▼
                [reflect/grade] ◄── tool call (vector | web | SQL | MCP)
                     │ bad → rewrite query / switch source / decompose
                     └ good → generate + cite → A
```

---

## 2. The survey: arXiv 2501.09136

- **Title:** *Agentic Retrieval-Augmented Generation: A Survey on Agentic RAG*
- **Authors:** Aditi Singh, Abul Ehtesham, Saket Kumar, Tala Talaei Khoei, Athanasios V. Vasilakos
- **Versions:** v1 2025-01-15; v2 2025-02-03; v3 2025-02-04; **v4 2026-04-01** (current). URL: https://arxiv.org/abs/2501.09136
- **Companion repo:** https://github.com/asinghcsu/AgenticRAG-Survey
- **v4 abstract:** the taxonomy is organized along four dimensions: **agent cardinality, control structure, autonomy, knowledge representation**. The survey also covers applications in healthcare, finance, education and enterprise document processing. It lists open challenges in evaluation, coordination, memory, efficiency and governance.

**Four agentic patterns** (from the repo):
1. **Reflection**: the agent critiques its own retrieval and output.
2. **Planning**: the agent decomposes the task into steps.
3. **Tool use**: retrievers, search engines, APIs and code.
4. **Multi-agent collaboration**: specialist agents that share work.

**Five workflow patterns** (the repo adopts these from Anthropic's "Building effective agents"):
Prompt Chaining, Routing, Parallelization, Orchestrator-Workers, Evaluator-Optimizer.

**Seven architecture families** (repo taxonomy):
1. Single-Agent RAG (Router-Based)
2. Multi-Agent RAG
3. Hierarchical Agentic RAG
4. Corrective Agentic RAG
5. Adaptive Agentic RAG
6. Graph-Based Agentic RAG (e.g., Agent-G, GeAR)
7. Agentic Document Workflows (ADW), a term LlamaIndex coined for end-to-end document processing such as invoice and contract review

---

## 3. Pattern catalogue (papers checked on arXiv)

| Pattern | Paper (exact title) | ID / venue | One-line mechanism | Key number |
|---|---|---|---|---|
| ReAct retrieval agent | *ReAct: Synergizing Reasoning and Acting in Language Models* (Yao et al.) | 2210.03629, ICLR 2023 | Interleaves Thought → Action (search[...]) → Observation | ReAct was the first widely used thought/action/observation loop over Wikipedia search |
| IRCoT | *Interleaving Retrieval with Chain-of-Thought Reasoning for Knowledge-Intensive Multi-Step Questions* (Trivedi, Balasubramanian, Khot, Sabharwal) | 2212.10509, ACL 2023 | Each new CoT sentence becomes the next retrieval query | Up to **+21 pts retrieval, +15 pts QA** with GPT-3 on HotpotQA, 2WikiMultihopQA, MuSiQue, IIRC |
| FLARE | *Active Retrieval Augmented Generation* (Jiang, Xu, Gao, Sun, Liu, Dwivedi-Yu, Yang, Callan, Neubig) | 2305.06983, EMNLP 2023 | Drafts the next sentence; if any token has low confidence, uses the draft as the query and regenerates | 4 long-form, knowledge-intensive tasks |
| Self-RAG | *Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection* (Asai, Wu, Wang, Sil, Hajishirzi) | 2310.11511, 2023-10-17 (ICLR 2024 oral [UNVERIFIED venue on the abs page]) | Trains one LM to emit **reflection tokens**: `Retrieve`, `ISREL`, `ISSUP`, `ISUSE` (token names come from the paper body) | 7B and 13B models beat ChatGPT and retrieval-augmented Llama2-chat on open-domain QA, reasoning and fact verification |
| CRAG | *Corrective Retrieval Augmented Generation* (Shi-Qi Yan, Jia-Chen Gu, Yun Zhu, Zhen-Hua Ling) | 2401.15884, v1 2024-01-29 | A T5-large **retrieval evaluator (~0.77B)** scores the documents and triggers one of three actions: **Correct** (refine with knowledge strips), **Incorrect** (discard and use web search through the Google Search API), **Ambiguous** (both). Uses *decompose-then-recompose* filtering | PopQA 52.8 → **59.8** (Self-RAG-LLaMA2-7B generator, RAG compared with CRAG); PubHealth 39.0 → **75.6** |
| Adaptive-RAG | *Adaptive-RAG: Learning to Adapt Retrieval-Augmented Large Language Models through Question Complexity* (Jeong, Baek, Cho, Hwang, Park) | 2403.14403, NAACL 2024 | A small LM classifier predicts query complexity and routes to **no retrieval / single-step / iterative (multi-step)** | Training labels are generated automatically from model outcomes |
| Plan-and-execute | LangChain/LangGraph "plan-and-execute" tutorial pattern (inspired by *Plan-and-Solve*, Wang et al., 2305.04091 [UNVERIFIED ID]) | — | A planner LLM writes a step list, an executor agent runs each step with tools, and a replanner revises the list | Cuts calls to the expensive model |
| Multi-agent RAG | Anthropic Research system (2025-06-13) | blog | Lead agent (Claude Opus 4) and parallel subagents (Sonnet 4), each with its own context window | **+90.2%** over single-agent Opus 4 on an internal research eval; agents use about **4×** the tokens of chat, multi-agent systems about **15×** |

Quotable line (Anthropic): *"Multi-agent systems work mainly because they help spend enough tokens to solve the problem."*

### Diagrams in words

**Router RAG (single-agent, router-based)**
```
Q ─► Router LLM (structured output: {"source": "vector"|"sql"|"web"|"none"})
      ├─ vector → Vector DB (product docs)
      ├─ sql    → Text-to-SQL over orders DB
      ├─ web    → Google Search / Tavily
      └─ none   → answer directly
   ─► Generator → A
```

**CRAG flow**
```
Q → retrieve k docs → T5 evaluator scores each
   max score > upper threshold   → CORRECT   → split into strips → filter → recompose → generate
   all scores < lower threshold  → INCORRECT → rewrite Q into keywords → web search → generate
   otherwise                     → AMBIGUOUS → refined internal + web → generate
```

**Self-RAG decoding**
```
segment t: model emits [Retrieve=yes?]
   yes → retrieve passages → for each passage generate continuation + [ISREL] + [ISSUP]
         → pick best by weighted critique score (+[ISUSE]) → next segment
   no  → continue generating
```

**Adaptive-RAG**
```
Q → classifier(T5-size) → A (simple)  → LLM only
                        → B (moderate) → single-step RAG
                        → C (complex)  → multi-step IRCoT-style loop
```

**IRCoT loop**
```
retrieve(Q) → CoT sentence 1 → retrieve(sentence 1) → CoT sentence 2 → retrieve(...) … → "answer is" → stop
```

---

## 4. Deep Research agents (productized agentic RAG)

| System | Launch | Mechanism | Facts |
|---|---|---|---|
| **OpenAI deep research** | 2025-02-02 (ChatGPT Pro first) | Agent built on o3, trained end-to-end with RL on browsing and reasoning tasks [mechanism wording UNVERIFIED; OpenAI page returned 403] | **26.6% on Humanity's Last Exam** (Fortune, 2025-02-12); new SOTA on GAIA. API models `o3-deep-research` and `o4-mini-deep-research` (Responses API). The API docs now say both are **scheduled for shutdown on 2026-07-23, replaced by `gpt-5.6-sol`** (check before quoting) |
| **Gemini Deep Research** | Gemini app Dec 2024; Interactions API public beta Dec 2025 | A planning step the user can edit (collaborative planning), then long-running background search and synthesis | Agent IDs: `deep-research-preview-04-2026`, `deep-research-max-preview-04-2026`; 1,048,576-token input, 65,536-token output; supports MCP servers and File Search. Docs: https://ai.google.dev/gemini-api/docs/interactions/deep-research |
| **LangChain open_deep_research** | 2025 | Supervisor plus parallel researcher sub-agents (legacy `multi_agent.py`); summarize → research → compress → final report | Deep Research Bench (100 PhD-level tasks, 22 fields), RACE score **0.4943 with GPT-5**, 0.4309 with defaults ($45.98). **Repo archived on 2026-08-21**; LangChain now points to **Deep Agents** (`deepagents`) [successor link inferred]. https://github.com/langchain-ai/open_deep_research |
| **GPT Researcher** (assafelovic) | 2023 onward | Planner → parallel crawler/execution agents → publisher, with source tracking | About 30.3k stars; MCP retriever (`RETRIEVER=tavily,mcp`), MCP server split out to `gptr-mcp`. https://github.com/assafelovic/gpt-researcher |

**Diagram in words: the canonical deep-research loop**
```
User Q → (clarify) → PLAN (research brief + sub-questions)
       → fan-out N researcher agents  ─┐  each: search → read → note → (repeat ≤ budget)
                                        ├─ COMPRESS findings (cite URLs)
       ← supervisor reflects: gaps? ───┘  yes → spawn more researchers
       → WRITE report with inline citations → (optional critic loop) → deliver
```

---

## 5. RL-trained search agents (the 2025–26 frontier)

The idea: drop the hand-written prompts and train the policy model with RL, often GRPO or PPO, so that it learns *when and how* to search. An outcome reward (exact match on the answer, plus a format check) is enough. Retrieved tokens are **masked out of the loss** so the model is not trained to imitate the documents.

| Paper (exact title) | arXiv / venue | Key facts |
|---|---|---|
| *Search-R1: Training LLMs to Reason and Leverage Search Engines with Reinforcement Learning* (Bowen Jin et al., UIUC/UMass/Google Cloud AI Research) | 2503.09516, COLM 2025 | **+24% (Qwen2.5-7B), +20% (Qwen2.5-3B)** over RAG baselines across 7 QA datasets; retrieved-token masking; outcome reward. Built on veRL; supports PPO/GRPO/REINFORCE. Rollout tags: `<think>`, `<search>`, `<information>`, `<answer>` (from the paper; not shown in the README). Repo: https://github.com/PeterGriffinJin/Search-R1 |
| *R1-Searcher: Incentivizing the Search Capability in LLMs via Reinforcement Learning* (Huatong Song, Jinhao Jiang, … Wayne Xin Zhao, Ji-Rong Wen) | 2503.05592 | **Two-stage** outcome-based RL: stage 1 rewards correct retrieval invocation and format, stage 2 rewards answer correctness. No SFT cold start |
| *ReSearch: Learning to Reason with Search for LLMs via Reinforcement Learning* (Mingyang Chen et al., Baichuan) | 2503.19470, NeurIPS 2025 | Search is part of the reasoning chain; Qwen2.5-7B/32B trained on one dataset generalize to others; reported 22–48% relative gain on multi-hop QA [figure from a secondary source, UNVERIFIED] |
| *DeepResearcher: Scaling Deep Research via Reinforcement Learning in Real-world Environments* (Yuxiang Zheng, … Pengfei Liu) | 2504.03160 | Trained against the **live open web**, not a fixed corpus: **+28.9 pts** over prompt-engineering baselines, **+7.2 pts** over RAG-based RL agents |

**Diagram in words: a Search-R1 rollout**
```
<think> need birthplace of X </think>
<search> X birthplace </search>
<information> …top-3 passages (MASKED from loss)… </information>
<think> found Y; now need Y's population </think>
<search> Y population 2020 </search>
<information> … </information>
<answer> 1.2 million </answer>   → reward = EM(answer, gold)  → GRPO update
```

---

## 6. MCP as the retrieval interface

- With MCP, retrieval becomes a standard tool server: any agent (ADK, LangGraph, Claude, ChatGPT, Gemini Deep Research) can call `search`/`fetch` on any corpus without per-framework glue code.
- OpenAI's deep-research API accepts an `mcp` tool only when the server implements **`search` and `fetch`** and `require_approval` is `"never"`. Retrieval as an interface is now a de facto contract.
- **Latest spec revision: `2026-07-28`** (prior: `2025-11-25`). Major changes (https://modelcontextprotocol.io/specification/latest/changelog):
  - **Stateless**: the `initialize` handshake is removed; each request carries its protocol version and capabilities in `_meta`; servers MUST implement `server/discover`.
  - Protocol sessions and the `Mcp-Session-Id` header are removed from Streamable HTTP.
  - `subscriptions/listen` replaces the GET stream and `resources/subscribe`.
  - Multi Round-Trip Requests (`InputRequiredResult`) replace server-initiated sampling and elicitation.
  - Roots, Sampling and Logging are **deprecated**; Tasks move to the extension `io.modelcontextprotocol/tasks`.
  - `tools/list` results carry `ttlMs`/`cacheScope` and should come in a deterministic order (better for prompt caching).
- RAG takeaway: an MCP retrieval server is now a cacheable, stateless HTTP service. Cross-call state, such as a search cursor, travels as explicit handles in tool arguments.

---

## 7. Code: LangGraph agentic RAG (retrieve → grade → rewrite loop)

Source: LangGraph docs, "Build a custom RAG agent", https://docs.langchain.com/oss/python/langgraph/agentic-rag (fetched 2026-10-23; this page version uses `@tool` and a custom router rather than `tools_condition`).

```python
from langchain.tools import tool
from langchain.chat_models import init_chat_model
from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field
from typing import Literal

@tool
def retrieve_blog_posts(query: str) -> str:
    """Search and return information about Lilian Weng blog posts."""
    docs = _get_retriever().invoke(query)
    return "\n\n".join(d.page_content for d in docs)

response_model = init_chat_model("openai:gpt-5.4-mini", temperature=0)

def generate_query_or_respond(state: MessagesState):
    return {"messages": [response_model.bind_tools([retrieve_blog_posts]).invoke(state["messages"])]}

class GradeDocuments(BaseModel):
    binary_score: str = Field(description="'yes' if relevant, 'no' if not")

def grade_documents(state: MessagesState) -> Literal["generate_answer", "rewrite_question"]:
    q, ctx = state["messages"][0].content, state["messages"][-1].content
    r = response_model.with_structured_output(GradeDocuments).invoke(
        [{"role": "user", "content": GRADE_PROMPT.format(question=q, context=ctx)}])
    return "generate_answer" if r.binary_score == "yes" else "rewrite_question"
```
```python
wf = StateGraph(MessagesState)
wf.add_node(generate_query_or_respond)
wf.add_node("retrieve", ToolNode([retrieve_blog_posts]))
wf.add_node(rewrite_question); wf.add_node(generate_answer)
wf.add_edge(START, "generate_query_or_respond")
wf.add_conditional_edges("generate_query_or_respond",
    lambda s: "tools" if getattr(s["messages"][-1], "tool_calls", None) else END,
    {"tools": "retrieve", END: END})
wf.add_conditional_edges("retrieve", grade_documents)   # CRAG-style gate
wf.add_edge("rewrite_question", "generate_query_or_respond")  # corrective loop
wf.add_edge("generate_answer", END)
graph = wf.compile()
```
Teaching point: the graph is **router, then Self-RAG/CRAG-lite**. The LLM chooses whether to retrieve, a grader checks relevance, and a failed grade leads to a query rewrite and another pass. In production, add a max-iterations counter to the state.

---

## 8. Code: Google ADK (Python, google-adk 2.x; latest release 2.12.0 on 2026-10-13 per release trackers)

### 8a. RAG tool on a Vertex AI RAG Engine corpus
Source: https://adk.dev/integrations/knowledge-engine/ (the page now calls the product "Knowledge Engine" while the import path still says `vertex_ai_rag_retrieval`)
```python
import os
from google.adk.agents import Agent
from google.adk.tools.retrieval.vertex_ai_rag_retrieval import VertexAiRagRetrieval
from vertexai.preview import rag

ask_vertex_retrieval = VertexAiRagRetrieval(
    name="retrieve_rag_documentation",
    description="Use this tool to retrieve documentation and reference materials for the question from the RAG corpus,",
    rag_resources=[rag.RagResource(rag_corpus=os.environ.get("RAG_CORPUS"))],  # projects/…/ragCorpora/…
    similarity_top_k=10,
    vector_distance_threshold=0.6,
)

root_agent = Agent(
    model="gemini-flash-latest",
    name="ask_rag_agent",
    instruction="Use the retrieve_rag_documentation tool to fetch relevant docs, then answer based on them.",
    tools=[ask_vertex_retrieval],
)
```
Caveat from the docs: `vertex_ai_rag_retrieval` and `google_search` can each be used only **by itself** within an agent instance. To use both, wrap each one in its own sub-agent and expose it with `AgentTool` (`from google.adk.tools.agent_tool import AgentTool`). This gives a multi-source router.

### 8b. Web-search agent (`google_search`)
Source: https://adk.dev/integrations/google-search/
```python
from google.adk.agents import Agent
from google.adk.tools import google_search

web_agent = Agent(name="basic_search_agent", model="gemini-2.0-flash",
                  instruction="Answer by searching the internet.", tools=[google_search])
```
(The docs require that Search suggestions, returned as `renderedContent`, be displayed in production.)

### 8c. Corrective / reflective loop with `LoopAgent`
Source: https://adk.dev/agents/workflow-agents/loop-agents/ (adapted: critic → refiner becomes grader → re-searcher)
```python
from google.adk.agents import LoopAgent, LlmAgent, SequentialAgent
from google.adk.tools.tool_context import ToolContext

def exit_loop(tool_context: ToolContext):
    """Call only when the evidence is sufficient."""
    tool_context.actions.escalate = True   # stops the LoopAgent
    return {}

grader = LlmAgent(name="Grader", model="gemini-2.5-flash", include_contents="none",
    instruction="Judge if {evidence} fully answers {question}. Reply 'SUFFICIENT' or list gaps.",
    output_key="critique")
researcher = LlmAgent(name="Researcher", model="gemini-2.5-flash",
    instruction="If {critique} is 'SUFFICIENT' call exit_loop; else search to fill the gaps.",
    tools=[exit_loop], output_key="evidence")   # add an AgentTool(web_agent) here
loop = LoopAgent(name="CorrectiveLoop", sub_agents=[grader, researcher], max_iterations=4)
pipeline = SequentialAgent(name="AgenticRAG", sub_agents=[initial_retriever, loop, writer])
```

### 8d. MCP retrieval server in ADK
Source: https://adk.dev/tools-custom/mcp-tools/
```python
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams

kb = McpToolset(
    connection_params=StreamableHTTPConnectionParams(url="https://kb.example.com/mcp", timeout=5),
    tool_filter=["search", "fetch"],          # expose only the retrieval surface
)
root_agent = LlmAgent(model="gemini-flash-latest", name="kb_agent",
                      instruction="Search the knowledge base, cite fetched docs.", tools=[kb])
```
Notes: `StdioConnectionParams` + `mcp.StdioServerParameters` cover local servers. The release notes say ADK 2.9.0 added MCP SDK 2.x compatibility and 2.5.0 added serving an ADK agent *as* an MCP server [both from a release aggregator; confirm on GitHub releases]. The old `google/adk-samples` RAG path (`python/agents/RAG/rag/agent.py`) now returns 404; the samples appear to have moved into `google/adk-recipes` (`core/` "RAG patterns") [UNVERIFIED exact path].

---

## 9. Code: hosted deep-research APIs

**Gemini Deep Research via the Interactions API** (source: https://ai.google.dev/gemini-api/docs/interactions/deep-research)
```python
import time
from google import genai
client = genai.Client()
interaction = client.interactions.create(
    input="Research the history of Google TPUs.",
    agent="deep-research-preview-04-2026",
    background=True,
)
while True:
    interaction = client.interactions.get(interaction.id)
    if interaction.status == "completed":
        print(interaction.steps[-1].content[0].text); break
    elif interaction.status == "failed":
        print(interaction.error); break
    time.sleep(10)
```

**OpenAI deep research via the Responses API** (source: https://developers.openai.com/api/docs/guides/deep-research)
```python
from openai import OpenAI
client = OpenAI(timeout=3600)
response = client.responses.create(
    model="o3-deep-research",               # docs: shutdown 2026-07-23 → gpt-5.6-sol
    input="Research the economic impact of semaglutide... include inline citations.",
    background=True,
    tools=[{"type": "web_search_preview"},
           {"type": "file_search", "vector_store_ids": ["<vs_id>"]},   # max 2 stores
           {"type": "code_interpreter", "container": {"type": "auto"}}],
)
print(response.output_text)
```

**GPT Researcher** (source: README)
```python
from gpt_researcher import GPTResearcher
researcher = GPTResearcher(query="why is Nvidia stock going up?")
await researcher.conduct_research()
report = await researcher.write_report()
```

**open_deep_research quick start** (archived repo, still runnable):
`uvx --refresh --from "langgraph-cli[inmem]" --with-editable . --python 3.11 langgraph dev --allow-blocking`, which serves on http://127.0.0.1:2024.

---

## 10. Real-world examples

- **Perplexity, ChatGPT search/deep research, Gemini Deep Research, Claude Research**: consumer agentic RAG over the open web, with citations.
- **Enterprise:** Vertex AI / Gemini Enterprise with RAG Engine ("Knowledge Engine") corpora behind ADK agents; OpenAI deep research over `file_search` vector stores plus an internal MCP server exposing `search`/`fetch`.
- **Document workflows (ADW):** invoice, contract and claims processing that pulls in rules and compares the document against them (LlamaIndex Agentic Document Workflows; healthcare, finance and legal examples from the survey).
- **Open-source research agents:** GPT Researcher (30k+ stars), LangChain open_deep_research (now archived, successor Deep Agents), and Search-R1, which is integrated into veRL, SkyRL and Thinking Machines' Tinker (README news, 2025).

## 11. Trade-offs to teach

- **Cost and latency:** agents use about 4× the tokens of chat and multi-agent systems about 15× (Anthropic). Deep Research Bench runs cost $20–$100 for 100 tasks (open_deep_research README).
- **Choose the simplest pattern that works:** use Adaptive-RAG-style routing to skip retrieval for easy questions.
- **Failure modes:** endless loops (cap them with `max_iterations`), query drift after rewriting, a grader that hallucinates "relevant", context bloat (fix with compression sub-agents), and prompt injection from retrieved web pages and MCP tools.
- **Evaluation:** HotpotQA, 2Wiki, MuSiQue (multi-hop); PopQA (long-tail); HLE and GAIA (agents); Deep Research Bench / RACE (long reports); BrowseComp [mentioned, not checked here].

---

## 12. Slide ideas (8)

1. **"From pipeline to policy"**: a straight classic-RAG arrow animates into a loop with decision diamonds (retrieve? which source? good enough?).
2. **Agentic RAG taxonomy (arXiv 2501.09136)**: radial map with 4 patterns in the inner ring, 5 workflow patterns in the middle ring and 7 architectures in the outer ring; the four v4 dimensions (cardinality, control, autonomy, knowledge representation) form the axes.
3. **Router RAG**: one question token flies to a router node and lights up one of four source icons (vector, SQL, web, none). A second click shows the Adaptive-RAG A/B/C complexity classifier.
4. **Self-RAG compared with CRAG**: split screen. Left shows reflection tokens popping up inline (`[Retrieve]`, `[ISREL]`, `[ISSUP]`). Right shows a traffic light (Correct/Ambiguous/Incorrect) that routes to refine, both, or web search. A bar chart puts PopQA 52.8 next to 59.8.
5. **IRCoT and FLARE timeline**: a sentence-by-sentence animation. Each CoT sentence (IRCoT) or low-confidence draft token highlighted in red (FLARE) fires a retrieval.
6. **LangGraph live graph**: render `graph.get_graph().draw_mermaid()`, then animate a token through generate → retrieve → grade → rewrite → generate, with the code on the right.
7. **ADK composition**: a nesting-box diagram, SequentialAgent[ initial retriever → LoopAgent[ Grader ↔ Researcher(AgentTool(google_search), VertexAiRagRetrieval) ] → Writer ], with the escalate arrow breaking out of the loop.
8. **Deep Research anatomy**: plan → fan-out of N researcher lanes (swimlanes) → compress → report. Overlay stats: 26.6% HLE (OpenAI, Feb 2025), +90.2% multi-agent and 15× tokens (Anthropic).
9. **RL-trained searchers**: an animated Search-R1 rollout with `<think>/<search>/<information>/<answer>`. The `<information>` span is greyed out ("masked from loss"). A leaderboard strip shows Search-R1 +24%/+20%, DeepResearcher +28.9/+7.2.
10. **MCP as the universal retrieval port**: a USB-C hub metaphor. ADK, LangGraph, ChatGPT and Gemini plug into `search`/`fetch` servers. Callout for the 2026-07-28 spec: stateless, `server/discover`, cacheable `tools/list`.

## 13. Source list (exact titles and URLs)

- Agentic Retrieval-Augmented Generation: A Survey on Agentic RAG — https://arxiv.org/abs/2501.09136 ; repo https://github.com/asinghcsu/AgenticRAG-Survey
- ReAct — https://arxiv.org/abs/2210.03629
- Interleaving Retrieval with Chain-of-Thought Reasoning… (IRCoT) — https://arxiv.org/abs/2212.10509
- Active Retrieval Augmented Generation (FLARE) — https://arxiv.org/abs/2305.06983
- Self-RAG — https://arxiv.org/abs/2310.11511
- Corrective Retrieval Augmented Generation — https://arxiv.org/abs/2401.15884
- Adaptive-RAG — https://arxiv.org/abs/2403.14403
- Search-R1 — https://arxiv.org/abs/2503.09516 ; https://github.com/PeterGriffinJin/Search-R1
- R1-Searcher — https://arxiv.org/abs/2503.05592
- ReSearch — https://arxiv.org/abs/2503.19470
- DeepResearcher — https://arxiv.org/abs/2504.03160
- How we built our multi-agent research system (Anthropic, 2025-06-13) — https://www.anthropic.com/engineering/multi-agent-research-system
- LangGraph "Build a custom RAG agent" — https://docs.langchain.com/oss/python/langgraph/agentic-rag
- ADK Knowledge Engine (VertexAiRagRetrieval) — https://adk.dev/integrations/knowledge-engine/
- ADK Google Search — https://adk.dev/integrations/google-search/
- ADK Loop agents — https://adk.dev/agents/workflow-agents/loop-agents/
- ADK MCP tools — https://adk.dev/tools-custom/mcp-tools/
- ADK releases — https://github.com/google/adk-python/releases
- Gemini Deep Research agent — https://ai.google.dev/gemini-api/docs/interactions/deep-research
- OpenAI deep research API guide — https://developers.openai.com/api/docs/guides/deep-research
- OpenAI Introducing deep research — https://openai.com/index/introducing-deep-research/ (403 when fetched; HLE figure via https://fortune.com/2025/02/12/openai-deepresearch-humanity-last-exam/)
- open_deep_research — https://github.com/langchain-ai/open_deep_research
- GPT Researcher — https://github.com/assafelovic/gpt-researcher
- MCP spec changelog (2026-07-28) — https://modelcontextprotocol.io/specification/latest/changelog
