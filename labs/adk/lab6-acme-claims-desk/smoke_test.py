"""Startup smoke test: fail loudly if the stdio toolset does not load.

ADK does not raise when a toolset fails: it logs "will run without the
tools from toolset ..." and the agent keeps answering without them.
Run from the lab folder, with claims_api.py up (agent.py fetches its spec).
"""
import asyncio

from claims_agent.agent import claims_tools

EXPECTED = {"get_claim", "approve_claim", "login"}


async def main() -> None:
    try:
        tools = await claims_tools.get_tools()
    except Exception as exc:  # crash, print, bad path, timeout
        raise SystemExit(f"FAIL toolset did not load: {exc!r}")
    names = {t.name.removeprefix("claims_") for t in tools}
    if names != EXPECTED:
        raise SystemExit(f"FAIL expected {EXPECTED}, got {names}")
    print("OK", sorted(names))


asyncio.run(main())
