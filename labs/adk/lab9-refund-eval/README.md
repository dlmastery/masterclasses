# Lab 9: Acme refund eval gate

Chapter 9 of the Google ADK deck. Build an eval gate for the Acme refund desk agent:
golden cases, a code metric for the $500 rule, simulated customers with rubrics, a
judge-free completion bit, an outcome-contract plugin, and a CI exit code.

Tested on **google-adk 2.13.0** (Python 3.11+). Sources: codelab
[Evaluating Agents with ADK](https://codelabs.developers.google.com/adk-eval/instructions),
[adk.dev Evaluate](https://adk.dev/evaluate/), samples `contributing/samples/evaluation/*`
in google/adk-python.

## Install

```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\Activate.ps1
pip install "google-adk[eval]==2.13.0"
pip install pytest pytest-asyncio scikit-learn         # only for the tests and judge_kappa.py
```

## Environment variables

```bash
export GOOGLE_GENAI_USE_ENTERPRISE=FALSE
export GOOGLE_API_KEY=<your AI Studio key>
cd labs/adk/lab9-refund-eval
export PYTHONPATH=$PWD          # PowerShell: $env:PYTHONPATH=$PWD  (custom metrics are imported by name)
```

All metrics in this lab run on the AI Studio key. Only `safety_v1` and the `multi_turn_*`
metrics need a Google Cloud project (`GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION`).

## Files

```
lab9-refund-eval/
  refund_agent/__init__.py              from . import agent
  refund_agent/agent.py                 tools, root_agent, OutcomeContractPlugin, app
  refund_agent/refund.evalset.json      2 golden cases (A-1001 refund, A-2040 escalate)
  refund_agent/test_config.json         trajectory IN_ORDER + LLM judge + refund_policy_score
  refund_agent/known_bad.evalset.json   a case a correct agent MUST fail
  refund_agent/sim_config.json          rubrics + simulator config + completion_bit
  refund_policy.py                      custom metric: 0 if issue_refund > 500 USD
  completion_bit.py                     judge-free completion metric
  scenarios.json, session_input.json    simulated customers (NOVICE, EXPERT)
  ci/eval_gate.sh                       gate script (pipefail, config check, case count, known-bad)
  ci/eval.yml                           GitHub Actions workflow (copy to .github/workflows/)
  test_refund.py                        AgentEvaluator.evaluate(num_runs=3)
  test_contract.py                      unit test for the plugin
  judge_kappa.py, labels.csv            Cohen's kappa of judge vs human labels (sample rows)
```

`agent.py` is the final state of the lab. To reproduce the slides step by step:
- Step 3 (custom metric fails): delete the sentence "If it is above 500 USD, never call
  issue_refund; ..." from the instruction and run the eval again.
- Step 7 (rubric fails): delete the sentence "Never tell the customer that a refund above
  500 USD is approved." and run the simulated set again.

## Run

```bash
# 1. chat and record golden cases (Eval tab -> Add current session)
adk web

# 2. golden set with the custom criteria
adk eval refund_agent refund_agent/refund.evalset.json \
  --config_file_path=refund_agent/test_config.json --print_detailed_results
echo "exit code: $?"            # 1 if any case failed or none ran (since 2.13.0)

# run one case only
adk eval refund_agent refund_agent/refund.evalset.json:large_refund_escalates \
  --config_file_path=refund_agent/test_config.json

# 3. simulated customers
adk eval_set create refund_agent refund_sim
adk eval_set add_eval_case refund_agent refund_sim \
  --scenarios_file scenarios.json --session_input_file session_input.json
adk eval refund_agent refund_sim --config_file_path refund_agent/sim_config.json \
  --print_detailed_results

# 4. the gate CI runs, plus the unit tests
bash ci/eval_gate.sh
pytest -q test_contract.py test_refund.py
python judge_kappa.py labels.csv
```

## Expected output (illustrative, not executed)

```
Eval Run Summary
refund_golden:
  Tests passed: 2
  Tests failed: 0
Eval Id: small_refund
Metric: tool_trajectory_avg_score, Status: PASSED, Score: 1.0, Threshold: 1.0
Metric: final_response_match_v2, Status: PASSED, Score: 1.0, Threshold: 0.8
Metric: refund_policy_score, Status: PASSED, Score: 1.0, Threshold: 1.0
Metric: token_usage_v1, Status: NOT_EVALUATED, Score: 2843.0, Threshold: None
exit code: 0
```

With the 500 USD sentence removed (illustrative):

```
Eval Id: large_refund_escalates
Metric: refund_policy_score, Status: FAILED, Score: 0.0, Threshold: 1.0
exit code: 1
```

## Gotchas

- A wrong `--config_file_path` is not an error: ADK logs
  `No config file supplied or file not found. Using default criteria.` `ci/eval_gate.sh` checks the file first.
- Before 2.13.0 `adk eval` always exited 0. A pipe into `tee` hides the exit code without `set -o pipefail`.
- A typo in an evalset key (`"tool_use"`) fails with `Extra inputs are not permitted`; a typo in `test_config.json` is dropped silently.
- `tool_trajectory_avg_score` on simulated cases fails with `expected_invocations is needed by this metric.`
- `add_eval_case` makes the case id from a hash of the scenario and skips duplicates: if you edit a scenario, delete the old case.
- `adk eval` has no repeat flag in 2.13.0. Use `AgentEvaluator.evaluate(..., num_runs=3)` (default 2).
