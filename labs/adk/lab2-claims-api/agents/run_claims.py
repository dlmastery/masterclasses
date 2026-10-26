"""Run the one claims App from Python, with SQLite sessions.

Run:  cd agents && python run_claims.py
"""
import asyncio

from google.adk import Runner
from google.adk.sessions.sqlite_session_service import (
    SqliteSessionService)
from google.genai import types

from claims_api.agent import app      # the one App, plugins included


async def main() -> None:
    sessions = SqliteSessionService(db_path="claims_sessions.db")
    runner = Runner(app=app, session_service=sessions,
                    auto_create_session=True)      # no plugins= here
    msg = types.UserContent(parts=[types.Part(text="Is glass covered?")])
    async for ev in runner.run_async(
            user_id="u-tom", session_id="claim-77", new_message=msg):
        if ev.is_final_response() and ev.content and ev.content.parts:
            print(ev.content.parts[0].text)
    await runner.close()


if __name__ == "__main__":
    asyncio.run(main())
