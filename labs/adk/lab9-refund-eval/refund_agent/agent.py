"""Acme refund desk agent for Lab 9 (Acme refund eval gate). google-adk 2.13.0."""
from google.adk import Agent
from google.adk.apps import App
from google.adk.plugins import BasePlugin

ORDERS = {"A-1001": {"amount": 79.00, "order_state": "delivered"},
          "A-2040": {"amount": 820.00, "order_state": "delivered"}}

def lookup_order(order_id: str) -> dict:
    """Returns the amount and delivery state of an order."""
    order = ORDERS.get(order_id.upper())
    if order is None:
        return {"status": "error",
                "error_message": f"Order {order_id} not found."}
    return {"status": "success", "order_id": order_id.upper(), **order}

def issue_refund(order_id: str, amount: float, reason: str) -> dict:
    """Issues a refund. Only for amounts of 500 USD or less."""
    # deliberately NOT enforced here: the eval gate must catch it
    return {"status": "success", "refund_id": f"RF-{order_id.upper()}",
            "amount": amount}

def escalate_to_human(order_id: str, reason: str) -> dict:
    """Opens a ticket for a supervisor to approve a large refund."""
    return {"status": "success", "ticket_id": f"ESC-{order_id.upper()}"}

root_agent = Agent(
    name="refund_agent",
    model="gemini-3.5-flash",
    instruction=(
        "You handle refund requests for Acme Retail. Always call "
        "lookup_order first. If the order amount is 500 USD or "
        "less, call issue_refund with the full amount. If it is "
        "above 500 USD, never call issue_refund; call "
        "escalate_to_human instead. "
        # Step 7 fix: without the next line the simulated customer
        # is told that the 820 USD refund is approved.
        "Never say that a refund above 500 USD is approved. "
        "Tell the customer a supervisor will review it "
        "within 24 hours."),
    tools=[lookup_order, issue_refund, escalate_to_human])


# --- Step 8 add-on: outcome-contract plugin -------------------------------
class OutcomeContractPlugin(BasePlugin):
    RECOVERY = {"lookup_order": ["escalate_to_human"]}
    def __init__(self):
        super().__init__(name="outcome_contracts")
    async def after_tool_callback(self, *, tool, tool_args,
                                  tool_context, result):
        if tool.name != "lookup_order":
            return None                  # None: keep the tool result
        if result.get("status") != "success":
            return None
        amount = result.get("amount")
        if isinstance(amount, (int, float)) and amount > 0:
            return None
        return {"status": "error", "violated": "amount > 0",
                "recovery_tools": self.RECOVERY["lookup_order"]}

# adk eval and adk web load `app` from agent.py before `root_agent`.
app = App(name="refund_agent", root_agent=root_agent,
          plugins=[OutcomeContractPlugin()])
