# Lab 8 step 1: context cache for the Acme support handbook

The Acme mobile support agent sends the same long handbook on every request.
`static_instruction` + `ContextCacheConfig` cache that prefix from turn 2.

## Install (pinned)

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
pip install "google-adk==2.13.0"
```

## Environment (.env or shell)

```bash
GOOGLE_GENAI_USE_ENTERPRISE=FALSE
GOOGLE_API_KEY=your-key
```

## Files

```
c08-context-cache/
  handbook.md              # you write it: 4,096+ tokens (~3,100 words) of plan terms
  handbook_app.py          # step 1: cache the static prefix
  handbook_app_tuned.py    # build-up: TTL 3600 s + compaction at 400K
```

Check the size first: `client.models.count_tokens(model="gemini-3.5-flash", contents=HANDBOOK)`.
Below 4,096 tokens on Gemini 3, the cache never starts.

## Run

```bash
python handbook_app.py
```

## Expected output (illustrative, not executed)

```
prompt=9120 cached=None   # turn 1: caching starts on turn 2
prompt=9310 cached=8960   # turn 2: HIT
prompt=9480 cached=8960   # turn 3: HIT
```

## Notes

- Keep timestamps and `{state}` placeholders out of `static_instruction`. They change the prefix and every turn misses.
- Cached input tokens cost less, but the cache also bills storage for each hour of TTL.
- Source: https://github.com/google/adk-python/blob/v2.13.0/src/google/adk/agents/context_cache_config.py
