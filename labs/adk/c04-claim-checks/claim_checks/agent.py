# Lab 4, step 1-2: Acme back office claim checks.
# Fan-out to three independent checks, a JoinNode barrier, one decision.
# No LLM node: runs offline, no API key, no .env.
import asyncio
from google.adk import Event, Workflow
from google.adk.workflow import JoinNode

POLICIES = {"POL-77": {"active": True, "deductible": 500, "limit": 20000}}
INACTIVE = {"active": False, "deductible": 0, "limit": 0}


def parse_claim(node_input: str) -> dict:   # "POL-77 rear-end collision 4200"
  policy_id, *desc, amount = node_input.split()
  return {"policy_id": policy_id, "desc": " ".join(desc), "amount": float(amount)}


async def policy_check(node_input: dict) -> dict:
  await asyncio.sleep(0.3)                     # stands in for the policy DB
  return POLICIES.get(node_input["policy_id"], INACTIVE)


async def fraud_score(node_input: dict) -> float:
  await asyncio.sleep(0.5)                     # stands in for the fraud model
  return 0.82 if "total loss" in node_input["desc"] else 0.07


async def damage_estimate(node_input: dict) -> float:
  await asyncio.sleep(0.2)                     # stands in for the estimator
  return round(node_input["amount"] * 0.95, 2)


# The join emits one dict keyed by predecessor node name (= function name):
# {"policy_check": {...}, "fraud_score": 0.07, "damage_estimate": 3990.0}
def decide(node_input: dict):
  pol, fraud = node_input["policy_check"], node_input["fraud_score"]
  est = node_input["damage_estimate"]
  payout = max(0, min(est, pol["limit"]) - pol["deductible"])
  if not pol["active"] or payout == 0:
    verdict = "DENY: policy inactive or payout 0"
  elif fraud > 0.6:
    verdict = f"REFER to SIU (fraud score {fraud:.2f})"
  else:
    verdict = f"APPROVE payout ${payout:,.2f}"
  yield Event(output=verdict, message=verdict)   # adk run prints message only


join_checks = JoinNode(name="join_checks")

root_agent = Workflow(
    name="claim_checks",
    max_concurrency=3,  # optional cap; the tuple below makes the fan-out
    edges=[("START", parse_claim, (policy_check, fraud_score, damage_estimate),
            join_checks, decide)],
)
