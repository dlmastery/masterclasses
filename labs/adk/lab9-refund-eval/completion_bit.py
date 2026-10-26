"""Judge-free completion bit for simulated chats (GAUGE, arXiv 2609.12191).

It passes only if the agent called a terminal tool. Completion is not
correctness: keep refund_policy_score and the rubrics next to it.
"""
from google.adk.evaluation.eval_case import get_all_tool_calls
from google.adk.evaluation.evaluator import (
    EvalStatus, EvaluationResult)

DONE = {"escalate_to_human", "issue_refund"}   # terminal tools

def completion_bit(eval_metric, actual_invocations,
                   expected_invocations, conversation_scenario):
    done = any(call.name in DONE for inv in actual_invocations
               for call in get_all_tool_calls(inv.intermediate_data))
    status = EvalStatus.PASSED if done else EvalStatus.FAILED
    return EvaluationResult(overall_score=1.0 if done else 0.0,
                            overall_eval_status=status)
