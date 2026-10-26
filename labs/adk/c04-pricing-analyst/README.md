# Lab 4 · build · Acme competitor premiums (AgentTool subagents)

`pricing_analyst` calls two subagents through `AgentTool`: `price_search` holds only `google_search`,
`price_math` runs Python in Gemini's sandbox (`BuiltInCodeExecutor`). Each subagent keeps its own
context; only a short result returns to the root.

```
pricing_analyst/
  __init__.py     # from . import agent
  agent.py
  .env            # built-in tools need Gemini
```

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install "google-adk==2.13.0"
```

## Environment (`pricing_analyst/.env`)

```
GOOGLE_GENAI_USE_ENTERPRISE=FALSE
GOOGLE_API_KEY=<key from Google AI Studio>
```

## Run

```bash
adk web .
```

Pick `pricing_analyst` and ask:
`What do the top US insurers charge for comprehensive cover on a 2024 Civic? Give the average.`

## Expected output (illustrative; P1..P3 are placeholders, not real premiums)

```
[pricing_analyst]: function_call price_search {"request": "2024 Civic comprehensive premium US"}
[pricing_analyst]: function_response [{"retailer": "Insurer A", "price_usd": P1, ...}, ...]
[pricing_analyst]: function_call price_math {"request": "prices = [P1, P2, P3]"}
[price_math]: executable_code: print(sum(prices) / len(prices), ...)
[price_math]: code_execution_result: MEAN MIN MAX SPREAD
[pricing_analyst]: Average $X (range $MIN-$MAX, spread $SPREAD). Sources: ...
```

## What to notice

- Gemini 2.x rejects `google_search` plus a function tool in one agent:
  `400 INVALID_ARGUMENT: Tool use with function calling is unsupported`.
  Gemini 3 and later accept the mix (`utils/model_name_utils.py` L199-214). On older models,
  `GoogleSearchTool(bypass_multi_tools_limit=True)` swaps in a search sub-agent for you.
- `AgentTool` returns control to the caller (unlike `sub_agents`, which transfer away).
- Since 2.13, `google_search` grounding is recorded on LLM spans, so you can audit the URLs.
- Recompute from raw numbers: arXiv 2609.37153 shows plausible but wrong tool evidence lowers
  data-agent task success by 26-39 points.

Sources: samples `tools/built_in_multi_tools` and `code_execution/code_execution` at
https://github.com/google/adk-python/tree/v2.13.0
