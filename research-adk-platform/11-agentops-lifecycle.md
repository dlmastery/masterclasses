# 11 - AgentOps: the agent lifecycle in production (Oct 2026)

Research date: 2026-10-23. Scope: AgentOps as practised on Google Cloud with ADK Python 2.x (latest **v2.13.0**, GitHub release 2026-10-23), **agents-cli** (which replaces Agent Starter Pack), **Agent Runtime** (the former Vertex AI Agent Engine, now under "Gemini Enterprise Agent Platform"), Cloud Trace, Cloud Logging and Cloud Monitoring, the BigQuery Agent Analytics plugin, and `adk optimize` (GEPA).

**How this was researched.** The web-search budget for this session ran out before this file was started. Every fact marked as verified comes from a direct WebFetch of a primary page on 2026-10-23, or from sibling research files in this repo (`research/01`, `03`, `05`, `06`) that were verified earlier the same day. Anything I could not confirm is marked **[UNVERIFIED]**. Canary, shadow and A/B rollout for agents have no first-party Google page dedicated to them. For those I describe the documented building blocks (Cloud Run revisions and tags, `eval compare`) and mark the agent-specific pattern as practice, not product.

Primary sources fetched:
- agents-cli docs home: https://google.github.io/agents-cli/
- agents-cli lifecycle: https://google.github.io/agents-cli/guide/lifecycle/
- agents-cli CLI reference: https://google.github.io/agents-cli/cli/
- agents-cli CI/CD: https://google.github.io/agents-cli/guide/cicd/
- agents-cli evaluation: https://google.github.io/agents-cli/guide/evaluation/
- agents-cli observability: https://google.github.io/agents-cli/guide/observability/
- Agent Starter Pack README (maintenance-mode notice): https://github.com/GoogleCloudPlatform/agent-starter-pack
- ASP deployment guide: https://googlecloudplatform.github.io/agent-starter-pack/guide/deployment.html
- ADK BigQuery Agent Analytics: https://adk.dev/integrations/bigquery-agent-analytics/ (old URL `google.github.io/adk-docs/observability/bigquery-agent-analytics/` returns a 301 redirect)
- ADK optimize (GEPA): https://adk.dev/optimize/
- Agent Runtime tracing: https://docs.cloud.google.com/agent-builder/agent-engine/manage/tracing (page title "Gemini Enterprise Agent Platform", last updated 2026-10-22)
- Agent Runtime monitoring: https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/runtime/monitoring (last updated 2026-10-22)
- Cloud Run rollouts, rollbacks and traffic migration: https://docs.cloud.google.com/run/docs/rollouts-rollbacks-traffic-migration (last updated 2026-10-22)
- GEPA paper: https://arxiv.org/abs/2507.19457

---

## 1. Definition: what AgentOps is

- **Google's definition** (Agents Companion whitepaper, Feb 2025, kaggle.com/whitepaper-agent-companion): AgentOps is "a subcategory of GenAIOps that focuses on the efficient operationalization of Agents". The things it versions and operates are tool management, the agent "brain" prompt, orchestration, memory and task decomposition. (Verified earlier today in `research/06`.)
- **The nesting**: DevOps (code) contains MLOps (models + data), which contains GenAIOps / LLMOps (prompts, foundation models, RAG), which contains AgentOps. AgentOps adds three things:
  - tools, which have side effects;
  - multi-step trajectories, which you evaluate as a path and not only as a final answer;
  - autonomy, which needs guardrails, identity and HITL.
- **Introduction to Agents** (Kaggle 5-Day Intensive, Day 1, Nov 2025) frames "Agent Ops" as four parts: KPIs, an LLM judge plus a golden set, OTel traces, and "feedback becomes tests". Source: a secondary summary in `research/06`.
- **Agent Quality** (Day 4, Nov 2025) describes an **Agent Quality Flywheel**: define quality, instrument, evaluate the process, feedback loop. In the feedback loop, "every production failure becomes a regression test in the golden set".
- **Prototype to Production** (Day 5, Nov 2025, kaggle.com/whitepaper-prototype-to-production): the Kaggle page loads but WebFetch returned only its title. The authors, page count and exact wording are **[UNVERIFIED]**. Secondary listings say it covers eval-gated CI/CD, security guardrails, deployment and A2A. A frequently quoted "Observe, Act, Evolve" operating loop is also attributed to it **[UNVERIFIED wording]**. Check the PDF before putting any quote on a slide.

**One-sentence definition for the deck**: AgentOps is the discipline of shipping non-deterministic, tool-using agents as versioned artefacts (code, prompt, tools, model, config), gated by trajectory-aware evals, and operated with traces, cost/latency SLOs and a feedback loop that turns production failures into new tests.

---

## 2. The lifecycle: build, evaluate, deploy, observe, improve

### 2.1 Google's official version: the agents-cli eight-phase lifecycle
Source: https://google.github.io/agents-cli/guide/lifecycle/

| # | Phase | agents-cli command(s) |
|---|---|---|
| 0 | Spec | none (write `.agents-cli-spec.md`) |
| 1 | Scaffold | `scaffold create` |
| 2 | Build | none (write the agent code) |
| 3 | Orchestrate | none (split work across specialist agents) |
| 4 | Evaluate | `eval run` (or `eval generate` + `eval grade`), `eval dataset synthesize`, `eval compare`, `eval analyze`, `eval metric list`, `eval optimize` |
| 5 | Deploy | `deploy` (`--dry-run`, `--no-wait`, `--status`) |
| 6 | Publish | `publish gemini` |
| 7 | Observe | none (enable `--bq-analytics` at scaffold time) |

