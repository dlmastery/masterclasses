"""Paper follow-up (arXiv 2610.18522): preselect the top-k skills per ticket.

Above ~50 skills, rank the catalog first and give the agent only the top k.
Run:  python -m refund_skill_agent.preselect   (from lab7-acme-refunds/)
"""
import asyncio
import pathlib

from google.adk.agents import LlmAgent
from google.adk.code_executors import UnsafeLocalCodeExecutor
from google.adk.runners import InMemoryRunner
from google.adk.skills import load_skill_from_dir
from google.adk.tools.skill_toolset import (
    SkillLifecycleConfig, SkillLifecycleMode, SkillToolset)
from refund_core import lookup_order

HERE = pathlib.Path(__file__).parent
CATALOG = {"refund-policy": "refund return chargeback prorate"}  # 1 line per folder


def preselect(ticket: str, k: int = 3) -> list:
    words = set(ticket.lower().split())           # swap for BM25 or embeddings
    rank = lambda s: len(words & set(CATALOG[s].split()))
    top = sorted(CATALOG, key=rank, reverse=True)[:k]
    return [load_skill_from_dir(HERE / "skills" / s) for s in top]


def build_agent(ticket: str) -> LlmAgent:
    skills = SkillToolset(
        skills=preselect(ticket),
        additional_tools=[lookup_order],
        code_executor=UnsafeLocalCodeExecutor(),
        # evicted skill text is pruned only with ADK_ENABLE_SKILL_LIFECYCLE=1
        lifecycle_config=SkillLifecycleConfig(
            default_mode=SkillLifecycleMode.BOUNDED, max_active_skills=3))
    return LlmAgent(name="refund_skill_agent", model="gemini-3.5-flash", tools=[skills])


async def main():
    t = "Order A-300 is a jacket I bought 42 days ago. Can I get a refund?"
    async with InMemoryRunner(agent=build_agent(t)) as r:
        await r.run_debug(t)


if __name__ == "__main__":
    asyncio.run(main())
