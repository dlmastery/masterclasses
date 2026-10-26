# Lab 5A: Acme refund approvals that wait for a manager

Refunds up to $500 go straight through. A larger refund stops at `manager_gate`,
the process exits, and a manager answers later from a new `adk run` process.
Slides: ADK deck, chapter 5 (`adk-c05-lab-*`). Adapted from
`contributing/samples/workflows/request_input_rerun` in google/adk-python v2.13.0.

## Install (pinned)

```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install "google-adk==2.13.0"                       # Python 3.11+
```

## Env vars

`refund_approval/` has an LLM node (`draft_reply`, `gemini-3.5-flash`), so it needs a key.
Copy `refund_approval/.env.example` to `refund_approval/.env`:

```
GOOGLE_GENAI_USE_ENTERPRISE=FALSE     # 2.x name; GOOGLE_GENAI_USE_VERTEXAI raises a DeprecationWarning
GOOGLE_API_KEY=<your AI Studio key>
```

`refund_confirm/` has no LLM node and needs no key.

## Folder

```
lab5a-refund-approval/          run every command from here
├── refund_approval/            RequestInput gate (steps 1-5)
│   ├── __init__.py             from . import agent
│   ├── .env
│   └── agent.py
└── refund_confirm/             node-level require_confirmation (build-up)
    ├── __init__.py
    └── agent.py
```

## Run: three separate processes, one session

```bash
adk run refund_approval "A-2040 820" --session_id case-2040 ; echo "exit=$?"
adk run refund_approval '{"approved": true, "note": "Offer 10% coupon too"}' --session_id case-2040
adk run refund_approval '{"approved": true, "amount": 700}' --session_id case-2040
```

Windows cmd: `"{\"approved\": true}"`. Windows PowerShell 5.1: `'{\"approved\": true}'`.

## Expected output (illustrative, not executed)

```
Session ID: case-2040
[draft_reply]: Dear customer, we are processing your refund of $820.0 for order A-2040 ...
[refund_approval]: (Paused for input...)
🚨 [PAUSED] Workflow is waiting for human input! 🚨
exit=2
Auto-resuming interrupt refund_approval_e7..._1 with input: {"approved": true, "note": "Offer 10% coupon too"}
[draft_reply]: Dear customer, your refund of $820.0 for A-2040 is on its way, plus a 10% coupon ...
[refund_approval]: (Paused for input...)
Auto-resuming interrupt refund_approval_e7..._2 with input: {"approved": true, "amount": 700}
[refund_approval]: REFUNDED $700.00 on A-2040 (idempotency key refund-A-2040).
```

The session lives in `refund_approval/.adk/` (SQLite). `adk run` exits with code 2 while paused.

## Build-up: node-level confirmation

```bash
adk run refund_confirm "A-2040 820" --session_id case-2040
adk run refund_confirm '{"confirmed": true}' --session_id case-2040
```

Illustrative output: `REFUNDED $820.00 on A-2040 (key refund-A-2040)`.
A plain `yes` reply raises
`WorkflowDataError: A tool confirmation response must be a ToolConfirmation payload, but got str.`
A rejection (`{"confirmed": false}`) skips the body; the node output is `{"error": "This tool call is rejected."}`.

## Reply types (the CLI JSON-parses replies when it can)

| manager types | `approve` | `42` | `true` | `{"approved": true}` |
|---|---|---|---|---|
| manager_gate gets | `str` | `int` | `bool` | `dict` |
| `ManagerDecision.model_validate` | ValidationError | ValidationError | ValidationError | ManagerDecision |

Docs: https://adk.dev/graphs/human-input/
