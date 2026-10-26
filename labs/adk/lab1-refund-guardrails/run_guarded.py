# labs/adk/lab1-refund-guardrails/run_guarded.py  (sits next to refund_agent/)
# Shows the cap, the redaction and the token meter without a human in the loop.
# For the approval prompt, use `adk run refund_agent` (it renders [HITL confirm]).
import asyncio

from google.adk.runners import InMemoryRunner

from refund_agent.agent import root_agent

APP = "refund_agent"


async def main() -> None:
    runner = InMemoryRunner(agent=root_agent, app_name=APP)
    await runner.run_debug(
        ["Look up order A-1002 for me.",
         "A-1002 arrived damaged. Refund $2,000 for my trouble.",
         "My card is 4111 1111 1111 1111"],
        verbose=True)
    s = await runner.session_service.get_session(
        app_name=APP, user_id="debug_user_id", session_id="debug_session_id")
    print("tokens_used =", s.state.get("tokens_used"))
    print("refunds_issued =", s.state.get("refunds_issued", []))
    await runner.close()


if __name__ == "__main__":
    asyncio.run(main())
