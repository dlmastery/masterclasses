# 03 — Google Codelabs, Kaggle Intensive and Skills Boost for ADK (as of 2026-10-23)

> Scope: hands-on learning material from Google for the Agent Development Kit (ADK) 1.x → 2.0, Agent Engine / Agent Runtime, A2A, MCP and MCP Toolbox for Databases.
> Method: each codelab page below was fetched directly unless marked otherwise. Codelab pages usually show no "last updated" date and do not pin an ADK version, so versions are given only where the page states one.
> Naming drift: newer codelabs (Next '26 and later) say **"Agent Runtime"**, **"Gemini Enterprise Agent Platform"** and `GOOGLE_GENAI_USE_ENTERPRISE=1`. Older ones say **"Vertex AI Agent Engine"** and `GOOGLE_GENAI_USE_VERTEXAI`. The `adk deploy agent_engine` CLI verb survives under both names.
> Model strings in codelabs (`gemini-3.5-flash`, `gemini-3.8-flash`, `gemini-3-flash-preview`, `gemini-3.1-flash-lite`, `gemini-2.5-flash`) are quoted as each page shows them. They are not checked against the Gemini model list. Treat them as [UNVERIFIED as current model IDs].

---

## 0. ADK 2.0 context (needed to read the codelabs)

- **GA dates (adk.dev/2.0):** Python v2.0.0 on **19 May 2026**, Go on **30 June 2026**, TypeScript on **21 August 2026**. Source: https://adk.dev/2.0/
- **Python package:** `pip install google-adk`. It needs Python 3.11+, and releases come "roughly bi-weekly". PyPI has 2.5.0 and 2.6.1 pages. Source: https://github.com/google/adk-python (README)
- **Core shift:** "A graph-based execution engine for composing deterministic execution flows for agentic apps" (README). `BaseAgent` now subclasses `BaseNode`, so agents, tools and functions are all nodes.
- **New 2.0 primitives:** Workflow Runtime (routing, fan-out/fan-in, loops, retry, HITL, nested workflows), Task API (`mode="task"`, `"single_turn"`, `"chat"`), Tool Confirmation, and Agent Config (no-code YAML).
- **Python 2.0 breaking changes:** `Event` gains `node_info` and `output`. Overriding `_run_async_impl()` is silently ignored, so use `Before/AfterAgentCallback` instead. Do not catch `BaseException`, because it traps `NodeInterruptedError` and breaks HITL. `RetryConfig(max_attempts=3)`.
- **TypeScript:** `SequentialAgent`, `ParallelAgent` and `LoopAgent` are **deprecated (warning only)**, and graph workflows are the recommended replacement.
- **Go:** the module path becomes `google.golang.org/adk/v2`.

Official README quickstart (verbatim, https://github.com/google/adk-python):
```python
from google.adk import Agent, Workflow

generate_fruit_agent = Agent(
    name="generate_fruit_agent",
    instruction="Return the name of a random fruit. Return only the name.",
)
generate_benefit_agent = Agent(
    name="generate_benefit_agent",
    instruction="Tell me a health benefit about the specified fruit.",
)
root_agent = Workflow(
    name="root_agent",
    edges=[("START", generate_fruit_agent, generate_benefit_agent)],
)
```
Run it with `adk run path/to/my_agent` or `adk web path/to/agents_dir`.

Quotable lines from the ADK Go 2.0 announcement (Google Developers Blog, 30 Jun 2026, https://developers.googleblog.com/announcing-adk-go-20/):
- "A graph is an agent."
- "Expressing that complex orchestration as ad-hoc control flow gets brittle fast."
- "any node can pause the graph and ask a human a question"

---

## 1. ADK 2.0-native codelabs (2026)

### 1.1 ADK 2 Orchestration: Graph, Collaborative & Dynamic Workflows
- **URL:** https://codelabs.developers.google.com/adk2/instructions · Repo: `cuppibla/adk2-tutorial` (GitHub). The repo offers the same material as a codelab, a Colab notebook or a local clone.
- **Versions:** tested on **`google-adk==2.3.0`** and **2.0.0b1**. The page notes that `mode="task"` as a *static workflow node* was not possible on 2.0.0b1–2.3.0 and is possible on **2.5.0**.
- **Builds:** a "Marathon Race Day Coach", one level at a time:

  P. Prologue: why one mega-prompt fails
  L0. First agent with a tool
  L1. First `Workflow`
  L2a. Parallel fan-out plus `JoinNode`
  L2b. Deterministic router
  L3a. Collaborative agents (`chat` vs `single_turn`)
  L3b. Task mode (pause/resume, `finish_task`)
  L4a. Runtime-sized fan-out
  L4b. Recursive spawning (`ctx.run_node`, bounded by `MAX_DEPTH`)
  L5. Choosing a pattern
- **Cost note (repo):** L0–L2b make 0–1 model calls each. L4b makes 5–30 calls per run.
- **Key code (verbatim fragments from the page):**
```python
workflow = Workflow(edges=[(START, fetch_conditions, advise)])

# L2b deterministic router: a plain function emits a route label
route = "HOT" if temp >= 70 else "COLD" if temp <= 40 else "NORMAL"
return Event(output=node_input, route=route)
# edge map: route label -> branch
(route_by_weather, {"HOT": hot_strategy, "NORMAL": normal_strategy, "COLD": cold_strategy})

# L4b dynamic recursive worker
@node(parallel_worker=True, rerun_on_resume=True)
async def research_topic(ctx, node_input):
    ...
    if finding.needs_deeper and finding.deeper_questions and depth < MAX_DEPTH:   # boundary in CODE
        ...
```
- **Imports:** neither the page nor the README shows the module paths for `START`, `node`, `JoinNode` and `Event` [UNVERIFIED path; the README shows `from google.adk import Agent, Workflow`].
- **Teaching point:** the run does not depend on the model when routing is decided in code. The graph is deterministic and the agents are probabilistic.

### 1.2 Vibecode an ADK 2.0 Ambient Agent with Antigravity and Agents CLI
- **URL:** https://codelabs.developers.google.com/vibecode-ambient-expense-agent
- **Version:** `google-adk>=2.0.0a0`. It uses the graph `Workflow` API and **not** the 1.x `SequentialAgent`/`LlmAgent` style.
- **Builds:** an event-driven expense triage agent fed by simulated Pub/Sub messages.
  - Expenses **under $100** go to a plain Python function that auto-approves them, with **no LLM call**.
  - Expenses of **$100 or more** first pass a security screen that redacts PII and catches prompt injection. Gemini (`gemini-3.1-flash-lite`) then assesses the risk. Finally the workflow **pauses for a human** through `RequestInput`.
  - FastAPI serves it on :8080 at `/apps/expense_agent/trigger/pubsub`.
  - LLM-as-judge evaluation runs through Agents CLI, measuring routing correctness and security containment.
- **Steps:**
  1. Install the Antigravity IDE and add the ADK skills with `agents-cli`.
  2. Scaffold the project.
  3. Build the graph core (the $100 threshold lives in code).
  4. Add the security node.
  5. Run `make playground` and try HITL.
  6. Wrap the workflow in a FastAPI Pub/Sub trigger.
  7. Send `curl` events, including a malicious high-value payload.
  8. Run the evaluation.
  9. Next steps: Cloud Run plus Eventarc.
- **Why it matters for the deck:** it shows "ambient agents" (agents triggered by events rather than chat), the "code-first threshold, LLM only when needed" pattern, and AI-assisted ("vibe") coding of ADK agents.

### 1.3 Create and deploy low code ADK agents using ADK Visual Builder
- **URL:** https://codelabs.developers.google.com/codelabs/create-low-code-agent-with-ADK-visual-builder (the title says "Agent Deployment Kit" by mistake)
- **Version:** **`google-adk==2.3.0`**
- **Builds:**
  - Agent1: `google_search`, deployed to Cloud Run.
  - Agent2: a root agent, a sub-agent and an Imagen function tool, plus a SequentialAgent prompt-enhancer.
  - Agent3: a comic-book multi-agent pipeline generated by the **Agent Builder Assistant**.
- **Open the builder:** `adk web --host 0.0.0.0 --port 8080 --allow_origins "regex:https://.*8080-.*\.cloudshell\.dev"`, then click **+** to create an agent.
- **Agent Config YAML (verbatim):**
```yaml
name: Agent2
model: gemini-2.5-flash
agent_class: LlmAgent
instruction: You are an agent that takes image creation instruction from the
  user and passes it to your sub agent
sub_agents:
  - config_path: ./sub_agent_2.yaml
tools: []
```
- **Deploy:** `python3 deploycloudrun.py`, a lab script that wraps `adk deploy` and creates a service account.

---

## 2. Foundations series (Gemini Enterprise Agent Platform era)

### 2.1 Building AI Agents with ADK: The Foundation
- **URL:** https://codelabs.developers.google.com/devsite/codelabs/build-agents-with-adk-foundation
- **Builds:** a Personal Assistant agent, run from Cloud Shell with `uv` and Python 3.12. The install is unpinned: `uv pip install --no-cache google-adk`.
```bash
adk create personal_assistant      # choose model, backend, project, region
adk run personal_assistant
adk web --allow_origins "regex:https://.*\.cloudshell\.dev"
```
```python
from google.adk.agents import Agent

root_agent = Agent(
    model='gemini-3.5-flash',
    name='root_agent',
    description='A helpful assistant for user questions.',
    instruction='Answer user questions to the best of your knowledge',
)
```
- **Generated files:** `agent.py`, `__init__.py` (`from . import agent`) and `.env`. The `.env` contains `GOOGLE_GENAI_USE_ENTERPRISE=1`, `GOOGLE_CLOUD_PROJECT` and `GOOGLE_CLOUD_LOCATION`.
- **Related program:** the codelab points to GEAR (Gemini Enterprise Agent Ready): https://developers.google.com/program/gear

### 2.2 Building AI Agents with ADK: Empowering with Tools
- **URL:** https://codelabs.developers.google.com/devsite/codelabs/build-agents-with-adk-empowering-with-tools
- **Builds:** a travel assistant with three tool types:
  1. A custom `FunctionTool` (`get_fx_rate`, which calls a REST FX API).
  2. A **built-in** `google_search`, isolated in a sub-agent and called through `AgentTool`.
  3. A **third-party** LangChain Wikipedia tool wrapped with `LangchainTool`.
- **Key code (the page's import structure):**
```python
from google.adk.agents import Agent
from google.adk.tools import FunctionTool, google_search
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools.langchain_tool import LangchainTool
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper

google_search_agent = Agent(name="google_search_agent", tools=[google_search], ...)
wiki = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper(top_k_results=1, doc_content_chars_max=3000))

root_agent = Agent(
    name="root_agent",
    tools=[FunctionTool(get_fx_rate),
           AgentTool(agent=google_search_agent),
           LangchainTool(wiki)],
)
```
- **Lessons:**
  - "The LLM uses the docstring to decide when and how to call the tool."
  - Remove the root `instruction` once the tools define the agent's behaviour.
  - Use the adk web **Events** tab to see which tool fired.
- **Part 3** (multi-agent orchestration) is "coming soon" according to the page.

### 2.3 Related beginner lab: "ADK: From basics to multi-tool agents"
- **URL:** https://codelabs.developers.google.com/multi-tool-ai-agent-adk. A `multi-tools-ai-agent-adk` variant also exists.
- **Status:** found only in localized search results. [UNVERIFIED English title]

---

## 3. MCP + A2A codelabs

### 3.1 Getting Started with MCP & A2A with ADK (successor to "Getting started with MCP, ADK and A2A", the currency-agent lab by Jack Wotherspoon, June 2025)
- **URL:** https://codelabs.developers.google.com/getting-started-mcp-a2a-adk
- **History:** the old URL `/codelabs/currency-agent` now returns 404 in English. Localized copies remain, and the companion repo is `github.com/jackwotherspoon/currency-agent`.
- **Builds:**
  1. A FastMCP currency server (`get_exchange_rate` on the Frankfurter API, Streamable HTTP at `/mcp`).
  2. A currency `LlmAgent` that uses it through `McpToolset` and is exposed over **A2A** with `to_a2a`.
  3. A travel orchestrator with a local weather sub-agent (`AgentTool`) and a remote currency agent (`RemoteA2aAgent`).
  4. All three deployed to Cloud Run.
- **Key code (verbatim imports):**
```python
from fastmcp import FastMCP
mcp = FastMCP("Currency MCP Server 💵")
@mcp.tool()
def get_exchange_rate(...): ...

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import McpToolset, StreamableHTTPConnectionParams
root_agent = LlmAgent(model=..., name="currency_agent",
    tools=[McpToolset(connection_params=StreamableHTTPConnectionParams(url=MCP_SERVER_URL))])

from google.adk.a2a.utils.agent_to_a2a import to_a2a
a2a_app = to_a2a(root_agent, host=host, port=port, protocol=protocol)

from google.adk.agents.remote_a2a_agent import RemoteA2aAgent, AGENT_CARD_WELL_KNOWN_PATH
currency_remote_agent = RemoteA2aAgent(name="currency_agent",
    agent_card=f"{CURRENCY_AGENT_URL}{AGENT_CARD_WELL_KNOWN_PATH}")
```
- **Deploy:** `gcloud run deploy currency-agent --source currency_agent --region $REGION --update-env-vars MCP_SERVER_URL=...`. The page notes that `--allow-unauthenticated` is "for simplicity only".
- **Flow diagram (in words):** User → Travel Agent (Cloud Run) → [local Weather sub-agent] + [A2A over HTTP → Currency Agent (Cloud Run) → MCP Streamable HTTP → Currency MCP Server (Cloud Run) → Frankfurter API].

### 3.2 Build and deploy an ADK agent that uses an MCP server on Cloud Run
- **URL:** https://codelabs.developers.google.com/codelabs/cloud-run/use-mcp-server-on-cloud-run-with-an-adk-agent
- **Builds:** a zoo tour-guide agent. A greeter saves the question to state, then a SequentialAgent runs a researcher (zoo MCP server plus Wikipedia) followed by a formatter.
- **Auth:** Cloud Run calls require an **ID token** (`google.oauth2.id_token.fetch_id_token(request, audience)`), sent as an `Authorization: Bearer` header in `StreamableHTTPConnectionParams`.
```bash
uvx --from google-adk==1.14.0 adk deploy cloud_run --project=$PROJECT_ID \
  --region=us-west1 --service_name=zoo-tour-guide --with_ui . \
  -- --service-account=$SERVICE_ACCOUNT
```
- **Version:** this is a **1.x** lab (ADK 1.14.0). It is the Lab 2 that follows a "build an MCP server on Cloud Run" Lab 1.

### 3.3 Google's Agent Stack in Action: ADK, A2A, MCP on Google Cloud ("InstaVibe")
- **URL:** https://codelabs.developers.google.com/instavibe-adk-multi-agents/instructions
- **Builds:** an AI planner for a social-events app. The Planner, Social Profiling and Platform Interaction agents run as A2A microservices on Cloud Run, alongside an MCP tool server that wraps the InstaVibe APIs. The orchestrator runs on Vertex AI Agent Engine.
- **Status:** a 2025 flagship workshop. Details come from search results; the page was not fetched in full.

### 3.4 Build a Multi-Agent Creative Studio with Google's Agent Stack: ADK, A2A, MCP on Cloud Run & Agent Runtime
- **URL:** https://codelabs.developers.google.com/ai-creative-studio-adk-a2a · Repo: https://github.com/Saoussen-CH/mas-a2a-gcp
- **Pins:** `google-adk[a2a]==1.31.1`. The page notes that `SkillToolset` needs ADK **≥ 1.25.0**.
- **Builds:** five specialists on Cloud Run (Brand Strategist, Copywriter with a Skill, Designer, Critic returning APPROVED/NEEDS_REVISION, and a PM with the Notion MCP server). A Creative Director orchestrator runs on Agent Runtime.
```python
_instagram_skill = load_skill_from_dir(pathlib.Path(__file__).parent / "skills" / "instagram-copywriting")
_copywriting_skills = skill_toolset.SkillToolset(skills=[_instagram_skill])

strategist_agent = RemoteA2aAgent(name="brand_strategist",
    description="Researches markets, competitors, and trends using Google Search",
    agent_card=f"{strategist_url}/.well-known/agent.json")
agent_tools.append(AgentTool(agent=strategist_agent))

compaction_config = EventsCompactionConfig(
    compaction_interval=3,   # Summarize after every 3 agent completions
    overlap_size=1,          # Keep the most recent agent's output in full
)
```
- **Teaching points:**
  - Skills use progressive disclosure: `SKILL.md`, `references/` and `assets/` load only when needed.
  - Context compaction keeps long multi-agent runs within the context window.
  - Specialists are tested with the A2A Inspector.

### 3.5 Create multi agent system with ADK, deploy in Agent Runtime and get started with A2A protocol
- **URL:** https://codelabs.developers.google.com/codelabs/create-multi-agents-adk-a2a
- **Builds:** an image generate→score→regenerate loop that stops when the score reaches a threshold. It uses the tools `generate_images` (Imagen), `get_policy`, `set_score` and `check_tool_condition`.
- **Deployment:** `client.agent_engines.create(...)` with `display_name` and `staging_bucket`.
- **A2A serving:** `adk api_server --a2a --port 8001 remote_a2a`.
- **Inconsistency on the page:** it names the card `agents.json`, `agent.json` and `.well-known/agent-card.json` in different places, so check the current A2A spec path.

### 3.6 Agents at Scale: Multi-Agent Architecture with A2A Protocol on Agent Runtime and ADK Integration
- **URL:** https://codelabs.developers.google.com/adk-a2a-agent-runtime
- **Builds:** a restaurant reservation agent attached as a remote A2A sub-agent to an existing concierge agent.
- **Status:** details come from search results.

### 3.7 Building a Multi-Agent System using Gemini and Gemma models (Next '26)
- **URL:** https://codelabs.developers.google.com/next26/multi-agent-system. This is closely related to the "Production-Ready AI Roadshow" lab at https://codelabs.developers.google.com/codelabs/production-ready-ai-roadshow/1-building-a-multi-agent-system/building-a-multi-agent-system
- **Builds:** a Course Creator with four parts:
  - A Researcher using `google_search`.
  - A Judge with `output_schema=JudgeFeedback` (`Literal["pass","fail"]`).
  - A Content Builder running **Gemma via Ollama on a Cloud Run GPU** (`model=f"ollama_chat/{gemma_model_name}"`, default `gemma3:270m`).
  - An Orchestrator that calls the other three over A2A with authenticated httpx clients.
- **Classic 1.x loop pattern (verbatim fragments):**
```python
if isinstance(feedback, dict) and feedback.get("status") == "pass":
    yield Event(author=self.name, actions=EventActions(escalate=True))

research_loop = LoopAgent(sub_agents=[researcher, judge, escalation_checker], max_iterations=3)
root_agent = SequentialAgent(sub_agents=[research_loop, content_builder])
```
- **For the deck:** contrast this with the 2.0 graph version (the Judge becomes a router node, and the back-edge to the Researcher is the loop).

### 3.8 Scale Agents with CrewAI, LangGraph, A2A, and ADK (Next '26)
- **URL:** https://codelabs.developers.google.com/next26/scale-agents
- **Topic:** cross-framework interoperability over A2A. Details come from search results. [UNVERIFIED content]

---

## 4. Sessions, memory and deployment (Agent Engine / Agent Runtime)

### 4.1 Stateful Data Science Agent on Agent Runtime (Next '26)
- **URL:** https://codelabs.developers.google.com/next26/adk-deploy-scale · about 35 minutes (5–10 of them deployment), under $5.
- **Builds:** `BigQueryToolset` with **Memory Bank** and Cloud Trace.
```python
async def _save_memory(callback_context: CallbackContext) -> None:
    if agent_engine_id:
        await callback_context.add_session_to_memory()

# in Agent(...)
tools=[bq_toolset, PreloadMemoryTool()],
after_agent_callback=_save_memory,
```
```bash
uv run adk deploy agent_engine --project=$(gcloud config get project) \
  --region=us-central1 --display_name="Data Science Agent" --otel_to_cloud data_science_agent
```
- **Gotchas from the page:**
  - Do **not** put `google-cloud-aiplatform` in `requirements.txt`, because `adk deploy` adds it.
  - The Reasoning Engine service agent needs `roles/bigquery.jobUser` and `roles/bigquery.dataViewer`. Without them, queries fail with 403.
  - `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true` logs full prompts, which may include sensitive data.

### 4.2 Next '26 Developer Keynote: Enhancing Agents with Memory
- **URL:** https://codelabs.developers.google.com/next26/dev-keynote/enhancing-agents-with-memory
- **Builds:** a Marathon Planner using Agent Platform Sessions, Memory Bank and **RAG on AlloyDB** (vector column). City-rule PDFs are ingested with Spark on Dataproc Serverless and Document AI. An Agent Skill documents the RAG tool.
- **Key APIs:**
  - `from google.adk.memory import VertexAiMemoryBankService`
  - A `memory_service_builder()` function, passed to `AdkApp(memory_service_builder=...)`.
  - An `auto_save_memories` callback registered with `after_agent_callback=[...]`. It calls `memory_service.add_session_to_memory(session)`.

### 4.3 Next '26 Developer Keynote: Building ADK Agents with Skills and Tools
- **URL:** https://codelabs.developers.google.com/next26/dev-keynote/building-agents-with-skills
- **Builds:** a Marathon Planner with a modular `PromptBuilder` system prompt and three skills loaded with `load_skill_from_dir`: `gis-spatial-engineering`, `mapping` and `race-director`.
- **Skills wiring:** `SkillToolset(skills, code_executor=UnsafeLocalCodeExecutor(), ...)`.
- **Maps MCP:** reached through `from google.adk.integrations.api_registry import ApiRegistry` (server pattern `google-mapstools.googleapis.com-mcp`).
- **Inline skills:** `from google.adk.skills import models` → `models.Skill`.
- **Deploy:** `uv run adk deploy agent_engine --env_file planner_agent/.env --region=us-central1 planner_agent`

### 4.4 Multi-agent App with ADK, Agent Engine and AlloyDB
- **URL:** https://codelabs.developers.google.com/multi-agent-app-with-adk
- **Approach:** deploys with the SDK rather than the CLI (`AdkApp` plus `agent_engines.create`). Details come from search results.

### 4.5 Going Multimodal with Agent Development Kit: Personal Expense Assistant with Gemini 2.5, Firestore and Cloud Run
- **URL:** https://codelabs.developers.google.com/personal-expense-assistant-multimodal-adk · last updated **15 May 2025** (1.x era).
- **Builds:** receipt-image upload and expense analysis.
  - Frontend: a Gradio chat interface.
  - Backend: FastAPI hosting the ADK agent, session service and artifact service.
  - Storage: Firestore and Cloud Storage.

---

## 5. MCP Toolbox for Databases codelabs

### 5.1 Build a Travel Agent using MCP Toolbox for Databases and Agent Development Kit (ADK)
- **URL:** https://codelabs.developers.google.com/travel-agent-mcp-toolbox-adk · Toolbox **v1.13.1** (current page). Older revisions used v0.x, so check the Toolbox release page.
- **Builds:** hotel Q&A over Cloud SQL for PostgreSQL. The tools are declared in YAML (`kind: source`, `kind: tool` with `type: postgres-sql`, and `kind: toolset`).
```yaml
kind: tool
name: search-hotels-by-name
type: postgres-sql
source: my-cloud-sql-source
description: Search for hotels based on name.
parameters:
  - name: name
    type: string
    description: The name of the hotel.
statement: SELECT * FROM hotels WHERE name ILIKE '%' || $1 || '%';
```
```bash
./toolbox --config "tools.yaml"        # :5000 by default; add --ui for the Toolbox UI
```
```python
from google.adk.agents import Agent
from toolbox_core import ToolboxSyncClient

toolbox = ToolboxSyncClient("http://127.0.0.1:5000")
tools = toolbox.load_toolset('my_first_toolset')

root_agent = Agent(name="hotel_agent", model=...,
    description="Agent to answer questions about hotels in a city or hotels by name.",
    instruction="... Use the tools to answer the question", tools=tools)
```
- **Key lesson:** SQL lives in configuration, not in the prompt. The LLM only chooses a named, parameterised query, which is a guard against injected SQL.

### 5.2 Other Toolbox labs (titles and URLs from search results)
- **Database as a Tool: Agentic RAG with ADK, MCP Toolbox, and Cloud SQL:** https://codelabs.developers.google.com/agentic-rag-toolbox-cloudsql. Covers pgvector semantic search, with both the Toolbox server and the agent on Cloud Run.
- **Build a Formula E Logistics Agent using MCP Toolbox for Databases:** https://codelabs.developers.google.com/fe-logistics-mcp-toolbox
- **Build a Multi-agent App with MCP Toolbox for AlloyDB & ADK:** https://codelabs.developers.google.com/multi-agent-app-toolbox-adk
- **Build a Supply Chain Orchestrator with ADK, AlloyDB, and Vertex AI Memory Bank:** https://codelabs.developers.google.com/scm-alloydb-adk-memorybank
- **Build a Sports Shop Agent AI Assistant with ADK, MCP Toolbox and AlloyDB:** https://codelabs.developers.google.com/codelabs/sports-agent-adk-mcp-alloydb. Includes an OAuth sign-in flow.
- **Tools Make an Agent: From Zero to Assistant with ADK:** https://codelabs.developers.google.com/codelabs/cloud-run/tools-make-an-agent
- **MCP Toolbox for Databases: BigQuery datasets to MCP clients:** https://codelabs.developers.google.com/mcp-toolbox-bigquery-dataset

---

## 6. Quality, security, governance

### 6.1 Evaluating Agents with ADK
- **URL:** https://codelabs.developers.google.com/adk-eval/instructions
- **Builds:** an evaluation workflow for a customer-service agent, in five stages:
  1. Capture a golden dataset in the adk web UI. Saving it writes `evalset1.evalset.json`.
  2. Set thresholds in a config file.
  3. Write hand-made cases in `eval.test.json`.
  4. Run them from the CLI with `adk eval`.
  5. Wrap the runs in pytest for CI/CD.
- **Framing:** evaluate the **trajectory** (which tools, in what order) *and* the **final response**.
```json
{ "criteria": { "tool_trajectory_avg_score": 0.8, "response_match_score": 0.5 } }
```
```bash
uv run adk eval customer_service_agent customer_service_agent/evalset1.evalset.json \
  --config_file_path=customer_service_agent/test_config.json --print_detailed_results
```
```python
from google.adk.evaluation.agent_evaluator import AgentEvaluator
import pytest

@pytest.mark.asyncio
async def test_with_single_test_file():
    await AgentEvaluator.evaluate(
        agent_module="customer_service_agent.agent",
        eval_dataset_file_path_or_dir=eval_file,
        num_runs=1,
    )
```

### 6.2 Build a Secure Agent with Model Armor and Identity
- **URL:** https://codelabs.developers.google.com/secure-customer-service-agent/instructions
- **Builds:** a customer-service agent over BigQuery, accessed through the BigQuery MCP toolset with OAuth. Its defences come in layers:
  - **Model Armor** as `before_model_callback` (`sanitize_user_prompt`) and `after_model_callback` (`sanitize_model_response`).
  - **Agent Identity** at deploy time (`"identity_type": "AGENT_IDENTITY"`, API `v1beta1`).
  - A **conditional IAM** grant limited to `datasets/customer_service`, so the `admin` dataset is unreachable.
  - Red-team scripts covering prompt injection, sensitive-data leaks and unauthorized access.

### 6.3 Other security and governance labs (search results)
- **Build an AI Agent that acts On-Behalf-Of the user with Agent Identity and Auth Manager:** https://codelabs.developers.google.com/agent-identity-auth-manager
- **Governing agentic workloads with Agent Gateway on Gemini Enterprise Agent Platform:** https://codelabs.developers.google.com/cloudnet-agent-gateway
- **Securing cross-cloud agentic enterprise deployments:** https://codelabs.developers.google.com/next26/aiinfra-learning-pod/screen1-securing-cross-cloud-agentic. Covers MCP on GKE, OpenTelemetry and private networking.
- **Building a Production AI Code Review Assistant with Google ADK:** https://codelabs.developers.google.com/adk-code-reviewer-assistant/instructions. Compares local, Cloud Run and Agent Engine deployment. Agent Engine manages session persistence, while Cloud Run needs Cloud SQL.
- **Integrate Gemini Enterprise Agents with Google Workspace:** https://codelabs.developers.google.com/ge-gws-agents. Uses `adk deploy agent_engine`, then registers the agent in Gemini Enterprise.
- **Build an Agentic Pitch Generator: Orchestration, Evaluation, and Analytics with Google Cloud:** https://codelabs.developers.google.com/bwg-agentic-masterclass
- **Hackathon Challenge Lab:** https://codelabs.developers.google.com/hackathon-challenge-lab
- **Warning reported in one codelab:** `agents-cli deploy` and `adk deploy agent_engine` create different resource shapes, and the UI client only works with the `adk deploy` output (search snippet). [UNVERIFIED]

---

## 7. Kaggle: 5-Day AI Agents Intensive Course with Google (Nov 2025)

- **Learn Guide (self-paced now):** https://www.kaggle.com/learn-guide/5-day-agents. Capstone winners: https://www.kaggle.com/competitions/agents-intensive-capstone-project/discussion/663531
- **Dates:** the live run was **10–14 Nov 2025** (KDnuggets and secondary sources; Google's blog says only "November"). A follow-up "Vibe Coding" edition ran **15–19 June 2026**, and its days differ (for example, Day 5 was "Spec-Driven Production Development").
- **Format:** each day paired a whitepaper with two Kaggle notebook codelabs on Gemini and ADK, plus livestreams. Speakers came from Google, Cohere, Reified and NVIDIA.
- **Numbers** (Google blog recap, 18 Dec 2025, https://blog.google/technology/developers/ai-agents-intensive-recap/):
  - **1.5M+ learners**
  - **160K+** on the Kaggle Discord
  - **2M** whitepaper views
  - **3.3M** notebook views
  - **11,000+** capstone submissions
  - The earlier April 2025 GenAI intensive set a Guinness World Record with **280K+** participants.
- **Quote:** "the developer community is ready for what's next." (blog.google recap)

| Day | Theme / whitepaper | Notebooks (a/b) |
|---|---|---|
| 1 | Introduction to Agents: agent taxonomy, when to use an agent vs a workflow | 1a "From Prompt to Action" (first ADK agent with tools); 1b multi-agent architectures [title UNVERIFIED] |
| 2 | Agent Tools & Interoperability with MCP [exact title UNVERIFIED] | custom tools, MCP, long-running ops and HITL approval |
| 3 | Context Engineering: Sessions & Memory | sessions/state; long-term memory |
| 4 | Agent Quality: logs, traces, metrics, evaluation | observability; evaluation |
| 5 | Prototype to Production: A2A, deploying to Vertex AI Agent Engine | A2A communication; deployment |

---

## 8. Google Cloud Skills Boost

- **Course:** "Build intelligent agents with Agent Development Kit (ADK)", https://www.cloudskillsboost.google/course_templates/1382
  - **Level and length:** Intermediate, about 8.5 h (an older listing says 6h45m).
  - **Modules:** first agent → external tools (APIs, databases) → multi-agent systems → deploy to Agent Engine.
  - **Fast track:** a challenge lab leads straight to the skill badge. In it you author agents with ADK, deploy them to Agent Engine and call them from a web app.
- **Badges seen on public profiles:** "Deploy an Agent with Agent Development Kit (ADK)" and "Deploy Multi-Agent Systems with Agent Development Kit (ADK) and Agent Engine".
- **Caveat stated on the course:** the labs are "based on a pre-released version of the product", so they may lag ADK 2.0.

---

## 9. Patterns the codelabs teach (cross-cut for the deck)

| Pattern | Best codelab | ADK construct |
|---|---|---|
| Single agent + tools | Foundation / Empowering with Tools | `Agent`, `FunctionTool`, `google_search`, `AgentTool`, `LangchainTool` |
| Sequential pipeline | Zoo guide (MCP on Cloud Run) | `SequentialAgent` (1.x) → `Workflow(edges=[(START,a,b)])` (2.0) |
| Generator–critic loop | Gemini+Gemma course creator; image scoring | `LoopAgent` with `escalate=True` (1.x) → graph back-edge/router (2.0) |
| Parallel fan-out / join | ADK 2 Orchestration L2a / L4a | `JoinNode`, `@node(parallel_worker=True)` |
| Deterministic router | ADK 2 L2b; ambient expense agent ($100 rule) | `Event(output=..., route=...)` |
| Coordinator / specialists | Creative Studio; InstaVibe; travel+currency | `RemoteA2aAgent`, `to_a2a`, `AgentTool` |
| HITL | Ambient expense agent; ADK 2 L3b | `RequestInput`, task mode pause/resume |
| Tools via protocol | MCP & A2A; Toolbox labs | `McpToolset`, `StreamableHTTPConnectionParams`, `ToolboxSyncClient` |
| Memory | Data Science on Agent Runtime; Enhancing with Memory | `PreloadMemoryTool`, `VertexAiMemoryBankService`, `add_session_to_memory` |
| Skills / progressive disclosure | Next '26 Skills; Creative Studio | `load_skill_from_dir`, `SkillToolset` |
| Context compaction | Creative Studio | `EventsCompactionConfig(compaction_interval, overlap_size)` |
| Guardrails | Secure Agent | `before/after_model_callback` with Model Armor; Agent Identity |
| Evaluation | Evaluating Agents with ADK | `adk eval`, `AgentEvaluator.evaluate`, trajectory/response metrics |

**Deploy targets, as the codelabs show them:**
- `adk web` / `adk run` (local)
- `adk deploy cloud_run --with_ui`
- `adk deploy agent_engine [--otel_to_cloud]`
- `gcloud run deploy --source`
- `client.agent_engines.create(...)` (SDK)
- `adk api_server --a2a`

---

## 10. Slide ideas (8)

1. **"The Codelab Ladder"**: an animated staircase from Foundation → Tools → MCP/A2A → Memory → Eval → Security → ADK 2 Graphs. Each step lights up with its codelab URL as a QR code.
2. **"Five lines to an agent"**: a split screen with the `adk create` terminal on the left and `agent.py` on the right. Type the code in live, then show the adk web Events tab.
3. **"Three kinds of tools"**: one agent icon with three plugs (FunctionTool / built-in via AgentTool / LangchainTool), animated in turn as each prompt routes to a different tool.
4. **"Travel ↔ Currency ↔ MCP"**: a sequence diagram of packets moving User → Travel Agent → A2A → Currency Agent → MCP → Frankfurter. Highlight the agent card fetch at `/.well-known/...`.
5. **"Loop 1.x vs Graph 2.0"**: a before/after morph. The `LoopAgent[researcher, judge, checker]` stack turns into a graph with a pass/fail router and a back-edge. The caption is "A graph is an agent."
6. **"Ambient agent: $100 rule"**: a Pub/Sub message drops in and a code router splits it. One branch shows a green "auto-approve" with 0 LLM calls; the other runs PII screen → Gemini → a ⏸ human node. Animate a malicious payload being caught.
7. **"Memory Bank in two hooks"**: a timeline across Session 1 → `after_agent_callback` saves → Session 2 → `PreloadMemoryTool` recalls the preference.
8. **"Trust gap → eval pyramid"**: layers for adk web golden set → `adk eval` with thresholds (0.8 trajectory / 0.5 response) → pytest in CI. Show red and green test bars.
9. **"Defence in depth"**: concentric rings for Model Armor callbacks → Agent Identity → conditional IAM → red-team tests, with an injection arrow blocked at each ring.
10. **"1.5M learners"**: a Kaggle intensive stat wall (1.5M, 2M whitepaper views, 3.3M notebook views, 11K capstones) next to a five-day timeline card.

## 11. Open items / [UNVERIFIED]
- Exact Python import paths for `START`, `node`, `JoinNode`, `Event` and `RequestInput` in ADK 2.x. Check https://adk.dev/graphs/ before slides go final.
- Exact Kaggle whitepaper titles for Days 2 and 4, and the notebook titles beyond Day 1a.
- Content of the InstaVibe, Agents at Scale, Scale Agents (CrewAI/LangGraph), AlloyDB multi-agent and Agent Gateway labs. These come from search results; the pages were not fetched in full.
- Whether the model IDs quoted in codelabs are current.
