"""Shared core for Lab 7: the Acme refund agent and its order lookup.

The MCP server (step 1), the A2A server (step 2) and the skill agent (step 5)
all import from this module, so there is exactly one refund agent.
"""
from google.adk.agents import LlmAgent

ORDERS = {
    "A-100": {"days_since_purchase": 12, "amount": 79.0, "category": "apparel"},
    "A-200": {"days_since_purchase": 45, "amount": 640.0, "category": "electronics"},
    "A-300": {"days_since_purchase": 42, "amount": 120.0, "category": "apparel"},
}


INSTRUCTION = (
    "Policy: apparel 30 days, electronics 14 days, refunds over $500 "
    "need a manager. Call lookup_order, then answer REFUNDABLE / "
    "NOT_REFUNDABLE / NEEDS_MANAGER with one sentence of reasoning."
)


def lookup_order(order_id: str) -> dict:
    """Return days since purchase, amount (USD) and category."""
    return ORDERS.get(order_id, {"error": f"unknown order {order_id}"})


refund_agent = LlmAgent(
    name="refund_agent",
    model="gemini-3.5-flash",
    description=("Checks refund eligibility for an order id "
                 "under Acme policy."),
    instruction=INSTRUCTION,   # 30/14-day windows, $500 cap
    tools=[lookup_order],
)
