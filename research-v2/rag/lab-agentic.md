# Hands-on labs: Agentic RAG (router + retriever + verifier, CRAG loops, multi-hop, LightRAG, citations)

Research date: 2026-10-23. Scope: 8 complete code labs for the "agentic RAG" chapter of the 100-slide RAG deck.
This file builds on `research-rag/03-agentic-rag.md`, `04-graph-structured.md` and `09-critic-corrections.md`. It does not repeat them. The old deck had theory only. Every lab here is concrete code with a named business scenario.

**Honesty note.** PyPI downloads are blocked on this machine, so I did **not run** any lab. I checked every import path, class name, parameter and error string against the library **source at the released tag** on GitHub (file and line are cited). All "Expected output" blocks are **illustrative**: they show the shape of the output, not a captured run. Anything I could not check in source or docs is marked **[UNVERIFIED]**.

---

## 0. Version table (PyPI JSON, fetched 2026-10-23)

| Package | Latest | Upload time (UTC) | Python | Used in |
|---|---|---|---|---|
| google-adk | **2.13.0** | 2026-10-23 18:26 | >=3.11 | Labs 1-3 |
| google-genai | **2.33.0** | 2026-10-23 00:06 | >=3.10 | Lab 8 (also pulled in by ADK) |
| langgraph | **1.2.17** | 2026-10-24 01:07 (it was already 10-24 in UTC) | >=3.10 | Labs 4-6 |
| langchain-core | **1.7.0** | 2026-10-22 | >=3.10 | Labs 4-6 |
| langchain | 1.4.7 | 2026-10-21 | >=3.10 | (not needed) |
| langchain-google-genai | **4.4.2** | 2026-10-13 | >=3.10 | Labs 4-6 |
| lightrag-hku | **1.5.7** | 2026-09-02 | >=3.10 | Lab 7 |

Note: langgraph 1.2.16 is in `09-critic-corrections.md`, but 1.2.17 came out a few hours later. Pin `langgraph==1.2.17`.

### Models (Gemini API "Models" page, https://ai.google.dev/gemini-api/docs/models, fetched 2026-10-23)
- Stable text models: `gemini-3.8-flash`, `gemini-3.6-flash`, `gemini-3.5-flash-lite`, `gemini-3.1-flash-lite`, `gemini-4-argon`. Preview: `gemini-3-flash-preview`, `gemini-3.1-pro-preview`. The page says "For any new projects, use our latest models: 3.5 Flash-Lite or 3.8 Flash."
- **Shut down:** `gemini-2.0-flash`, `gemini-2.0-flash-lite`, `gemini-3-pro-preview`, `gemini-3.1-flash-lite-preview`. **Legacy** (past users only): `gemini-2.5-flash`, `gemini-2.5-pro`.
- Embeddings: `gemini-embedding-001`, `gemini-embedding-2-preview`.
- **Gotcha:** ADK 2.13.0 sets `LlmAgent.DEFAULT_MODEL = 'gemini-3.5-flash'` (`src/google/adk/agents/llm_agent.py` L289). That ID is **not on the models page**. The page lists only `gemini-3.5-flash-lite` [UNVERIFIED whether `gemini-3.5-flash` is still served]. So **every lab sets the model explicitly**, from `MODEL` (default `gemini-3.8-flash`).
- **Gotcha (slide-worthy):** many official samples are now out of date. The LightRAG Gemini demo (`examples/lightrag_gemini_demo.py` @ v1.5.7) uses `gemini-2.0-flash` (shut down) and `models/text-embedding-004`. The ADK google_search doc sample uses `gemini-2.0-flash` (see 09-critic C16). Copy-paste from these samples fails today.

### Common env vars
```bash
# Gemini Developer API (AI Studio key)
export GOOGLE_API_KEY="AIza..."          # ADK, google-genai, langchain-google-genai read this first
export GEMINI_API_KEY="$GOOGLE_API_KEY"  # LightRAG's Gemini binding reads GEMINI_API_KEY / LLM_BINDING_API_KEY, NOT GOOGLE_API_KEY
export GOOGLE_GENAI_USE_VERTEXAI=FALSE
export MODEL=gemini-3.8-flash
```
Sources: google-genai `_api_client.py` L162-172 ("prioritizing GOOGLE_API_KEY"; it warns "Both GOOGLE_API_KEY and GEMINI_API_KEY are set. Using GOOGLE_API_KEY."). LightRAG `lightrag/llm/gemini.py` L136-150 `_ensure_api_key`. langchain-google-genai `_common.py` L170-176 (GOOGLE_API_KEY takes precedence over GEMINI_API_KEY).

---

## 1. What changed in 2026 that the labs depend on (verified in source)

1. **ADK 2.x has a graph engine: `Workflow`.** `from google.adk import Agent, Event, Workflow` (`src/google/adk/__init__.py` exports exactly `Agent, Context, Event, Runner, Workflow`). You declare edges as tuples: `("START", a, b, c)` is a chain, and `(node, {"route_name": target})` is a conditional edge. A node picks its route with `yield Event(route="...")`. Event convenience kwargs: `message`→content, `state`→`actions.state_delta`, `route`→`actions.route` (`events/event.py` L166-235). Samples: `contributing/samples/workflows/route/agent.py`, `workflows/loop/agent.py`, `workflows/agent_in_workflow/agent.py`, `workflows/classifier_node/agent.py` @ v2.13.0.
2. **Plain Python functions are nodes.** Their parameters are bound **from session state by name**. Two names are special: `node_input` (the output of the previous node) and `ctx`. If a parameter is missing from state and has no default, you get `WorkflowDataError` (`workflow/_function_node.py` L468-557).
3. **An LlmAgent used as a workflow node defaults to `mode="single_turn"` with `include_contents='none'`.** It sees only its input, not the chat history (`docs/guides/agents/llm_agent/single_turn.md`). Its `output_schema` result is validated and stored as a **dict** under `output_key` (`workflow/_llm_agent_wrapper.py` L384-415, `utils/_schema_utils.py` L235-247).
4. **`AgentTool` is now "discouraged".** The AgentTool docstring says to prefer `mode='single_turn'` on the sub-agent plus `sub_agents=[...]` (`tools/agent_tool.py` L115-133). There is a dedicated **`GoogleSearchAgentTool`** workaround for mixing `google_search` with other tools. It sets `propagate_grounding_metadata=True` (`tools/google_search_agent_tool.py`).
5. **The RAG Engine SDK import moved.** The ADK RAG sample now uses `from agentplatform.preview import rag` (package `google-cloud-agentplatform`) and no longer `vertexai.preview` (`contributing/samples/integrations/rag_agent/agent.py` @ v2.13.0). This matches the rename map in 09-critic (Vertex AI → Gemini Enterprise Agent Platform).
6. **The Gemini File Search docs now use the Interactions API** (`client.interactions.create`). Citations come back as `annotations` of type `file_citation`, and `start_index` is **measured in bytes** (`google/genai/_gaos/types/interactions/filecitation.py` @ v2.33.0).
7. **LangGraph's default recursion limit is now 10007, not 25** (`langgraph/_internal/_config.py` L42-44 @ 1.2.17: `getenv("LANGGRAPH_DEFAULT_RECURSION_LIMIT", "10007")`). An unbounded CRAG rewrite loop can now spend thousands of LLM calls before it fails. Set `recursion_limit` yourself, and keep a counter in state.
8. **`init_chat_model("gemini-...")` without a prefix infers `google_vertexai`.** langchain's `chat_models/base.py` L586-589 warns: "Inferred `model_provider='google_vertexai'` from ... This default will change to 'google_genai' in the next major release." Use the `google_genai:` prefix, or use `ChatGoogleGenerativeAI` directly (as the labs do).

---

## 2. arXiv insights from the last 3 months (2026-07-23 .. 2026-10-23) and which lab uses them

All papers were found with the arXiv API (`sortBy=submittedDate`) and the abstracts were read. The numbers below are quoted from the abstracts.

