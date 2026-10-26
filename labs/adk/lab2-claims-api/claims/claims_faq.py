"""Lab 2, build: state prefixes decide what survives into a new chat.

Run from the lab folder:
    python claims/claims_faq.py
"""
import asyncio

from google.adk import Agent
from google.adk.runners import InMemoryRunner
from google.adk.tools import ToolContext
from google.genai import types

POLICIES = {
    "glass": "Glass damage is covered with no deductible.",
    "collision": "Collision is covered after a $500 deductible.",
    "rental": "A rental car is covered for up to 10 days.",
}


def get_policy(topic: str, tool_context: ToolContext) -> dict:
    """Return the policy text for a topic: glass, collision or rental."""
    tool_context.state["temp:last_topic"] = topic        # this turn only
    asked = tool_context.state.get("user:topics_asked", [])
    tool_context.state["user:topics_asked"] = asked + [topic]
    text = POLICIES.get(topic)
    if text is None:
        return {"status": "error", "error_message": "unknown topic"}
    return {"status": "success", "policy": text}


faq_agent = Agent(
    name="claims_faq_agent",
    model="gemini-3.5-flash",
    instruction=("Help {user:customer_name} at {app:company_name}. "
                 "Reply in {user:language?}. "
                 "Quote get_policy exactly."),
    tools=[get_policy],
    output_key="last_answer",           # this chat only
)


async def main() -> None:
    runner = InMemoryRunner(agent=faq_agent, app_name="claims_api")
    svc = runner.session_service
    s1 = await svc.create_session(
        app_name="claims_api", user_id="u-tom",
        state={"app:company_name": "Acme", "user:customer_name": "Tom"})
    msg = types.UserContent(parts=[types.Part(text="Is glass covered?")])
    async for _ in runner.run_async(
            user_id="u-tom", session_id=s1.id, new_message=msg,
            state_delta={"user:language": "English"}):
        pass
    s1 = await svc.get_session(app_name="claims_api", user_id="u-tom",
                               session_id=s1.id)
    print("s1.state:", s1.state)
    s2 = await svc.create_session(app_name="claims_api", user_id="u-tom")
    print("s2.state:", s2.state)          # app: and user: keys only


if __name__ == "__main__":
    asyncio.run(main())
