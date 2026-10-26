# labs/adk/lab1-refund-tools/run_refund.py  (sits next to the refund_agent/ folder)
import asyncio

from google.adk.runners import InMemoryRunner
from google.genai import types

from refund_agent.agent import root_agent

APP = "refund_agent"   # match the folder name


async def main() -> None:
    runner = InMemoryRunner(agent=root_agent, app_name=APP)

    # 1) Two-line debugging: creates session "debug_session_id" on first use.
    await runner.run_debug(
        "Is order A-1001 refundable? Changed my mind.",
        verbose=True)

    # 2) Production loop: explicit session, event stream.
    session = await runner.session_service.create_session(
        app_name=APP, user_id="cust-dana")
    msg = types.UserContent(parts=[types.Part(
        text="Is A-1003 refundable? It arrived damaged.")])
    async for event in runner.run_async(
            user_id="cust-dana", session_id=session.id, new_message=msg):
        for call in event.get_function_calls():
            print(f"  TOOL CALL  {call.name}({call.args})")
        for resp in event.get_function_responses():
            print(f"  TOOL RESULT {resp.name} -> {resp.response}")
        final = event.is_final_response()
        if final and event.content and event.content.parts:
            text = "".join(p.text or "" for p in event.content.parts)
            print(f"[{event.author}] {text}")

    # 3) Isolation: a new user/session does not see Dana's history.
    await runner.run_debug("What did I ask before?",
                           user_id="cust-li", session_id="li-1")
    await runner.close()


if __name__ == "__main__":
    asyncio.run(main())
