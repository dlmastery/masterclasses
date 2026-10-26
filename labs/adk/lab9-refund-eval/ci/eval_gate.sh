#!/usr/bin/env bash
# Eval gate that cannot pass silently. Run from labs/adk/lab9-refund-eval/.
# Tested with google-adk[eval]==2.13.0.
#  - pipefail: `| tee` no longer hides the exit code of adk eval
#  - PYTHONPATH: importlib finds refund_policy and completion_bit
#  - test -f: a wrong config path would silently use the default criteria
#  - case count: update N when you add cases
set -euo pipefail
export PYTHONPATH=$PWD
CFG=refund_agent/test_config.json
test -f "$CFG" || { echo "missing $CFG"; exit 1; }

adk eval refund_agent refund_agent/refund.evalset.json \
  --config_file_path="$CFG" --print_detailed_results | tee eval.log
N=$(grep -c '^Eval Id:' eval.log || true)
test "$N" -eq 2 || { echo "ran $N of 2 cases"; exit 1; }
grep -q 'Metric: refund_policy_score' eval.log || exit 1

# known-bad: expects issue_refund on A-2040, so it MUST fail
if adk eval refund_agent refund_agent/known_bad.evalset.json \
     --config_file_path="$CFG"; then
  echo "gate passed a known-bad case"; exit 1
fi
echo "eval gate OK"
