# Lab 1 · Acme refund desk: typed tools, `adk run`, `adk web`, Python runner

Chapter 1 of the Google ADK deck (slides `adk-c01-lab-*`). Tested against the
google-adk **2.13.0** source (tag v2.13.0). Nothing here was executed by the deck
authors, so every output below is **illustrative**: the shape is right, the model's
wording will differ.

## Install (Python 3.11+)

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install "google-adk==2.13.0"
```

## Environment

Copy `refund_agent/.env.example` to `refund_agent/.env`, or export in the shell:

```bash
GOOGLE_GENAI_USE_ENTERPRISE=0
GOOGLE_API_KEY=your-ai-studio-key
```

`GOOGLE_GENAI_USE_VERTEXAI` still works but raises
`DeprecationWarning: GOOGLE_GENAI_USE_VERTEXAI is deprecated, please use GOOGLE_GENAI_USE_ENTERPRISE instead`.

## Files

```
lab1-refund-tools/
├── refund_agent/          # folder = Python package: no hyphens
│   ├── __init__.py        # from . import agent
│   ├── agent.py           # defines root_agent + two tools
│   └── .env.example
├── run_refund.py          # InMemoryRunner: run_debug, run_async, isolation
└── run_capped.py          # RunConfig(max_llm_calls=20) gotcha fix
```

To start from scratch instead: `adk create refund_agent --model gemini-3.5-flash --api_key $GOOGLE_API_KEY`,
then replace `agent.py` with the one in this folder.

## Run (from this folder, the one that contains `refund_agent/`)

```bash
adk run refund_agent "Can I return order A-1002? I just changed my mind."   # one-shot
adk run refund_agent                                                         # interactive; type exit
adk run refund_agent --in_memory --jsonl "Is A-1003 refundable? It arrived damaged."
adk web --port 8000        # open http://127.0.0.1:8000, pick refund_agent, open the Events tab
python run_refund.py
python run_capped.py
```

## Expected output (illustrative)

`adk run refund_agent "Can I return order A-1002? I just changed my mind."`

```
[user]: Can I return order A-1002? I just changed my mind.
[refund_agent]: I checked order A-1002 (electronics, $1,299.00). It was delivered 41 days ago,
and our policy allows change-of-mind returns within 30 days, so it is not eligible for a refund.
If the item is damaged or is the wrong item, it is refundable regardless of the window.
```

`python run_refund.py`

```
refund_agent > [Calling tool: lookup_order({'order_id': 'A-1001'})]
refund_agent > [Tool result: {'status': 'success', 'order': {'email': 'dana@example.com', ...}}]
refund_agent > [Calling tool: check_refund_eligibility({'order_id': 'A-1001', 'reason': 'changed_mind'})]
refund_agent > [Tool result: {'status': 'success', 'eligible': True, 'window_days': 30, 'days_since_delivery': 12}]
refund_agent > Yes. A-1001 (apparel) was delivered 12 days ago, inside our 30-day window, so it is eligible.
  TOOL CALL  lookup_order({'order_id': 'A-1003'})
  TOOL RESULT lookup_order -> {'status': 'success', 'order': {...}}
  TOOL CALL  check_refund_eligibility({'order_id': 'A-1003', 'reason': 'damaged'})
  TOOL RESULT check_refund_eligibility -> {'status': 'success', 'eligible': True, 'rule': 'defect_override'}
[refund_agent] A-1003 is groceries, which are normally final sale, but damaged items are always refundable.
refund_agent > I don't have any earlier messages from you in this conversation.
```

## What to look at

- The docstring becomes the tool description verbatim; ADK does not parse an `Args:` section.
  Per-parameter text goes in `Annotated[str, Field(description=...)]`.
- `Literal[...]` becomes an enum; a default makes the parameter optional.
- A missing mandatory argument comes back to the model as an error dict:
  ``Invoking `check_refund_eligibility()` failed as the following mandatory input parameters are not present: ...``
- Return a `dict`. Any other return value arrives as `{'result': value}`.
- `run_debug()` is "for debugging and experimentation only". Production code uses `run_async()`
  and logs every function call and response.

## Common errors

| Message | Fix |
|---|---|
| ``Found invalid agent name: `refund-agent`. Agent name must be a valid identifier...`` | Use `name="refund_agent"`; never `user` |
| `Invalid agent name: 'refund-agent'. Agent names must be valid Python identifiers ...` | Rename the folder to `refund_agent` |
| `No root_agent found for 'refund_agent'. Searched in ...` | Name the variable `root_agent`; keep `from . import agent` in `__init__.py` |
| `Session not found: <id>` | `create_session(app_name=APP, ...)` first, or `Runner(..., auto_create_session=True)` |
| ``Max number of llm calls limit of `500` exceeded`` | Clear error dicts; `RunConfig(max_llm_calls=20)` or `ADK_MAX_LLM_CALLS=20` |
| `WARNING: The --reload flag is not supported on Windows ... Forcing --no-reload.` | Expected on Windows: restart `adk web` after each edit |

## Sources

- Python Quickstart for ADK: https://adk.dev/get-started/python/
- Codelab, Building AI Agents with ADK: The Foundation: https://codelabs.developers.google.com/devsite/codelabs/build-agents-with-adk-foundation
- google/adk-python v2.13.0, `contributing/samples/core/runner_debug_example`: https://github.com/google/adk-python/tree/v2.13.0
