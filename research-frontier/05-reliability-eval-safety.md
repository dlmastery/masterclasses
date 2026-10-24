# 05 - Agent Reliability, Evaluation and Safety (frontier view, Oct 2026)

Research date: 2026-10-23. Scope: what top labs and practitioners ship **now** (mid-2025 to Oct 2026). Companion to `research/06-eval-observability-safety.md`, which holds the full ADK metric catalogue and plugin API. This file covers the cross-lab frontier and maps each idea onto Google ADK 2.x (current `google-adk` **2.13.0**, 2026-10-23; 2.0 GA 2026-05-19).

Method note: the WebSearch budget ran out partway through. Everything below was checked with WebFetch against the primary page cited, or taken from the project's own verified notes (`research/01-adk2-whats-new.md`, `research/06-...`). Anything not checked this way is marked **[UNVERIFIED]**.

---

## 0. The one-slide thesis

Old picture (2023-24): one ReAct loop, a system prompt that says "be safe", and a vibe check on a few demo chats.

What labs build now:
1. **Eval-driven development.** Evals come first, a few dozen tasks taken from real failures, gated in CI. Every production failure becomes a regression case.
2. **Grade the outcome and the trace.** Check the final environment state with deterministic code, grade the trajectory with rubric LLM judges, and report pass^k for consistency, not pass@1.
3. **Simulated users.** An LLM plays the user (with personas) in multi-turn, dual-control environments (tau2-bench, ADK user simulation).
4. **OpenTelemetry GenAI traces** as the shared substrate for debugging, grading and cost accounting.
5. **Security by architecture, not by detection.** Prompt injection is treated as unsolved. Agents are designed so that a successful injection can't do much damage: Rule of Two, CaMeL / dual-LLM, sandboxing, least-privilege identities, human approval on the risky edge only.
6. **Cost and latency as reliability properties.** Cache-friendly context, deterministic workflow nodes instead of LLM hops, model routing and failover, and hard call budgets.

---

## 1. Eval-driven agent development (EDD)

**Definition.** You write the eval suite before or alongside the agent and treat it as the spec. Changes to prompts, tools, models or the harness ship only if capability evals improve and regression evals stay near 100%.

**Primary source.** Anthropic Engineering, *"Demystifying evals for AI agents"*, **Jan 9, 2026**, Mikaela Grace, Jeremy Hadfield, Rodrigo Olivares, Jiri De Jonghe. https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents

Vocabulary from that post (use these exact terms on the slide):
- **Task**: one test with inputs and success criteria. **Trial**: one attempt (run several, because outputs vary). **Grader**: logic that scores one aspect. **Transcript / trace / trajectory**: the full record of a trial. **Outcome**: the final environment state ("whether a reservation actually exists in a database, not just whether the agent said it was booked").
- **Agent harness (scaffold)**: "evaluating 'an agent' means evaluating the harness and model together."
- **Capability evals** start at a low pass rate (a hill to climb). **Regression evals** sit near 100%. A capability eval "graduates" into the regression suite once it saturates.

Roadmap (condensed from the post): (0) start early, **20-50 tasks from real failures** is enough; (1) convert manual checks and bug reports into tasks; (2) write unambiguous tasks with reference solutions; (3) balance the set, testing both when a behaviour should occur and when it shouldn't; (4) start every trial from a clean, isolated environment; (5) prefer deterministic graders, add LLM graders where needed, validate with humans; (6) **read the transcripts**; (7) watch for saturation; (8) maintain the suite long term with a dedicated owner.

Numbers worth a slide:
- Opus 4.5 scored **42% on CORE-Bench** before grading bugs were fixed and **95%** after fixes and a less constrained scaffold. The eval was broken, not the model.
- **0% pass@100** almost always means a broken task.
- pass^k arithmetic: 75% per trial over 3 trials gives pass^3 = 0.75^3, about **42%**.

Quotes:
- "A good task is one where two domain experts would independently reach the same pass/fail verdict."
- "grade what the agent produced, not the path it took"
- "Evals give the whole team a clear hill to climb"
- "Read the transcripts!"

**Why it replaced older approaches.** "Vibe-check plus a public benchmark" can't catch regressions in a multi-step, non-deterministic system. Fixing one production failure silently breaks another, which Anthropic calls "reactive loops".

**Google framing.** The *Agent Quality* whitepaper (Kaggle 5-Day Agents Intensive, Nov 2025) describes the **Agent Quality Flywheel**: define quality, instrument, evaluate the process, feed failures back as regression tests. Quote: "Agent quality is an architectural pillar, not a final testing phase."

**ADK 2.x implementation (CI gate):**
```python
# tests/test_agent_eval.py -- runs in CI on every PR
import pytest
from google.adk.evaluation.agent_evaluator import AgentEvaluator

@pytest.mark.asyncio
async def test_refund_agent_regressions():
    await AgentEvaluator.evaluate(
        agent_module="refund_agent",
        eval_dataset_file_path_or_dir="tests/evals/regression.evalset.json",
        num_runs=3,              # several trials per task, for consistency
    )
```
Behaviour to know: since ADK **v2.10.0**, `AgentEvaluator.evaluate` raises `ValueError` if zero eval cases ran, where it used to pass silently, a classic "green but empty" CI failure. Efficiency metrics (`tool_call_count_v1`, `inference_call_count_v1`, `token_usage_v1`, `invocation_duration_v1`) are always reported (v2.10.0). In v2.13.0 duration is split into model, tool and framework time.

