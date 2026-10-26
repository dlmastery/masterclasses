# labs/adk/lab1-refund-tools/run_capped.py
# Gotcha fix: cap LLM calls per run so a tool-call loop fails fast and cheap.
# Default cap is 500 (ADK_MAX_LLM_CALLS overrides it); a loop then ends in
# LlmCallsLimitExceededError: "Max number of llm calls limit of `500` exceeded".
import asyncio

from google.adk.agents.run_config import RunConfig
from google.adk.runners import InMemoryRunner
from google.genai import types

from refund_agent.agent import root_agent

APP = "refund_agent"


async def main() -> None:
    runner = InMemoryRunner(agent=root_agent, app_name=APP)
    session = await runner.session_service.create_session(
        app_name=APP, user_id="cust-dana")
    msg = types.UserContent(parts=[types.Part(
        text="Is A-1002 refundable? I changed my mind.")])
    cfg = RunConfig(max_llm_calls=20)  # or ADK_MAX_LLM_CALLS=20
    async for ev in runner.run_async(
            user_id="cust-dana", session_id=session.id,
            new_message=msg, run_config=cfg):
        for call in ev.get_function_calls():
            print("TOOL CALL", call.name, call.args)
        if ev.is_final_response() and ev.content and ev.content.parts:
            text = "".join(p.text or "" for p in ev.content.parts)
            print(f"[{ev.author}] {text}")
    await runner.close()


if __name__ == "__main__":
    asyncio.run(main())