| arXiv id (date) | Title | Practical takeaway | Lab |
|---|---|---|---|
| 2610.21184 (10-15) | *Beyond Retrieval Failure: Understanding Why LLMs Miss Evidence in Multi-Hop RAG* | They name the failure **search drift**. A training-free **requirement register** of open sub-questions cut wrong answers with unretrieved evidence from 382→234 (MiniLM) on 1,000 MuSiQue questions. But "premature resolutions and abstentions increase". The bottleneck **moves to verifying sufficiency**. | 6 |
| 2607.24010 (07-27) | *When Should Active RAG Retrieve? A Budget-Aware Evaluation* | "Retrieval harm is non-negligible". Router rankings change across datasets. "Simple uncertainty or retrieval-score baselines often rival learned utility routers." Report realized usage and harm rate, not only accuracy. | 1, 4 |
| 2609.16453 (09-15) | *Predicting Partial Answer Quality and Utility in Agentic RAG* | Answer quality "often plateaus before natural termination". Early stopping cut iterations by about 11% and kept about 98% of the quality. This supports a hard `MAX_ATTEMPTS`. | 2, 5 |
| 2608.20627 (08-20) | *When Failures Propagate: Causal Failure Attribution in Agentic RAG* | A hop-1 retrieval error shows up as a wrong answer at hop 3. Coverage-based diagnosis found hop-1 faults (0.91) but **0.00** at hops 2-3. So log the **per-hop** evidence (Lab 6 keeps a register). | 6 |
| 2610.26951 (10-18) | *The Bottleneck Is Retrieval, Not Reading* | Similarity retrieval finds *any* relevant chunk much more reliably than *all* required chunks. Chunking loses document meta-information. Line-level citations show grounding failures that answer-only evaluation misses. | 4, 6, 8 |
| 2609.15660 (09-14) | *CiteShade: Citation Laundering in Multi-Source RAG* | One attacker-controlled source raised wrong answers 0.01→0.68 **and** made the model cite a trusted source that does not support the claim. "Perplexity filtering and citation-support checking are each insufficient". Their fix is a counterfactual check of which source drove the answer. | 4 (extension) |
| 2609.14245 (09-13) | *The Attribution-Compression Frontier in RAG* | After RECOMP-style compression, citations scored 0.86 precision against the summaries but **0.12 against the source spans**. Do not compress context before citing. Cite the raw chunk ids. | 4, 8 |
| 2610.14428 (10-10) | *Frustratingly Easy Agentic RAG via Portable Skills: Customer Support* | One NL instruction, a retrieval API, format-check scripts and an LLM-written "Wikipedia-style" navigation index gave 99.2% procedural equivalence and 83.3% evidence sufficiency. It took 1-2 engineer days, but it is **about 10x slower** (~90 s vs ~8-9 s). | 3 (discussion) |
| 2610.22652 (10-15) | *Evidence-Gated Bilingual RAG for Consumer Banking Search* | A three-outcome gate (**Answer / Related Mismatch / No Answer**) plus hybrid retrieval and a cross-encoder raised Top-1 from 50.48%→79.05%. The authors call it preliminary (n=210 queries). | 2 (3-way grade) |
| 2609.11646 (09-10) | *Your Retriever Already Knows: Distribution-Shape QPP for RAG Retrieval Sufficiency* | Score-distribution features predict retrieval sufficiency at AUROC 0.856 in **2 ms**. A local LLM judge got 0.649. A cheap pre-gate can come before the LLM grader. | 2 (variation) |
| 2609.18099 (09-16) | *When Is Graph Structure Worth Its Cost? (EffiRAG)* | EffiRAG beat LightRAG-hybrid on 93/120 UltraDomain questions at 57% lower total cost. It uses the graph to *locate* passages and answers from the original text. | 7 |
| 2609.10239 (09-09) | *LiteRAG: Cost-Efficient Graph-Based RAG* | Over 100x lower latency and over 99% lower cost than GraphRAG Global/DRIFT. Matches LinearRAG at about 14x fewer tokens. | 7 |
| 2610.05034 (10-04) | *Agentic RAG Evaluation: Budget Allocation* | Temperature 0 cut answer disagreement from 14.3%→3.4%. More *questions* beat more trajectories per token budget. | eval tips |
| 2610.30435 (10-21) | *SARL: Self-Assessment RL for Search-State Awareness* | Agents "lack search-state awareness", which causes hallucinated reasoning and stopping too early. SARL trains that awareness in with RL (+24.3% relative). The register in Lab 6 is the prompt-level version of this idea. | 6 |

---

## Lab 1 — ADK 2.x `Workflow`: router + retriever + verifier (HR policy helpdesk)

> **VERIFIED against google-adk 2.13.0 wheel source (verifier pass, 2026-10-23).** Imports, class/function names and parameters re-checked in the released package; code still not executed.

**Goal.** Northwind's HR helpdesk bot sends each employee message to one of three branches: HR policy, IT support or out-of-scope. HR questions run *retrieve → answer → verify*. The bot shows an answer only if a separate verifier agent confirms that every claim is in the retrieved policy text. Otherwise it opens an HR ticket.