The page describes the lifecycle as a loop driven by four verbs: **scaffold, eval, deploy, observe**. Production data feeds the next eval dataset.

Verbatim example sequence from the page:
```bash
agents-cli scaffold create outage-recovery-bot --agent adk --deployment-target agent_runtime
agents-cli playground
agents-cli eval run
agents-cli eval compare prev.json latest.json
agents-cli deploy --dry-run
agents-cli deploy
agents-cli publish gemini
```

### 2.2 The loop as a diagram (described for drawing)
A circular track with five stations, run clockwise:
1. **BUILD**: the ADK agent (code + instruction + tools + model id) lives in a Git repo. Artefact: a commit SHA.
2. **EVALUATE**: an eval set (golden cases + simulated users) runs through `adk eval`, pytest `AgentEvaluator`, or `agents-cli eval run`. Artefact: `grade_results.json`. A **gate** compares candidate scores against the baseline with `eval compare`.
3. **DEPLOY**: CI builds a container and pushes it to Artifact Registry. It deploys to **staging** and runs a load test. A **manual approval** follows, then the **same image** goes to **prod**. The rollout can be progressive (Cloud Run traffic split).
4. **OBSERVE**: OTel spans go to Cloud Trace. Logs go to Cloud Logging. Metrics go to Cloud Monitoring (`reasoning_engine/request_count`, `request_latencies`). Event rows go to BigQuery `agent_events` (Agent Analytics plugin). Prompt/response JSONL goes to GCS and the BigQuery `completions` table.
5. **IMPROVE**: failure clustering (`eval analyze`) produces new eval cases, which feed prompt optimisation (`adk optimize` / `agents-cli eval optimize`, GEPA). The result is a new commit, and the loop returns to BUILD.

A side arc from OBSERVE back to DEPLOY is labelled **"rollback"**. A side arc from OBSERVE to EVALUATE is labelled **"traces become test cases"**.

### 2.3 What has changed since 2025 (dates matter for the deck)
- **Agent Starter Pack (ASP) is in maintenance mode.** README, verbatim: "Active development has moved to agents-cli, the next evolution of Agent Starter Pack." and "ASP will continue to receive critical fixes only — no new features, no new templates, no new deployment targets." Migration guide: https://google.github.io/agents-cli/reference/from-agent-starter-pack/
- **agents-cli** is "CLI and skills for building agents on Google Cloud". It installs with `uvx google-agents-cli setup`, which also installs ADK skills into coding agents (Antigravity CLI, Claude Code, Codex). Announced around May 2026 (`research/08`). The docs page gives no launch date.
- **Product renames** (per `research/05`):
  - Vertex AI → Gemini Enterprise Agent Platform (Apr 2026).
  - Agent Engine → **Agent Runtime**. The docs still use `aiplatform.googleapis.com/ReasoningEngine` as the monitored resource, and the env var still says `AGENT_ENGINE`.
- **ADK 2.0 GA** was 2026-05-19. AgentOps-relevant releases since then:
  - 2.2.0 (2026-06-04): `AutoTracingPlugin`, native OTel `gen_ai.client.*` metrics.
  - 2.3.0 (2026-06-17): `GEPARootAgentOptimizer`.
  - 2.7.0 (2026-08-13): `pyarrow` moved to the `bigquery-analytics` extra.
  - 2.8.0 (2026-08-25): Model Armor plugin and `ADK_MAX_LLM_CALLS`.
  - 2.9.0 (2026-09-10): model failover.
  - 2.10.0 (2026-09-24): eval efficiency metrics. Also, `AgentEvaluator` now raises `ValueError` if zero cases ran.
  - 2.13.0 (2026-10-23): **BREAKING**. Telemetry defaults to the OTel GenAI v2 schema and the `call_llm` span is removed (opt out with `ADK_TELEMETRY_SCHEMA_VERSION_OPT_IN`).

---

## 3. CI/CD with eval gates (Google Cloud view)

### 3.1 Pipeline stages (same in ASP and agents-cli)
Sources: the ASP deployment guide and https://google.github.io/agents-cli/guide/cicd/
1. **CI on pull request**: unit and integration tests. Files: `.cloudbuild/pr_checks.yaml` or `.github/workflows/pr_checks.yaml` (ASP naming).
2. **Staging CD on merge to `main`**: build the container, push to Artifact Registry, deploy to staging, run an automated load test.
3. **Production**: requires **manual approval**, then "deploys the same container image that was tested in staging". The image is promoted, not rebuilt.

Setup commands:
```bash
# Agent Starter Pack (legacy, maintenance mode)
uvx agent-starter-pack setup-cicd
make setup-dev-env
make deploy

# agents-cli (current) - CI/CD guide form
agents-cli infra cicd \
  --staging-project my-staging-project \
  --prod-project my-prod-project

# agents-cli CLI-reference form (subcommand name in the reference)
agents-cli infra setup-cicd --dev-project D --staging-project S --prod-project P \
  --cicd-runner github_actions --apply      # without --apply only a Terraform plan is shown
```
The guide page writes `infra cicd`. The CLI reference lists `infra setup-cicd`. Run `agents-cli infra --help` to confirm which one your installed version uses **[naming discrepancy between two official pages]**.

- **Runner detection**: GitHub Actions is detected from `wif.tf` (Workload Identity Federation, keyless). Cloud Build is detected from the Terraform config, which also sets up a Cloud Build connection to GitHub.
- **Terraform variables** (`deployment/terraform/variables.tf`): `project_name`, `prod_project_id`, `staging_project_id`, `cicd_runner_project_id`, `region`, `repository_name`, `repository_owner`, `app_sa_roles`, `cicd_roles`.
  - The default `region` is documented as `us-west1` in the agents-cli guide, `us-east1` in the ASP guide, and `us-east1` for `create --region`. The discrepancy is in the docs.
