"""Lab 8 build-up: production cache TTL and compaction for the Acme handbook agent.

Same agent as handbook_app.py. Only the App settings change (Uber's levers).
Tested against google-adk 2.13.0 source.
Measure it: run with
  ADK_EXPERIMENTAL_TELEMETRY_FEATURES=context_cache,compaction,token_usage
to add cache and compaction counters to the ADK telemetry spans.
"""
from google.adk.agents.context_cache_config import ContextCacheConfig
from google.adk.apps.app import App, EventsCompactionConfig  # not from google.adk.apps

from handbook_app import agent  # handbook_agent from step 1, unchanged

app = App(name="acme_support", root_agent=agent,
    context_cache_config=ContextCacheConfig(
        min_tokens=4096,
        ttl_seconds=3600,      # Uber: 5 min -> 1 h
        cache_intervals=10),
    events_compaction_config=EventsCompactionConfig(
        token_threshold=400_000,   # Uber: 400K on 1M models
        event_retention_size=10),  # keep the last 10 raw events
)
