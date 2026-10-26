"""Gotcha: get_session returns a copy, so write state through an event.

Run from the lab folder, after claims_followup.py has created claim-77:
    python claims/mark_reviewed.py
"""
import asyncio
import sys

from google.adk import Runner
from google.genai import types

from claims_followup import app, sessions    # same App, same SQLite file


async def main() -> None:
    runner = Runner(app=app, session_service=sessions,
                    auto_create_session=True)
    key = dict(app_name="claims_api", user_id="u-tom",
               session_id="claim-77")
    s = await sessions.get_session(**key)
    if s is None:
        sys.exit("Run claims/claims_followup.py first.")
    s.state["claim_status"] = "reviewed"         # edits the copy: lost
    s = await sessions.get_session(**key)
    print("after the copy edit:", s.state.get("claim_status"))

    msg = types.UserContent(
        parts=[types.Part(text="Mark the claim reviewed.")])
    async for _ in runner.run_async(
            user_id="u-tom", session_id="claim-77", new_message=msg,
            state_delta={"claim_status": "reviewed"}):
        pass                     # the delta rides on this turn
    s = await sessions.get_session(**key)
    print("after state_delta:", s.state["claim_status"])
    await runner.close()


if __name__ == "__main__":
    asyncio.run(main())