- **Project topology**: dev, staging, prod and an optional CI/CD runner project. Four projects is the reference architecture.

### 3.2 Where the eval gate goes (and the documentation gap)
The agents-cli CI/CD and evaluation pages, and the CLI reference, **do not document a pass/fail eval threshold in the pipeline**. `eval grade` produces scores and `eval compare BASELINE CANDIDATE` produces a diff. You add the gate yourself. Two documented building blocks exist:

(a) **ADK pytest gate**: thresholds live in `test_config.json`. `AgentEvaluator` fails the test if a criterion falls below its threshold, and since v2.10 it raises `ValueError` when zero cases ran, which closes the "empty eval passes CI" hole. Source: https://adk.dev/evaluate/
```python
import pytest
from google.adk.evaluation.agent_evaluator import AgentEvaluator

@pytest.mark.asyncio
async def test_agent_regression():
    await AgentEvaluator.evaluate(
        agent_module="my_agent",
        eval_dataset_file_path_or_dir="tests/integration/fixture/my_agent/",
    )
```
```json
{"criteria": {
  "tool_trajectory_avg_score": {"threshold": 1.0, "match_type": "IN_ORDER"},
  "final_response_match_v2": {"threshold": 0.8,
     "judge_model_options": {"judge_model": "gemini-flash-latest", "num_samples": 5}},
  "safety_v1": 0.8
}}
```
(This is a condensed form of the adk.dev criteria example; see `research/06` §4.)

(b) **Candidate-vs-baseline regression gate** (this is a pattern, not a documented Google step): run `agents-cli eval run --output artifacts/candidate/` on the PR, download the `main` baseline artefact, then run `agents-cli eval compare baseline.json candidate.json`. Fail the build if any core metric drops by more than delta (for example 2 points), or if any "must-pass" case fails. Why use a delta rather than an absolute threshold: LLM-judge scores are noisy, so gate on regressions and keep absolute floors only for safety and must-pass cases.

**Efficiency as a gate**: ADK reports `tool_call_count_v1`, `inference_call_count_v1`, `token_usage_v1` and `invocation_duration_v1` on every eval. These are always reported and **never pass/fail** (v2.13 splits duration into model, tool and framework time). To gate on cost or latency, parse them in CI and compare them with the baseline yourself.

### 3.3 Cost of running evals in CI
The judge-based metrics (`final_response_match_v2`, `safety_v1`, `multi_turn_*`) call Gemini or the Agent Platform Gen AI Eval service, and `num_samples: 5` means five judge calls per criterion. `eval grade` defaults to `--qps 15.0`. Keep the PR suite small (smoke set, about 20-50 must-pass cases) and run the full suite nightly or before a release. This tiering is common practice, not a Google rule.

---

## 4. Versioning: prompts, agents, tools, models

An agent's behaviour = **code + instruction (prompt) + tool schemas/descriptions + model id/version + generation config + skills + eval set + judge config**. All of these must be versioned **together**, because changing any one of them changes the trajectory.

| Thing | How to version it on Google Cloud / ADK | Notes |
|---|---|---|
| Agent code + instruction | Git commit; container image digest in Artifact Registry | Prod promotes the **same image** that passed staging (ASP/agents-cli) |
| Instruction text | Lives in code (or ADK 2.7+ Jinja2 instruction templates). GEPA writes **new instruction text** that you commit | Keep prompts in files, not inline strings, so diffs are readable |
| Tools | Tool name + docstring/schema are part of the prompt. MCP servers should be pinned | ADK 2.10 added a skill lifecycle (`ADK_ENABLE_SKILL_LIFECYCLE=1`) |
| Model | Pin explicit model versions in prod; `gemini-flash-latest` aliases move underneath you | Doc examples use `-latest` for judges. Prefer pinned versions for the agent under test |
| Secrets | `agents-cli deploy --secrets ENV=SECRET:VERSION` pins a Secret Manager version | Verified in the CLI reference |
| Templates | `scaffold upgrade` does a 3-way merge to newer templates; `--base-template` accepts `@tag` refs | Verified in the CLI reference |
| Eval datasets | Versioned in Git (`tests/eval/datasets/*.json`). Old `*.evalset.json` files need migration | https://google.github.io/agents-cli/reference/eval-dataset-migration/ |
| Telemetry schema | `ADK_TELEMETRY_SCHEMA_VERSION_OPT_IN` (v2.13 breaking change) | Dashboards are versioned artefacts too |
| Session schema | `adk migrate session` | From the ADK CLI listing in `research/01` |

**Rule for the slide**: "A prompt change is a deploy." It goes through the same PR, eval gate and staged rollout as code.

---

## 5. Progressive delivery: canary, shadow, A/B, rollback

