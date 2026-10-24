# 07 - Per-Step Verifiers and Evals for Agents (Google ADK 2.x + Gemini Enterprise Agent Platform)

Research date: 2026-10-23. Latest ADK Python release seen: **2.13.0 (2026-10-22)** (CHANGELOG). Items not confirmed against a primary source are marked **[UNVERIFIED]**.

Primary sources used:
- ADK docs (moved from `google.github.io/adk-docs` to **https://adk.dev**; the old URLs return 301 redirects): https://adk.dev/evaluate/ , /evaluate/criteria/ , /evaluate/user-sim/ , /evaluate/custom_metrics/ , /evaluate/environment_simulation/ , /optimize/ , /graphs/ , /graphs/routes/ , /graphs/dynamic/ , /graphs/data-handling/ , /workflows/patterns/ , /plugins/ , /integrations/reflect-and-retry/ , /api-reference/cli/ , /2.0/
- Source: https://github.com/google/adk-python (`src/google/adk/workflow/`, `src/google/adk/evaluation/`, `src/google/adk/plugins/`, `CHANGELOG.md`, `contributing/samples/evaluation/`)
- Agent Platform eval docs: https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/evaluation-agents-client , .../rubric-metric-details , https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/evaluation-agents , .../evaluation-overview
- Codelab: **"Evaluating Agents with ADK"**: https://codelabs.developers.google.com/adk-eval/instructions

---

## 0. Names and renames (state these correctly on slides)

| Today (Oct 2026) | Former name | Evidence / date |
|---|---|---|
| **Gemini Enterprise** (the employee-facing agent app/portal) | Google Agentspace | Announced 2025-10-09 at the Gemini Enterprise launch. Not re-fetched in this session, so treat the exact date as [UNVERIFIED]. |
| **Gemini Enterprise Agent Platform** ("Agent Platform") | Vertex AI (Gen AI / agent part) | The docs page titles now read "... \| Gemini Enterprise Agent Platform" and URLs live under `docs.cloud.google.com/gemini-enterprise-agent-platform/...`. Old `vertex-ai/generative-ai/docs` paths still resolve. Rename date [UNVERIFIED]; likely Google Cloud Next 2026 (April 2026). |
| **Agent Runtime** | Vertex AI Agent Engine (and before that, LangChain on Vertex AI / Reasoning Engine) | The docs call it "Agent Runtime". The SDK still uses `client.agent_engines.create(...)`, `vertexai.agent_engines.AdkApp`, and the env var `GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY`. Rename date [UNVERIFIED]. |
| **Gen AI evaluation service** (inside Agent Platform) | Vertex AI Gen AI evaluation service | The overview page is still titled "Gen AI evaluation service overview". |
| ADK docs at **adk.dev** | google.github.io/adk-docs | 301 observed 2026-10-23. |

ADK 2.0 GA dates (https://adk.dev/2.0/): **Python 2.0.0: 2026-05-19**, **Go 2.0.0: 2026-06-30**, **TypeScript 2.0.0: 2026-08-21**. The headline 2.0 feature is the graph-based **Workflow Runtime**: agents, tools and functions run as nodes, with routing, fan-out/fan-in, loops, retry, HITL and nested workflows.

---

## 1. Concept map: a verifier at every step

An agent run is a trajectory: `user -> [LLM step -> tool call -> tool result]* -> final answer`. Errors compound along it. If each step is 95% reliable, a 20-step run succeeds about 0.95^20 ≈ 36% of the time. So you verify **each step**, not only the final answer.

Verifier types, from cheapest and most reliable to most expensive:

1. **Programmatic checks.** Regexes, value ranges, ID existence, SQL `EXPLAIN`, compiling or linting code. Deterministic, sub-millisecond, zero tokens.
2. **Schema validation.** Pydantic `input_schema` / `output_schema` / `state_schema` on ADK 2.x nodes.
3. **Unit tests / executable checks.** Run the generated code against tests (as in the "code + lint + fixer" dynamic-workflow loop in /graphs/dynamic/).
4. **LLM-as-judge with a rubric.** Binary yes/no rubric items, sampled N times with a majority vote. ADK's `rubric_based_*` and `final_response_match_v2` metrics work this way.
5. **Process reward models (PRMs).** A model trained to score intermediate steps rather than outcomes (from the research literature: "Let's Verify Step by Step", OpenAI 2023). ADK has no built-in PRM. You plug one in as a custom node or custom metric. [No Google-managed PRM product found.]
6. **Human verification.** Tool confirmation / `RequestInput` HITL nodes.

Where checks happen (runtime vs offline):
- **Runtime (online) verifiers** live inside the graph: guard nodes, callbacks, plugins, retry policies.
- **Offline evals** replay evalsets: `adk eval`, pytest, Agent Platform `create_evaluation_run`.
- **Online evals / monitoring** score production traces. Agent Platform can sample datasets "directly from production logs" (eval overview). Traces come from Agent Runtime telemetry. The ADK 2.13 changelog adds "agent evaluation session and turn trace views (plugins)".

---

## 2. Runtime verification in ADK 2.x graphs

### 2.1 Building blocks (verified against source)

`google.adk.workflow.__all__` = `BaseNode, DEFAULT_ROUTE, Edge, FunctionNode, JoinNode, Node, NodeTimeoutError, RetryConfig, START, Workflow, node`.

Fields on `BaseNode` (`src/google/adk/workflow/_base_node.py`) that matter for verification:

| Field | Default | Verification role |
|---|---|---|
| `retry_config: RetryConfig \| None` | `None` (no retry) | Retry a step when it raises an exception |
| `timeout: float \| None` | `None` | Cancels the node with `NodeTimeoutError`. Retryable. |
| `input_schema` / `output_schema` | `None` | "Validates and coerces" data in and out |
| `state_schema: type[BaseModel]` | `None` | Validates `ctx.state` mutations. `app:`/`user:`/`temp:` keys bypass it. |
| `wait_for_output` | `False` | Node is COMPLETED only after it yields output or a route |
| `rerun_on_resume` | `False` | Required on parents that call `ctx.run_node` |

`RetryConfig` (`_retry_config.py`, Pydantic). Each field is `None` by default and resolves to the value in brackets:
`max_attempts` [5, includes the first try; 0 or 1 means no retry], `initial_delay` [1.0 s], `max_delay` [60.0 s], `backoff_factor` [2.0], `jitter` [1.0], `exceptions` [None = retry on every exception; accepts class names or classes].

Retry semantics (from source docstrings):
- When a node fails, the node reruns in full, including children it started with `ctx.run_node()`.
- Children that already completed are **replayed, not re-executed**.
- When a sub-workflow fails, the whole sub-workflow is retried.
- With `parallel_worker=True`, the retry policy applies per item.

The `@node` decorator signature (`_node.py`):
```python
def node(node_like=None, *, name=None, rerun_on_resume=None,
         retry_config: RetryConfig | None = None, timeout: float | None = None,
         parallel_worker: bool = False, max_parallel_workers: int | None = None,
         auth_config=None, require_confirmation: bool | Callable[..., bool] | None = None,
         parameter_binding: Literal['state', 'node_input'] = 'state') -> Any
```

**Key insight.** Retry fires on **exceptions**. So a verifier can trigger a retry simply by **raising**. The ADK 2.0 migration guide (https://adk.dev/2.0/) warns that a broad `except Exception:` inside a tool "masks the failure from the framework" and disables automatic retries. Catching `BaseException` also traps `NodeInterruptedError` and breaks HITL pauses.

### 2.2 Pattern A: guard node with routed back-edge (graph engineering)

Routing in ADK 2.x works like this: a node returns `Event(route=...)`, and the edge dict maps each route value to the next node (https://adk.dev/graphs/routes/). The docs warn: **"a graph cycle is not bounded automatically"**, so you must count attempts yourself.

```python
from google.adk import Agent, Event, Workflow
from pydantic import BaseModel

class Draft(BaseModel):
    sql: str
    attempts: int = 0

writer = Agent(name="sql_writer", model="gemini-flash-latest",
               instruction="Write a BigQuery SQL query for the request. Return only SQL.",
               output_schema=Draft)          # schema verifier #1 (structural)

MAX_ATTEMPTS = 3

def sql_guard(node_input: Draft):            # programmatic verifier #2
    ok = node_input.sql.strip().upper().startswith("SELECT") and "DELETE" not in node_input.sql.upper()
    if ok:
        return Event(route="PASS", output=node_input)
    if node_input.attempts + 1 >= MAX_ATTEMPTS:
        return Event(route="GIVE_UP", output=node_input)
    return Event(route="FAIL", output=node_input.model_copy(update={"attempts": node_input.attempts + 1}))

root_agent = Workflow(
    name="verified_sql",
    edges=[
        ("START", writer, sql_guard),
        (sql_guard, {"PASS": run_query, "FAIL": writer, "GIVE_UP": escalate_to_human}),
    ],
)
```
The edge syntax (`("START", a, b)` chains and `(router, {"ROUTE": node})` dicts), `Event(route=...)`, and the `from google.adk import Agent, Event, Workflow` imports are verified in /graphs/ and /graphs/routes/. Combining `route=` with `output=` in one `Event` is shown in the TS docs. For Python, treat that combination as [UNVERIFIED]. `run_query` and `escalate_to_human` are your own nodes. Feeding the guard's failure reason back to the writer (via state or input) is what makes this "reflect", not just "retry".

### 2.3 Pattern B: dynamic workflow verifier loop (loop engineering in code)

/graphs/dynamic/ shows a code-generation loop: generate, run lint/compile, then `ctx.run_node(fixer_agent, {...})` until the check passes. The Python sample is unbounded (`while check_resp.findings:`). The TS sample bounds it with `MAX_FIX_ROUNDS = 3`. **Always bound it.**

```python
from google.adk import Context
from google.adk.workflow import node

@node(rerun_on_resume=True)               # required for parents that call ctx.run_node
async def code_workflow(ctx: Context, node_input: str):
    code = await ctx.run_node(coder_agent, node_input=node_input)
    for _ in range(3):                    # bounded loop
        check = await ctx.run_node(lint_and_test, node_input=code)   # unit-test verifier
        if not check.findings:
            return code
        code = await ctx.run_node(fixer_agent, node_input={"code": code, "findings": check.findings})
    raise RuntimeError("verification failed after 3 rounds")   # surfaces to RetryConfig / HITL
```
`ctx.run_node`, `@node(rerun_on_resume=True)`, `from google.adk import Context` and `from google.adk.workflow import node` are verified. The `ctx`/`node_input` parameter binding shown here is a sketch.

### 2.4 Pattern C: classic LoopAgent generator-critic (1.x style, still documented)

From /workflows/patterns/:
- "Generate and review": a `SequentialAgent` of a generator, then a FactChecker reviewer that outputs "valid"/"invalid".
- "Iterative refinement": a `LoopAgent(max_iterations=5)` of refiner, quality checker and a custom `StopChecker(BaseAgent)` that does `yield Event(author=self.name, actions=EventActions(escalate=should_stop))` when `quality_status == 'pass'`.

### 2.5 Pattern D: ReflectAndRetry plugins (verifiers at the tool and model boundary)

Exports in `google.adk.plugins` (source `__all__`): `ReflectAndRetryToolPlugin`, `ReflectAndRetryModelPlugin`, `ToolCallIntegrityPlugin`, `ToolCallIntegrityError`, `ToolResultClassifier`, `ToolResultClassification`, `ForceEscalationPlugin`, `LoggingPlugin`, `DebugLoggingPlugin`, `ModelConsultObservabilityPlugin`, `BasePlugin`, `PluginManager`.

```python
from google.adk.apps.app import App
from google.adk.plugins import ReflectAndRetryToolPlugin

class StatusAwareRetry(ReflectAndRetryToolPlugin):
    async def extract_error_from_result(self, *, tool, tool_args, tool_context, result):
        if result.get("status") == "error":      # treat soft errors as failures
            return result
        return None

app = App(name="my_app", root_agent=root_agent,
          plugins=[StatusAwareRetry(max_retries=3)])
```
Source: https://adk.dev/integrations/reflect-and-retry/
- Defaults: `max_retries=3` (so 4 attempts in total), `throw_exception_if_retry_exceeded=True`, `tracking_scope=TrackingScope.INVOCATION` (the alternative is `GLOBAL`).
- By default, an error *inside a successful result* is **not** retried. That is why you override `extract_error_from_result`.
- The plugin returns a `ToolFailureResponse` with `response_type, error_type, error_details, retry_count, reflection_guidance`. The guidance tells the model not to repeat the same call and to check params, preconditions, an alternative tool, decomposition, and the tool name.
- **`ReflectAndRetryModelPlugin`**: same knobs plus `on_model_errors` (default `[FinishReason.MALFORMED_FUNCTION_CALL]`). It does **not** handle empty responses or output-schema failures (per source).
- **`ToolCallIntegrityPlugin(secret_key=...)`**: stamps each function call with an HMAC-SHA256 and re-verifies it before runs and tool calls. It blocks tampered or replayed calls in restored history.
- Register plugins on `App(plugins=[...])`. The `plugins=` argument on `Runner` is deprecated, and passing both raises `ValueError`.

### 2.6 Pattern E: callback guards

`before_tool_callback` returns a `dict` and `before_model_callback` returns an `LlmResponse`. In both cases the return value **skips** the real call and is used as the step's result (https://adk.dev/callbacks/design-patterns-and-best-practices/). Plugin hooks: `before_/after_/on_*_error_callback` for agent, model and tool, plus `on_user_message_callback`, `before_run_callback`, `on_event_callback`, `after_run_callback` (/plugins/). The Model Armor plugin covers prompt-injection and safety screening.

### 2.7 Self-consistency and majority vote

- **At runtime:** fan out N candidates, join them, then vote or verify.
  ```
  ("START", fan_out) -> [cand_1, cand_2, cand_3] -> JoinNode -> voter
  ```
  `JoinNode` is in `google.adk.workflow`. Its exact Python fan-out syntax is not shown in the docs: [UNVERIFIED]. Alternatively, use `@node(parallel_worker=True, max_parallel_workers=N)`.
- **In the eval judge:** `judge_model_options.num_samples` (e.g. 5) samples the judge N times, and **majority vote** decides each invocation (criteria docs). `num_samples=0` is rejected at construction (CHANGELOG).
- **Across runs:** `multi_run_config` (next section) gives pass@k-style reliability statistics.

---

## 3. Offline evaluation with ADK (`adk eval`)

### 3.1 Files
- `*.test.json`: one session (multi-turn), best for unit-style tests. A folder can hold a `test_config.json`.
- `*.evalset.json`: many eval cases. Fields: `eval_set_id, name, description, eval_cases[]`. Each case has `eval_id`, `conversation[]` (with `invocation_id, user_content, final_response, intermediate_data{tool_uses[{name,args}], intermediate_responses}`), `session_input{app_name,user_id,state}`, and optional `rubrics[]`. A case can also carry a `conversation_scenario` for user simulation.
- Migration helper: `AgentEvaluator.migrate_eval_data_to_new_schema`.

### 3.2 Commands (verified against /api-reference/cli/ and /evaluate/)
```bash
adk eval <AGENT_DIR> <EVALSET_PATH_OR_ID>... [--config_file_path=PATH] [--print_detailed_results] \
         [--eval_storage_uri=gs://...] [--log_level=INFO]
adk eval agent_dir file.evalset.json:eval_1,eval_2        # run selected cases
adk eval_set create <AGENT_DIR> <EVAL_SET_ID>
adk eval_set add_eval_case <AGENT_DIR> <EVAL_SET_ID> --scenarios_file s.json --session_input_file si.json
adk eval_set generate_eval_cases <AGENT_DIR> <EVAL_SET_ID> --user_simulation_config_file=cfg.json
adk optimize <AGENT_DIR> --sampler_config_file_path sampler_config.json [--optimizer_config_file_path ...]
adk conformance record <PATHS> {none|sse|bidi}   ;   adk conformance test --mode replay --generate_report
```
From the repo root (README):
```bash
adk eval contributing/samples/evaluation/home_automation_agent \
  contributing/samples/evaluation/basic_criteria/home_automation.evalset.json \
  --config_file_path contributing/samples/evaluation/basic_criteria/eval_config.json
```
- Paths and eval-set IDs cannot be mixed in one command.
- `--num_runs` is referenced in the `eval_config.py` docstring but is absent from the CLI reference: [UNVERIFIED flag].
- **2.13.0 (2026-10-22): "`adk eval` exit code now reflects passed/failed".** This is what makes a CI gate possible.

### 3.3 Criteria (17 total; https://adk.dev/evaluate/criteria/)

| Criterion | Kind | Notes |
|---|---|---|
| `tool_trajectory_avg_score` | deterministic | `match_type`: `EXACT` (default), `IN_ORDER`, `ANY_ORDER`. `ignore_args` option added in 2.9.0. Default threshold 1.0. |
| `response_match_score` | ROUGE-1 | Default 0.8 |
| `response_evaluation_score` | LLM coherence (Vertex) | Table only |
| `final_response_match_v2` | LLM judge, valid/invalid vs reference | `num_samples` majority vote |
| `rubric_based_final_response_quality_v1` | rubric judge | case rubrics with `type: FINAL_RESPONSE_QUALITY` merge in |
| `rubric_based_tool_use_quality_v1` | rubric judge on tool use | `TOOL_USE_QUALITY` |
| `rubric_based_multi_turn_trajectory_quality_v1` | rubric judge on whole conversation | First N-1 turns `NOT_EVALUATED`. `TRAJECTORY_QUALITY` |
| `hallucinations_v1` | segmenter + validator | Labels: supported / unsupported / contradictory / disputed / not_applicable. `evaluate_intermediate_nl_responses`. Grounding metadata added to judge context in 2.12. |
| `safety_v1` | Agent Platform Eval SDK | Needs `GOOGLE_CLOUD_PROJECT`/`LOCATION`. Version pinned in 2.10. |
| `per_turn_user_simulator_quality_v1` | judges the *simulator* | `stop_signal` e.g. `"</finished>"` |
| `multi_turn_task_success_v1`, `multi_turn_trajectory_quality_v1`, `multi_turn_tool_use_quality_v1` | Agent Platform managed | Reference-free |
| `tool_call_count_v1`, `inference_call_count_v1`, `token_usage_v1`, `invocation_duration_v1` | **efficiency, INFORMATIONAL** | Never pass or fail. Setting a threshold is an error. Added 2.10. 2.13 splits duration into model, tool and framework time. |

Rubric config (verbatim shape from the criteria page):
```json
{
  "criteria": {
    "rubric_based_tool_use_quality_v1": {
      "threshold": 1.0,
      "judge_model_options": {"judge_model": "gemini-flash-latest", "num_samples": 5},
      "rubrics": [
        {"rubric_id": "geocoding_called",
         "rubric_content": {"text_property": "The agent calls the GeoCoding tool before calling the GetWeather tool."}}
      ]
    },
    "tool_trajectory_avg_score": {"threshold": 1.0, "match_type": "IN_ORDER"},
    "hallucinations_v1": {"threshold": 0.8, "evaluate_intermediate_nl_responses": true}
  }
}
```
The effective rubric list must be non-empty, or the evaluator raises `ValueError`. Since 2.13, Vertex rubric verdicts and explanations appear in eval results.

### 3.4 Multi-run reliability (`multi_run_config`, from `eval_config.py`)
```json
{
  "criteria": {"tool_trajectory_avg_score": 1.0, "response_match_score": 0.8},
  "multi_run_config": {
    "num_runs": 3,
    "cross_run_scoring_by_metric": {
      "response_match_score": "min_over_runs",
      "tool_trajectory_avg_score": {"method": "pass_rate", "threshold": 0.9}
    },
    "cross_run_criteria": [{"method": "pass_rate", "threshold": 0.8}]
  }
}
```
- Score-combining methods: `mean_over_invocations` (default), `mean_of_runs`, `min_over_runs`.
- Counting method: `{"method": "pass_rate", "threshold": x}`.
- `max_crashed_runs` defaults to 0.
- Use `min_over_runs` when **every** run must be good (pass^k thinking). Use `pass_rate` when you can tolerate some flakiness.

### 3.5 Custom metric (programmatic verifier as an eval)
Real sample `contributing/samples/evaluation/custom_metric/temperature_safety.py`:
```python
from google.adk.evaluation.eval_case import get_all_tool_calls, Invocation, ConversationScenario
from google.adk.evaluation.eval_metrics import EvalMetric
from google.adk.evaluation.evaluator import EvalStatus, EvaluationResult, PerInvocationResult

def temperature_safety_score(eval_metric: EvalMetric, actual_invocations: list[Invocation],
                             expected_invocations, conversation_scenario) -> EvaluationResult:
    ...  # per invocation: any set_temperature call outside 18..30 -> score 0.0
```
`eval_config.json`:
```json
{"criteria": {"temperature_safety_score": 1.0},
 "custom_metrics": {"temperature_safety_score": {
   "code_config": {"name": "temperature_safety.temperature_safety_score"},
   "description": "Fails if any set_temperature call is outside 18-30 Celsius."}}}
```
- You must set `overall_eval_status`. A score alone is not a pass.
- The function may be `async`. Custom metrics exist since v1.18.0 and are supported in `AgentEvaluator` since 2.8.0.

### 3.6 User simulation (dynamic multi-turn evals)
`ConversationScenario`:
```json
{"starting_prompt": "Hello, what can you help me with?",
 "conversation_plan": "Ask the agent to roll a 12-sided die, then ask whether the result is even.",
 "user_persona": "EXPERT"}
```
- Personas are prebuilt (`NOVICE`, `EXPERT`) or a custom `UserPersona{id, description, behaviors[{name, description, behavior_instructions, violation_rubrics}]}`.
- `user_simulator_config` keys: `model` (default `gemini-flash-latest`), `model_configuration`, `max_allowed_invocations` (default 20), `include_function_calls` (default false), and `custom_instructions` (Jinja placeholders `{{ stop_signal }}`, `{{ conversation_plan }}`, `{{ conversation_history }}`, `{{ persona }}`).
- Reference-based criteria (`tool_trajectory_avg_score`, `response_match_score`, `final_response_match_v2`) are **not supported** with simulation.

### 3.7 Environment simulation (fault injection for tools; experimental, v1.24.0+)
```python
config = EnvironmentSimulationConfig(tool_simulation_configs=[
    ToolSimulationConfig(tool_name="get_user_profile", injection_configs=[
        InjectionConfig(injected_error=InjectedError(
            injected_http_error_code=503, error_message="Service temporarily unavailable."))])])
```
- Plug it in with `EnvironmentSimulationFactory.create_plugin(config)` (passed to `App(plugins=...)`) or `create_callback(config)` (used as a `before_tool_callback`).
- Knobs: `injection_probability` plus `random_seed` (reproducible flakiness), `match_args`, `injected_latency_seconds` (max 120), `injected_response`, and `MOCK_STRATEGY_TOOL_SPEC`. The last mocks stateful tools with an LLM, optionally seeded with `environment_data`/`tracing`.
- **Use it to test that your verifiers and retries actually fire.**

### 3.8 pytest regression gate
```python
import pytest
from google.adk.evaluation.agent_evaluator import AgentEvaluator

@pytest.mark.asyncio
async def test_agent_regression():
    await AgentEvaluator.evaluate(
        agent_module="home_automation_agent",
        eval_dataset_file_path_or_dir="tests/integration/fixture/home_automation_agent/",
    )
```
- Since 2.10, `evaluate` raises `ValueError` if zero cases run.
- 2.13 "Honor each metric's own `eval_status`".
- 2.7 added CSV export and result persistence.

### 3.9 Eval-driven optimization: `adk optimize` (v1.24.0+)
- `GEPARootAgentPromptOptimizer` is the default and rewrites only the root instruction.
- `GEPARootAgentOptimizer` also rewrites `SkillToolset` skills.
- Config: `max_metric_calls` (100), `reflection_minibatch_size` (3), plus `run_dir` for warm starts.
- The sampler (`LocalEvalSampler`) uses `train_eval_set` and an optional `validation_eval_set`. Keep the validation set held out to avoid overfitting the prompt to the evalset.

---

## 4. Agent Platform Gen AI evaluation service (cloud, managed)

Two SDKs:
- **GenAI Client** (`from vertexai import Client`; `client.evals.*`): recommended, **Preview**, supports adaptive rubrics.
- **`EvalTask` evaluation module**: GA. Supports LLM-judge and computation metrics, but no adaptive rubrics.

Agent flow, verbatim from https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/evaluation-agents-client:
```python
from vertexai import Client, types
from google.genai import types as genai_types
client = Client(project=PROJECT_ID, location=LOCATION,
                http_options=genai_types.HttpOptions(api_version="v1beta1"))

app = vertexai.agent_engines.AdkApp(agent=my_agent)
remote = client.agent_engines.create(agent=app, config={
    "staging_bucket": "gs://BUCKET",
    "requirements": ["google-cloud-aiplatform[adk,agent_engines]"],
    "env_vars": {"GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY": "true"}})

session_inputs = types.evals.SessionInput(user_id="user_123", state={})
ds = pd.DataFrame({"prompt": prompts, "session_inputs": [session_inputs] * len(prompts)})
ds_inf = client.evals.run_inference(agent=remote.api_resource.name, src=ds)
agent_info = types.evals.AgentInfo.load_from_agent(my_agent, remote.api_resource.name)
run = client.evals.create_evaluation_run(dataset=ds_inf, agent_info=agent_info,
        metrics=[types.RubricMetric.FINAL_RESPONSE_QUALITY, types.RubricMetric.TOOL_USE_QUALITY,
                 types.RubricMetric.HALLUCINATION, types.RubricMetric.SAFETY], dest=GCS_DEST)
run = client.evals.get_evaluation_run(name=run.name, include_evaluation_items=True); run.show()
```
The published page has `"staging_bucket": gs://BUCKET_NAME` unquoted, which is a syntax error. It is fixed above. Deploying to Agent Runtime takes up to about 10 minutes.

Managed rubric metrics (rubric-metric-details page):
- **Adaptive** (rubrics generated per prompt, then validated pass/fail): `GENERAL_QUALITY` (general_quality_v2), `TEXT_QUALITY`, `INSTRUCTION_FOLLOWING`, `MULTI_TURN_GENERAL_QUALITY`, `FINAL_RESPONSE_QUALITY` (v2; needs developer_instruction, tool_declarations, intermediate_events), `TOOL_USE_QUALITY` (v2), `FINAL_RESPONSE_REFERENCE_FREE` (needs rubric_groups), `MULTI_TURN_TASK_SUCCESS`, `MULTI_TURN_TOOL_USE_QUALITY`, `MULTI_TURN_TRAJECTORY_QUALITY` (all v1).
- **Static:** `GROUNDING` (v2), `SAFETY` (safety_v3; six policies), `FINAL_RESPONSE_MATCH` (v3), `HALLUCINATION` (v2).
- Pin a version with `types.RubricMetric.GENERAL_QUALITY(version='v1')`.
- Judges: Gemini 3.5 Flash for the latest versions. Agent rubric generation also uses Gemini 3.1 Pro. Multi-turn agent metrics use Gemini 3 Flash.

Older `EvalTask` trajectory metrics (evaluation-agents page):
- `trajectory_exact_match`, `trajectory_in_order_match`, `trajectory_any_order_match`, `trajectory_precision`, `trajectory_recall`, `trajectory_single_tool_use`, plus default `latency` and `failure`.
- Dataset columns: `predicted_trajectory`/`reference_trajectory`, each a list of `{tool_name, tool_input}`.
- Public datasets at `gs://cloud-ai-demo-datasets/agent-eval-datasets/` ("on-device", "customer-support", "content-creation").

How it connects to ADK:
- ADK's `safety_v1` and `multi_turn_*` criteria **delegate** to this service (the "Agent Platform Eval SDK").
- ADK eval session IDs are now "Agent Engine-compliant" (2.12).

---

## 5. Online vs offline evals, and CI regression gates

| | Offline | Online |
|---|---|---|
| Data | Golden evalsets (often captured in `adk web` and exported), synthetic scenarios (`generate_eval_cases`) | Sampled production traces (Agent Runtime telemetry, Cloud Trace, BigQuery Agent Analytics plugin) |
| Metrics | Reference-based (trajectory, ROUGE, match) plus rubric metrics | Reference-free only: rubric, hallucination, safety, task success, efficiency |
| When | Every PR (CI gate) and before deploy | Continuously, on dashboards, with alerts on drift |
| Tools | `adk eval`, pytest `AgentEvaluator`, `client.evals.evaluate` | Agent Platform eval on log samples; `BigQueryAgentAnalyticsPlugin`; 2.13 trace views. A managed "online eval" product name for Agent Runtime is [UNVERIFIED]. |

The codelab ("Evaluating Agents with ADK", step 10 "CI/CD with Pytest") wraps evals in pytest "so a pipeline can block deployments". A GitHub Actions gate looks like this:
```yaml
name: agent-eval-gate
on: [pull_request]
jobs:
  eval:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: uv sync
      - name: Fast deterministic gate (trajectory + custom checks)
        run: uv run adk eval my_agent my_agent/tests/smoke.evalset.json --config_file_path my_agent/tests/det_config.json
        env: { GOOGLE_API_KEY: "${{ secrets.GOOGLE_API_KEY }}" }
      - name: Rubric / hallucination gate (multi-run)
        run: uv run pytest tests/eval -q
```
This is a sketch: it relies on the 2.13 non-zero exit code. The action versions are standard GitHub actions, not from Google docs.

Gate design:
- Use tiers. Tier 1 is deterministic and cheap, and runs on every PR. Tier 2 is LLM-judged with multi-run, and runs nightly or on release. Tier 3 is online.
- Never change thresholds and the prompt in the same PR.
- Track efficiency metrics (tokens, calls, duration) as **informational trend lines**, not as gates.

---

## 6. Failure modes (and the fix)

1. **Unbounded verifier loops.** Graph cycles are not auto-bounded, and the Python dynamic sample uses `while findings:`. Fix: an attempt counter, `LoopAgent(max_iterations)`, or a `GIVE_UP` route to HITL.
2. **Swallowed exceptions.** `except Exception:` in tools disables `RetryConfig`. Catching `BaseException` breaks HITL (`NodeInterruptedError`).
3. **Soft errors not retried.** `{"status":"error"}` in a successful result is ignored by `ReflectAndRetryToolPlugin` unless you override `extract_error_from_result`.
4. **Retry is not reflection.** Re-running with the same input gives the same failure. Pass the verifier's reason back to the generator.
5. **Over-strict trajectories.** `EXACT` fails on harmless extra lookups. Use `IN_ORDER`/`ANY_ORDER`, `ignore_args`, or rubric tool-use metrics.
6. **ROUGE false negatives.** Paraphrases score low (the samples use 0.6). Prefer `final_response_match_v2`.
7. **Judge variance and bias.** Single-sample judges flip. Use `num_samples` majority vote, binary rubrics, a pinned judge version, and calibrate it (Agent Platform has an "Evaluate a judge model" page).
8. **Simulator drift.** The simulated user goes off-plan. Measure it with `per_turn_user_simulator_quality_v1` and cap with `max_allowed_invocations`.
9. **Zero-case "green" CI.** Fixed in 2.10 (`ValueError` when no cases run). Crashes before any metric now fail (2.7). Metrics that never ran are `NOT_EVALUATED`, not failed (2.9).
10. **Evalset overfitting with `adk optimize`.** Use a held-out `validation_eval_set`.
11. **Stale state between cases.** Use `reset_data()` hooks (as in the home_automation sample) or `session_input.state`.
12. **Cost blow-up.** Rubric metrics with `num_samples=5`, 3 runs and N cases mean 15N judge calls per metric. Tier them.

---

## 7. Interview questions (crisp answers)

1. **Why verify per step instead of only the final answer?** Errors compound multiplicatively over long trajectories, and an early verifier localizes the failure and enables a cheap local retry. Final-answer checks can't tell you *which* step broke.
2. **Where do you place a verifier in an ADK 2.x graph?** Right after any non-deterministic node whose output feeds an irreversible action (a tool write, a payment, an external send). Make it a function node returning `Event(route="PASS"|"FAIL"|"GIVE_UP")`, with a back-edge to the generator and a bounded counter.
3. **`RetryConfig` vs a routed back-edge?** `RetryConfig` handles exceptions and transient faults with exponential backoff, replaying completed children. A back-edge handles semantic failures, where the output is valid but wrong, and carries feedback.
4. **What does `ReflectAndRetryToolPlugin` add over plain retry?** It feeds the model a structured `reflection_guidance` (error, args, attempt k of N, "don't repeat the same call"), so the *model* changes its plan. Default is 3 retries, per-invocation scope.
5. **`EXACT` vs `IN_ORDER` vs `ANY_ORDER`?** EXACT allows no extra or missing calls. IN_ORDER requires the expected calls in sequence but allows extras. ANY_ORDER ignores order.
6. **How does ADK reduce LLM-judge noise?** Binary yes/no rubric items, `num_samples` majority vote, per-case rubrics typed by `FINAL_RESPONSE_QUALITY`/`TOOL_USE_QUALITY`/`TRAJECTORY_QUALITY`, and `multi_run_config` with `min_over_runs` or `pass_rate`.
7. **How does `hallucinations_v1` work?** A segmenter splits the response into sentences. A validator labels each against the context (supported, unsupported, contradictory, disputed, not_applicable). The score is the fraction supported or not_applicable. Intermediate NL responses are optional.
8. **Offline vs online evals?** Offline uses golden or simulated sets with references, and gates releases. Online uses reference-free judges on sampled production traces, and detects drift and new failure modes, which you then feed back into the offline set.
9. **How do you test the verifiers themselves?** Environment simulation injects 503s, latency and wrong data with seeded probability. Then assert that retries fire and guards route correctly. Conformance record/replay handles regressions.
10. **What is a PRM, and does Google ship one?** A process reward model scores intermediate reasoning steps rather than the outcome. ADK has no built-in PRM. You'd wrap one as a guard node or a custom metric.
11. **How do you make `adk eval` a CI gate?** Use `adk eval ... --config_file_path` (exit code reflects pass/fail since 2.13) or pytest `AgentEvaluator.evaluate`. Tier deterministic checks before rubric checks, and keep efficiency metrics informational.
12. **ADK's `rubric_based_*` vs Agent Platform `RubricMetric.*`?** ADK rubrics are developer-written and run locally with a chosen judge. Agent Platform adaptive rubrics are *generated per prompt* by the service (e.g. `FINAL_RESPONSE_QUALITY` v2, which uses Gemini 3.1 Pro for rubric generation) and run as managed evaluation runs.

---

## 8. Slide ideas (with explaining animation)

1. **"0.95^20 = 36%"**: a 20-step trajectory bar where each step fades in a little red. Then insert verifier diamonds after every step and watch the end-to-end success counter climb.
2. **The verifier ladder**: a staircase of regex, schema, unit test, LLM-judge, PRM, human. A cost meter rises and a latency clock spins as you climb. The message: "use the lowest rung that catches the error."
3. **Guard node in a graph**: generator, then a diamond `sql_guard` that splits three ways (PASS to execute, FAIL looping back, GIVE_UP to a human). A token animates around the loop with an attempt counter ticking 1, 2, 3, then exits to GIVE_UP.
4. **RetryConfig vs back-edge**: split screen. Left: an exception lightning bolt triggers backoff dots (1 s, 2 s, 4 s…) and completed children glow "replayed". Right: a semantic FAIL carries a speech bubble of feedback back to the generator.
5. **ReflectAndRetry in action**: the tool call fails and a `ToolFailureResponse` card flips open showing `retry_count 1/3` and `reflection_guidance`. The model's next call morphs with corrected args and turns green.
6. **Self-consistency fan-out**: one prompt splits into 5 parallel candidates via `JoinNode`. The ballots tally, the majority answer lifts up, and the outlier fades away. Overlay: "num_samples=5 in judges is the same idea."
7. **Anatomy of an evalset**: an exploding diagram of `.evalset.json` into eval_cases, conversation, tool_uses, rubrics, session_input. Each part highlights as the matching criterion lights up (trajectory, response, rubric).
8. **Trajectory match types**: the expected sequence A-B-C against an actual A-X-B-C. EXACT gives a red X. IN_ORDER slides X aside and turns green. ANY_ORDER shuffles the cards and turns green.
9. **User + environment simulation**: a simulated persona (NOVICE/EXPERT) chats with the agent while a "chaos dial" injects 503s and 5 s latency into the tools. A scoreboard of hallucination, task success and efficiency fills in live.
10. **The eval flywheel and CI gate**: a loop of prod traces, then the online judge, then a new failing case added to the evalset, then a PR. In the CI pipeline, a deterministic gate opens, then a rubric gate. A red run blocks deploy. Optionally an `adk optimize` (GEPA) arrow rewrites the prompt against a held-out validation set.

---

### Uncertainty log
- Rename dates for Vertex AI to Gemini Enterprise Agent Platform and for Agent Engine to Agent Runtime: [UNVERIFIED]. Current names are confirmed from docs page titles.
- The Agentspace to Gemini Enterprise date (2025-10-09) is from prior knowledge and was not re-fetched in this session: [UNVERIFIED].
- `adk eval --num_runs` flag; Python `Event(route=..., output=...)` combined; Python `JoinNode` fan-out syntax; a named managed "online evaluation" feature for Agent Runtime: [UNVERIFIED].
- The web search budget ran out mid-research. Google Cloud Next 2026 and I/O 2026 session titles were not verified, so none are cited.
