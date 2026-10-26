"""Lab 2, step 1: turn a loss email into a validated ClaimIntake dict.

Run from the lab folder:
    python claims/claim_intake.py claims/email_77.txt
"""
import asyncio
import json
import sys
from typing import Literal, Optional

from pydantic import BaseModel, Field
from google.adk import Agent
from google.adk.runners import InMemoryRunner


class ClaimIntake(BaseModel):
    """First notice of loss, extracted from a customer email."""
    reasoning: str = Field(
        description="One sentence: the facts behind the labels.")
    claim_type: Literal["auto_collision", "auto_glass", "home_water",
                        "home_theft", "other"]
    severity: Literal["low", "medium", "high"] = Field(
        description="low < $2k, medium $2k-$10k, high = injury or > $10k")
    policy_number: Optional[str] = Field(
        None, description="POL-######, or null")
    incident_date: Optional[str] = Field(
        None, description="YYYY-MM-DD, or null if unknown")
    estimated_loss_usd: Optional[float] = None
    injuries_reported: bool


intake_agent = Agent(
    name="claim_intake",
    model="gemini-3.5-flash",
    instruction=("Extract a ClaimIntake from the email. "
                 "Never guess a value."),
    output_schema=ClaimIntake,     # not generate_content_config
    output_key="claim",
)


# A business rule that the schema cannot express (arXiv 2609.23742).
def check_claim(claim: dict) -> None:
    big_loss = claim.get("estimated_loss_usd", 0) > 10_000
    hurt = claim.get("injuries_reported", False)
    if claim["severity"] == "high" and not (hurt or big_loss):
        raise ValueError("severity=high needs injury or > $10k loss")


async def main(email: str) -> None:
    runner = InMemoryRunner(agent=intake_agent, app_name="claims_api")
    # run_debug makes its own session: debug_user_id / debug_session_id
    await runner.run_debug(email, quiet=True)
    s = await runner.session_service.get_session(
        app_name="claims_api",
        user_id="debug_user_id", session_id="debug_session_id")
    claim = s.state["claim"]            # a dict, None fields dropped
    check_claim(claim)                  # meaning check, after the schema
    print(json.dumps(claim))
    date = claim.get("incident_date")   # None, not KeyError
    typed = ClaimIntake.model_validate(claim)   # typed object back
    print("incident_date:", date, "| severity:", typed.severity)


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as f:
        asyncio.run(main(f.read()))