### 5.1 What exists as product (verified)
**Cloud Run revisions** are the documented progressive-delivery primitive (https://docs.cloud.google.com/run/docs/rollouts-rollbacks-traffic-migration). An ADK agent deployed with `adk deploy cloud_run` or `agents-cli deploy -d cloud_run` is a Cloud Run service, so these commands apply directly:
```bash
# 1. deploy the new agent revision with 0% traffic and a tag (gets its own URL)
gcloud run deploy myservice --image IMAGE_URL --no-traffic --tag TAG_NAME
# 2. canary: shift a slice of traffic
gcloud run services update-traffic SERVICE --to-revisions REVISION=PERCENTAGE
# 3. rollback: send 100% back to the previous known-good revision
gcloud run services update-traffic SERVICE --to-revisions REVISION=100
```
The tagged revision URL lets you run the eval suite against the **live candidate** before any user traffic reaches it, using `agents-cli eval run --url <tag-url>`. `--url` is documented on `eval run` and `eval generate`.

**Agent Runtime (Agent Engine)**: no traffic-splitting or revision-rollback feature was found in the pages fetched today **[UNVERIFIED either way]**. The practical pattern is blue/green: deploy a second Agent Runtime resource, then switch the client or gateway to the new resource id. Roll back by switching it back. `agents-cli deploy --update-only` updates an existing deployment in place, which gives fast deploys but no instant rollback.

### 5.2 Agent-specific patterns (practice; describe as such)
- **Canary for agents**: 1%, then 5%, then 25%, then 100%. Each step is held until the guard metrics are steady:
  - error rate (PromQL ratio below);
  - p99 latency;
  - tokens per invocation and tool calls per invocation, from the BigQuery `v_llm_response` and `v_tool_completed` views;
  - online LLM-judge score on sampled traffic;
  - user-feedback rate.

  Cloud Run splits traffic per request, which breaks multi-turn sessions. Use **session-sticky routing** (a header or tag-URL routing at the gateway) so that one conversation is never served by two prompt versions **[pattern; Cloud Run session affinity is cookie-based per instance, not per revision; verify for your setup]**.
- **Shadow (dark launch)**: mirror real user inputs to the candidate agent without returning its output to the user. Compare trajectories and answers offline with `eval grade` / `eval compare`. **Danger**: tools have side effects. The shadow agent must run with **read-only or stubbed tools** (for example a mock refund API, or `BigQueryToolConfig(write_mode=WriteMode.BLOCKED)`). Otherwise a shadow deploy issues a real refund.
- **A/B for agents**: split users rather than requests, and hold the assignment for the whole session. Primary metric: task success or resolution rate (an online judge such as `multi_turn_task_success`, plus business KPIs). Guardrail metrics: cost per resolved task, p95 latency, escalation-to-human rate, safety flags. You need far more samples than a classic UI A/B test, because judge noise adds variance. **Pairwise judging** (candidate vs control on the same input), which the Agent Quality whitepaper recommends over 1-5 scores, needs fewer samples.
- **Rollback triggers** (write these down before launch): the error-rate SLO is breached; p99 is above X; tokens per invocation is more than 1.5x baseline (a loop signature); any safety or Model Armor block spike; the judge score drops more than delta; the tool-error rate for one `tool_origin` spikes (for example an MCP server change upstream).

### 5.3 Error-rate alert (verbatim PromQL from the Agent Runtime monitoring docs)
```promql
sum_over_time(
      sum(
        rate(
          aiplatform_googleapis_com:reasoning_engine_request_count{
            monitored_resource='aiplatform.googleapis.com/ReasoningEngine',
            reasoning_engine_id='RESOURCE_ID',
            response_code='500'
          }
          [10m]
        )
      )
      [10m:10m]
    )
    /
    sum_over_time(
      sum(
        rate(
          aiplatform_googleapis_com:reasoning_engine_request_count{
            monitored_resource='aiplatform.googleapis.com/ReasoningEngine',
            reasoning_engine_id='RESOURCE_ID',
          }
          [10m]
        )
      )
      [10m:10m]
    )
```
The same page's latency alert guidance: Request Latency, a rolling 5-minute window, the **99th percentile**, and a threshold such as **5000 ms**.

---

## 6. Observability stack (what to switch on)

### 6.1 Agent Runtime telemetry (verbatim env vars)
Source: https://docs.cloud.google.com/agent-builder/agent-engine/manage/tracing
```python
env_vars = {
      "GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY": "true",
      "OTEL_SEMCONV_STABILITY_OPT_IN": "gen_ai_latest_experimental",
      "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT": "EVENT_ONLY",
    }
```
- `..._ENABLE_TELEMETRY` turns on traces, logs and metrics, but **excludes prompt/response content**. The docs recommend it over the older `enable_tracing` flag.
- `CAPTURE_MESSAGE_CONTENT` logs prompts, responses and `user.id`. The docs say to confirm end-user consent and data-handling policies first. `user.id` logging applies to opt-ins made from **2026-05-22 with ADK 2.1**; earlier deployments must redeploy and opt in again.
- The Telemetry API (traces) and Cloud Logging API (logs) must be enabled.
- In the console, open Agent Platform, then Deployments, select the instance, and open the **Traces** tab (Session view or Span view). Attribute values may be truncated at Cloud Trace quota limits.

### 6.2 Built-in metrics (verbatim names)
Monitored resource `aiplatform.googleapis.com/ReasoningEngine`:
- `aiplatform.googleapis.com/reasoning_engine/request_count`, with labels `response_code` and `response_code_class`
- `aiplatform.googleapis.com/reasoning_engine/request_latencies`
- `aiplatform.googleapis.com/reasoning_engine/cpu/allocation_time`
- `aiplatform.googleapis.com/reasoning_engine/memory/allocation_time`

Resource labels: `resource_container`, `location`, `reasoning_engine_id`, `project_id`. With ADK **2.6.0+** and the telemetry env var set, the agent also exports OTel GenAI metrics to Cloud Monitoring as user-defined metrics. The docs also show a log-based counter metric, `tool_calling_count`, built with a regex over `textPayload`.

### 6.3 agents-cli defaults (privacy-by-default split)
Source: https://google.github.io/agents-cli/guide/observability/

| Environment | Cloud Trace spans | Prompt-response logging |
|---|---|---|
| Local (`agents-cli playground`) | on, no content | off |
| Deployed via Terraform | on, no content | **on**: full prompts/responses to GCS JSONL + BigQuery `completions` table |
| Bare `agents-cli deploy` (no bucket) | on, no content | off |

Switches:
- `LOGS_BUCKET_NAME` enables prompt-response logging.
- `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT` defaults to `NO_CONTENT`.
- `ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=false` keeps content out of spans.

The design principle is "full content in GCS/BigQuery, no content in traces". Traces are widely readable; content stores are access-controlled.

### 6.4 OTel span tree (ADK, GenAI semconv)
Spans: `invoke_agent {agent}`, `invoke_workflow {workflow}` (2.0 graphs), `generate_content {model}`, `execute_tool {tool}`. Key attributes: `gen_ai.agent.name`, `gen_ai.conversation.id`, `gen_ai.request.model`, `gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens`. v2.13 removes `call_llm`, so **update any dashboard that filters on it**. Local export: `adk web --otel_to_cloud` or `agents-cli playground --otel-to-cloud`.

### 6.5 BigQuery Agent Analytics plugin (the AgentOps data lake)
Source: https://adk.dev/integrations/bigquery-agent-analytics/
- Supported in Python **v1.21.0+**, Java v1.5.0+ and Kotlin v0.8.0+. ADK 2.0 workflow events and `event_id` need Python **v2.7.0+**.
- Writes through the **BigQuery Storage Write API**, which is a paid service.
- agents-cli: `create --bq-analytics`.
```python
# pip install "google-adk[bigquery-analytics]>=2.7.0"
from google.adk.apps import App
from google.adk.plugins.bigquery_agent_analytics_plugin import BigQueryAgentAnalyticsPlugin

plugin = BigQueryAgentAnalyticsPlugin(project_id="your-gcp-project-id",
                                      dataset_id="your-big-query-dataset-id")
app = App(name="my_agent", root_agent=root_agent, plugins=[plugin])
```
(These identifiers are verbatim from the docs. The line layout is condensed.)

- **Config** (`BigQueryLoggerConfig`):
  - which events to log: `event_allowlist` / `event_denylist`;
  - large content: `gcs_bucket_name` (offload), `max_content_length` (default 500 KB inline);
  - write tuning: `batch_size`, `batch_flush_interval`, `shutdown_timeout`;
  - masking and views: `content_formatter` (PII masking), `create_views`, `view_prefix`;
  - delivery: `exactly_once_delivery` (reduces duplicates but is not lossless), `flush_on_run_end`;
  - other: `payload_column_denylist`, `enable_otel_correlation`, `final_response_tool_names`.
- **Table** `agent_events`: partitioned by date and clustered by `event_type`, `agent`, `user_id`. Columns: `timestamp`, `event_id`, `event_type`, `agent`, `session_id`, `invocation_id`, `user_id`, `trace_id`, `span_id`, `parent_span_id`, `content` (JSON), `content_parts`, `attributes`, `latency_ms` (JSON), `status`, `error_message`, `is_truncated`.
- **Event types**:
  - LLM: `LLM_REQUEST`, `LLM_RESPONSE`, `LLM_ERROR`.
  - Tools: `TOOL_STARTING`, `TOOL_COMPLETED`, `TOOL_ERROR`, `TOOL_PAUSED`.
  - Agent and invocation: `USER_MESSAGE_RECEIVED`, `INVOCATION_*`, `AGENT_*`.
  - State and HITL: `STATE_DELTA`, `HITL_*_REQUEST` and their `_COMPLETED` counterparts.
  - A2A: `A2A_INTERACTION`.
  - ADK 2.0 workflows: `AGENT_TRANSFER`, `AGENT_STATE_CHECKPOINT`, `EVENT_COMPACTION`, `NODE_OUTPUT`, `NODE_ERROR`.
- Tool events carry `tool_origin` (LOCAL, MCP, SUB_AGENT, A2A, TRANSFER_AGENT), which lets you blame an upstream MCP server.
- **Views**: one per event type, `{prefix}_{event_type}` (for example `v_llm_response`). `v_llm_response` exposes `usage_total_tokens`, `usage_prompt_tokens`, `usage_completion_tokens`, `total_ms` and `ttft_ms`. `v_tool_completed` has `tool_name`, `tool_origin` and `total_ms`.
- **Limitations**:
  - The plugin emits no OTel spans of its own. `trace_id` is inherited from the active span, or generated per invocation as a fallback.
  - Batches can drop after retries are exhausted. Monitor drop reasons and deduplicate on `event_id`.
  - Java emits only `TOOL_PAUSED` from the 2.0 workflow events.
  - Kotlin logs only invocation start and end.

SLO queries built on the documented views and columns. **The SQL is my composition, not verbatim; the views and columns are verified**:
```sql
-- Daily token SLO per agent (p50/p95 tokens per LLM call)
SELECT DATE(timestamp) AS day, agent,
       APPROX_QUANTILES(usage_total_tokens, 100)[OFFSET(50)] AS p50_tokens,
       APPROX_QUANTILES(usage_total_tokens, 100)[OFFSET(95)] AS p95_tokens,
       AVG(ttft_ms) AS avg_ttft_ms
FROM `proj.agent_logs.v_llm_response`
GROUP BY day, agent ORDER BY day DESC;

-- Slowest tools, split by origin (find the bad MCP server)
SELECT tool_name, tool_origin, COUNT(*) n, AVG(total_ms) avg_ms
FROM `proj.agent_logs.v_tool_completed`
GROUP BY tool_name, tool_origin ORDER BY avg_ms DESC;

-- Dedup pattern (verbatim clause from docs)
-- QUALIFY event_id IS NULL
--   OR ROW_NUMBER() OVER (PARTITION BY event_id ORDER BY timestamp) = 1;
```

---

## 7. SLOs for agents: cost, latency, tokens, quality

| SLI | Source | Example SLO (illustrative) |
|---|---|---|
| Availability (non-5xx share) | `reasoning_engine/request_count` by `response_code_class` | 99.5% / 28 days |
| End-to-end latency p99 | `reasoning_engine/request_latencies` | < 5 s (the docs' example alert threshold is 5000 ms) |
| Time to first token | `v_llm_response.ttft_ms` | p95 < 1.5 s for chat UX |
| Tokens per invocation | `v_llm_response.usage_*`; eval `token_usage_v1` | p95 within 1.3x of baseline |
| LLM calls per invocation | eval `inference_call_count_v1`; hard cap `ADK_MAX_LLM_CALLS` (ADK 2.8) | Hard cap stops runaway loops |
| Tool error rate | `v_tool_error` by `tool_origin` | < 1% per tool |
| Cost per resolved task | tokens x price / resolved count (join with task-success label) | Business-owned budget |
| Quality (online) | sampled LLM-judge on production traces (the agents-cli docs list "LLM-as-judge scoring on production traffic" as a BQ analytics use) | Judge score >= baseline - delta |
| Safety | Model Armor blocks (`custom_metadata['model_armor_blocked']`), `safety` metric | Alert on spike |

Teaching points:
- For agents, **cost is a reliability metric**. A loop does not show up as an error; it shows up as tokens per invocation going up 10x.
- "Up to 8x faster execution turns for string-model agents" (ADK 2.13 notes) and "40% faster time-to-first-model-request in long sessions" (2.12) are framework-level latency wins. Re-baseline your latency SLOs after upgrading.

---

## 8. Incident response for agents

**What makes agent incidents different**:
- the failure is often *semantic*: wrong answer, wrong tool, a policy violation, with HTTP 200;
- the cause is often *external*: a model alias moved, an MCP server changed its schema, a retrieval index drifted, or a prompt injection arrived in tool output;
- the blast radius includes *side effects*: refunds issued, emails sent.

Runbook (in the order you would draw it):
1. **Detect**: alerts on error rate, p99, token spikes, tool-error spikes, Model Armor blocks, a judge-score drop, or a jump in thumbs-down.
2. **Triage with traces**: find the `trace_id`, open the span tree in Cloud Trace, and query BigQuery `WHERE trace_id = '...' ORDER BY timestamp`. Locate the first bad span: `generate_content` (model), `execute_tool` (tool) or a sub-agent.
3. **Contain** (fastest lever first):
   - shift traffic back to the previous revision (`update-traffic --to-revisions PREV=100`);
   - disable a tool or skill;
   - switch to a fallback model (model failover, ADK 2.9);
   - lower `ADK_MAX_LLM_CALLS`;
   - force escalation to a human (`ForceEscalationPlugin`, 2.13);
   - make Model Armor fail-closed.
4. **Assess the side effects**: query `TOOL_COMPLETED` rows for the write tools in the incident window, and reverse transactions where possible.
5. **Root cause**: run `eval analyze --eval-result ...` to cluster failures. Diff the prompt, model, tool and image versions between the good and bad deploys.
6. **Learn**: turn every incident trace into a **regression eval case** (golden trajectory + expected answer). Add it to the must-pass set, and only then ship the fix (the Agent Quality flywheel).

The agents-cli lifecycle page names the kinds of failure the loop is meant to catch: "hallucinated remediations" and "tool API changes".

---

## 9. Feedback loop: production traces become eval sets

Documented pieces:
- the BigQuery `agent_events` / `completions` tables (full content);
- `agents-cli eval generate` / `eval grade`, which operate on traces, so you can **re-grade stored traces without re-running the agent**;
- `eval dataset synthesize`, which generates synthetic multi-turn cases with a user simulator (`-n 3` default, `--max-turns 5`);
- `adk web` "Add current session", which freezes a session into an evalset;
- `adk eval_set generate_eval_cases`, which auto-generates scenarios;
- `eval analyze`, which clusters failures by theme (`--metric multi_turn_task_success|multi_turn_tool_use_quality`).

**Gap**: the agents-cli evaluation page explicitly **does not cover** a one-command path from production traces to an eval dataset. You build it yourself.

Pipeline in words, for a diagram:
- BigQuery query (thumbs-down, low judge score, escalations, tool errors) → sample N traces per week → **PII scrub** (`content_formatter` at log time, plus a DLP pass) → human labels the correct trajectory and answer → convert to the dataset format (`tests/eval/datasets/*.json`) → PR → the case joins the regression gate.
- Split the cases: a **train** set for the optimizer, a **validation** set for selecting the optimizer's best candidate, and a **held-out** set that the CI gate uses and that the optimizer never sees. Otherwise you overfit prompts to your tests.

---

## 10. Prompt and agent optimisation: `adk optimize` (GEPA)

Source: https://adk.dev/optimize/ (support stated as ADK Python **v1.24.0+**; `GEPARootAgentOptimizer` arrived in 2.3.0, 2026-06-17).

```bash
adk optimize [OPTIONS] AGENT_MODULE_FILE_PATH
adk optimize contributing/samples/core/hello_world \
  --sampler_config_file_path contributing/samples/core/hello_world/sampler_config.json
# options: --optimizer_config_file_path PATH, --print_detailed_results, --log_level
```
`sampler_config.json` (verbatim):
```json
{
  "eval_config": {
    "criteria": {
      "response_match_score": 0.75
    }
  },
  "app_name": "hello_world",
  "train_eval_set": "train_eval_set"
}
```
Optional fields: `train_eval_case_ids`, `validation_eval_set`, `validation_eval_case_ids`. If you give no validation set, the train set is reused, which is an overfitting risk. Say this on the slide.

**Optimizers**:
- `GEPARootAgentPromptOptimizer` (the default) optimizes only the root agent's instruction.
- `GEPARootAgentOptimizer` optimizes the root instruction plus the instructions of skills in a `SkillToolset`.
- `SimplePromptOptimizer` runs a single sequential refine loop instead of keeping a pool of candidates.
- Neither GEPA optimizer touches sub-agents or agent tools. Both are **experimental**: they warn when constructed and their API may change.

**GEPA config fields**:
- `optimizer_model`;
- `model_configuration`, which defaults to a 10K thinking budget for the prompt optimizer and `ThinkingLevel` HIGH for the full optimizer;
- `max_metric_calls` (default **100**);
- `reflection_minibatch_size` (default **3**);
- `run_dir` (warm starts).

**How it works (a loop to animate)**:
1. The sampler runs the candidate agent on the train eval set via `LocalEvalService`.
2. It scores the runs with the configured criteria.
3. It returns per-example scores plus trajectories (`UnstructuredSamplingResult`).
4. A reflection LLM reads the failing trajectories in minibatches of 3 and proposes an edited instruction.
5. The candidates are scored on the validation set.
6. The candidate pool evolves until `max_metric_calls` is used up.
7. You take the best candidate and **commit it through the normal PR + eval gate**.

agents-cli wrapper: `agents-cli eval optimize --dataset ... --target-metric ... --config tests/eval/optimization_config.json` (experimental; runs `adk optimize`). The guide warns that runs take "minutes to several hours". Use it only after manual prompt fixes have plateaued.

**GEPA paper**: "GEPA: Reflective Prompt Evolution Can Outperform Reinforcement Learning", Agrawal et al. (with Khattab, Zaharia, Stoica, Klein, Potts, Dimakis and others). arXiv:2507.19457, v1 25 Jul 2025, v2 14 Feb 2026. Abstract: "Across six tasks, GEPA outperforms GRPO by 6% on average and by up to 20%, while using up to 35x fewer rollouts." It also "outperforms the leading prompt optimizer, MIPROv2, by over 10% (e.g., +12% accuracy on AIME-2025)". The core idea is reflective mutation in natural language plus Pareto-front candidate selection.

---

## 11. Failure modes (AgentOps-specific)

1. **Silent model drift**: a `-latest` alias moves and trajectories change with no deploy. Fix: pin versions, and run the nightly eval against prod.
2. **Empty eval passes CI**: fixed in ADK 2.10 (`ValueError` when zero cases ran). Older pipelines are still exposed.
3. **Telemetry schema break**: v2.13 removes `call_llm`, so dashboards and alerts that filter on it go blank. Detection itself becomes an outage.
4. **Shadow deploy with live tools**: side effects get duplicated. Fix: stubbed or read-only tools.
5. **Per-request canary on multi-turn sessions**: one conversation hits two prompt versions, giving incoherent state. Fix: session-sticky routing.
6. **Optimizer overfitting**: GEPA without a validation set reuses the train set. The gate must use held-out cases.
7. **Judge noise mistaken for regression**: single-sample judges flap. Use `num_samples` (majority vote), pairwise comparison, and delta gates.
8. **Content leak through traces**: prompts in spans are visible to anyone with Trace access. Use the agents-cli default (no content in spans) and keep full content only in access-controlled BQ/GCS. Get consent before turning on `CAPTURE_MESSAGE_CONTENT`.
9. **Analytics data loss**: BQ plugin batches drop after retries are exhausted, and `exactly_once_delivery` is not lossless. Monitor drop stats and deduplicate on `event_id`.
10. **Runaway loop cost**: no error, just a token bill. Fix: `ADK_MAX_LLM_CALLS` plus a tokens-per-invocation alert.
11. **Upstream tool/MCP change**: tool errors spike in one `tool_origin`. Pin MCP server versions and run contract tests.
12. **Rebuild between staging and prod**: the binary you tested is not the one you ship. ASP and agents-cli promote the same image; keep it that way.
13. **Deploy-path mismatch**: one codelab reports that `agents-cli deploy` and `adk deploy agent_engine` create different resource shapes **[UNVERIFIED]**.

---

## 12. Codelabs and hands-on resources

(Verified URLs from `research/03` and `research/06` unless marked.)
- **Evaluating Agents with ADK**: https://codelabs.developers.google.com/adk-eval/instructions (starter repo https://github.com/cuppibla/adk_eval_starter). Covers evalsets, `adk eval` and pytest gates.
- **Stateful Data Science Agent on Agent Runtime** (Next '26): https://codelabs.developers.google.com/next26/adk-deploy-scale. About 35 minutes, under $5. Covers Memory Bank and Cloud Trace.
- **Building a Production AI Code Review Assistant with Google ADK**: https://codelabs.developers.google.com/adk-code-reviewer-assistant/instructions. Compares local, Cloud Run and Agent Engine deployment.
- **Build an Agentic Pitch Generator: Orchestration, Evaluation, and Analytics with Google Cloud**: https://codelabs.developers.google.com/bwg-agentic-masterclass
- **Production-Ready AI Roadshow: building a multi-agent system**: https://codelabs.developers.google.com/codelabs/production-ready-ai-roadshow/1-building-a-multi-agent-system/building-a-multi-agent-system
- **Governing agentic workloads with Agent Gateway**: https://codelabs.developers.google.com/cloudnet-agent-gateway
- **Securing cross-cloud agentic enterprise deployments** (OTel, private networking): https://codelabs.developers.google.com/next26/aiinfra-learning-pod/screen1-securing-cross-cloud-agentic
- **agents-cli hands-on tutorial**: https://google.github.io/agents-cli/guide/hands-on-tutorial/ (listed in the site navigation; content not fetched)
- **Kaggle 5-Day AI Agents Intensive**: https://www.kaggle.com/learn-guide/5-day-agents. Day 4 is the Agent Quality whitepaper (https://www.kaggle.com/whitepaper-agent-quality). Day 5 is Prototype to Production (https://www.kaggle.com/whitepaper-prototype-to-production; content [UNVERIFIED]).

---

## 13. Interview questions (crisp answers)

1. **How is AgentOps different from MLOps?** MLOps versions models and data. AgentOps also has to version prompts, tool schemas and orchestration, evaluate *trajectories* rather than only outputs, and govern side-effecting actions with identity, guardrails and HITL. Google calls it "a subcategory of GenAIOps".
2. **What goes into an agent "version"?** Code, instruction, tool schemas/descriptions, model id, generation config, skills, plus the eval set and judge config that certified it. Shipping the same container image digest from staging to prod is how you freeze it.
3. **Where is the eval gate in Google's reference pipeline?** Unit and integration tests run on PRs, a load test runs in staging, and prod needs a manual approval. A quality threshold gate is *not* built in. You add one with `AgentEvaluator` thresholds or `eval compare` baseline-vs-candidate deltas.
4. **Why gate on a delta and not an absolute score?** Judge scores are noisy and drift with the judge model. A regression delta against the current `main` baseline catches real regressions. Absolute floors are reserved for safety and must-pass cases.
5. **How would you canary an agent on Cloud Run?** Deploy with `--no-traffic --tag`, run evals against the tag URL, then shift traffic with `update-traffic --to-revisions REV=5`, keep sessions sticky, watch error rate, p99, tokens per invocation and judge score, then ramp or roll back with `REV_PREV=100`.
6. **What's the main risk of shadow testing an agent?** Duplicated side effects. Shadow agents need stubbed or read-only tools.
7. **Name three agent SLIs a web SRE wouldn't track.** Tokens per invocation, LLM calls per invocation, and online judge or task-success score. Tool error rate by `tool_origin` is a fourth.
8. **How do you stop a runaway loop in production?** A hard cap (`ADK_MAX_LLM_CALLS`), an alert on tokens per invocation, and in workflows an `abort_signal` (ADK 2.11) plus a fallback to escalation.
9. **What does the BigQuery Agent Analytics plugin give you that Cloud Trace doesn't?** Durable, SQL-queryable event rows (LLM, tool, HITL, A2A and workflow events with tokens, latency and `tool_origin`), joinable with business data, for dashboards, offline eval and online judging. Trace is for per-request debugging.
10. **What does GEPA optimise in ADK, and what doesn't it touch?** By default, the root agent's instruction. `GEPARootAgentOptimizer` also covers skill instructions. It does not touch sub-agents or agent tools. It is experimental, with `max_metric_calls` defaulting to 100.
11. **How do you avoid overfitting prompts with an optimizer?** Separate train, validation and held-out sets. Set `validation_eval_set` explicitly (otherwise the train set is reused), and gate on the held-out set the optimizer never sees.
12. **What changed in ADK 2.13 that could break your monitoring?** The OTel GenAI v2 schema is now the default and the `call_llm` span is gone. Update dashboards or set `ADK_TELEMETRY_SCHEMA_VERSION_OPT_IN`.
13. **What happens to every production incident afterwards?** It becomes a regression eval case before the fix ships (the Agent Quality flywheel).

---

## 14. Slide ideas (with animation)

1. **"AgentOps ⊂ GenAIOps ⊂ MLOps ⊂ DevOps"**: nested rounded rectangles. Animate each ring zooming in, with the new artefacts appearing per ring (code, then data and model, then prompt and RAG, then tools, trajectories and autonomy).
2. **The loop**: a five-station circular track (Build, Evaluate, Deploy, Observe, Improve), with an agent token travelling around it. On the second lap, "rollback" (Observe to Deploy) and "traces become tests" (Observe to Evaluate) shortcut arcs light up.
3. **agents-cli phases 0-7**: a horizontal timeline of command chips (`scaffold create`, `eval run`, `deploy`, `publish gemini`). A banner sweeps in: "ASP is now in maintenance mode, so use agents-cli".
4. **Same image, three projects**: dev, staging and prod boxes. One container icon (with a digest hash) slides from staging to prod past a "manual approval" turnstile. A crossed-out "rebuild" arrow fades away.
5. **Eval gate as a turnstile**: baseline vs candidate bar charts from `eval compare`. One metric drops more than delta, the turnstile closes red, and the PR is blocked.
6. **Canary dial**: a traffic gauge going 0, 1, 5, 25, 100% with four guard needles (errors, p99, tokens per invocation, judge score). On a bad run the token needle spikes and the dial snaps back to 0 (`--to-revisions PREV=100`).
7. **Shadow-mode trap**: the user's request forks to prod and shadow. The shadow's "issue_refund" tool flashes red, then gets wrapped in a "stub" glove.
8. **The BigQuery event lake**: span tree on the left, `agent_events` rows filling in on the right (`LLM_RESPONSE`, `TOOL_COMPLETED` with `tool_origin=MCP`). A SQL query highlights the slowest MCP tool.
9. **Incident runbook as a five-step ladder**: Detect, Triage (trace), Contain (rollback, failover, escalate), Side-effect audit, Learn (new eval case). The final step drops a card into the "must-pass" deck.
10. **GEPA evolution**: a pool of prompt cards. A reflection LLM reads three failing trajectories, edits one card, and the scores update on a Pareto front. The best card goes into a PR, which still has to pass the gate. Caption: "+6% avg vs GRPO with up to 35x fewer rollouts (arXiv 2507.19457)".
