# Lab 4, step 3: Acme back office ad-copy review.
# Evaluator-optimizer loop: write_copy drafts, review_copy grades, gate routes.
# Two exits: "done" (compliant) and "escalate" (MAX_ROUNDS reached).
from typing import Literal
from google.adk import Agent, Context, Event, Workflow
from pydantic import BaseModel, Field

MAX_ROUNDS = 3


class Review(BaseModel):
  grade: Literal["compliant", "needs_fix"]
  feedback: str = Field(
      description="What to change to meet the policy.")


def brief(node_input: str):
  yield Event(state={"brief": node_input, "feedback": "", "round": 0})


write_copy = Agent(
    name="write_copy", model="gemini-3.5-flash", output_key="draft",
    instruction="Write a 2-sentence ad for: {brief}. "
                "Previous draft (may be empty): {draft?} "
                "Feedback to apply (may be empty): {feedback?}")

review_copy = Agent(
    name="review_copy", model="gemini-3.5-flash",
    output_schema=Review, output_key="review",
    instruction="Policy: no guaranteed returns, no 'risk-free', must "
                "say 'Capital at risk.' Grade this ad: {draft}")


def gate(ctx: Context, node_input: Review):
  ctx.state["round"] = ctx.state["round"] + 1
  if node_input.grade == "compliant":
    yield Event(route="done")
  elif ctx.state["round"] >= MAX_ROUNDS:   # MAX_ROUNDS = 3
    yield Event(route="escalate")
  else:
    yield Event(state={"feedback": node_input.feedback},
                route="retry")


def publish(draft: str):               # draft is read from ctx.state
  yield Event(message=f"PUBLISHED:\n{draft}")


def escalate(draft: str, round: int):  # both read from ctx.state
  yield Event(message=f"Escalated to Legal after {round} rounds.\n{draft}")


root_agent = Workflow(name="copy_review", edges=[
    ("START", brief, write_copy, review_copy, gate),
    (gate, {"retry": write_copy, "done": publish,
            "escalate": escalate})])
