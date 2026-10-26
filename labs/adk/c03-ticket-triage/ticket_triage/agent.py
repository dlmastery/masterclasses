"""Lab 3.3 - Acme support desk: the LLM classifies, a function routes.

START -> intake -> classify -> route_ticket -> {billing | page_oncall | how_to | DEFAULT: human_queue}
Tested against google-adk 2.13.0 source (not executed on this machine).
"""
from typing import Literal

from google.adk import Agent, Event, Workflow
from google.adk.workflow import DEFAULT_ROUTE        # not exported by google.adk
from pydantic import BaseModel, Field


class Triage(BaseModel):
  labels: list[Literal["billing", "outage", "how_to", "other"]] = Field(
      description="All labels that apply to the ticket.")
  priority: Literal["p1", "p2", "p3"]


def intake(node_input: str):
  yield Event(state={"ticket": node_input})


classify = Agent(
    name="classify", model="gemini-3.5-flash",
    instruction="Classify this support ticket. Ticket: {ticket}",
    output_schema=Triage, output_key="triage",
)


def route_ticket(node_input: Triage):
  routes = list(node_input.labels)
  if node_input.priority == "p1" and "outage" not in routes:
    routes.append("outage")                     # p1 always pages on-call
  yield Event(output=node_input.model_dump(), route=routes)   # list => every match runs


billing = Agent(name="billing", model="gemini-3.5-flash",
                instruction="Draft a billing reply for: {ticket}. Mention invoice lookup.")


def page_oncall(node_input: dict):              # gets route_ticket's output
  yield Event(message=f"PAGED on-call (priority={node_input['priority']}).")


how_to = Agent(name="how_to", model="gemini-3.5-flash",
               instruction="Answer the product question in 4 steps: {ticket}")


def human_queue():
  yield Event(message="Routed to the human L1 queue.")


root_agent = Workflow(
    name="ticket_triage",
    edges=[
        ("START", intake, classify, route_ticket),
        (route_ticket, {"billing": billing, "outage": page_oncall,
                        "how_to": how_to, DEFAULT_ROUTE: human_queue}),
    ],
)
