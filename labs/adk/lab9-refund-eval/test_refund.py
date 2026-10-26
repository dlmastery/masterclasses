"""Run the golden set from pytest. adk eval has no repeat flag in 2.13.0.

pip install pytest pytest-asyncio
pytest -q test_refund.py
"""
import pytest
from google.adk.evaluation.agent_evaluator import AgentEvaluator


@pytest.mark.asyncio
async def test_refund_golden():
    await AgentEvaluator.evaluate(
        agent_module="refund_agent",
        eval_dataset_file_path_or_dir=
            "refund_agent/refund.evalset.json",
        num_runs=3)   # default is 2
