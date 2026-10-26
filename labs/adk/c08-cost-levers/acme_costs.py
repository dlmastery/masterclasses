"""Uber's cost levers expressed in ADK 2.13.0 for the Acme support agent.

Levers: reasoning effort (thinking_level), cheaper subagent model, 1 h cache TTL,
compaction at 400K tokens, and a loop guard (max_llm_calls, not a budget).
"""
from google.adk import Agent
from google.adk.agents.context_cache_config import ContextCacheConfig
from google.adk.agents.run_config import RunConfig
from google.adk.apps.app import App, EventsCompactionConfig
from google.genai import types

ROOT_MODEL = "gemini-3.5-flash"       # re-benchmark every few weeks
SUB_MODEL = "gemini-3.1-flash-lite"   # cheaper, if evals pass
bill_lookup = Agent(name="bill_lookup", model=SUB_MODEL)
support = Agent(name="handbook_agent", model=ROOT_MODEL,
    sub_agents=[bill_lookup],
    generate_content_config=types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(
            thinking_level="medium")))         # Gemini 3 default: high
app = App(name="acme_support", root_agent=support,
    context_cache_config=ContextCacheConfig(
        min_tokens=4096, ttl_seconds=3600),    # 5 min -> 1 h
    events_compaction_config=EventsCompactionConfig(
        token_threshold=400_000, event_retention_size=10))
run_config = RunConfig(max_llm_calls=25)   # loop guard, not a budget
# pass it: runner.run_async(..., run_config=run_config)
