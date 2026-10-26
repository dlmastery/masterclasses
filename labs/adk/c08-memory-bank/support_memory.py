"""Lab 8 step 2: Acme support remembers the customer across sessions with Memory Bank.

Usage:  python support_memory.py day1   then   python support_memory.py day2
Tested against google-adk 2.13.0 source. Output in README.md is illustrative.
"""
import asyncio
import os
import sys

from google.adk import Agent, Runner
from google.adk.memory import VertexAiMemoryBankService
from google.adk.sessions import InMemorySessionService
from google.adk.tools import preload_memory
from google.genai import types

APP = "acme_support"
USER = "cust-42"


async def save_to_memory(callback_context) -> None:
    # Runs after every agent turn: send the session so far to Memory Bank.
    await callback_context.add_session_to_memory()


agent = Agent(
    name="support_agent",
    model="gemini-3.5-flash",
    instruction="Acme support. Use remembered preferences.",
    tools=[preload_memory],              # searches memory with the user turn, before the model call
    after_agent_callback=save_to_memory,
)

memory = VertexAiMemoryBankService(
    project=os.environ["GOOGLE_CLOUD_PROJECT"],
    location=os.environ["GOOGLE_CLOUD_LOCATION"],
    agent_engine_id=os.environ["AGENT_ENGINE_ID"],
)

runner = Runner(
    agent=agent, app_name=APP,
    session_service=InMemorySessionService(),
    memory_service=memory,               # without it: "memory service is not available"
    auto_create_session=True,
)


async def wait_for_memory() -> None:   # async generation
    # Memory generation is asynchronous: poll for up to 1 min.
    for _ in range(12):
        r = await memory.search_memory(app_name=APP, user_id=USER, query="SMS")
        if r.memories:
            return
        await asyncio.sleep(5)


async def say(session_id: str, text: str) -> None:
    msg = types.Content(role="user", parts=[types.Part(text=text)])
    async for ev in runner.run_async(user_id=USER, session_id=session_id, new_message=msg):
        if ev.is_final_response():
            print(f"[{session_id}] agent>", ev.content.parts[0].text)


async def main(day: str) -> None:
    if day == "day1":
        await say("day1", "I'm on the Family 4-line plan and please only contact me by SMS.")
    else:
        await wait_for_memory()
        await say("day2", "My bill looks wrong this month. "
                          "How will you follow up?")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1]))
