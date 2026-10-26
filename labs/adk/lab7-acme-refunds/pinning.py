"""Industry pattern (Rippling): variable pinning with Acme order ids.

The model works with a short handle (ord_1); code resolves the real id from state.
Add find_order and issue_refund as tools on any LlmAgent.
"""
from google.adk.tools.tool_context import ToolContext
from refund_core import ORDERS     # stands in for the order DB (real ids: UUIDs)


def find_order(order_id: str, tool_context: ToolContext) -> dict:
    """Find an order. Returns a short handle, never the raw id."""
    if order_id not in ORDERS:
        return {"error": f"unknown order {order_id}"}
    pins = dict(tool_context.state.get("pins", {}))
    handle = next((h for h, v in pins.items() if v == order_id), f"ord_{len(pins) + 1}")
    tool_context.state["pins"] = {**pins, handle: order_id}
    return {"handle": handle, **ORDERS[order_id]}


def issue_refund(handle: str, amount: float, tool_context: ToolContext) -> dict:
    """Refund an order by its handle."""
    order_id = tool_context.state.get("pins", {}).get(handle)   # code resolves the id
    if order_id is None:
        return {"error": f"unknown handle {handle}"}
    return {"status": "ok", "order_id": order_id, "refunded": amount}