**Adapted from:** ADK sample "ADK Workflow Routing Sample" (`contributing/samples/workflows/route/`, https://github.com/google/adk-python/tree/v2.13.0/contributing/samples/workflows/route) and `workflows/agent_in_workflow/agent.py` (route-on-check pattern).

**Prerequisites**
```bash
python -m venv .venv && source .venv/bin/activate      # Python >= 3.11 (google-adk requires it)
pip install "google-adk==2.13.0"
export GOOGLE_API_KEY=... GOOGLE_GENAI_USE_VERTEXAI=FALSE MODEL=gemini-3.8-flash
```

**Code — `lab1_hr_router.py`**
```python
import asyncio, os, re
from typing import Literal
from pydantic import BaseModel, Field
from google.adk import Agent, Event, Workflow
from google.adk.runners import InMemoryRunner

MODEL = os.getenv("MODEL", "gemini-3.8-flash")
HR_DOCS = {
    "PTO-2026": "Full-time staff accrue 1.75 PTO days per month. At most 5 unused PTO days carry over into the next year.",
    "PARENTAL-2026": "Birth and adoptive parents get 16 weeks of paid leave after 90 days of employment.",
    "REMOTE-2026": "Staff may work remotely up to 3 days per week with manager approval. Working abroad over 30 days needs HR approval.",
}

class Route(BaseModel):
    category: Literal["hr_policy", "it_support", "out_of_scope"]

class Verdict(BaseModel):
    supported: bool = Field(description="True only if EVERY claim in the draft is stated in the evidence")
    unsupported_claims: list[str] = Field(description="Claims of the draft not found in the evidence")

def take_question(node_input: str):
    return Event(state={"question": node_input})

router = Agent(name="router", model=MODEL, output_schema=Route, output_key="route",
               instruction="Classify this employee message: {question}")

def route_on_category(node_input: Route):
    yield Event(route=node_input.category)

def retrieve_hr(question: str, k: int = 2):
    words = set(re.findall(r"[a-z]+", question.lower()))
    ranked = sorted(HR_DOCS.items(), key=lambda kv: -len(words & set(re.findall(r"[a-z]+", kv[1].lower()))))
    return Event(state={"evidence": "\n".join(f"[{d}] {t}" for d, t in ranked[:k])})

answerer = Agent(name="answerer", model=MODEL, output_key="draft",
                 instruction="Answer: {question}\nUse ONLY this evidence and cite ids like [PTO-2026]:\n{evidence}")
verifier = Agent(name="verifier", model=MODEL, output_schema=Verdict, output_key="verdict",
                 instruction="Evidence:\n{evidence}\n\nDraft:\n{draft}\n\nCheck each claim of the draft against the evidence.")

def gate(node_input: Verdict, draft: str):
    if node_input.supported:
        yield Event(message=f"VERIFIED: {draft}")
    else:
        yield Event(message=f"Opened HR ticket; could not verify: {node_input.unsupported_claims}")

it_agent = Agent(name="it_agent", model=MODEL, instruction="Give a 2-line IT first-aid tip for: {question}")

def refuse():
    yield Event(message="I can only help with HR policy and IT questions.")

root_agent = Workflow(name="hr_helpdesk", edges=[
    ("START", take_question, router, route_on_category),
    (route_on_category, {"hr_policy": retrieve_hr, "it_support": it_agent, "out_of_scope": refuse}),
    (retrieve_hr, answerer, verifier, gate),
])

async def main():
    runner = InMemoryRunner(node=root_agent)
    for i, q in enumerate(["How many PTO days can I carry over into 2027?", "Can you book me a pizza?"]):
        await runner.run_debug(q, session_id=f"s{i}")

if __name__ == "__main__":
    asyncio.run(main())
```

**Run**
```bash
python lab1_hr_router.py
# or the dev UI: put the file in hr_helpdesk/agent.py with an __init__.py containing "from . import agent", then: adk web
```

**Expected output (illustrative, not captured)**
```
User > How many PTO days can I carry over into 2027?
[router]: {"category": "hr_policy"}
[answerer]: You can carry over at most 5 unused PTO days into the next year [PTO-2026].
[verifier]: {"supported": true, "unsupported_claims": []}
[gate]: VERIFIED: You can carry over at most 5 unused PTO days into the next year [PTO-2026].
User > Can you book me a pizza?
[router]: {"category": "out_of_scope"}
[refuse]: I can only help with HR policy and IT questions.
```
(The exact print format comes from `print_event` in `run_debug`, `runners.py` L1852-1950.)

**Walk-through of the key lines**
- `Workflow(name=..., edges=[...])`: `("START", a, b, c)` is a chain. `(route_on_category, {...})` is a conditional edge map. The graph is built and validated in `model_post_init` (`workflow/_workflow.py` L144-195).
- `router = Agent(..., output_schema=Route, output_key="route")`: as a workflow node the agent is `single_turn` with no history. Its JSON is validated against `Route`, saved as a dict in `state["route"]`, and passed as `node_input` to the next node.
- `def route_on_category(node_input: Route)`: FunctionNode turns the dict back into `Route` through the type hint (`_coerce_param` uses a Pydantic `TypeAdapter`, `_function_node.py` L625-640). `Event(route=...)` picks the outgoing edge.
- `def retrieve_hr(question: str, k: int = 2)`: `question` comes **from state** by name, and `k` falls back to its default. Returning `Event(state={...})` writes `evidence` into state for the next agent's `{evidence}` placeholder.
- `def gate(node_input: Verdict, draft: str)`: this is the verifier gate. The answer reaches the user only if the separate verifier agent approves it. Pattern from the `agent_in_workflow` sample's `check_identity`.
- `InMemoryRunner(node=root_agent)`: a `Workflow` is a `BaseNode`, not a `BaseAgent`, so pass it as `node=` (`runners.py` L2390-2400; `agent=` and `node=` are mutually exclusive).

**Common errors**
1. `KeyError: Context variable not found: \`evidence\` in agent 'answerer'.` (`flows/llm_flows/prompt/_instructions_utils.py` L195-197). The cause is a route that reaches an agent before the state key exists. Fix: write the key earlier, or make it optional with `{evidence?}` (the `?` syntax is in the `workflows/loop` sample: `{feedback?}`).
2. `WorkflowDataError: Missing value for parameter "draft" of function "gate". It was not found in state and has no default value.` (`_function_node.py` L550-556). The cause is that the answerer has no `output_key="draft"`, or the name is misspelled. Fix: make the `output_key` match the parameter name, or add a default.
3. `GraphValidationError: Graph validation failed. Duplicate node names found: ['answerer'] ...` (`workflow/utils/_graph_validation.py` L66-80). The cause is two different `Agent(name="answerer")` objects. Fix: reuse the same instance, or give them unique names.
4. `TypeError: Runner root 'hr_helpdesk' is a node, not an agent.` (`runners.py` L345-350) comes from agent-only code paths (for example `runner.agent.sub_agents`). Fix: treat `runner.agent` as a node, or wrap the workflow in an `App`.

**Best practice.** Use a **different agent (and ideally a different model or temperature) for verification than for generation**. Pass it only `{evidence}` + `{draft}`, not the conversation. ADK's node default of `include_contents='none'` gives you this isolation for free. Following arXiv 2607.24010, log how often the router picks each branch (the "realized usage"). Router quality changes with traffic mix.

**Variation / extension.** Replace the LLM router with the experimental `ClassifierNode` (`from google.adk.labs.classifiers import ClassifierNode, Choice, Binary, LlmClassifier`). It is used in `workflows/classifier_node/agent.py` and supports `threshold=0.7` on a `Binary` question, for example "is this urgent?". For production retrieval, swap `retrieve_hr` for `VertexAiRagRetrieval` (`google.adk.tools.retrieval.vertex_ai_rag_retrieval`) on a RAG Engine corpus, as in `integrations/rag_agent/agent.py`.

---

## Lab 2 — ADK `Workflow`: CRAG-style self-correcting retrieval (insurance claims)

> **VERIFIED against google-adk 2.13.0 wheel source (verifier pass, 2026-10-23).** Imports, class/function names and parameters re-checked in the released package; code still not executed.

**Goal.** Harbor Mutual's claims assistant grades its own retrieval before it answers, in the style of CRAG (Corrective RAG, arXiv 2401.15884): `correct` → answer, `ambiguous/incorrect` → rewrite the query and retrieve again. After `MAX_ATTEMPTS` it abstains and hands the case to a human adjuster. This pattern does not use `LoopAgent`/`escalate`. The loop is a **routed back-edge** in the graph.

**Adapted from:** `contributing/samples/workflows/loop/agent.py` (generate → evaluate → route back) @ v2.13.0. The 3-way grade follows arXiv 2610.22652 (Answer / Related-Mismatch / No-Answer). The attempt cap follows arXiv 2609.16453 (quality plateaus early).

**Prerequisites:** same as Lab 1 (`pip install "google-adk==2.13.0"`, `GOOGLE_API_KEY`).

**Code — `lab2_claims_crag.py`**
```python
import asyncio, os, re
from typing import Literal
from pydantic import BaseModel, Field
from google.adk import Agent, Event, Workflow
from google.adk.runners import InMemoryRunner

MODEL = os.getenv("MODEL", "gemini-3.8-flash")
MAX_ATTEMPTS = 3
CLAIMS_KB = {
    "AUTO-7.2": "Windshield chip repair is covered at 100 percent with no deductible under comprehensive coverage.",
    "AUTO-7.3": "Full windshield replacement is subject to the comprehensive deductible.",
    "HOME-4.1": "Water damage from a sudden burst pipe is covered; gradual leaks lasting over 14 days are excluded.",
    "HOME-4.5": "Mold remediation is capped at USD 5,000 per claim.",
}

class Grade(BaseModel):
    label: Literal["correct", "ambiguous", "incorrect"] = Field(
        description="correct: evidence fully answers; ambiguous: partly; incorrect: irrelevant")
    missing: str = Field(description="What the evidence is missing, or ''")

def start(node_input: str):
    return Event(state={"question": node_input, "query": node_input, "attempts": 0})

def retrieve(query: str, attempts: int):
    q = set(re.findall(r"[a-z]+", query.lower()))
    scored = sorted(((len(q & set(re.findall(r"[a-z]+", t.lower()))), d, t) for d, t in CLAIMS_KB.items()), reverse=True)
    hits = [f"[{d}] {t}" for s, d, t in scored[:2] if s >= 2]
    return Event(state={"evidence": "\n".join(hits) or "(no results)", "attempts": attempts + 1})

grader = Agent(name="grader", model=MODEL, output_schema=Grade, output_key="grade",
               instruction="Question: {question}\nRetrieved evidence:\n{evidence}\nGrade the evidence.")

def decide(node_input: Grade, attempts: int):
    if node_input.label == "correct":
        yield Event(route="answer")
    elif attempts >= MAX_ATTEMPTS:
        yield Event(route="abstain")
    else:
        yield Event(route="rewrite")

rewriter = Agent(name="rewriter", model=MODEL, output_key="query",
                 instruction="Query '{query}' failed; missing: {grade}. Write ONE better keyword query "
                             "for an insurance policy manual for: {question}. Output only the query.")
answerer = Agent(name="answerer", model=MODEL,
                 instruction="Answer {question} from this evidence only; cite clause ids in brackets:\n{evidence}")

def abstain(question: str, attempts: int):
    yield Event(message=f"Escalated to a human adjuster after {attempts} searches: '{question}'.")

root_agent = Workflow(name="claims_crag", edges=[
    ("START", start, retrieve, grader, decide),
    (decide, {"answer": answerer, "rewrite": rewriter, "abstain": abstain}),
    (rewriter, retrieve),                      # the corrective back-edge
])

async def main():
    runner = InMemoryRunner(node=root_agent)
    await runner.run_debug("My windscreen has a small crack from a stone. Do I pay anything?")
    s = await runner.session_service.get_session(app_name=runner.app_name, user_id="debug_user_id",
                                                 session_id="debug_session_id")
    print("attempts:", s.state["attempts"], "| final query:", s.state["query"])

if __name__ == "__main__":
    asyncio.run(main())
```

**Run:** `python lab2_claims_crag.py`

**Expected output (illustrative)**
```
[grader]: {"label": "incorrect", "missing": "nothing about windscreen cracks"}   # 'windscreen' != 'windshield'
[rewriter]: windshield chip crack repair deductible comprehensive
[grader]: {"label": "correct", "missing": ""}
[answerer]: A small chip can be repaired at 100% with no deductible [AUTO-7.2]. If the whole windshield must be replaced, your comprehensive deductible applies [AUTO-7.3].
attempts: 2 | final query: windshield chip crack repair deductible comprehensive
```
The first miss is the point of the demo. The lexical retriever does not know that "windscreen" (UK) means "windshield" (US), and the corrective rewrite fixes it.

**Walk-through of the key lines**
- `(rewriter, retrieve)`: this back-edge makes a cycle. ADK accepts it only because the cycle passes through a **routed** edge (`decide → rewrite`). Without that edge you get the unconditional-cycle error below.
- `rewriter = Agent(..., output_key="query")`: the rewriter's text output **overwrites `state["query"]`**. The next `retrieve(query: str, attempts: int)` reads the new value by parameter name.
- `return Event(state={... "attempts": attempts + 1})`: the counter lives in session state, so it survives the loop and you can inspect it after the run (`session_service.get_session`).
- `def decide(node_input: Grade, attempts: int)`: this is the routing policy. It mixes the LLM grade (`node_input`) with a deterministic budget (`attempts`). Keep the budget in code, not in the prompt.
- `"(no results)"` plus `if s >= 2`: retrieval must be able to return **nothing**. A retriever that always returns its top-k trains the grader to say "ambiguous" forever.

**Common errors**
1. `GraphValidationError: Graph validation failed. Unconditional cycle detected: retrieve -> grader -> decide -> retrieve. Cycles must include at least one conditional (routed) edge to avoid infinite loops.` (`_graph_validation.py` L45-53). You get this if you write `(decide, rewriter)` without a route map. Fix: use the `{route: node}` dict form.
2. The model never returns `correct`, and the loop always ends in `abstain`. The cause is that `{grade}` renders as a raw dict and the rewriter just repeats the query. Fix: pass only `missing` (store it with `Event(state={"missing": node_input.missing})` in `decide`), and log `query` on each attempt.
3. `pydantic_core.ValidationError` for `Grade` when the model outputs a label outside the `Literal`. Fix: keep the label set small and describe each label in `Field(description=...)`. Avoid synonyms like "partially_correct".
4. `KeyError: Context variable not found: \`grade\` in agent 'rewriter'.` can appear if you later route straight to `rewriter` from `start`. Fix: `{grade?}`.

**Best practice.** Put a **deterministic budget** (`MAX_ATTEMPTS`) and an explicit **abstain** branch into the graph. Per arXiv 2609.16453 most quality gain arrives early. Per 2610.21184, if you push harder for evidence, you get more *premature* answers. So the grader, not the generator, must decide when to stop.

**Variation / extension.** (a) Add a cheap **pre-gate** before the LLM grader, in the spirit of arXiv 2609.11646 (score-distribution QPP, 2 ms). For a vector store: if `top1_score - top5_score < 0.02` and `top1_score < τ`, route straight to `rewrite` without an LLM call. (b) Add a fourth route `"web"` to a `single_turn` agent with `google_search` (Lab 3). That is the original CRAG "incorrect → web search" branch.

---

## Lab 3 — ADK `LlmAgent`: one agent, internal KB tool + web-search sub-agent, with grounding sources (support-ticket triage)

> **VERIFIED against google-adk 2.13.0 wheel source (verifier pass, 2026-10-23).** Imports, class/function names and parameters re-checked in the released package; code still not executed.

**Goal.** Acme Cloud's ticket-triage agent checks the **internal known-issues KB first**. It falls back to **Google Search** only when the KB has no match, for example for a third-party outage. It returns severity, queue and citations. The code also prints the web sources from `grounding_metadata`.

**Why this shape.** `google_search` is a Gemini built-in tool and cannot share a request with function tools. ADK ships `GoogleSearchAgentTool`: "a workaround to support using google_search tool with other tools" (`tools/google_search_agent_tool.py`). It wraps a search-only sub-agent and sets `propagate_grounding_metadata=True`. The GoogleSearchTool docstring adds that a non-Gemini model raises an error.

**Adapted from:** `contributing/samples/tools/agent_tool_with_grounding_metadata/agent.py` @ v2.13.0 (`AgentTool(agent=..., propagate_grounding_metadata=True)`) and the ADK docs page "Google Search" (https://adk.dev/integrations/google-search/).

**Prerequisites:** `pip install "google-adk==2.13.0"`, `GOOGLE_API_KEY`. Google Search grounding is billed per grounded prompt [pricing UNVERIFIED for 3.8 Flash]. The docs require you to show the Search suggestions (`renderedContent`) in production UIs (03-agentic-rag §8b).

**Code — `lab3_ticket_triage.py`**
```python
import asyncio, os, re
from google.adk import Agent
from google.adk.runners import InMemoryRunner
from google.adk.tools.google_search_agent_tool import GoogleSearchAgentTool, create_google_search_agent

MODEL = os.getenv("MODEL", "gemini-3.8-flash")
KNOWN_ISSUES = {
    "KI-311": "Checkout returns HTTP 502 when the payments webhook secret was rotated without redeploying. Fix: redeploy payments-svc. Queue: platform. Severity P1.",
    "KI-207": "Invoices show the wrong VAT for EU customers created before 2026-03-01. Queue: billing. Severity P3.",
}

def search_known_issues(query: str) -> dict:
    """Searches Acme's internal known-issues knowledge base.

    Args:
      query: Keywords from the support ticket, e.g. error codes and product area.

    Returns:
      A dict with 'results': a list of {'id', 'text'} for matching known issues.
    """
    words = set(re.findall(r"[a-z0-9]+", query.lower()))
    hits = [{"id": k, "text": v} for k, v in KNOWN_ISSUES.items()
            if len(words & set(re.findall(r"[a-z0-9]+", v.lower()))) >= 2]
    return {"status": "ok", "results": hits}

web_search = GoogleSearchAgentTool(create_google_search_agent(MODEL))   # tool name: google_search_agent

triage_agent = Agent(
    name="ticket_triage", model=MODEL, tools=[search_known_issues, web_search],
    instruction="""You triage Acme Cloud support tickets.
1. ALWAYS call search_known_issues first.
2. Call google_search_agent ONLY if no internal issue matches (e.g. a vendor outage).
3. Reply exactly: Severity: P1-P4 | Queue: billing/platform/integrations | Why: ... with citations
   [KI-xxx] for internal issues or the web page title for web results. Never invent an issue id.""")

async def main():
    runner = InMemoryRunner(agent=triage_agent, app_name="ticket_triage")
    for i, ticket in enumerate(["Customers get 502 errors at checkout since we rotated the webhook secret",
                                "Our Stripe-hosted checkout is down, is Stripe having an incident today?"]):
        events = await runner.run_debug(ticket, session_id=f"t{i}", quiet=True)
        for e in events:
            if e.author == "ticket_triage" and e.content and e.content.parts and e.content.parts[0].text:
                print("ANSWER:", e.content.parts[0].text)
            if e.grounding_metadata and e.grounding_metadata.grounding_chunks:
                for c in e.grounding_metadata.grounding_chunks:
                    if c.web:
                        print("  web source:", c.web.title, c.web.uri)

if __name__ == "__main__":
    asyncio.run(main())
```

**Run:** `python lab3_ticket_triage.py`

**Expected output (illustrative)**
```
ANSWER: Severity: P1 | Queue: platform | Why: matches [KI-311] (502 after webhook-secret rotation); redeploy payments-svc.
ANSWER: Severity: P2 | Queue: integrations | Why: the vendor status page reports an ongoing checkout incident (status.stripe.com).
  web source: status.stripe.com https://vertexaisearch.cloud.google.com/grounding-api-redirect/...
```
[UNVERIFIED] The web URIs in grounding chunks are usually Google redirect URLs, not the final page. Show `title`, and resolve the URL only if your policy allows it.

**Walk-through of the key lines**
- `create_google_search_agent(MODEL)` builds `LlmAgent(name='google_search_agent', tools=[google_search], ...)` with the instruction "Do not attempt to invoke a client-side function call" (source file above).
- `GoogleSearchAgentTool(...)` subclasses `AgentTool` and calls `super().__init__(agent=..., propagate_grounding_metadata=True)`. This brings the search sub-agent's `grounding_metadata` back into the parent's events.
- `search_known_issues` docstring: ADK turns the function signature and the Google-style docstring into the tool's function declaration. The return value is a dict with a `status` field, which is the ADK function-tool convention.
- `e.grounding_metadata`: `Event` extends `LlmResponse`, which has `grounding_metadata: Optional[types.GroundingMetadata]` (`models/llm_response.py` L69). `grounding_chunks[i].web.{uri,title}` comes from google-genai `types.GroundingChunk`.
- `InMemoryRunner(agent=..., app_name=...)`: use this for agents (not `node=`). `run_debug(..., quiet=True)` returns all events so you can inspect them (`runners.py` L1852-1950).

**Common errors**
1. `ValueError: Google search tool is not supported for model claude-...` (`tools/google_search_tool.py` L66-71). The cause is a non-Gemini model on the search sub-agent. Fix: keep that sub-agent on Gemini, even if the parent uses LiteLLM or another model.
2. HTTP **400 INVALID_ARGUMENT** when you put `google_search` and a function tool (or `VertexAiRagRetrieval`, or File Search) in the **same** agent's `tools` list. The docs say "can only be used by itself", and 09-critic records the 400 from the File Search codelab [exact error text UNVERIFIED]. Fix: use `GoogleSearchAgentTool`, a `single_turn` sub-agent, or `GoogleSearchTool(bypass_multi_tools_limit=True)` (this constructor flag exists in `google_search_tool.py` L26-44; whether a given model accepts the mix is [UNVERIFIED]).
3. The agent goes to web search first. Fix: write the order into the instruction (step 1 / step 2). Also return `results: []` explicitly, so the model sees an empty KB and not an error.

**Best practice.** Search **internal first, web second** and cite both kinds the same way. Keep the web branch in its own sub-agent so you can rate-limit it, log it and turn it off per tenant. arXiv 2610.14428 (customer support) shows how far one well-written instruction plus a small set of tools can go. It also reports the cost: about 10x the latency of a fixed pipeline.

**Variation / extension.** Use the ADK 2.x-preferred form. Declare the web researcher as `Agent(name="web_researcher", mode="single_turn", tools=[google_search], description=...)` and attach it with `sub_agents=[web_researcher]`. The framework exposes it as a tool automatically (`docs/guides/agents/llm_agent/single_turn.md` §2; sample `multi_agent/single_turn_sub_agent/agent.py`). [UNVERIFIED] whether grounding metadata is propagated in that mode. Check this before you rely on it for citations.

---

## Lab 4 — LangGraph: router + retriever + verifier with a regenerate loop (e-commerce refund agent)

> **VERIFIED against langgraph 1.2.17 + langchain-core 1.7.0 + langchain-google-genai 4.4.2 wheels source (verifier pass, 2026-10-23).** Imports, class/function names and parameters re-checked in the released package; code still not executed.

**Goal.** Acme Outfitters' refund agent routes each message (`refund_policy` / `order_status` / `other`). For policy questions it retrieves from a vector store, drafts an answer with `[REF-n]` citations, and runs a **sentence-level verifier**. If the verifier finds unsupported claims, the graph regenerates once with those claims listed. Then it either publishes the answer or falls back.

**Adapted from:** LangGraph docs "Build a custom RAG agent" (https://docs.langchain.com/oss/python/langgraph/agentic-rag). That page's retrieve → grade → rewrite graph is in 03-agentic-rag §7. Here it is rebuilt on Gemini, with a post-generation verifier instead of a pre-generation grader.

**Prerequisites**
```bash
pip install "langgraph==1.2.17" "langchain-core==1.7.0" "langchain-google-genai==4.4.2"
export GOOGLE_API_KEY=... MODEL=gemini-3.8-flash
```

**Code — `lab4_refund_graph.py`**
```python
import os
from typing import Literal, TypedDict
from pydantic import BaseModel, Field
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langgraph.graph import StateGraph, START, END

llm = ChatGoogleGenerativeAI(model=os.getenv("MODEL", "gemini-3.8-flash"))
POLICY = ["Unworn items can be returned within 30 days of delivery for a full refund to the original payment method.",
          "Sale items are final sale and cannot be refunded, only exchanged within 14 days.",
          "Refunds are issued within 5 business days after the warehouse inspects the return.",
          "Customers pay a USD 6 return-shipping fee unless the item arrived damaged."]
store = InMemoryVectorStore.from_texts(POLICY, GoogleGenerativeAIEmbeddings(model="gemini-embedding-001"),
                                       metadatas=[{"id": f"REF-{i}"} for i in range(1, len(POLICY) + 1)])

class Route(BaseModel):
    route: Literal["refund_policy", "order_status", "other"]
class Verdict(BaseModel):
    grounded: bool = Field(description="True only if every sentence is supported by its cited source")
    unsupported: list[str] = Field(default_factory=list, description="Sentences not supported by the sources")
class State(TypedDict, total=False):
    question: str; route: str; context: str; answer: str; unsupported: list[str]; tries: int

def router(s: State):
    r = llm.with_structured_output(Route).invoke(f"Route this customer message: {s['question']}")
    return {"route": r.route, "tries": 0}

def retrieve(s: State):
    docs = store.similarity_search(s["question"], k=3)
    return {"context": "\n".join(f"[{d.metadata['id']}] {d.page_content}" for d in docs)}

def generate(s: State):
    fix = f"\nYour last draft had UNSUPPORTED sentences, remove them: {s['unsupported']}" if s.get("unsupported") else ""
    msg = llm.invoke(f"Answer using ONLY the sources; put [REF-n] after every sentence.{fix}\n"
                     f"Sources:\n{s['context']}\nCustomer: {s['question']}")
    return {"answer": msg.text, "tries": s["tries"] + 1}

def verify(s: State):
    v = llm.with_structured_output(Verdict).invoke(f"Sources:\n{s['context']}\n\nAnswer:\n{s['answer']}\n"
                                                   "Check each sentence against the source it cites.")
    return {"unsupported": [] if v.grounded else v.unsupported}

def after_verify(s: State) -> Literal["publish", "generate", "fallback"]:
    if not s["unsupported"]:
        return "publish"
    return "generate" if s["tries"] < 2 else "fallback"

g = StateGraph(State)
g.add_node(router); g.add_node(retrieve); g.add_node(generate); g.add_node(verify)
g.add_node("publish", lambda s: {})
g.add_node("fallback", lambda s: {"answer": "I'm handing this to a refunds specialist."})
g.add_node("handoff", lambda s: {"answer": f"Routing to the {s['route']} team."})
g.add_edge(START, "router")
g.add_conditional_edges("router", lambda s: "retrieve" if s["route"] == "refund_policy" else "handoff",
                        ["retrieve", "handoff"])
g.add_edge("retrieve", "generate"); g.add_edge("generate", "verify")
g.add_conditional_edges("verify", after_verify, ["publish", "generate", "fallback"])
for n in ("publish", "fallback", "handoff"): g.add_edge(n, END)
app = g.compile()

if __name__ == "__main__":
    out = app.invoke({"question": "I bought a jacket on sale 10 days ago. Can I get my money back?"},
                     {"recursion_limit": 25})
    print(out["route"], "| tries:", out["tries"], "\n", out["answer"])
```

**Run:** `python lab4_refund_graph.py` (optional: `print(app.get_graph().draw_mermaid())` to paste the graph into a slide).

**Expected output (illustrative)**
```
refund_policy | tries: 1
 Sale items are final sale and cannot be refunded [REF-2]. You can exchange it, because you are still within the 14-day exchange window [REF-2].
```

**Walk-through of the key lines**
- `ChatGoogleGenerativeAI(model=...)`: this uses the Gemini Developer API with `GOOGLE_API_KEY`. No `temperature` is set on purpose. Google's Gemini 3 guidance says to keep the default temperature [UNVERIFIED for 3.8]. For **evaluation runs**, arXiv 2610.05034 measured that temperature 0 cuts answer disagreement from 14.3% to 3.4%, so pick the setting per purpose.
- `llm.with_structured_output(Verdict)`: the default method is `json_schema`, Gemini's native structured output (`chat_models.py` ~L2556-2576 on main). It returns a `Verdict` instance.
- `msg.text`: in langchain-core 1.x `.text` is a **property** (`messages/base.py` L262-263). Gemini 3 models can return `content` as a list of content blocks, so `msg.content` may not be a `str` [UNVERIFIED for 3.8 in every case]. `.text` always gives a string.
- `g.add_conditional_edges("verify", after_verify, [...])`: the third argument (`path_map`) lists the possible targets. It lets `draw_mermaid()` draw the edges. `StateGraph.add_conditional_edges` is at `graph/state.py` L982 @ 1.2.17.
- `{"recursion_limit": 25}`: **required in 2026**. The default is now 10007 (`_internal/_config.py` L42-44). A verify ↔ generate ping-pong would otherwise run for thousands of steps. The `tries` counter is the real guard, and the recursion limit is the safety net.

**Common errors**
1. `langgraph.errors.GraphRecursionError: Recursion limit of 25 reached without hitting a stop condition. You can increase the limit by setting the \`recursion_limit\` config key.` (`pregel/main.py` ~L3094-3099 / L3573-3578). The cause is a loop with no exit. Fix: route on the counter (`tries < 2`), and do not raise the limit.
2. `KeyError: 'unsupported'` in `generate` on the first pass, if you use `s["unsupported"]`. With `TypedDict(total=False)`, missing keys are not filled in. Fix: `s.get(...)`, as in the code.
3. Requests go to **Vertex AI** and fail with auth errors when you swap in `init_chat_model("gemini-3.8-flash")`. You also see the warning "Inferred `model_provider='google_vertexai'` ... This default will change to 'google_genai' in the next major release." (`langchain/chat_models/base.py` L586-589). Fix: `init_chat_model("google_genai:gemini-3.8-flash")`.
4. `ValueError` / auth error from `GoogleGenerativeAIEmbeddings` with no key set. It reads `GOOGLE_API_KEY` first, then `GEMINI_API_KEY` (`embeddings.py` L136-140).

**Best practice.** Verify **sentences against the source each one cites**, not "the answer against all context". That catches mis-citation, which arXiv 2609.15660 (CiteShade) shows an attacker can cause on purpose. Also cite **raw chunk ids**, not summaries of them: 2609.14245 found citations that looked 0.86 precise against compressed text were only 0.12 precise against source spans.

**Variation / extension.** Add CiteShade's counterfactual idea as a node. For each cited `[REF-n]`, regenerate the answer **without** that source. If the answer does not change, the citation was not causal, so flag it. Also add a persistent checkpointer so a human can approve fallbacks: `g.compile(checkpointer=...)` together with `langgraph.types.interrupt` (`types.py` L896-903 @ 1.2.17).

---

## Lab 5 — LangGraph: CRAG with per-passage grading ("knowledge refinement") and query rewrite (travel & expense policy)

> **VERIFIED against langgraph 1.2.17 + langchain-google-genai 4.4.2 wheels source (verifier pass, 2026-10-23).** Imports, class/function names and parameters re-checked in the released package; code still not executed.

**Goal.** An employee asks the T&E (travel and expense) bot something that the first retrieval answers badly. The graph grades **each retrieved passage** and keeps only the useful ones (CRAG's refinement step). If nothing survives, it rewrites the query and tries again, up to 3 attempts. Then it answers with citations or abstains. Lab 4 verified the *answer*. This lab cleans the *evidence*.

**Adapted from:** LangGraph "Build a custom RAG agent" (`grade_documents` → `rewrite_question` loop, URL above). CRAG: Yan et al., "Corrective Retrieval Augmented Generation", arXiv 2401.15884.

**Prerequisites:** same as Lab 4.

**Code — `lab5_te_crag.py`**
```python
import os
from typing import Literal, TypedDict
from pydantic import BaseModel, Field
from langchain_core.documents import Document
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langgraph.graph import StateGraph, START, END

llm = ChatGoogleGenerativeAI(model=os.getenv("MODEL", "gemini-3.8-flash"))
store = InMemoryVectorStore(GoogleGenerativeAIEmbeddings(model="gemini-embedding-001"))
store.add_documents([
    Document("Per diem for meals is EUR 60 per day in Germany and EUR 75 in Switzerland.", metadata={"id": "TE-3.1"}),
    Document("Alcohol is never reimbursable, including at client dinners.", metadata={"id": "TE-3.4"}),
    Document("Ride-hailing is reimbursable when public transport takes 45+ minutes longer.", metadata={"id": "TE-5.2"}),
    Document("Business class is allowed only on flights longer than 8 hours.", metadata={"id": "TE-2.1"}),
    Document("The office cafeteria is open from 8:00 to 15:00.", metadata={"id": "FAC-1"}),
])

class Relevance(BaseModel):
    relevant: bool = Field(description="Does this passage contain facts that help answer the question?")

class S(TypedDict, total=False):
    question: str; query: str; docs: list[Document]; kept: list[Document]; attempts: int; answer: str

def retrieve(s: S):
    return {"docs": store.similarity_search(s.get("query") or s["question"], k=3),
            "attempts": s.get("attempts", 0) + 1}

def grade(s: S):   # CRAG knowledge refinement: drop passages that do not help
    grader = llm.with_structured_output(Relevance)
    votes = grader.batch([f"Question: {s['question']}\nPassage: {d.page_content}" for d in s["docs"]])
    return {"kept": [d for d, v in zip(s["docs"], votes) if v.relevant]}

def decide(s: S) -> Literal["generate", "rewrite", "abstain"]:
    if s["kept"]:
        return "generate"
    return "abstain" if s["attempts"] >= 3 else "rewrite"

def rewrite(s: S):
    q = llm.invoke("Rewrite as a short keyword query for a corporate travel & expense policy. Output only the query.\n"
                   f"Question: {s['question']}\nQuery that failed: {s.get('query', s['question'])}").text
    return {"query": q.strip()}

def generate(s: S):
    ctx = "\n".join(f"[{d.metadata['id']}] {d.page_content}" for d in s["kept"])
    return {"answer": llm.invoke(f"Answer only from these passages and cite ids.\n{ctx}\nQ: {s['question']}").text}

def abstain(s: S):
    return {"answer": "The T&E policy does not cover this; I've forwarded it to travel@ for a ruling."}

g = StateGraph(S)
for fn in (retrieve, grade, rewrite, generate, abstain):
    g.add_node(fn)
g.add_edge(START, "retrieve"); g.add_edge("retrieve", "grade")
g.add_conditional_edges("grade", decide, ["generate", "rewrite", "abstain"])
g.add_edge("rewrite", "retrieve"); g.add_edge("generate", END); g.add_edge("abstain", END)
app = g.compile()

if __name__ == "__main__":
    for step in app.stream({"question": "Can I expense an Uber in Zurich and the wine at dinner with a client?"},
                           {"recursion_limit": 20}, stream_mode="updates"):
        print(step)
```

**Run:** `python lab5_te_crag.py`

**Expected output (illustrative; `stream_mode="updates"` prints one dict per node)**
```
{'retrieve': {'docs': [Document(... 'TE-3.4'), Document(... 'TE-3.1'), Document(... 'TE-5.2')], 'attempts': 1}}
{'grade': {'kept': [Document(... 'TE-5.2'), Document(... 'TE-3.4')]}}
{'generate': {'answer': 'The Uber is reimbursable only if public transport would take 45+ minutes longer [TE-5.2]. The wine is not reimbursable, even at a client dinner [TE-3.4].'}}
```

**Walk-through of the key lines**
- `grader.batch([...])`: this grades all k passages **in parallel** in one call site. Per-passage grading costs k LLM calls per attempt, so batching is what keeps CRAG usable.
- `{"kept": [d for d, v in zip(...) if v.relevant]}`: this is the refinement. The generator never sees `FAC-1` or the per-diem passage. Short, clean context also makes citations cleaner (2609.14245).
- `def decide(s) -> Literal[...]`: a router function returns the next node's name. The explicit list in `add_conditional_edges` lets LangGraph check the targets and draw them.
- `g.add_edge("rewrite", "retrieve")`: this is the corrective loop. `retrieve` prefers `s.get("query")` over the original question.
- `app.stream(..., stream_mode="updates")`: you see each node's state delta. Use this view in a live demo to show the loop happening.

**Common errors**
1. `GraphRecursionError: Recursion limit of 20 reached ...`: the `attempts` counter was not incremented (for example, you moved it to `rewrite` but routed `abstain` on it first). Fix: increment in `retrieve` and route on it in `decide`.
2. `InvalidUpdateError` [UNVERIFIED exact text] if two nodes write the same key in the same super-step. That happens if you fan out graders as parallel *nodes* with `Send` without a reducer. Fix: batch inside one node (as here), or declare `Annotated[list, operator.add]`.
3. The grader keeps everything: a "relevant" bias. Fix: ask "contains facts that help answer" (not "is related to"), and include one negative example in the prompt.

**Best practice.** Grade per passage only when k is small (≤5), and **batch** the calls. For large k, put a reranker before the grader. arXiv 2607.24010 also warns that **retrieval can harm** answers (the "harm rate"). Abstaining when no passage survives is a feature, not a failure.

**Variation / extension.** The banking paper (2610.22652) uses a **three-outcome** decision: Answer / *Related Mismatch* / No Answer. Add a `related_mismatch` route. It answers "we have a policy about X, not Y" and links the closest passage. In support data this is often the most helpful reply.

---

## Lab 6 — LangGraph: multi-hop QA with a requirement register (supplier compliance)

> **VERIFIED against langgraph 1.2.17 + langchain-google-genai 4.4.2 wheels source (verifier pass, 2026-10-23).** Imports, class/function names and parameters re-checked in the released package; code still not executed.

**Goal.** A compliance analyst asks: *"Who must approve a return of the jacket made by the supplier that failed the March 2026 audit?"* No single passage answers this. The graph keeps a **requirement register** of sub-questions. It resolves them one hop at a time and substitutes earlier answers into later sub-questions (`#1`, `#2`). It **refuses to answer** while any sub-question is still open.

**Grounded in:** arXiv 2610.21184, *Beyond Retrieval Failure* (ExecutionRAG's "training-free requirement register that records open sub-questions and their supporting evidence"). Also 2608.20627 (log evidence per hop for failure attribution) and 2610.30435 (search-state awareness). The code below is my own implementation of the idea, not the paper's code [the paper links no repo in its abstract].

**Prerequisites:** same as Lab 4.

**Code — `lab6_multihop_register.py`**
```python
import os
from typing import Literal, TypedDict
from pydantic import BaseModel, Field
from langchain_core.documents import Document
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langgraph.graph import StateGraph, START, END

llm = ChatGoogleGenerativeAI(model=os.getenv("MODEL", "gemini-3.8-flash"))
store = InMemoryVectorStore(GoogleGenerativeAIEmbeddings(model="gemini-embedding-001"))
store.add_documents([Document(t, metadata={"id": i}) for i, t in [
    ("AUD-1", "In the March 2026 supplier audit, Kestrel Textiles failed the chemical-safety check."),
    ("AUD-2", "Bluefin Gear passed the March 2026 audit with no findings."),
    ("SUP-4", "Kestrel Textiles manufactures the TrailLite rain jacket for Acme Outfitters."),
    ("SUP-5", "Bluefin Gear manufactures the Summit fleece."),
    ("RET-2", "Returns of products from a supplier on audit hold must be approved by the Quality Lead, Priya Natarajan."),
    ("RET-1", "Standard returns are approved automatically by the returns portal.")]])

class Plan(BaseModel):
    subquestions: list[str] = Field(description="2-4 single-fact sub-questions in order; refer to earlier answers as #1, #2")
class Hop(BaseModel):
    answer: str = Field(description="Short answer, or UNKNOWN if the passages do not state it")
    source_id: str = Field(description="Id of the passage that states the answer, or ''")
class S(TypedDict, total=False):
    question: str; register: list[dict]; hops: int; answer: str

def plan(s: S):
    p = llm.with_structured_output(Plan).invoke(f"Decompose into single-fact sub-questions: {s['question']}")
    return {"register": [{"q": q, "a": None, "src": None, "tries": 0} for q in p.subquestions], "hops": 0}

def hop(s: S):
    reg = [dict(r) for r in s["register"]]
    i = next(n for n, r in enumerate(reg) if r["a"] is None)       # first open requirement
    q = reg[i]["q"]
    for n, r in enumerate(reg[:i], 1):
        q = q.replace(f"#{n}", r["a"])                              # bridge entity substitution
    docs = store.similarity_search(q, k=2 + 2 * reg[i]["tries"])   # widen k on retry
    ctx = "\n".join(f"[{d.metadata['id']}] {d.page_content}" for d in docs)
    res = llm.with_structured_output(Hop).invoke(f"Passages:\n{ctx}\nSub-question: {q}")
    reg[i].update(q=q, tries=reg[i]["tries"] + 1)
    if res.answer != "UNKNOWN" and res.source_id:
        reg[i].update(a=res.answer, src=res.source_id)
    return {"register": reg, "hops": s["hops"] + 1}

def next_step(s: S) -> Literal["hop", "answer"]:
    still_open = any(r["a"] is None for r in s["register"])
    return "hop" if still_open and s["hops"] < 2 * len(s["register"]) else "answer"

def answer(s: S):
    open_q = [r["q"] for r in s["register"] if r["a"] is None]
    if open_q:                                                       # sufficiency gate
        return {"answer": f"Cannot answer yet; unresolved: {open_q}"}
    chain = "\n".join(f"{r['q']} -> {r['a']} [{r['src']}]" for r in s["register"])
    return {"answer": llm.invoke(f"Using only this evidence chain, answer: {s['question']}\n{chain}\n"
                                 "Cite every id used.").text}

g = StateGraph(S)
g.add_node(plan); g.add_node(hop); g.add_node(answer)
g.add_edge(START, "plan"); g.add_edge("plan", "hop")
g.add_conditional_edges("hop", next_step, ["hop", "answer"]); g.add_edge("answer", END)
app = g.compile()

if __name__ == "__main__":
    out = app.invoke({"question": "Who must approve a return of the jacket made by the supplier that failed the March 2026 audit?"},
                     {"recursion_limit": 20})
    for r in out["register"]:
        print(r)
    print("\nANSWER:", out["answer"])
```

**Run:** `python lab6_multihop_register.py`

**Expected output (illustrative)**
```
{'q': 'Which supplier failed the March 2026 audit?', 'a': 'Kestrel Textiles', 'src': 'AUD-1', 'tries': 1}
{'q': 'Which jacket does Kestrel Textiles make?', 'a': 'TrailLite rain jacket', 'src': 'SUP-4', 'tries': 1}
{'q': 'Who approves returns of products from a supplier on audit hold?', 'a': 'Priya Natarajan, Quality Lead', 'src': 'RET-2', 'tries': 1}

ANSWER: The Quality Lead, Priya Natarajan, must approve it [RET-2]. The TrailLite rain jacket [SUP-4] is made by Kestrel Textiles, which failed the March 2026 audit [AUD-1].
```

**Walk-through of the key lines**
- `Plan.subquestions` with `#1, #2` placeholders: the planner commits to an explicit dependency chain up front. Each hop query is **rewritten with resolved bridge entities**. This is the fix for "search drift" (2610.21184): later searches keep tracking the open sub-question.
- `reg = [dict(r) for r in s["register"]]`: copy, do not mutate. LangGraph state updates are returned values. Mutating `s` in place can skip checkpoint history.
- `k=2 + 2 * reg[i]["tries"]`: a cheap corrective action. On a miss, widen recall before you rephrase.
- `if res.answer != "UNKNOWN" and res.source_id`: a hop counts as resolved only **with a source id**. This keeps per-hop provenance for later failure attribution (2608.20627 found post-hoc traces miss hop-2/3 faults).
- `answer()` gate: if any requirement is open, the bot says so. This targets the paper's finding that recovering evidence *raises* premature resolutions. The register makes "sufficient evidence" a hard check.

**Common errors**
1. `StopIteration` in `hop` when the planner returned zero sub-questions, so `next(...)` finds no open entry. Fix: in `plan`, fall back to `[s["question"]]` when `p.subquestions` is empty.
2. A sub-question still contains a literal `#1` because the model wrote "(#1)" or "answer 1". Fix: show the placeholder format in the `Field(description=...)` (as here), and assert `"#" not in q` after substitution.
3. `GraphRecursionError`: the hop cap `2 * len(register)` is larger than `recursion_limit`. Fix: keep `recursion_limit` above `2 + 2*max_subquestions + 1`.

**Best practice.** Make the **register the unit of observability**: log it per request. When a multi-hop answer is wrong, you can see at once which hop failed and whether retrieval or reasoning failed (the evidence was retrieved but the answer is wrong, cf. 2609.33778, "Evidence-Inference Reconstruction").

**Variation / extension.** Run independent sub-questions (those with no `#n` dependency) **in parallel** with LangGraph's `Send` API (`langgraph.types.Send`, `types.py` L738 @ 1.2.17), and join them before the dependent hops. Or replace `similarity_search` with LightRAG `aquery_data(mode="local")` (Lab 7) so each hop can follow entity edges.

---

## Lab 7 — LightRAG quickstart on Gemini (GraphRAG-style KG over insurance claim files)

> **VERIFIED against lightrag-hku 1.5.7 wheel source (verifier pass, 2026-10-23).** Imports, class/function names and parameters re-checked in the released package; code still not executed.

**Goal.** Build a small knowledge graph over three claim-handling documents, then compare `naive` / `local` / `global` / `mix` retrieval on a question that crosses documents. Get **references** for citations, and get the raw entities, relations and chunks with `aquery_data`.

**Adapted from:** `examples/lightrag_gemini_demo.py` @ v1.5.7 (https://github.com/HKUDS/LightRAG/blob/v1.5.7/examples/lightrag_gemini_demo.py). That demo has two problems today. It uses the **shut-down** `gemini-2.0-flash` and `text-embedding-004`. And it decorates its embedding function with `send_dimensions=True` while the function accepts only `texts`. `EmbeddingFunc.__call__` then injects `embedding_dim=` (`lightrag/utils.py` L712-728), which should raise `TypeError` [not run; inferred from source]. The code below fixes both.

**Prerequisites**
```bash
pip install "lightrag-hku==1.5.7"            # the Gemini binding imports google-genai; install it if missing: pip install "google-genai==2.33.0"
export GEMINI_API_KEY=...                    # LightRAG reads GEMINI_API_KEY (or LLM_BINDING_API_KEY), not GOOGLE_API_KEY
export MODEL=gemini-3.8-flash
```

**Code — `lab7_lightrag_claims.py`**
```python
import asyncio, os
import numpy as np
from lightrag import LightRAG, QueryParam
from lightrag.llm.gemini import gemini_model_complete, gemini_embed
from lightrag.utils import wrap_embedding_func_with_attrs

MODEL = os.getenv("MODEL", "gemini-3.8-flash")
WORKING_DIR = "./claims_kg"
DOCS = {
    "claims/storm-2026-041.txt": "Claim 2026-041: hail damaged the roof of 12 Elm St on 2026-05-03. Adjuster Maria Lopez approved USD 18,400.",
    "claims/storm-2026-057.txt": "Claim 2026-057: hail damaged a car at 14 Elm St on 2026-05-03. Adjuster Maria Lopez flagged possible fraud.",
    "policy/hail-guidelines.txt": "Hail claims from the same street and date must be reviewed together by the Special Investigations Unit (SIU).",
}

async def llm_model_func(prompt, system_prompt=None, history_messages=None, **kwargs):
    return await gemini_model_complete(prompt, system_prompt=system_prompt,
                                       history_messages=history_messages or [], model_name=MODEL, **kwargs)

@wrap_embedding_func_with_attrs(embedding_dim=1536, send_dimensions=True, max_token_size=2048,
                                model_name="gemini-embedding-001")
async def embedding_func(texts: list[str], embedding_dim: int | None = None, context: str = "document") -> np.ndarray:
    return await gemini_embed.func(texts, model="gemini-embedding-001", embedding_dim=embedding_dim, context=context)

async def main():
    os.makedirs(WORKING_DIR, exist_ok=True)
    rag = LightRAG(working_dir=WORKING_DIR, llm_model_func=llm_model_func,
                   llm_model_name=MODEL, embedding_func=embedding_func)
    await rag.initialize_storages()                       # REQUIRED (no auto-init)
    try:
        await rag.ainsert(list(DOCS.values()), file_paths=list(DOCS.keys()))
        q = "Which Elm St hail claims must the SIU review together, and who handled them?"
        for mode in ("naive", "local", "global", "mix"):
            ans = await rag.aquery(q, param=QueryParam(mode=mode, include_references=True))
            print(f"--- {mode} ---\n{ans}\n")
        data = await rag.aquery_data(q, param=QueryParam(mode="mix"))
        print("entities:", [e["entity_name"] for e in data["data"]["entities"]][:8])
        for ref in data["data"]["references"]:
            print("ref", ref["reference_id"], "->", ref["file_path"])
    finally:
        await rag.finalize_storages()

if __name__ == "__main__":
    asyncio.run(main())
```

**Run:** `python lab7_lightrag_claims.py` (the first run extracts entities with the LLM. Later runs reuse `./claims_kg` and the LLM cache.)

**Expected output (illustrative)**
```
--- naive ---
Claim 2026-041 ... (may miss that the guideline links both claims)
--- local ---
Claims 2026-041 (roof, 12 Elm St) and 2026-057 (car, 14 Elm St) share street and date (2026-05-03), so the SIU must review them together. Both were handled by adjuster Maria Lopez.
### References
- [1] policy/hail-guidelines.txt
- [2] claims/storm-2026-041.txt
- [3] claims/storm-2026-057.txt
...
entities: ['Maria Lopez', 'Elm St', 'Claim 2026-041', 'Claim 2026-057', 'Special Investigations Unit', ...]
ref 1 -> policy/hail-guidelines.txt
```

**Walk-through of the key lines**
- `gemini_model_complete(..., model_name=MODEL)`: the binding takes the model from `hashing_kv.global_config["llm_model_name"]` and falls back to the `model_name` kwarg. If it finds neither, it raises (`lightrag/llm/gemini.py` L652-682). Set **both** `llm_model_name=` on `LightRAG` and `model_name=` here, as the official demo does.
- `@wrap_embedding_func_with_attrs(embedding_dim=1536, send_dimensions=True, ...)`: this declares a 1536-d vector and *injects* `embedding_dim` into the call, which `gemini_embed` sends as `output_dimensionality` (L784-786). Below 3072 dimensions the binding L2-normalizes the vectors (L812-819). The `context` parameter makes the function "asymmetric", so query and document embeddings can differ (`utils.py` L2528-2540).
- `await rag.initialize_storages()` / `finalize_storages()`: these are required. `auto_manage_storages_states` defaults to `False` and is marked deprecated (`lightrag.py` L963-966).
- `ainsert(..., file_paths=[...])`: the file paths become the **citation targets** for `include_references=True`. Note: `ainsert` "always chunks with the fixed-token (F) strategy" (`lightrag.py` L1794-1810).
- `QueryParam(mode=...)`: modes are `local, global, hybrid, naive, mix, bypass`, and the **default is `mix`** (`lightrag/base.py` QueryParam). `aquery_data` returns entities, relationships, chunks and references **without generation** (`lightrag.py` L3998-4060). Use it to feed your own agent (Lab 6 variation).

**Common errors**
1. `ValueError: Gemini API key not provided. Set LLM_BINDING_API_KEY or GEMINI_API_KEY in the environment.` (`llm/gemini.py` L143-149). The cause is that you set only `GOOGLE_API_KEY`. Fix: `export GEMINI_API_KEY=$GOOGLE_API_KEY`.
2. `ValueError: Embedding dimension mismatch detected: total elements (...) cannot be evenly divided by expected dimension (...).` (`utils.py` ~L750-756). The cause is a declared dimension that differs from the returned one. Fix: keep `send_dimensions=True`. **Never change the embedding model or dimension on an existing `working_dir`.** Delete it and re-index.
3. `ValueError: Gemini model name not provided in configuration.` (`llm/gemini.py` L669-670). Fix: pass `llm_model_name=` to `LightRAG(...)`.
4. 404 / model-not-found errors from the stock demo's `gemini-2.0-flash` [exact text UNVERIFIED]. Fix: use a current model from the models page.

**Best practice.** Graph RAG is an **ingestion-cost decision**, so measure it. Two new papers say to use the graph to *locate* passages and answer from the **original text**. EffiRAG (2609.18099) beat LightRAG-hybrid on 93/120 questions at 57% lower cost. LiteRAG (2609.10239) cut cost by over 99% vs GraphRAG Global. In LightRAG terms: prefer `mix` (graph + chunks) and cite chunk file paths, not entity summaries.

**Variation / extension.** Plug in a reranker (`rerank_model_func=` on `LightRAG`, field at `lightrag.py` L755). Note that `QueryParam.enable_rerank` defaults to `True` through `RERANK_BY_DEFAULT`. Or run the server UI with `pip install "lightrag-hku[api]"` and `lightrag-server` [server CLI name per README; flags UNVERIFIED for 1.5.7].

---

## Lab 8 — Managed grounding with citations: Gemini File Search via the Interactions API (employee benefits handbook)

> **VERIFIED against google-genai 2.33.0 wheel (Interactions + file_search_stores) source (verifier pass, 2026-10-23).** Imports, class/function names and parameters re-checked in the released package; code still not executed.

**Goal.** Upload Northwind's 2026 benefits handbook to a **File Search store** with metadata and custom chunking. Ask a question restricted to EU documents with `metadata_filter`. Then render **inline citations** from `file_citation` annotations, handling the byte offsets correctly.

**Adapted from:** Gemini API docs "File search" (https://ai.google.dev/gemini-api/docs/file-search, fetched 2026-10-23; all its Python samples now use `client.interactions.create`). Google codelab "Using Google Gemini File Search Tool for RAG" (https://codelabs.developers.google.com/gemini-file-search-for-rag, from 09-critic).

**Prerequisites**
```bash
pip install "google-genai==2.33.0"
export GOOGLE_API_KEY=... MODEL=gemini-3.8-flash
```
Facts from the docs page: storage and query-time embeddings are free, and indexing is billed at embedding rates. Limits: 100 MB per document, and project stores of 1 GB (Free) / 10 GB (Tier 1) / 100 GB (Tier 2) / 1 TB (Tier 3). Keep each store under 20 GB. Raw files are deleted after 48 h, but the embeddings persist. File Search **cannot be combined with Google Search grounding or URL Context**, but Gemini 3/4 can combine it with custom function calling.

**Code — `lab8_filesearch_citations.py`**
```python
import os, pathlib, time
from google import genai

MODEL = os.getenv("MODEL", "gemini-3.8-flash")
client = genai.Client()
pathlib.Path("benefits_eu_2026.txt").write_text(
    "Gym subsidy (EU): Northwind reimburses 50% of a gym membership, up to EUR 40 per month.\n"
    "To claim it, upload the monthly invoice in Workday > Expenses > Wellbeing before the 10th of the next month.\n"
    "Bike leasing (EU): employees in Germany and the Netherlands may lease one e-bike via payroll.\n", encoding="utf-8")

store = client.file_search_stores.create(config={"display_name": "northwind-benefits-2026"})
op = client.file_search_stores.upload_to_file_search_store(
    file="benefits_eu_2026.txt", file_search_store_name=store.name,
    config={"display_name": "Benefits Handbook EU 2026",
            "custom_metadata": [{"key": "region", "string_value": "EU"}],
            "chunking_config": {"white_space_config": {"max_tokens_per_chunk": 200, "max_overlap_tokens": 20}}})
while not op.done:                          # indexing is async: query only after done
    time.sleep(5)
    op = client.operations.get(op)

try:
    inter = client.interactions.create(
        model=MODEL,
        input="How much is the gym subsidy and how do I claim it?",
        tools=[{"type": "file_search", "file_search_store_names": [store.name],
                "metadata_filter": 'region="EU"', "top_k": 5}])
    for step in inter.steps or []:
        if step.type != "model_output":
            continue
        for block in step.content or []:
            if block.type != "text":
                continue
            raw = block.text.encode("utf-8")                     # offsets are BYTES, not characters
            cites = [a for a in (block.annotations or []) if a.type == "file_citation" and a.end_index is not None]
            for a in sorted(cites, key=lambda a: a.end_index, reverse=True):   # insert right-to-left
                raw = raw[:a.end_index] + f" [{a.file_name or a.document_uri}]".encode("utf-8") + raw[a.end_index:]
            print(raw.decode("utf-8"))
            for a in cites:
                print(f"  - {a.file_name} p.{a.page_number}: {(a.source or '')[:80]}")
finally:
    client.file_search_stores.delete(name=store.name, config={"force": True})
```

**Run:** `python lab8_filesearch_citations.py`

**Expected output (illustrative)**
```
Northwind reimburses 50% of your gym membership, up to EUR 40 per month [Benefits Handbook EU 2026]. Upload the monthly invoice in Workday > Expenses > Wellbeing before the 10th of the following month [Benefits Handbook EU 2026].
  - Benefits Handbook EU 2026 p.None: Gym subsidy (EU): Northwind reimburses 50% of a gym membership, up to EUR 40 ...
```

**Walk-through of the key lines**
- `client.file_search_stores.upload_to_file_search_store(*, file_search_store_name, file, config)` returns an operation. Poll it with `client.operations.get(op)` (signature at `file_search_stores.py` L789-795 @ v2.33.0). The config fields `display_name`, `custom_metadata`, `chunking_config` and `mime_type` are in `types.UploadToFileSearchStoreConfig` (types.py ~L17848-17875). `CustomMetadata` has `key`, `string_value`, `numeric_value` and `string_list_value`.
- `tools=[{"type": "file_search", ...}]`: the Interactions `FileSearch` tool has `file_search_store_names`, `metadata_filter` and `top_k` (`_gaos/types/interactions/filesearch.py`). The filter syntax `'region="EU"'` follows the docs example `'author="Robert Graves"'`.
- `step.type == "model_output"` → `block.type == "text"` → `block.annotations`: these types are `ModelOutputStep` and `TextContent.annotations: Optional[List[Annotation]]`. `Annotation` is a union of URL, place and file citations (`_gaos/types/interactions/{modeloutputstep,textcontent,annotation}.py`).
- `raw = block.text.encode("utf-8")`: `FileCitation.start_index` is documented as "measured in bytes" (`filecitation.py`). The same holds for `types.Segment.start_index/end_index` in the classic `generate_content` grounding (types.py ~L7908-7920). Slicing a Python `str` puts citations in the wrong place as soon as the text has `€`, `é` or emoji. Inserting **right-to-left** keeps the earlier offsets valid.
- `client.file_search_stores.delete(name=..., config={"force": True})`: `force` is in `DeleteFileSearchStoreConfig`. It deletes a store that still contains documents. Use it in demos, never by accident in production.

**Common errors**
1. Empty or uncited answer right after upload. Cause: you queried before `op.done`. Fix: keep the polling loop (no error is raised, which makes this a silent failure).
2. An error when you also pass a Google Search tool in the same request. The docs say "Built-in grounding tools cannot be combined in one request"; 09-critic records it as **400 INVALID_ARGUMENT** [exact message UNVERIFIED]. Fix: run two calls, or use ADK sub-agents (codelab pattern: RagAgent + SearchAgent as tools).
3. `AttributeError: 'Interaction' object has no attribute 'candidates'`: older `generate_content` code reads `response.candidates[0].grounding_metadata`. Interactions returns `steps` and `annotations` instead. Fix: use the loop above, or keep using `generate_content` with `types.Tool(file_search=...)` if your code base depends on `grounding_metadata` [whether that path is still supported for File Search in 2.33.0 is UNVERIFIED; the docs page no longer shows it].
4. Images fail to index. The docs say image support needs `gemini-embedding-2`, and images must be PNG/JPEG up to 4K x 4K. Audio and video are not supported.

**Best practice.** Use **managed citations as data, not decoration**. Store `(answer_span_bytes, file_name, page_number, source)` per answer for audit. Then run a Lab 4-style support check on a sample. Per CiteShade (2609.15660), a citation is a claim about *which source supports the text*, and attackers can fake that claim. Use `metadata_filter` for tenancy and region, and do not trust the prompt to keep regions apart.

**Variation / extension.** (a) Add `custom_metadata` with `numeric_value` (for example `{"key": "year", "numeric_value": 2026}`), filter on it, and compare the answers. (b) Call File Search from **ADK**: ADK 2.13.0 has `src/google/adk/tools/` modules for Vertex AI Search and RAG Engine. The v2.13.0 repo tree has **no file with "file_search" in its path** (checked through the GitHub tree API), so there is no dedicated ADK File Search tool. Follow the codelab's agent-as-tool pattern, or wrap the Lab 8 call in a function tool.

---

## 3. Cross-lab gotchas (slide material)

1. **Retrieval should be able to return nothing.** Every lab's retriever can return "(no results)" or an empty `kept` list. A top-k that is never empty hides retrieval failure from the grader (Labs 2 and 5).
2. **Budgets live in code, not prompts.** ADK: an `attempts` state key plus a route. LangGraph: a counter plus `recursion_limit`. The default is now **10007** steps.
3. **The verifier sees only evidence + draft.** ADK nodes default to `include_contents='none'`. In LangGraph you pass only `context` and `answer`.
4. **Cite raw chunk ids or byte spans.** Compressing before citing kills attribution (2609.14245). Offsets are bytes (Lab 8).
5. **Keep built-in grounding tools apart.** `google_search`, File Search and RAG Engine retrieval each need their own request or sub-agent (Labs 3 and 8).
6. **Sample rot.** `gemini-2.0-flash` is shut down, the LightRAG demo's embedding wrapper does not match its decorator, and `vertexai.preview.rag` is now `agentplatform.preview.rag`. Pin versions and models.
7. **Agentic ≠ better by default.** 2610.14428 is about 10x slower than the fixed pipeline. 2607.24010 says simple uncertainty or score baselines often match learned routers. Use the graph only where its routes earn their latency.

## 4. Sources (exact)

- ADK source @ v2.13.0: https://github.com/google/adk-python/tree/v2.13.0. Files: `src/google/adk/__init__.py`, `agents/llm_agent.py` (L289 DEFAULT_MODEL, L410-464 mode/include_contents/output_schema/output_key), `workflow/_workflow.py`, `workflow/_function_node.py`, `workflow/_llm_agent_wrapper.py`, `workflow/utils/_graph_validation.py`, `events/event.py`, `events/event_actions.py` (L198 route), `runners.py` (L280-350, L1852, L2377), `tools/agent_tool.py`, `tools/google_search_tool.py`, `tools/google_search_agent_tool.py`, `flows/llm_flows/prompt/_instructions_utils.py`, `docs/guides/agents/llm_agent/single_turn.md`
- ADK samples @ v2.13.0: `contributing/samples/workflows/{route,loop,loop_self,agent_in_workflow,classifier_node,state}/agent.py`, `integrations/rag_agent/agent.py`, `tools/agent_tool_with_grounding_metadata/agent.py`, `multi_agent/single_turn_sub_agent/agent.py`
- LangGraph @ 1.2.17: https://github.com/langchain-ai/langgraph/tree/1.2.17/libs/langgraph/langgraph. Files: `graph/__init__.py`, `graph/state.py`, `types.py`, `errors.py`, `_internal/_config.py`
- langchain-core: `libs/core/langchain_core/vectorstores/in_memory.py`, `messages/base.py`. langchain: `libs/langchain_v1/langchain/chat_models/base.py`
- langchain-google-genai 4.4.2: https://github.com/langchain-ai/langchain-google/tree/main/libs/genai/langchain_google_genai (`chat_models.py`, `embeddings.py`, `_common.py`)
- LangGraph docs "Build a custom RAG agent": https://docs.langchain.com/oss/python/langgraph/agentic-rag
- LightRAG @ v1.5.7: https://github.com/HKUDS/LightRAG/tree/v1.5.7 (`lightrag/lightrag.py`, `lightrag/base.py`, `lightrag/utils.py`, `lightrag/llm/gemini.py`, `examples/lightrag_gemini_demo.py`)
- google-genai @ v2.33.0: https://github.com/googleapis/python-genai/tree/v2.33.0 (`google/genai/file_search_stores.py`, `types.py`, `_api_client.py`, `_gaos/types/interactions/{filecitation,filesearch,modeloutputstep,textcontent,annotation,createmodelinteraction,interaction}.py`)
- Gemini API docs: "Models" https://ai.google.dev/gemini-api/docs/models · "File search" https://ai.google.dev/gemini-api/docs/file-search
- Codelab: "Using Google Gemini File Search Tool for RAG" https://codelabs.developers.google.com/gemini-file-search-for-rag
- arXiv (abstract pages, https://arxiv.org/abs/<id>): 2610.21184, 2607.24010, 2609.16453, 2608.20627, 2610.26951, 2609.15660, 2609.14245, 2610.14428, 2610.22652, 2609.11646, 2609.18099, 2609.10239, 2610.05034, 2610.30435, 2609.33778. Background: CRAG 2401.15884, LightRAG 2410.05779.
