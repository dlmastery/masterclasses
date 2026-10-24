# 06 - ADK Evaluation, Observability and Safety

Research date: 2026-10-23. Scope: Google Agent Development Kit (ADK) Python 2.x, current release **v2.13.0** (GitHub release dated 23 Oct 2026, changelog entry 2026-10-22). ADK Python 2.0.0 reached GA on **19 May 2026** (adk.dev/2.0). Go 2.0 GA 30 Jun 2026, TypeScript 2.0 GA 21 Aug 2026. Docs moved from `google.github.io/adk-docs` to **https://adk.dev** (301 redirect).

Primary sources:
- Evaluate overview: https://adk.dev/evaluate/
- Criteria reference: https://adk.dev/evaluate/criteria/
- User simulation: https://adk.dev/evaluate/user-sim/
- Traces: https://adk.dev/observability/traces/
- Plugins: https://adk.dev/plugins/
- Safety & security: https://adk.dev/safety/
- Model Armor plugin: https://adk.dev/integrations/model-armor/
- Releases: https://github.com/google/adk-python/releases
- Codelab "Evaluating Agents with ADK": https://codelabs.developers.google.com/adk-eval/instructions (starter repo https://github.com/cuppibla/adk_eval_starter)

---

## 1. Why agent evaluation differs (the first-principles framing)

Classic unit tests assert `f(x) == y`. An agent is non-deterministic and takes a *path*: plan, then tool calls, then observations, then the answer. So ADK evaluates two things:
1. **The trajectory (process)**: which tools were called, in what order, with which args.
2. **The final response (output)**: is it correct, grounded, safe?

Quotable lines:
- "Agent quality is an architectural pillar, not a final testing phase." (Agent Quality whitepaper, Nov 2025)
- "The Trajectory is the Truth: ... The true measure of an agent's quality and safety lies in its entire decision-making process." (Agent Quality, p.7)
- "For agents, the final answer is merely the last sentence of a long story." (Agent Quality, p.47)
- "An AI can help grade the test, but a human writes the rubric and decides what an 'A+' really means." (Agent Quality, p.47)
- "Performance metrics tell us if the agent can do the job, but safety evaluation tells us if it should." (Agent Quality, p.29)
- "An agent that is 100% effective but causes harm is a total failure." (Agent Quality, p.28)

---

## 2. Eval data model: test files vs evalsets

| Concept | File | Use |
|---|---|---|
| Test file | `*.test.json` (only the suffix is checked) | Unit-style: one session, fast, run during dev / pytest |
| EvalSet | `*.evalset.json` (e.g. `evalset1.evalset.json` created by Web UI) | Integration-style: many eval cases, each its own session, multi-turn |
| Config | `test_config.json` in the folder, or `--config_file_path` | `criteria` thresholds (an `EvalConfig`) |

EvalSet schema (top level): `eval_set_id`, `name`, `description`, `eval_cases[]`.
Each eval case: `eval_id`, `conversation[]`, `session_input {app_name, user_id, state}`.
Each turn (an *Invocation*): `invocation_id`, `user_content`, `final_response` (reference), `intermediate_data {tool_uses[{name,args}], intermediate_responses[]}`.