**Failure modes.** Saturated evals that give no signal. Leakage, where eval tasks get copied into prompts. Tests that are one-sided (only "should call tool", never "should not"). Shared state between trials causing correlated failures. Treating a grader bug as an agent bug (the CORE-Bench story).

---

## 2. Trajectory evals: outcome first, then the path

**Definition.** Grade the sequence of tool calls, arguments and intermediate steps, not just the final text.

**The 2026 nuance (the interview point).** Rigid step-matching is out of favour as the main signal. Anthropic advises grading outcomes and allowing partial credit, because agents find valid alternative paths. Google's *Agent Quality* paper states the same order as **"Outside-In"**: black-box task success first, then open the box for diagnosis (planning, tool selection and parameters, interpretation of tool responses, RAG, efficiency, multi-agent dynamics). Its slogan, "The Trajectory is the Truth", is about diagnosis and safety, not about requiring one exact path.

Trajectory checks that do belong in gates:
- **Safety-critical ordering**: `verify_identity` must come before `issue_refund`.
- **Forbidden calls**: never `delete_*` in this scenario.
- **Argument correctness**: the right `order_id`, an amount within policy.
- **Efficiency budgets**: under N tool calls and under M tokens.

**ADK:** `tool_trajectory_avg_score` with `match_type` = `EXACT` | `IN_ORDER` | `ANY_ORDER`. Use `IN_ORDER` or `ANY_ORDER` for most cases and `EXACT` only for strict, regulated flows. Rubric metrics `rubric_based_tool_use_quality_v1` and `rubric_based_multi_turn_trajectory_quality_v1` grade the path without a single reference.

**OpenAI equivalent:** **Trace grading**, "assigning structured scores or labels to an agent's trace", run at scale as trace evals in the dashboard. https://developers.openai.com/api/docs/guides/trace-grading

**Failure mode.** Over-specified expected trajectories punish better plans. When the model improves, the "pass rate" drops and teams roll back a better model.

---

## 3. LLM-as-judge with rubrics

**Definition.** A (usually cheaper) model scores outputs or traces against explicit, dimension-specific rubrics. It is calibrated against human labels and sampled several times to reduce variance.

2026 best practice, cross-checked across Anthropic and Google:
1. **One judge per dimension.** Use isolated judges for correctness, groundedness and tone, not one "rate 1-10" prompt (Anthropic).
2. **Escape hatch.** "give the LLM a way out, like providing an instruction to return 'Unknown' when it doesn't have enough information." (Anthropic)
3. **Calibrate against humans**, then spot-check periodically. Human graders mostly exist to grade the grader. ("Evaluating the evaluator", Agents Companion, Feb 2025.)
4. **Prefer pairwise win-rate over absolute 1-5 scores** (Agent Quality whitepaper, Nov 2025).
5. **Sample and vote.** ADK `judge_model_options.num_samples: 5` samples the judge five times and takes the majority.
6. **Agent-as-a-Judge.** The judge reads the whole trace, not just the answer (Agent Quality).

ADK rubric config (shape verified at adk.dev/evaluate/criteria):
```json
{
  "criteria": {
    "rubric_based_final_response_quality_v1": {
      "threshold": 0.8,
      "judge_model_options": {"judge_model": "gemini-flash-latest", "num_samples": 5},
      "rubrics": [
        {"rubric_id": "policy_cited",
         "rubric_content": {"text_property": "The response states the refund policy clause it relied on."}},
        {"rubric_id": "no_overpromise",
         "rubric_content": {"text_property": "The response does not promise a refund before issue_refund succeeded."}}
      ]
    },
    "hallucinations_v1": {"threshold": 0.8, "evaluate_intermediate_nl_responses": true}
  }
}
```

**Why it replaced older approaches.** ROUGE and BLEU punish correct paraphrases. In the ADK eval codelab, correct answers scored ROUGE 0.55-0.68 (see `research/06`). Pure human review doesn't scale.

