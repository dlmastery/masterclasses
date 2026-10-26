# Lab 4, step 4: Acme back office expense audit.
# Orchestrator-workers: one auditor run per expense line, started at run time
# with ctx.run_node, plus a deterministic second opinion for hotel lines.
import asyncio
from typing import Literal
from google.adk import Agent, Context, Event, Workflow
from google.adk.workflow import node
from pydantic import BaseModel


class LineVerdict(BaseModel):
  line: str
  status: Literal["ok", "flag"]
  reason: str


auditor = Agent(name="auditor", model="gemini-3.5-flash",
    output_schema=LineVerdict,
    instruction=("You audit one expense line from the user message "
                 "against policy: meals <= $75/person, no alcohol, "
                 "hotels <= $250/night. Return a verdict."))


@node(parameter_binding="node_input")   # deterministic, no LLM
def policy_math(line: str, limit: float) -> bool:
  amount = float(line.rsplit("$", 1)[1])
  return amount <= limit


@node(rerun_on_resume=True)  # REQUIRED for any ctx.run_node caller
async def orchestrate(ctx: Context, node_input: str):
  lines = [l.strip() for l in node_input.split(";") if l.strip()]
  yield Event(message=f"Auditing {len(lines)} lines in parallel.")
  raw = await asyncio.gather(*[
      ctx.run_node(auditor, node_input=l, use_sub_branch=True)
      for l in lines])
  verdicts = [LineVerdict.model_validate(v) for v in raw]
  for v in verdicts:
    if v.status == "flag" and "hotel" in v.line.lower():
      ok = await ctx.run_node(policy_math,
          node_input={"line": v.line, "limit": 250.0})
      if ok:
        v.status = "ok"
        v.reason = "Within hotel cap per deterministic check."
  flagged = [v for v in verdicts if v.status == "flag"]
  yield Event(state={"flagged": [v.model_dump() for v in flagged]})
  yield Event(output=[v.model_dump() for v in verdicts],
              message="\n".join(f"{v.status.upper():4} {v.line} — {v.reason}" for v in verdicts))


root_agent = Workflow(name="expense_audit", edges=[("START", orchestrate)])