Minimal eval case (adapted from the codelab's `eval.test.json`, refund case):
```json
{
  "eval_id": "refund_request",
  "conversation": [{
    "invocation_id": "inv-1",
    "user_content": {"role": "user", "parts": [{"text": "I want a refund for order ORD-102, it arrived damaged."}]},
    "final_response": {"role": "model", "parts": [{"text": "Your refund for ORD-102 has been issued."}]},
    "intermediate_data": {
      "tool_uses": [{"name": "issue_refund", "args": {"order_id": "ORD-102", "reason": "damaged"}}],
      "intermediate_responses": []
    }
  }],
  "session_input": {"app_name": "customer_service_agent", "user_id": "user", "state": {}}
}
```
Source: https://codelabs.developers.google.com/adk-eval/instructions (structure verified; the response texts are illustrative).

---

## 3. Three ways to run evals

### 3a. Web UI (`adk web`) - build the golden set by chatting
1. `adk web <agents_dir>`, chat with the agent.
2. **Eval** tab, create/select eval set, click **"Add current session"**. This freezes the tool trajectory + final text as ground truth.
3. Edit a case (pencil icon): modify responses, delete messages.
4. **Run Evaluation**: sliders for *Tool trajectory avg score* and *Response match score*, then **Start**.
5. Hover **Fail** to diff actual vs expected. Use the **Trace** tab to see each step's args.
v2.12.0 added efficiency metrics to Dev-UI evals; v2.13.0 added "agent evaluation session and turn trace views".

### 3b. CLI
```bash
adk eval <AGENT_DIR> <EVAL_SET_FILE_OR_ID>... [--config_file_path=...] [--print_detailed_results]
# run selected cases only
adk eval my_agent my_agent/sample.evalset.json:eval_1,eval_2
# codelab example
uv run adk eval customer_service_agent customer_service_agent/evalset1.evalset.json \
  --config_file_path=customer_service_agent/test_config.json --print_detailed_results
```
- `AGENT_DIR` is a directory whose `__init__.py` exposes `agent` with `root_agent`.
- Can pass file paths or IDs created by `adk eval_set create`; cannot mix both.
Source: https://adk.dev/evaluate/

### 3c. pytest (CI/CD)
```python
import pytest
from google.adk.evaluation.agent_evaluator import AgentEvaluator

@pytest.mark.asyncio
async def test_with_single_test_file():
    """Runs the agent against a .test.json file and asserts thresholds."""
    await AgentEvaluator.evaluate(
        agent_module="home_automation_agent",
        eval_dataset_file_path_or_dir="tests/integration/fixture/home_automation_agent/simple_test.test.json",
    )
```
Source: https://adk.dev/evaluate/ (pattern; the codelab adds `num_runs=1`). Behaviour changes: v2.10.0 makes `AgentEvaluator.evaluate` / `evaluate_eval_set` **raise `ValueError` if zero eval cases ran** (previously passed silently); v2.8.0 "support custom metrics in AgentEvaluator" and parallelized LLM-as-judge.

---

## 4. The metric catalogue (criteria)

`test_config.json` default if nothing set: `tool_trajectory_avg_score: 1.0`, `response_match_score: 0.8`.

| Criterion | Measures | Needs reference? | LLM judge? | Works with user sim? |
|---|---|---|---|---|
| `tool_trajectory_avg_score` | Tool-call trajectory match; `match_type` = `EXACT` (default), `IN_ORDER`, `ANY_ORDER` | Yes | No | No |
| `response_match_score` | ROUGE-1 overlap with reference | Yes | No | No |
| `response_evaluation_score` | Vertex AI coherence score | Yes | Yes | No |
| `final_response_match_v2` | Semantic equivalence to reference | Yes | Yes | No |
| `rubric_based_final_response_quality_v1` | Response vs custom rubrics | No (rubrics) | Yes | Yes |
| `rubric_based_tool_use_quality_v1` | Tool use vs custom rubrics | No (rubrics) | Yes | Yes |
| `rubric_based_multi_turn_trajectory_quality_v1` | Multi-turn path vs rubrics | No (rubrics) | Yes | Yes |
| `hallucinations_v1` | Groundedness vs context (optionally intermediate NL responses) | No | Yes | Yes |
| `safety_v1` | Harmlessness | No | Yes | Yes |
| `per_turn_user_simulator_quality_v1` | Does the simulator stick to scenario/persona | No | Yes | Yes |
| `multi_turn_task_success_v1` | Did the conversation achieve its goal | No | Yes | Yes |
| `multi_turn_trajectory_quality_v1` | Overall conversation path quality | No | Yes | Yes |
| `multi_turn_tool_use_quality_v1` | Function-call quality across turns | No | Yes | Yes |

Efficiency criteria, always reported, never pass/fail, not configurable: `tool_call_count_v1`, `inference_call_count_v1`, `token_usage_v1`, `invocation_duration_v1` (added v2.10.0; v2.13.0 splits duration into model / tool / framework time).

Notes: `safety_v1` and the `multi_turn_*` metrics delegate to the Agent Platform (Vertex) Gen AI Eval SDK and need `GOOGLE_CLOUD_PROJECT` + `GOOGLE_CLOUD_LOCATION`. Rubric criteria with an empty rubric list raise `ValueError`. Docs examples use judge model `gemini-flash-latest`.

Config (condensed from https://adk.dev/evaluate/criteria/):
```json
{
  "criteria": {
    "tool_trajectory_avg_score": {"threshold": 1.0, "match_type": "IN_ORDER"},
    "final_response_match_v2": {
      "threshold": 0.8,
      "judge_model_options": {"judge_model": "gemini-flash-latest", "num_samples": 5}
    },
    "rubric_based_final_response_quality_v1": {
      "threshold": 0.8,
      "judge_model_options": {"judge_model": "gemini-flash-latest", "num_samples": 5},
      "rubrics": [{"rubric_id": "conciseness",
                   "rubric_content": {"text_property": "The agent's response is direct and to the point."}}]
    },
    "hallucinations_v1": {"threshold": 0.8, "evaluate_intermediate_nl_responses": true},
    "safety_v1": 0.8
  }
}
```

Teaching points:
- `num_samples: 5` = the judge is sampled 5 times and majority-voted, reducing judge variance.
- ROUGE punishes paraphrase: the codelab saw ROUGE about 0.55-0.68 on correct answers and lowered the threshold to 0.5. That is the motivation for `final_response_match_v2`.
- Mapping to the Agents Companion lenses: EXACT = "exact match", IN_ORDER = "in-order match", ANY_ORDER = "any-order match". The Companion also lists precision, recall, single-tool use (not first-class ADK criteria [as of v2.13.0 docs]).

---

## 5. User simulation (dynamic multi-turn evals)

Problem: fixed scripts break when the agent asks a clarifying question. Solution: an LLM plays the user. Supported since ADK Python v1.18.0; personas since v1.26.0; v2.13.0 accepts `BaseLlm` instances for the simulator.

`ConversationScenario`: `starting_prompt` (fixed first message), `conversation_plan` (goals the simulated user must achieve), `user_persona` (prebuilt e.g. `"NOVICE"` or custom `UserPersona {id, description, behaviors[{name, description, behavior_instructions, violation_rubrics}]}`).

Example `scenarios.json` (shape from docs; text illustrative):
```json
{"scenarios": [{
  "starting_prompt": "What can you do for me?",
  "conversation_plan": "Ask the agent to roll a 6-sided die twice, then ask whether the results are prime.",
  "user_persona": "NOVICE"
}]}
```
```bash
adk eval_set create <agent_dir> <eval_set_name>
adk eval_set add_eval_case <agent_dir> <eval_set_name> \
  --scenarios_file scenarios.json --session_input_file session_input.json
adk eval <agent_dir> <eval_set_name> --config_file_path eval_config.json --print_detailed_results
# auto-generate scenarios (needs Agent Platform API + ADC)
adk eval_set generate_eval_cases <AGENT_DIR> <EVAL_SET_ID> --user_simulation_config_file=config.json
```
Simulator config: `model` (default `gemini-flash-latest`), `model_configuration` (`GenerateContentConfig`), `max_allowed_invocations` (default 20, -1 = unlimited, not recommended), `include_function_calls` (default false), `custom_instructions` (Jinja: `{{ stop_signal }}`, `{{ conversation_plan }}`, `{{ conversation_history }}`, `{{ persona }}`). Audio: `"type": "llm_audio"`, `audio_model` = `"cloud_tts"` or a Gemini TTS model, for Live agents (`google-adk[eval]` extra).
Constraint: reference-based criteria (`tool_trajectory_avg_score`, `response_match_score`, `final_response_match_v2`) are **not supported** with simulation; use `hallucinations_v1`, `safety_v1`, `multi_turn_task_success_v1`, rubric metrics.
Source: https://adk.dev/evaluate/user-sim/

---

## 6. Observability: OpenTelemetry-native tracing

ADK emits OTel spans following the **OTel GenAI semantic conventions**. Span names (adk.dev/observability/traces):
- `invoke_agent {agent.name}`
- `invoke_workflow {workflow.name}` (2.0 graph Workflow Runtime; `gen_ai.workflow.nested` for nested)
- `execute_tool {tool.name}`
- `generate_content {model.name}`

**Breaking in v2.13.0**: default schema is OTel GenAI v2 (`otel_semconv_1_44`), **`call_llm` span removed**; set `ADK_TELEMETRY_SCHEMA_VERSION_OPT_IN` to keep v1. Other recent items: spans marked when response came from a callback (v2.11), skill tool spans named after the skill (v2.12), Google Search grounding recorded on LLM spans and compaction counts per workflow (v2.13).

Key attributes: `gen_ai.operation.name`, `gen_ai.agent.name`, `gen_ai.conversation.id`, `gen_ai.request.model`, `gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens`.

Trace tree in words (one user turn):
```
invoke_agent root_agent
 |- generate_content gemini-flash-latest   (tokens in/out)
 |- execute_tool lookup_product_info       (args, result)
 |- invoke_agent refund_specialist
 |    |- generate_content ...
 |    |- execute_tool issue_refund
 |- generate_content ...                   (final answer)
```

Export options:
- CLI: `adk web --otel_to_cloud` exports to Google Cloud Trace.
- Env: `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=http://collector:4318/v1/traces`, `OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_SERVICE_NAME`, `OTEL_RESOURCE_ATTRIBUTES`.
- Code (identifiers verified; arrangement adapted):
```python
import os
from google.adk.telemetry.google_cloud import get_gcp_exporters
from google.adk.telemetry.setup import maybe_set_otel_providers

os.environ["OTEL_SERVICE_NAME"] = "your-adk-agent"
os.environ["OTEL_RESOURCE_ATTRIBUTES"] = "deployment.environment=prod"
gcp_exporters = get_gcp_exporters(enable_cloud_tracing=True)
maybe_set_otel_providers([gcp_exporters])
```
Phoenix (Arize, OpenInference) from https://adk.dev/integrations/phoenix/:
```python
# pip install openinference-instrumentation-google-adk google-adk arize-phoenix-otel
import os
from phoenix.otel import register
os.environ["PHOENIX_API_KEY"] = "..."
os.environ["PHOENIX_COLLECTOR_ENDPOINT"] = "https://app.phoenix.arize.com/s/<space>"
tracer_provider = register(project_name="my-llm-app", auto_instrument=True)
```
BigQuery Agent Analytics plugin (ADK >= 1.21.0; `pip install "google-adk[bigquery-analytics]>=2.7.0"`):
```python
from google.adk.apps import App
from google.adk.plugins.bigquery_agent_analytics_plugin import BigQueryAgentAnalyticsPlugin

plugin = BigQueryAgentAnalyticsPlugin(project_id="my-project", dataset_id="agent_logs")
app = App(name="my_agent", root_agent=root_agent, plugins=[plugin])
```
Listed observability integrations (adk.dev/integrations): AgentOps, Arize AX, BigQuery Agent Analytics, Google Cloud Trace, Datadog, Freeplay, Future AGI, Galileo, Grafana Cloud, Langfuse, LangWatch, Latitude, MLflow Tracing, Monocle, Phoenix, Respan, W&B Weave, Zespan. These are the real-world ecosystem examples for a slide.

Whitepaper framing (Agent Quality, ch.3): **three pillars** = Logging ("the agent's diary"), Tracing ("following the agent's footsteps", the narrative), Metrics ("the agent's health report": system vital signs + quality metrics). Kitchen analogy: traditional software is a **line cook** (monitoring a fixed recipe); an agent is a **gourmet chef** (you need observability into its judgement).

---

## 7. Guardrails: callbacks and plugins

Callback contract: return `None` = proceed; return an object = short-circuit (the object replaces the model/tool result).

Model-level guardrail (verbatim core from adk-docs `examples/python/snippets/callbacks/before_model_callback.py`, trimmed):
```python
from typing import Optional
from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse, LlmRequest
from google.genai import types

def simple_before_model_modifier(callback_context: CallbackContext,
                                 llm_request: LlmRequest) -> Optional[LlmResponse]:
    last_user_message = ""
    if llm_request.contents and llm_request.contents[-1].role == 'user':
        if llm_request.contents[-1].parts:
            last_user_message = llm_request.contents[-1].parts[0].text
    if "BLOCK" in last_user_message.upper():
        return LlmResponse(content=types.Content(role="model",
            parts=[types.Part(text="LLM call was blocked by before_model_callback.")]))
    return None

agent = LlmAgent(name="ModelCallbackAgent", model="gemini-flash-latest",
                 instruction="You are a helpful assistant.",
                 before_model_callback=simple_before_model_modifier)
```
Tool-level guardrail (from https://adk.dev/safety/):
```python
def validate_tool_params(tool: BaseTool, args: Dict[str, Any],
                         tool_context: ToolContext) -> Optional[Dict]:
    expected_user_id = tool_context.state.get("session_user_id")
    if args.get("user_id_param") != expected_user_id:
        return {"error": "Tool call blocked: User ID mismatch."}
    return None

root_agent = LlmAgent(model='gemini-flash-latest', name='root_agent', instruction="...",
                      before_tool_callback=validate_tool_params, tools=[...])
```

**Plugins** = cross-cutting callbacks registered once on the `App` (Python: `Runner(plugins=...)` is **deprecated**; use `App(plugins=[...])`; CLI `adk web --extra_plugins=<import path>`). Base class `google.adk.plugins.base_plugin.BasePlugin`. Hooks: `on_user_message_callback`, `before_run_callback`, `before/after_agent_callback`, `on_agent_error_callback`, `before/after_model_callback`, `on_model_error_callback`, `before/after_tool_callback`, `on_tool_error_callback`, `on_event_callback`, `after_run_callback`, `on_run_error_callback`, `close()`.
Precedence: plugin callbacks run **before** object-level callbacks; the first plugin returning non-`None` wins and skips the rest.
```python
from google.adk.plugins.base_plugin import BasePlugin

class SafetyPlugin(BasePlugin):
    def __init__(self) -> None:
        super().__init__(name="safety")
    async def before_model_callback(self, *, callback_context, llm_request):
        ...  # screen input; return LlmResponse to block, None to allow
    async def before_tool_callback(self, *, tool, tool_args, tool_context):
        ...  # validate args / redact PII

app = App(name="secure_app", root_agent=root_agent, plugins=[SafetyPlugin()])
```
(Class/registration pattern verified from https://adk.dev/plugins/; the exact keyword names of `before_tool_callback` in plugins are [UNVERIFIED] - check `base_plugin.py`.)
Agent Quality whitepaper tip: "the callback is the mechanism (the hook provided by ADK), while the Plugin is the reusable module you build."

Prebuilt plugins (adk.dev/plugins): Reflect and Retry Tools, Reflect and Retry Model, BigQuery Analytics, Model Armor, Context Filter, Global Instruction, Save Files as Artifacts, Auto Tracing, Multimodal Tool Results, Logging (`LoggingPlugin`), Debug Logging, Tool Call Integrity (v2.11). v2.13 adds `ForceEscalationPlugin`.

---

## 8. Model Armor (Google Cloud managed screening)

Model Armor inspects prompts and responses for prompt injection & jailbreak, harmful content, and sensitive data (per ADK page; other filters such as malicious URLs are in Cloud docs, https://docs.cloud.google.com/model-armor, not verified here). ADK plugin since **v2.8.0** ("add Model Armor guardrail plugin"); install `pip install 'google-adk[gcp]'`.
```python
from google.adk.agents import LlmAgent
from google.adk.apps import App
from google.adk.integrations.model_armor import ModelArmorConfig, ModelArmorPlugin

agent = LlmAgent(model="gemini-flash-latest", name="screened_agent",
                 instruction="You are a helpful assistant.")
app = App(
    name="model_armor_demo",
    root_agent=agent,
    plugins=[ModelArmorPlugin(config=ModelArmorConfig(
        prompt_template_name="projects/my-project/locations/us-central1/templates/my-prompt-template",
        response_template_name="projects/my-project/locations/us-central1/templates/my-response-template",
    ))],
)
```
Options: `prompt_template_name`, `response_template_name` (full resource paths, same region, at least one required), `input_blocked_message` / `output_blocked_message` (default "I'm sorry, but I can't help with that request."), `block_on_screening_failure=True` (**fail-closed** by default; False = fail-open). Blocked turns carry `custom_metadata['model_armor_blocked']`.
Source: https://adk.dev/integrations/model-armor/

---

## 9. Defence in depth and prompt injection

ADK safety page (https://adk.dev/safety/) risk sources: misalignment, "jailbreaks and prompt injections from adversarial users", "indirect prompt injections via tool use"; harms: toxic/off-brand content, unsafe actions (purchases, PII leakage, exfiltration).

Layers (diagram: concentric rings):
1. **Identity & authz**: Agent-Auth (service account; "appropriate for agents where all users share the same level of access") vs User-Auth (OAuth; scopes often too broad).
2. **In-tool guardrails**: tool exposes only intended actions; developer-set Tool Context policy (e.g. only `SELECT` on allow-listed tables).
3. **Gemini safety filters**: non-configurable (CSAM, PII) + configurable harm categories + system instructions.
4. **Callbacks & plugins**: `before_tool_callback` validation; **Gemini as a Judge** plugin (Flash Lite screens input, tool I/O, output for "appropriateness, prompt injection, and jailbreak detection"); Model Armor; PII Redaction plugin.
5. **Sandboxed code execution**: hermetic, no network, clean between runs.
6. **Evaluation & tracing**.
7. **VPC Service Controls** perimeter (coarse).
8. **UI escaping**: "an indirect prompt injection can trick a model to include an img tag" that leaks session data.

ADK-level hardening seen in releases: v2.8.0 "fence relayed agent output so it cannot pose as instructions" (multi-agent injection); v2.9.0 A2A requires https for non-loopback agent cards; optional OIDC verification for Pub/Sub / Eventarc triggers; v2.11 ToolCallIntegrityPlugin.
HITL: Agent Quality tip, pause before high-stakes tools (`execute_payment`, `delete_database_entry`) for human approval (ADK tool confirmation).
Introduction to Agents (Nov 2025): defence in depth = deterministic guardrails outside the model (e.g. spending limits) + reasoning-based defences (guard models, Model Armor); agents as a new class of principal with verifiable identity (SPIFFE), least privilege. Quote: "Every ounce of power introduces corresponding risk."
Related research (citation from memory, verify before slide): "Defeating Prompt Injections by Design" (CaMeL), Debenedetti et al., Google DeepMind, arXiv:2503.18813, 2025 [UNVERIFIED in this session].

---

## 10. The Google whitepapers: key ideas

| Paper | Date | Authors | Key ideas for this module |
|---|---|---|---|
| **Agents** (kaggle.com/whitepaper-agents) | Sept 2024 | Julia Wiesinger, Patrick Marlow, Vladimir Vuskovic | Agent = model + tools + orchestration layer; tools as Extensions, Functions, Data Stores; ReAct / CoT / ToT reasoning. (Date/author from secondary listing; PDF not fetched.) |
| **Agents Companion** (kaggle.com/whitepaper-agent-companion) | Feb 2025, 76 pp | Antonio Gulli, Lavi Nigam, Julia Wiesinger, Vladimir Vuskovic, Irina Sigler, Ivan Nardini, Nicolas Stroppa, Sokratis Kartakis, Narek Saribekyan, Alan Bount (PDF cover) | **AgentOps** = "a subcategory of GenAIOps that focuses on the efficient operationalization of Agents" (tool mgmt, agent brain prompt, orchestration, memory, task decomposition). Evaluation = 3 parts: capabilities (public benchmarks: BFCL, tau-bench, PlanBench, AgentBench), **trajectory & tool use**, **final response** (autorater = "an LLM that acts as a judge"), plus HITL to calibrate autoraters ("evaluating the evaluator"). Six trajectory metrics: exact match, in-order, any-order, precision, recall, single-tool use. Multi-agent eval: cooperation, planning/task assignment. |
| **Introduction to Agents** (Kaggle 5-Day Intensive Day 1) | Nov 2025 | Alan Blount, Antonio Gulli, Shubham Saboo, Michael Zimmermann, Vladimir Vuskovic (via secondary summary) | Levels 0-4 taxonomy (core reasoning, connected, strategic, multi-agent, self-evolving); Agent Ops (KPIs, LLM judge + golden set, OTel traces, feedback becomes tests); agent identity. Quote: "An agent is a system dedicated to the art of context window curation." |
| **Agent Quality** (kaggle.com/whitepaper-agent-quality; Day 4) | Nov 2025, 51 pp | Meltem Subasioglu, Turan Bulmus, Wafae Bakkali (curated by Anant Nawalgaria, Kanchana Patlolla) | Four pillars: Effectiveness, Efficiency, Robustness, Safety & Alignment. **Outside-In hierarchy**: black-box end-to-end (task success, CSAT) first, then glass-box trajectory: (1) LLM planning, (2) tool selection & parameterization, (3) tool response interpretation, (4) RAG, (5) efficiency & robustness, (6) multi-agent dynamics. Evaluators: automated metrics as trend indicators ("first filter"), LLM-as-a-Judge (prefer **pairwise** win-rate over 1-5 scores), Agent-as-a-Judge (judge the trace), HITL. Three observability pillars. **Agent Quality Flywheel**: Define quality, Instrument, Evaluate process, Feedback loop (every production failure becomes a regression test in the golden set). |
| **Prototype to Production** (Day 5) | Nov 2025 | [UNVERIFIED authors] | Eval-gated CI/CD, security guardrails, deployment, A2A. |

Kaggle 5-Day AI Agents Intensive: Nov 2025, each day a whitepaper + ADK codelabs; Day 4 = Agent Quality; reported 1.5M+ sign-ups [secondary source, kdnuggets]; reran June 15-19 2026 (vibe-coding theme). Learn guide: https://www.kaggle.com/learn-guide/5-day-agents

---

## 11. End-to-end flow for a lecture (diagram in words)

```
Chat in adk web --> "Add current session" --> evalset.json (golden trajectory + answer)
      |                                                   |
  Trace tab (debug)                         test_config.json thresholds
      |                                                   |
 adk eval / pytest AgentEvaluator  <--- CI gate on every PR (GitHub Actions / Cloud Build)
      |
 deploy (Agent Engine / Cloud Run) with plugins: ModelArmor + SafetyPlugin + BigQueryAgentAnalytics
      |
 OTel spans --> Cloud Trace / Phoenix / Langfuse ; logs --> BigQuery
      |
 thumbs-down / failures --> review queue --> new eval case (flywheel closes)
```

---

## 12. Slide ideas

1. **"Unit tests can't grade a chef"**: line-cook vs gourmet-chef split screen (Agent Quality analogy); animate deterministic `assert` cracking under non-determinism.
2. **Outside-In: black box, then glass box**: a sealed box with a score (task success) that lifts its lid to reveal 6 numbered trajectory checkpoints lighting up one by one.
3. **Anatomy of an EvalSet**: annotated JSON tree (eval_set > eval_case > invocation > user_content / tool_uses / final_response) with callouts building in.
4. **EXACT vs IN_ORDER vs ANY_ORDER**: three rows of tool-call chips (expected vs actual); animate an extra step and a swapped pair to show which pass.
5. **Metric map**: 2x2 grid (reference-based vs reference-free; deterministic vs LLM-judge) placing all `*_v1/_v2` criteria; efficiency metrics as a ribbon underneath.
6. **ROUGE vs semantic judge**: same correct paraphrase scoring 0.55 on ROUGE and pass on `final_response_match_v2` with `num_samples: 5` voting dots.
7. **User simulation loop**: two chat bubbles ping-ponging (simulated NOVICE persona vs agent) with a turn counter to `max_allowed_invocations=20` and a conversation_plan checklist ticking.
8. **Trace waterfall**: Gantt-style OTel span tree (`invoke_agent`, `generate_content`, `execute_tool`), with v2.13 `call_llm` struck out; exporters fanning out to Cloud Trace / Phoenix / Langfuse logos.
9. **Defence-in-depth onion**: concentric rings (identity, in-tool policy, Gemini filters, plugins/Model Armor, sandbox, VPC-SC, UI escaping); animate a prompt-injection arrow being stopped at successive rings.
10. **Plugin pipeline**: request flowing left-to-right through hook points (on_user_message, before_model, before_tool, after_model, on_event), with ModelArmorPlugin returning a canned reply and short-circuiting; then the Agent Quality Flywheel spinning to close the module.
