"""Test the outcome-contract plugin without a broken API: call the callback directly.

pytest -q test_contract.py
"""
import asyncio
from types import SimpleNamespace

from refund_agent.agent import OutcomeContractPlugin


def test_negative_amount_becomes_error():
    bad = {"status": "success", "order_id": "A-1001", "amount": -79.0}
    out = asyncio.run(OutcomeContractPlugin().after_tool_callback(
        tool=SimpleNamespace(name="lookup_order"), tool_args={},
        tool_context=None, result=bad))
    assert out["status"] == "error"
    assert out["recovery_tools"] == ["escalate_to_human"]


def test_good_amount_is_kept():
    good = {"status": "success", "order_id": "A-1001", "amount": 79.0}
    out = asyncio.run(OutcomeContractPlugin().after_tool_callback(
        tool=SimpleNamespace(name="lookup_order"), tool_args={},
        tool_context=None, result=good))
    assert out is None