**Failure modes.** Self-preference bias (the judge favours its own model family). Position and verbosity bias in pairwise comparisons. Judge drift when the judge model version changes, so pin judge versions. Rubric gaming once the rubric shows up in the optimisation loop (for example ADK's GEPA optimizer, v2.3.0). Use a held-out rubric set.

---

## 4. Simulation-based evals: user simulators and dual control

**Definition.** An LLM plays the user, with a goal and a persona, against the agent in a stateful environment. The grader checks the final environment state against the goal, run k times.

**Lineage.** tau-bench (Sierra, 2024) introduced the simulated user plus database-state check, and the **pass^k** metric. **tau2-bench** (*"τ²-Bench: Evaluating Conversational Agents in a Dual-Control Environment"*, Barres, Dong, Ray, Si, Narasimhan, arXiv **2506.07982**, June 9 2025) adds **dual control**: the user also has tools and must act on shared state (telecom tech support, modelled as a Dec-POMDP).

Numbers from tau2-bench:
- Telecom pass^1: gpt-4.1 **34%** (vs 74% retail, 56% airline), o4-mini **42%**, claude-3.7-sonnet **49%**.
- Going from "no-user" mode (the agent does everything) to dual control drops gpt-4.1 by **18 pp** and o4-mini by **25 pp**. Guiding a human is its own skill.
- Making the simulator reliable is part of the method. Constraining it to "reactive tool use based on agent requests" cut the total simulator error rate to **16%** in telecom, versus 40% in retail and 47% in airline.
- pass^k falls faster with k in telecom, which signals inconsistency.

(Those model names are mid-2025. The method, not the leaderboard, is what's current.)

**ADK user simulation** (announced on the Google Developers Blog, *"Announcing User Simulation in ADK Evaluation"*, Nov 7 2025. Docs: https://adk.dev/evaluate/user-sim/. Personas since ADK Python v1.26.0.)
```json
{"scenarios": [{
  "starting_prompt": "My internet keeps dropping.",
  "conversation_plan": "Get the agent to diagnose the router. Only reboot it when asked. Confirm the fix.",
  "user_persona": "NOVICE"
}]}
```
```json
{"criteria": {"multi_turn_task_success_v1": 0.8, "hallucinations_v1": 0.8, "safety_v1": 0.8,
              "per_turn_user_simulator_quality_v1": 0.8},
 "user_simulator_config": {"model": "gemini-flash-latest",
                           "max_allowed_invocations": 20, "include_function_calls": false}}
```
```bash
adk eval_set create support_agent sim_set
adk eval_set add_eval_case support_agent sim_set --scenarios_file scenarios.json --session_input_file session_input.json
adk eval support_agent sim_set --config_file_path eval_config.json --print_detailed_results
# generate scenarios automatically:
adk eval_set generate_eval_cases support_agent sim_set --user_simulation_config_file=gen.json
```
Built-in personas: **EXPERT**, **NOVICE**, **EVALUATOR**. A custom `UserPersona` has `behaviors[]`, and each behavior has `behavior_instructions` and `violation_rubrics`. An `llm_audio` simulator type exists for Live (voice) agents.

ADK constraint (interview-worthy): reference-based criteria (`tool_trajectory_avg_score`, `response_match_score`, `final_response_match_v2`) are **not supported** with simulation, because there is no fixed script to compare against. Use goal and rubric metrics. `per_turn_user_simulator_quality_v1` evaluates the simulator itself.

**Architecture flow (diagram).** Scenario (goal + persona) feeds the simulator LLM, which sends user turns to the agent under test. The agent calls tools that change environment state, and responses go back to the simulator. This loops until the stop signal or `max_allowed_invocations`. Then the outcome grader (state check plus `multi_turn_task_success`) and the rubric judges run. Repeat k times, then compute pass^k.

**Failure modes.** The simulator "helps too much" (leaks the solution), gives up early, or drifts off-persona. Simulator error gets counted as agent error, which is why tau2 reports simulator error rates. The simulator and agent sharing one model family inflates scores [UNVERIFIED, practitioner folklore].

---

## 5. Observability: OpenTelemetry GenAI semantic conventions

**Definition.** A vendor-neutral span and attribute schema for agent runs, so one trace can feed debugging, cost dashboards and trace graders across any backend (Cloud Trace, Phoenix, Langfuse, Datadog, Honeycomb).

**Status as of Oct 2026.** The GenAI conventions have **moved to their own repo**, `github.com/open-telemetry/semantic-conventions-genai` (the old page on opentelemetry.io now says it "is no longer maintained in this repository"). All agent spans are still **Development** stability.

Agent and framework operations (from `docs/gen-ai/gen-ai-agent-spans.md`, fetched 2026-10-23):

| Operation | Span name | Kind |
|---|---|---|
| `create_agent` | `create_agent {gen_ai.agent.name}` | CLIENT |
| `invoke_agent` | `invoke_agent {gen_ai.agent.name}` | CLIENT (remote, e.g. OpenAI Assistants, Bedrock Agents) / INTERNAL (in-process, e.g. LangChain, CrewAI, ADK) |
| `invoke_workflow` | `invoke_workflow {gen_ai.workflow.name}` | INTERNAL. Multi-agent or graph runs only, "should not be reported for standalone agent invocations" |
| `plan` | `plan {gen_ai.agent.name}` | INTERNAL. Only when planning can be reliably identified |
| `execute_tool` | `execute_tool {gen_ai.tool.name}` | (one span per tool call) |

Key attributes: `gen_ai.operation.name`, `gen_ai.provider.name`, `gen_ai.agent.name|id|version`, `gen_ai.conversation.id` (conditionally required when available), `gen_ai.request.model`, `gen_ai.response.finish_reasons`, `gen_ai.usage.input_tokens|output_tokens`. Prompt, completion and tool-argument content is **opt-in**, not captured by default, because of PII.

**ADK 2.x mapping.** Spans are `invoke_agent`, `invoke_workflow` (with `gen_ai.workflow.nested`), `execute_tool`, `generate_content`. **Breaking in v2.13.0**: telemetry defaults to OTel GenAI v2 and the legacy `call_llm` span is removed (opt out with `ADK_TELEMETRY_SCHEMA_VERSION_OPT_IN`). v2.2.0 added the `AutoTracingPlugin` and native `gen_ai.client.*` metrics. Export with `adk web --otel_to_cloud` or the standard `OTEL_EXPORTER_OTLP_*` env vars.

**Trace tree (diagram).**
`invoke_workflow refund_flow` > `invoke_agent triage` > `generate_content gemini-flash` > `execute_tool lookup_order` > `invoke_agent refunder` > `execute_tool issue_refund [confirmation pending]` > `generate_content` (final).

**Why it matters for eval.** The same spans are the input to trace graders (OpenAI trace grading, ADK's v2.13 "session and turn trace views" for evals). Online evals are just graders run over sampled production traces.

**Failure modes.** High-cardinality span names (putting user IDs in names). Logging raw prompts with PII. Schema churn while the spec is in Development (the ADK v2.13 break is a live example). Sampling away exactly the rare failures you need. Use tail-based sampling on errors and low judge scores.

---

## 6. Prompt injection: the 2025-26 consensus is "design for compromise"

### 6.1 The evidence that detection alone fails
- **"The Attacker Moves Second"** (Nasr, Carlini, Tramèr and others, 14 authors from OpenAI, Anthropic and Google DeepMind, arXiv **2510.09023**, Oct 10 2025). It broke **12 published defenses**. Adaptive attacks hit **above 90%** success against most of them, where the defenses had reported near-zero. **Human red-teaming hit 100%** (500 participants, $20k prize pool). Takeaway: static attack sets are useless for evaluating defenses. (Via Simon Willison's write-up, https://simonwillison.net/2025/Nov/2/new-prompt-injection-papers/)
- Meta: "Prompt injection is a fundamental, unsolved weakness in all LLMs."

### 6.2 Lethal trifecta to Agents Rule of Two
- Simon Willison, *"The lethal trifecta for AI agents"*, **Jun 16 2025**: private data + untrusted content + external communication means exfiltration. "LLMs are unable to reliably distinguish the importance of instructions based on where they came from."
- **Meta, *"Agents Rule of Two: A Practical Approach to AI Agent Security"*, Oct 31 2025** (https://ai.meta.com/blog/practical-ai-agent-security/). Within one session an agent may have **at most two** of:
  - **[A]** processes untrustworthy inputs
  - **[B]** accesses sensitive systems or private data
  - **[C]** changes state or communicates externally

  If a task needs all three, start a fresh session or add supervision (human approval). Quote: "When this framework is followed, the severity of security risks is deterministically reduced." Willison notes it generalises the trifecta to **state changes**, not just exfiltration. Meta clarified that [B] covers any sensitive *system*, not only private data.
- Meta's worked example: an Email-Bot hit by an injected spam message needs ABC. Dropping one property blocks it: trusted senders only gives [BC], a test environment with no sensitive data gives [AC], approving recipients and drafts gives [AB].

### 6.3 Architectural patterns (provable or structural)
- **CaMeL**, *"Defeating Prompt Injections by Design"*, Debenedetti, Shumailov et al. (Google, Google DeepMind, ETH Zurich), arXiv **2503.18813** (Mar 2025, revised later). A **Privileged LLM** turns the trusted user query into a program. A **Quarantined LLM** (no tools) parses untrusted data. A custom Python interpreter tracks **data provenance (capabilities)** and enforces policy at each tool call, so untrusted data can never change control flow. Utility on AgentDojo with provable security is reported as **67% / 77%** depending on paper version, vs about 84% undefended [check the version cited]. No model changes are required. Code: `github.com/google-research/camel-prompt-injection`.
- **"Design Patterns for Securing LLM Agents against Prompt Injections"**, Beurer-Kellner, Tramèr, Debenedetti, Paverd et al. (14 authors, IBM, Invariant Labs, ETH, Google, Microsoft and others [affiliations UNVERIFIED]), arXiv **2506.08837**, Jun 2025. Principle: once an agent has ingested untrusted input, "it must be constrained so that it is impossible for that input to trigger any consequential actions." Six patterns:
  1. **Action-Selector**: the LLM picks from fixed actions, and results never flow back in.
  2. **Plan-Then-Execute**: tool-call plan fixed before touching untrusted data.
  3. **LLM Map-Reduce**: isolated sub-LLM per untrusted item, constrained outputs, then a reduce step.
  4. **Dual LLM**: privileged planner never sees untrusted text and handles it only by reference (`$VAR1`).
  5. **Code-Then-Execute**: the LLM writes a program and the program handles the data (CaMeL generalised).
  6. **Context-Minimization**: strip untrusted or user text from context before later steps.

**ADK 2.0 connection.** Graph `Workflow`s are essentially plan-then-execute and action-selector by construction. The graph fixes which actions are reachable, and function nodes are deterministic. The *"Why we built ADK 2.0"* post (Google Developers Blog, Jul 1 2026) argues workflows shrink the prompt-injection blast radius and context bloat (illustrative refund example: **5,152 to 2,265 tokens** per run, **7.2 s to 5.7 s**). ADK v2.8.0 also "fence[s] relayed agent output so it cannot pose as instructions" for multi-agent injection.

```python
# Plan-then-execute / action-selector in ADK 2.x: the LLM classifies, code decides what can run.
from google.adk import Agent, Workflow, Event

triage = Agent(name="triage", model="gemini-flash-latest",
               instruction="Classify the email as one of: INVOICE, SUPPORT, SPAM. Output only the label.")

def route(node_input: str):
    return Event(route=[node_input.strip()])

root_agent = Workflow(name="inbox", edges=[
    ("START", triage, route),
    (route, {"INVOICE": file_invoice,      # deterministic function node, no send-email tool
             "SUPPORT": draft_reply_agent, # drafts only; sending requires confirmation
             "SPAM": archive}),
])
```
(Pattern from adk.dev/graphs. `file_invoice`, `draft_reply_agent` and `archive` are illustrative.)

### 6.4 Google's defence in depth for Gemini
*"Mitigating prompt injection attacks with a layered defense strategy"*, Google GenAI Security Team, **Jun 13 2025** (https://blog.google/security/mitigating-prompt-injection-attacks/). Five layers:
1. **Prompt-injection content classifiers** (ML models that block, filter or allow)
2. **Security thought reinforcement** (instructions around untrusted content that keep focus on the user task)
3. **Markdown sanitisation and suspicious-URL redaction** (no external image rendering, Safe Browsing), which closes the image-tag exfiltration channel
4. **User confirmation framework** for risky actions (for example deleting calendar events)
5. **End-user security notifications**

Plus model hardening via adversarial training (Gemini 2.5). Quote: "we are meaningfully elevating the difficulty, expense, and complexity faced by an attacker." Note the honest framing: this raises cost and doesn't claim to solve the problem.

**ADK equivalents.** `ModelArmorPlugin` (v2.8.0, fail-closed by default) maps to layer 1. The "Gemini as a Judge" safety plugin (Flash Lite screens inputs, tool I/O and output) maps to layers 1 and 2. UI escaping guidance maps to layer 3. `require_confirmation` maps to layer 4.

**Failure modes.** Classifier-only defences fail under adaptive attack (6.1). Thought-reinforcement prompts give a false sense of safety. Dual-LLM utility collapses on tasks that truly need the planner to read the data. Rule-of-Two sessions leak capabilities through shared memory or long-term stores across sessions [design caution, UNVERIFIED as a published incident].

---

## 7. Human-in-the-loop approvals, done right

**Definition.** Execution pauses before a consequential action. A human approves, edits or rejects through a structured payload, and the run resumes durably, even hours later.

**The 2025-26 lesson is approval fatigue.** Anthropic, *"Beyond permission prompts: making Claude Code more secure and autonomous"*, **Oct 20 2025**, David Dworken and Oliver Weller-Davies (https://www.anthropic.com/engineering/claude-code-sandboxing). Frequent prompts train users to click "yes", so Anthropic moved the boundary into a sandbox instead: "sandboxing safely reduces permission prompts by **84%**", "effective sandboxing requires both filesystem and network isolation", "even a successful prompt injection is fully isolated". It is built on bubblewrap (Linux) and seatbelt (macOS) and is open source. In Claude Code on the web, git credentials stay outside the sandbox behind a scoped proxy.

Design rule: **sandbox the reversible, approve the irreversible, and make approvals specific** (show amount, recipient and diff, not "allow tool?"). Dynamic thresholds beat blanket prompts.

**ADK** (tool confirmation since Python v1.14.0. `require_confirmation` for workflow nodes since v2.12.0. HITL resumption for `NodeTool` since v2.5.0):
```python
from google.adk.tools import FunctionTool, ToolContext

async def needs_approval(amount: int, tool_context: ToolContext) -> bool:
    return amount > 1000            # only high-value refunds interrupt a human

root_agent = Agent(name="refunder", model="gemini-flash-latest",
                   tools=[FunctionTool(issue_refund, require_confirmation=needs_approval)])

# Structured approval with an editable payload:
def request_time_off(days: int, tool_context: ToolContext):
    c = tool_context.tool_confirmation
    if not c:
        tool_context.request_confirmation(hint="Manager: approve days off", payload={"approved_days": 0})
        return {"status": "Manager approval is required."}
    approved = min(c.payload["approved_days"], days)
    return {"status": "ok" if approved else "rejected", "approved_days": approved}
```
(Verbatim pattern from https://adk.dev/tools-custom/confirmation/. The docs mark it experimental and list `DatabaseSessionService` / `VertexAiSessionService` as unsupported for this flow. Check before deploying.)

**Failure modes.** Rubber-stamping. Approval UIs that render attacker-controlled text, so the injection talks to the human too. Lost state on resume (ADK 2.9 changed failed nodes to re-run on resume, so make tools idempotent). Approval asked *after* the side effect.

---

## 8. Least-privilege tools and agent identity

**Definition.** Every agent is its own principal with a verifiable identity and the minimum scopes for its job. Tokens are bound to one audience, short-lived and never passed through.

**Google Cloud Agent Identity** (Agent Engine docs, updated 2026-10-22, https://docs.cloud.google.com/agent-builder/agent-engine/agent-identity). Each agent gets a **SPIFFE** ID (`spiffe://TRUST_DOMAIN/resources/SERVICE/RESOURCE_PATH`), shown in IAM as a `principal://` identifier. It receives an auto-renewed **24-hour X.509 cert** and certificate-bound access tokens. The identity can't be impersonated and you can't mint long-lived keys for it. **Principal Access Boundary** policies cap reachable resources. The doc's tagline: "per-agent identities instead of shared service accounts". GA vs preview status: [UNVERIFIED]. Caveat from the doc: deleting an agent leaves its IAM bindings behind, so clean them up.

**MCP Authorization spec (2025-11-25)** (https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization):
- An MCP server is an **OAuth 2.1 resource server** and MUST publish **Protected Resource Metadata (RFC 9728)**.
- Clients MUST send the **`resource` parameter (RFC 8707)** so the token is audience-bound. Servers MUST reject tokens not issued for them.
- "The MCP server **MUST NOT** pass through the token it received from the MCP client" (prevents confused deputy).
- **PKCE S256** is mandatory. **Client ID Metadata Documents** (HTTPS URL as `client_id`) are now preferred over Dynamic Client Registration.
- Least privilege is built in: request scopes from the `WWW-Authenticate` challenge, then **step-up** via `403 insufficient_scope`.

**ADK.** Agent-Auth (the agent's own identity, for example read-only) vs User-Auth (OAuth on behalf of the user). In-tool policy (for example `SELECT` only on allow-listed tables). `before_tool_callback` argument validation (user-ID match). `McpToolset` OAuth PKCE (v1.34.0). A2A requires https for non-loopback agent cards (v2.9.0).

**Failure modes.** One shared service account for all agents, so audit logs can't tell who did what. Broad OAuth scopes "because the client is generic". Token passthrough across MCP hops. Orphaned IAM bindings.

---

## 9. Cost and latency control as reliability

**Definition.** Cost and latency budgets are enforced the way error budgets are. They are measured per trace and gated in evals.

Techniques and evidence:
1. **Cache-friendly context.** Manus, *"Context Engineering for AI Agents: Lessons from Building Manus"*, Yichao "Peak" Ji, **Jul 18 2025**. KV-cache hit rate is "the most important metric for a production-stage AI agent". The average input:output ratio is about **100:1**. Cached vs uncached Claude Sonnet input is **$0.30 vs $3 per MTok (10x)**. Rules: stable prefix, append-only context, deterministic serialisation, and **"mask, don't remove" tools** (logit masking via a state machine instead of editing the tool list). "even a single-token difference can invalidate the cache from that token onward."
   **ADK:** `App(context_cache_config=ContextCacheConfig(min_tokens=2048, ttl_seconds=600, cache_intervals=5))` plus `static_instruction` for a stable prefix (v1.15.0). `EventsCompactionConfig(token_threshold=..., event_retention_size=...)` handles long sessions.
2. **Context minimalism.** Anthropic, *"Effective context engineering for AI agents"*, Sep 29 2025: "find the smallest set of high-signal tokens that maximize the likelihood of your desired outcome". Context rot means recall degrades as context grows.
3. **Replace LLM hops with code.** ADK 2.0 workflows (about 50% fewer tokens and about 20% lower latency in Google's illustrative benchmark). v2.13.0 claims "up to 8x faster execution turns for string-model agents". v2.12.0 claims 40% faster time-to-first-model-request in long sessions.
4. **Model routing and failover.** A cheap model for classification, judging and simulation (ADK docs default to `gemini-flash-latest` for judges and simulators, and the safety judge uses Flash Lite). An expensive model only on hard nodes. ADK v2.9.0 model failover (`FallbackModel` per project notes). The `ModelConsultTool` (v2.11) lets a cheap agent consult a stronger model [behaviour detail UNVERIFIED].
5. **Hard budgets.** `ADK_MAX_LLM_CALLS` (v2.8.0). `abort_signal` on Runner, Workflow and nodes (v2.11.0). Efficiency metrics in every eval run (v2.10.0).

**Failure modes.** Timestamps or a reshuffled tool list in the system prompt (cache miss on every turn). Compaction that drops pending function calls or HITL events (fixed in ADK 1.27 and 1.34, a good "why test your infra" anecdote). Routing a hard query to a cheap model that fails silently: gate on judge scores, not just cost.

---

## 10. Reference architecture (one diagram, in words)

Left to right:
1. **Identity layer.** User, then an OAuth / Agent Identity (SPIFFE) gateway.
2. **Ingress guard.** Model Armor / classifier plugin, fail-closed.
3. **ADK 2.x Workflow graph.** Deterministic function nodes, LLM nodes with least-privilege tools, a quarantined "reader" LLM for untrusted content (dual-LLM), and Rule-of-Two session partitioning.
4. **Action edge.** `before_tool_callback` policy check, then `require_confirmation` on irreversible tools, then a sandboxed executor (filesystem + network isolation).
5. **Egress.** Markdown / URL sanitisation before rendering.
6. **Telemetry.** Every hop emits OTel GenAI spans to a collector (Cloud Trace / Phoenix / Langfuse), with token and cost metrics.
7. **Quality loop.** Offline: `adk eval` (evalset + user simulation + rubric judges, k trials) as a CI gate. Online: trace graders on sampled production traces. Failures go to triage, then become new eval cases (the flywheel).

---

## 11. Likely interview questions (crisp answers)

1. **pass@k vs pass^k?** pass@k is the chance that at least one of k trials succeeds (good for "one success is enough", like code with tests). pass^k is the chance that all k succeed (consistency, for customer-facing agents). 75% per trial gives pass^3 of about 42%.
2. **Why not just grade the final answer?** Agents change state. The answer can claim success while the database disagrees. Grade the outcome state first, then use the trace to diagnose and to enforce safety-ordering constraints.
3. **Why not require an exact tool trajectory?** It punishes valid alternative plans and makes better models look worse. Use `IN_ORDER` or `ANY_ORDER`, or rubrics. Reserve `EXACT` for regulated flows.
4. **How do you trust an LLM judge?** One judge per dimension, an explicit rubric, an "Unknown" escape hatch, calibration against human labels, multiple samples with a vote, a pinned judge version, and periodic human audits.
5. **What does a user simulator add?** Multi-turn realism. Agents ask clarifying questions, and a fixed script breaks. tau2 shows a roughly 18-25 pp drop going from solo to dual control, so you need to measure guiding a user.
6. **Simulator pitfalls?** Leaking the goal, drifting off persona, simulator error counted as agent error. Measure the simulator (`per_turn_user_simulator_quality_v1`, tau2's error rates).
7. **Can we filter prompt injection with a classifier?** Not reliably. Adaptive attacks broke 12 defenses at over 90%, and human red-teamers reached 100%. Classifiers are one layer. The guarantees come from architecture (Rule of Two, CaMeL, plan-then-execute) and blast-radius limits.
8. **Explain the Agents Rule of Two.** At most two of: untrusted input [A], sensitive access [B], state change or external communication [C] per session. If all three are needed, add human approval or split sessions.
9. **CaMeL in one sentence?** A privileged LLM writes a program from the trusted query, a tool-less quarantined LLM parses untrusted data, and an interpreter tracks provenance so tainted data can't reach a sensitive sink without passing policy.
10. **Why did Anthropic sandbox instead of prompting more?** Approval fatigue. Sandboxing gave 84% fewer prompts and contains a successful injection. You need both filesystem and network isolation.
11. **What is OTel GenAI and why care?** A standard span schema (`invoke_agent`, `invoke_workflow`, `execute_tool`, token usage) that makes traces portable across vendors and usable as grader input. It is still in Development stability, so expect breaks (ADK 2.13 removed `call_llm`).
12. **Agent identity best practice?** A per-agent principal (SPIFFE / Agent Identity), short-lived audience-bound tokens (RFC 8707), no token passthrough, PKCE, step-up scopes, and per-agent audit trails.
13. **Biggest cost lever?** KV / context cache hit rate, given the 100:1 input:output ratio and 10x cheaper cached tokens. After that, replace LLM hops with deterministic workflow nodes, then route to cheaper models.
14. **How does ADK 2.0 improve reliability over 1.x?** A graph Workflow runtime: deterministic routing, retries, durable HITL resume, typed node I/O, fewer LLM hops, and a smaller injection surface, all with the same eval and telemetry stack.

---

## 12. Slide ideas (with the animation that explains each)

1. **"From vibe check to flywheel"**: a lone chat bubble with a thumbs-up morphs into a spinning four-stage wheel (Define, Instrument, Evaluate, Feed back). A red production failure drops in and turns into a green regression test card.
2. **"pass@k lies, pass^k tells"**: three dice roll per trial. The pass@3 bar shoots up while the pass^3 bar shrinks to 42% as each failure flashes. A k slider animates both curves diverging toward 100% and 0%.
3. **"Grade the world, not the words"**: the agent says "Booked!". Zoom into the database: the row is missing and a red X appears. Then a version where the row exists and the outcome grader turns green.
4. **"Rigid vs rubric trajectory"**: two paths to the same goal. The `EXACT` matcher flags the shorter, smarter path red. Switch to `ANY_ORDER` + rubric and it turns green, with the "safety ordering" constraint shown as a locked gate.
5. **"The judge panel"**: one big "rate 1-10" judge splits into three small judges (correctness, groundedness, tone), each sampled 5 times. Dots vote, the majority lights up, and an "Unknown" card slides in for missing evidence.
6. **"Simulated users, dual control"**: a ping-pong between a NOVICE persona and the agent. In the second half the user also gets a router icon (tools), the success meter drops by about 20 pp, and the caption reads "guiding humans is a skill".
7. **"The trace waterfall"**: a Gantt chart of OTel spans builds turn by turn (`invoke_workflow` > `invoke_agent` > `execute_tool`). Token counters tick up and the spans flow into three backend logos and a "grader" box.
8. **"The attacker moves second"**: 12 defense shields with "~0% ASR" labels shatter one by one to ">90%". A crowd icon (500 humans) hits 100%. The caption reads "detect is not enough, so design".
9. **"Rule of Two Venn"**: three circles A/B/C. An injected email arrow passes through the triple overlap (exfiltration). Remove any circle and the arrow bounces off. The ABC zone then shows a human-approval stamp.
10. **"CaMeL / dual-LLM airlock"**: the privileged LLM writes a program on the left. Untrusted email enters an airlock where a tool-less quarantined LLM extracts `$VAR1`. Taint-coloured data flows to `send_email`, and a policy gate blocks it unless the recipient is trusted.
11. **"Sandbox, don't nag"**: a wall of permission pop-ups collapses by 84% into a sandbox box with filesystem and network walls. An injected command bounces off the network wall.
12. **"Cost is a reliability metric"**: a context bar with a stable cached prefix (blue, $0.30) vs a churned prefix (red, $3). A timestamp inserted at the top turns everything red. Then LLM hops get replaced by function nodes and the token meter drops from 5,152 to 2,265.

---

## 13. Source list (exact titles, dates, URLs)

| Source | Date | URL |
|---|---|---|
| Anthropic, "Demystifying evals for AI agents" | 2026-01-09 | https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents |
| Anthropic, "Beyond permission prompts: making Claude Code more secure and autonomous" | 2025-10-20 | https://www.anthropic.com/engineering/claude-code-sandboxing |
| Anthropic, "Effective context engineering for AI agents" | 2025-09-29 | https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents |
| Meta, "Agents Rule of Two: A Practical Approach to AI Agent Security" | 2025-10-31 | https://ai.meta.com/blog/practical-ai-agent-security/ |
| Nasr, Carlini, Tramèr et al., "The Attacker Moves Second" | 2025-10-10 | arXiv 2510.09023 (via https://simonwillison.net/2025/Nov/2/new-prompt-injection-papers/) |
| Debenedetti et al., "Defeating Prompt Injections by Design" (CaMeL) | 2025-03 (v1) | https://arxiv.org/abs/2503.18813 |
| Beurer-Kellner et al., "Design Patterns for Securing LLM Agents against Prompt Injections" | 2025-06-10 (v3 06-27) | https://arxiv.org/abs/2506.08837 |
| Google GenAI Security Team, "Mitigating prompt injection attacks with a layered defense strategy" | 2025-06-13 | https://blog.google/security/mitigating-prompt-injection-attacks/ |
| Simon Willison, "The lethal trifecta for AI agents" | 2025-06-16 | https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/ |
| Barres et al., "τ²-Bench: Evaluating Conversational Agents in a Dual-Control Environment" | 2025-06-09 | https://arxiv.org/abs/2506.07982 |
| Google Developers Blog, "Announcing User Simulation in ADK Evaluation" | 2025-11-07 | https://developers.googleblog.com/announcing-user-simulation-in-adk-evaluation/ |
| ADK docs: User simulation / Criteria / Tool confirmation / Safety | living (checked 2026-10-23) | https://adk.dev/evaluate/user-sim/ , https://adk.dev/evaluate/criteria/ , https://adk.dev/tools-custom/confirmation/ , https://adk.dev/safety/ |
| Google Developers Blog, "Why we built ADK 2.0" | 2026-07-01 | https://developers.googleblog.com/en/why-we-built-adk-20/ |
| OpenTelemetry, GenAI semantic conventions (agent spans) | Development status, checked 2026-10-23 | https://github.com/open-telemetry/semantic-conventions-genai (docs/gen-ai/gen-ai-agent-spans.md) |
| MCP Specification 2025-11-25, Authorization | 2025-11-25 | https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization |
| Google Cloud, Agent Engine "Agent Identity" | updated 2026-10-22 | https://docs.cloud.google.com/agent-builder/agent-engine/agent-identity |
| OpenAI, Trace grading guide | living | https://developers.openai.com/api/docs/guides/trace-grading |
| Manus, "Context Engineering for AI Agents: Lessons from Building Manus" | 2025-07-18 | https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus |
| Google/Kaggle, "Agent Quality" whitepaper (5-Day AI Agents Intensive, Day 4) | 2025-11 | https://www.kaggle.com/whitepaper-agent-quality |

Not reached this session (search budget exhausted): OpenAI's Atlas prompt-injection hardening post (fetch returned 403), AI Engineer World's Fair 2026 and Google I/O / Cloud Next 2026 session talks on evals. Add them if time allows. [UNVERIFIED]
