# refund_confirm/agent.py  -  Lab 5A build-up: node-level require_confirmation
# (google-adk 2.12+, tested against 2.13.0 source). A yes/no gate only:
# no draft, no revise loop, no partial amount. Keep refund_approval/ for those.
# No LLM node, so no API key is needed.
from google.adk import Event, Workflow
from google.adk.workflow import node

AUTO_APPROVE_LIMIT = 500.0


def intake(node_input: str):     # "A-2040 820"
  order_id, amount = node_input.split()[:2]
  yield Event(state={"order_id": order_id, "amount": float(amount)})


# The predicate gets `amount` by name from state. Return a real bool.
@node(require_confirmation=lambda amount: amount > AUTO_APPROVE_LIMIT)
def issue_refund(order_id: str, amount: float):  # args = state keys
  key = f"refund-{order_id}"                     # idempotency key
  yield Event(message=f"REFUNDED ${amount:.2f} on {order_id} "
                      f"(key {key})")


root_agent = Workflow(name="refund_confirm",
                      edges=[("START", intake, issue_refund)])
