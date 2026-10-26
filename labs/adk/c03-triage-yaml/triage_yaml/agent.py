# no root_agent here: the loader falls through to root_agent.yaml
from typing import Literal

from google.adk import Event
from pydantic import BaseModel


class Triage(BaseModel):
  label: Literal["billing", "outage", "other"]


def intake(node_input: str):
  yield Event(state={"ticket": node_input})


def route_ticket(node_input: Triage):
  yield Event(route=node_input.label)


def page_oncall():
  yield Event(message="PAGED on-call.")


def human_queue():
  yield Event(message="Routed to the human L1 queue.")
