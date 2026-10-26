# refund_approval/agent.py  -  Lab 5A, Acme refund approvals (google-adk 2.13.0)
# Refunds up to $500 go straight through. Larger ones pause at manager_gate
# until a manager answers from a later `adk run ... --session_id` call.
# Adapted from contributing/samples/workflows/request_input_rerun (v2.13.0).
from typing import Optional

from google.adk import Agent, Context, Event, Workflow
from google.adk.events import RequestInput
from google.adk.workflow import node
from pydantic import BaseModel

AUTO_APPROVE_LIMIT = 500.0


class ManagerDecision(BaseModel):
  approved: bool
  amount: Optional[float] = None          # partial refund
  note: str = ""


def intake(node_input: str):     # "A-2040 820"
  order_id, amount = node_input.split()[:2]
  yield Event(state={"order_id": order_id,
                     "amount": float(amount), "note": ""})


draft_reply = Agent(
    name="draft_reply", model="gemini-3.5-flash",
    output_key="draft",          # -> state["draft"]
    instruction=("Draft a 2-sentence customer email for a refund of "
                 "${amount} on order {order_id}. "
                 "Manager note to apply (may be empty): {note?}"),
)


@node(rerun_on_resume=True)
def manager_gate(ctx: Context, amount: float, draft: str):
  if amount <= AUTO_APPROVE_LIMIT:
    yield Event(route="approved", state={"final_amount": amount})
    return
  iid = f"refund_approval_{ctx.invocation_id}_{ctx.run_id}"
  answer = ctx.resume_inputs.get(iid)     # None on the first run
  if answer is None:
    yield RequestInput(
        interrupt_id=iid, response_schema=ManagerDecision,
        payload={"amount": amount, "draft": draft},
        message=(f"Refund ${amount:.2f} needs approval. Reply JSON "
                 '{"approved": true|false, "amount": <opt>, "note": "<opt>"}'
                 f"\n---\n{draft}"))
    return
  d = ManagerDecision.model_validate(answer)
  if not d.approved:
    yield Event(route="rejected")
  elif d.note:
    yield Event(state={"note": d.note}, route="revise")
  else:
    yield Event(state={"final_amount": d.amount or amount},
                route="approved")


def issue_refund(order_id: str, final_amount: float, draft: str):
  key = f"refund-{order_id}"        # idempotency key: same on every retry
  yield Event(message=f"REFUNDED ${final_amount:.2f} on {order_id} "
                      f"(idempotency key {key}).\n{draft}")


def notify_rejected(order_id: str):
  yield Event(message=f"Refund for {order_id} rejected by manager.")


root_agent = Workflow(name="refund_approval", edges=[
    ("START", intake, draft_reply, manager_gate),
    (manager_gate, {"approved": issue_refund,
                    "rejected": notify_rejected,
                    "revise": draft_reply}),
])
