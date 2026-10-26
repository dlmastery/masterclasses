"""Lab 8 step 1: cache the static Acme handbook prefix with ContextCacheConfig.

Tested against google-adk 2.13.0 source. Output in README.md is illustrative.
"""
import asyncio
import pathlib

from google.adk import Agent, Runner
from google.adk.agents.context_cache_config import ContextCacheConfig
from google.adk.apps import App
from google.adk.sessions import InMemorySessionService
from google.genai import types

# The handbook must exceed the model minimum: 4,096 tokens on Gemini 3 (2,048 on Gemini 2.5).
HANDBOOK = pathlib.Path("handbook.md").read_text(encoding="utf-8")

agent = Agent(
    name="handbook_agent",
    model="gemini-3.5-flash",
    # Sent first and never templated: this is the byte-stable, cacheable prefix.
    static_instruction=types.Content(role="user", parts=[types.Part(text=HANDBOOK)]),
    # With static_instruction set, ADK sends this as user content after the prefix.
    instruction="Customer: {customer_name}. Answer only from the handbook. Cite the section.",
)

app = App(
    name="acme_support",
    root_agent=agent,
    context_cache_config=ContextCacheConfig(
        min_tokens=4096,      # compared with the previous request's prompt_token_count
        ttl_seconds=900,      # default 1800
        cache_intervals=10,   # invocations that reuse one cache before a refresh (1..100)
    ),
)

QUESTIONS = [
    "What does the Family 4-line plan include?",
    "Is roaming in Canada included?",
    "How do I dispute a charge?",
]


async def main() -> None:
    sessions = InMemorySessionService()
    runner = Runner(app=app, session_service=sessions)
    await sessions.create_session(
        app_name="acme_support", user_id="cust-42", session_id="s1",
        state={"customer_name": "Priya"},
    )
    for q in QUESTIONS:
        msg = types.Content(role="user", parts=[types.Part(text=q)])
        async for ev in runner.run_async(user_id="cust-42", session_id="s1", new_message=msg):
            if ev.is_final_response() and ev.usage_metadata:
                u = ev.usage_metadata
                print(f"prompt={u.prompt_token_count}", f"cached={u.cached_content_token_count}")


if __name__ == "__main__":
    asyncio.run(main())
