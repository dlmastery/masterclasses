# labs/adk/lab1-refund-tools/refund_agent/agent.py
# Acme refund desk, Lab 1: two typed tools. Tested against google-adk 2.13.0 source.
from typing import Annotated, Literal

from pydantic import Field
from google.adk import Agent

ORDERS = {
    "A-1001": {"email": "dana@example.com", "total_usd": 89.0, "days_since_delivery": 12, "category": "apparel"},
    "A-1002": {"email": "li@example.com", "total_usd": 1299.0, "days_since_delivery": 41, "category": "electronics"},
    "A-1003": {"email": "sam@example.com", "total_usd": 24.5, "days_since_delivery": 3, "category": "grocery"},
}
RETURN_WINDOW_DAYS = {"apparel": 30, "electronics": 30, "grocery": 0}
INSTRUCTION = (
    "You are a refund desk assistant. Use lookup_order, then "
    "check_refund_eligibility. Quote the rule you applied. Never promise a "
    "refund the tool did not approve."
)


def lookup_order(
    order_id: Annotated[str, Field(description="Order ID, e.g. A-1001")],
) -> dict:
    """Look up an order.

    Always call this before answering a refund question."""
    order = ORDERS.get(order_id.strip().upper())
    if order is None:
        return {"status": "error",
                "error_message": f"No order with ID {order_id}."}
    return {"status": "success", "order": order}


Reason = Literal["changed_mind", "damaged", "wrong_item"]   # becomes an enum


def check_refund_eligibility(
    order_id: str, reason: Reason = "changed_mind"
) -> dict:
    """Apply the refund policy: 30-day window.

    Grocery is final sale unless damaged. Damaged or wrong items are
    always refundable, inside or outside the window.
    """
    order = ORDERS.get(order_id.strip().upper())
    if order is None:
        return {"status": "error",
                "error_message": f"No order with ID {order_id}."}
    if reason in ("damaged", "wrong_item"):
        return {"status": "success", "eligible": True, "rule": "defect_override"}
    window = RETURN_WINDOW_DAYS[order["category"]]
    eligible = order["days_since_delivery"] <= window
    return {"status": "success", "eligible": eligible, "window_days": window,
            "days_since_delivery": order["days_since_delivery"]}


root_agent = Agent(
    name="refund_agent", model="gemini-3.5-flash",
    description="Answers refund-eligibility questions for Acme retail orders.",
    instruction=INSTRUCTION,  # quote the rule; never promise a refund
    tools=[lookup_order, check_refund_eligibility],
)
