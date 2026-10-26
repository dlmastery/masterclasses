"""Lab 3.1 / 3.2 - Acme refund desk: a typed chain of four nodes.

START -> parse_request -> check_policy -> write_reply -> audit_log
Tested against google-adk 2.13.0 source (not executed on this machine).
"""
from google.adk import Agent, Context, Event, Workflow
from pydantic import BaseModel

ORDERS = {
    "A-1001": {"amount": 89.00, "days_since_delivery": 12, "category": "electronics"},
    "A-1002": {"amount": 1450.00, "days_since_delivery": 41, "category": "furniture"},
}


class RefundCase(BaseModel):
  order_id: str
  amount: float
  days_since_delivery: int
  eligible: bool


def parse_request(node_input: str) -> str:       # -> "A-1001"
  """'refund A-1001 arrived broken' -> 'A-1001'."""
  return next(t for t in node_input.split()
              if t.upper().startswith("A-")).upper()


def check_policy(ctx: Context, node_input: str) -> RefundCase:
  order = ORDERS[node_input]
  eligible = order["days_since_delivery"] <= 30          # 30-day policy
  ctx.state["refund_case"] = {"order_id": node_input, **order,
                              "eligible": eligible}
  # RefundCase ignores the extra "category" key (pydantic default extra="ignore")
  return RefundCase(order_id=node_input, eligible=eligible, **order)


# {refund_case} reads ctx.state, not the RefundCase on the edge
write_reply = Agent(
    name="write_reply",
    model="gemini-3.5-flash",
    instruction=("You are a refunds agent. Case: {refund_case}. "
                 "If eligible is true, confirm the refund amount. Otherwise explain "
                 "the 30-day policy politely and offer store credit. Max 3 sentences."),
    output_key="reply_text",
)


def audit_log(reply_text: str):                          # bound from ctx.state["reply_text"]
  yield Event(message=f"[audit] reply length={len(reply_text)} chars. WORKFLOW COMPLETED.")


root_agent = Workflow(
    name="refund_flow",
    edges=[("START", parse_request, check_policy, write_reply, audit_log)],
)
