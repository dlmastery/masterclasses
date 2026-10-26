# Uber's cost levers in ADK

Uber writes AI spend as users x sessions x turns x requests x tokens/request x price/token.
`acme_costs.py` sets the levers that act on the last two terms.

## Install (pinned)

```bash
pip install "google-adk==2.13.0"
```

## Environment

```bash
GOOGLE_GENAI_USE_ENTERPRISE=FALSE
GOOGLE_API_KEY=your-key
```

## Use

```python
from acme_costs import app, run_config
runner = Runner(app=app, session_service=InMemorySessionService())
# runner.run_async(user_id=..., session_id=..., new_message=..., run_config=run_config)
```

Measure before and after with
`ADK_EXPERIMENTAL_TELEMETRY_FEATURES=context_cache,compaction,token_usage`.

## Numbers (Uber post, 2026-08-27)

- Weekly agentic requests 9.4x (Feb-Aug 2026), weekly users 7x.
- Cost per session -52% from the June peak; cost per 1,000 model requests almost -34%.
- Interactive cache TTL 5 min -> 1 h; compaction at 400K tokens on 1M models.
- Source: https://uber.com/us/en/blog/efficient-software-factory
