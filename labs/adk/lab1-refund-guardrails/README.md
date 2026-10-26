# Lab 1 build-up · Acme refund desk: policy in code (callbacks + human approval)

Chapter 1 of the Google ADK deck (slides `adk-c01-callbacks-*`, `adk-c01-hitl-*`).
It extends `../lab1-refund-tools` with a third tool, `issue_refund`, four callbacks and a
confirmation gate. Tested against the google-adk **2.13.0** source. Nothing was executed by
the deck authors: every output below is **illustrative**.

## Install (Python 3.11+)

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install "google-adk==2.13.0"
```

## Environment

Copy `refund_agent/.env.example` to `refund_agent/.env`:

```bash
GOOGLE_GENAI_USE_ENTERPRISE=0
GOOGLE_API_KEY=your-ai-studio-key
```

## Files

```
lab1-refund-guardrails/
├── refund_agent/
│   ├── __init__.py      # from . import agent
│   ├── agent.py         # 3 tools, 4 callbacks, FunctionTool(require_confirmation=needs_approval)
│   └── .env.example
└── run_guarded.py       # run_debug: cap, redaction, card guard, token meter
```

## What each control does

| Hook | Function | Effect |
|---|---|---|
| `before_model_callback` | `block_card_numbers` | A card number in the user turn never reaches the model |
| `before_tool_callback` | `refund_cap` | `issue_refund` over `app:refund_cap_usd` (default 1500) returns an error dict; the tool does not run |
| `after_tool_callback` | `redact_pii` | Emails in `lookup_order` results become `[email redacted]` |
| `after_model_callback` | `meter_tokens` | Adds `usage_metadata.total_token_count` to `state["tokens_used"]` |
| `FunctionTool(..., require_confirmation=needs_approval)` | `needs_approval` | Refunds over $200 wait for a human yes |

Return rules: model callbacks stop the chain on a truthy value; tool callbacks stop on any
non-None value, even `{}`. Plugin callbacks run first. Each `*_callback` field also takes a list.

## Run (from this folder)

```bash
adk run refund_agent          # try: "A-1002 arrived damaged. Refund the $1,299."  then answer: no
python run_guarded.py
```

## Expected output (illustrative)

`adk run refund_agent`

```
[user]: A-1002 arrived damaged. Refund the $1,299.
[HITL confirm] Please approve or reject the tool call issue_refund() by responding with a FunctionResponse with an expected ToolConfirmation payload.
  Type "yes" to confirm, anything else to reject.
[user]: no
[refund_agent]: I'm sorry, a supervisor declined the $1,299 refund for order A-1002.
```

`python run_guarded.py`

```
refund_agent > [Calling tool: lookup_order({'order_id': 'A-1002'})]
refund_agent > [Tool result: {'status': 'success', 'order': {'email': '[email redacted]', 'total_usd': 1299.0, ...}}]
refund_agent > [Calling tool: issue_refund({'order_id': 'A-1002', 'amount_usd': 2000.0})]
refund_agent > [Tool result: {'status': 'error', 'error_message': 'Refunds over $1500 are blocked by policy.'}]
refund_agent > I can't issue $2,000: refunds over $1,500 are blocked by policy.
refund_agent > For your security, please don't share card numbers here. I've flagged the ticket.
tokens_used = 2875
refunds_issued = []
```

## Gate messages (exact text from the 2.13.0 source)

- First gated call: `{"error": "This tool call requires confirmation, please approve or reject."}`
- Rejected: `{"error": "This tool call is rejected."}`
- In your own client: watch `event.long_running_tool_ids` and send a `FunctionResponse` with the
  same `id` and `{"confirmed": true}` or `{"confirmed": false}`. `adk web` shows a dialog.

## Gotchas

- A predicate that falls through returns `None`, and `None` skips the gate
  (https://github.com/google/adk-python/issues/7010, open). Always return a real `bool`.
- The predicate gets the tool's own arguments, so it must take the same parameter names
  (including `tool_context`), or Python raises
  `TypeError: needs_approval() got an unexpected keyword argument 'tool_context'`.
- Read the threshold from `app:` state if ops must change it without a deploy.

## Sources

- Types of callbacks: https://adk.dev/callbacks/types-of-callbacks/
- google/adk-python v2.13.0, `tools/function_tool.py`: https://github.com/google/adk-python/blob/v2.13.0/src/google/adk/tools/function_tool.py
- arXiv 2608.11274, Agent Safety Should Be a Runtime Contract: https://arxiv.org/abs/2608.11274
