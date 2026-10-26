# Acme support desk: the opening graph of the course (preview of Lab 3).
# Tested against google-adk 2.13.0. Default model: gemini-3.5-flash.
from typing import Literal

from google.adk import Agent, Context, Event, Workflow
from pydantic import BaseModel


class Ticket(BaseModel):
  route: Literal["refund", "question"]
  order_id: str = ""


def intake(node_input: str):
  yield Event(state={"ticket": node_input})


classify = Agent(
    name="classify", output_schema=Ticket,
    instruction="Label refund or question; copy order id: {ticket}")


def pick(node_input: Ticket):
  yield Event(route=node_input.route,
              output=node_input.model_dump())


def refund(ctx: Context, node_input: dict):
  oid = node_input["order_id"]          # from pick's output=
  ctx.state["outcome"] = f"refund queued for {oid}"
  # returns None; the edge to audit still runs


answer = Agent(
    name="answer", output_key="outcome",
    instruction="Answer in 2 sentences: {ticket}")


def audit(outcome: str):   # not node_input or ctx: read from state
  yield Event(message=f"[audit] {outcome}")


root_agent = Workflow(name="acme_desk", edges=[
    ("START", intake, classify, pick),
    (pick, {"refund": refund, "question": answer}),
    (refund, audit), (answer, audit)])
