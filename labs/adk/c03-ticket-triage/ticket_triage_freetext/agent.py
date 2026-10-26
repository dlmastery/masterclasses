"""Gotcha reproduction - free-text labels and no DEFAULT_ROUTE.

If the model writes "Billing" (capital B), no dict key matches. Nothing raises:
the branch ends and you get one WARNING log line. Compare with ../ticket_triage.
"""
from google.adk import Agent, Event, Workflow
from pydantic import BaseModel


class Triage(BaseModel):
  labels: list[str]          # free text: "Billing" is legal
  priority: str


def intake(node_input: str):
  yield Event(state={"ticket": node_input})


classify = Agent(
    name="classify", model="gemini-3.5-flash",
    instruction="Classify this support ticket. Ticket: {ticket}",
    output_schema=Triage, output_key="triage",
)


def route_ticket(node_input: Triage):
  yield Event(output=node_input.model_dump(),
              route=list(node_input.labels))


billing = Agent(name="billing", model="gemini-3.5-flash",
                instruction="Draft a billing reply for: {ticket}. Mention invoice lookup.")


def page_oncall(node_input: dict):
  yield Event(message=f"PAGED on-call (priority={node_input['priority']}).")


how_to = Agent(name="how_to", model="gemini-3.5-flash",
               instruction="Answer the product question in 4 steps: {ticket}")


root_agent = Workflow(name="ticket_triage_freetext", edges=[
    ("START", intake, classify, route_ticket),
    (route_ticket, {"billing": billing, "outage": page_oncall,
                    "how_to": how_to}),
])
