"""Lab 2, build: a claim conversation that survives a process restart.

Run from the lab folder, twice, as two separate processes:
    python claims/claims_followup.py "My car is a 2024 Civic."
    python claims/claims_followup.py "Which car did I say I have?"
"""
import asyncio
import sys

from google.adk import Agent, Runner
from google.adk.apps import App
from google.adk.sessions.sqlite_session_service import (
    SqliteSessionService)
from google.genai import types

# Postgres instead (needs pip install "google-adk[db]==2.13.0" asyncpg):
# from google.adk.sessions import DatabaseSessionService
# sessions = DatabaseSessionService(
#     db_url="postgresql+asyncpg://adk:pw@localhost:5432/adk")

claims_followup = Agent(
    name="claims_followup",
    model="gemini-3.5-flash",
    instruction="You handle claim {claim_id}. Remember what the user said.",
)
app = App(name="claims_api", root_agent=claims_followup)
# the file is created in the current directory
sessions = SqliteSessionService(db_path="claims_sessions.db")


async def main(text: str) -> None:
    runner = Runner(app=app, session_service=sessions,
                    auto_create_session=True)
    sid, uid = "claim-77", "u-tom"
    old = await sessions.get_session(app_name="claims_api",
                                     user_id=uid, session_id=sid)
    delta = None if old else {"claim_id": sid}  # seed once
    msg = types.UserContent(parts=[types.Part(text=text)])
    async for ev in runner.run_async(
            user_id=uid, session_id=sid,
            new_message=msg, state_delta=delta):
        if ev.is_final_response() and ev.content and ev.content.parts:
            print(f"[{ev.author}] {ev.content.parts[0].text}")
    s = await sessions.get_session(app_name="claims_api",
                                   user_id=uid, session_id=sid)
    print(f"(events stored: {len(s.events)})")
    await runner.close()


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1]))
