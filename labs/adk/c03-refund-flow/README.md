# c03 · Lab 3.1-3.2 · Acme refund desk: a typed chain

`START -> parse_request -> check_policy -> write_reply -> audit_log`, one `Workflow` chain tuple.
Two function nodes, one LLM node, one function node. Slides: `adk-c03-lab-*` (chain, functions, reply, data paths, run).

## Install (pinned)

Python 3.11 or newer.

```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install "google-adk==2.13.0"
```

## Environment

Copy `refund_flow/.env.example` to `refund_flow/.env`:

| Variable | Value |
|---|---|
| `GOOGLE_GENAI_USE_ENTERPRISE` | `FALSE` (Gemini API key), or `TRUE` for Vertex AI |
| `GOOGLE_API_KEY` | your AI Studio key |

## Folder

```
c03-refund-flow/          <- run adk from here (the parent of refund_flow/)
└── refund_flow/
    ├── __init__.py       from . import agent
    ├── agent.py
    └── .env
```

## Run

```bash
adk run refund_flow "refund A-1001 arrived broken"
adk run refund_flow "refund A-1002 wobbly legs" --jsonl    # one JSON event per line, with node_path
adk web                                                    # pick refund_flow; the graph tab draws the chain
```

## Expected output (illustrative: not executed, model text invented)

```
[write_reply]: Thanks for reaching out about order A-1001. Your refund of $89.00 has been approved and will reach your card in 3-5 business days.
[refund_flow]: [audit] reply length=142 chars. WORKFLOW COMPLETED.
```

With `--jsonl` each event carries a `"node_path"` such as `"refund_flow@1/check_policy@1"`.
A-1002 was delivered 41 days ago (> 30), so `eligible` is `false` and the reply offers store credit.

## What to notice

- A plain function becomes a `FunctionNode`; its type hints set the input and output schemas.
- The return value of a node is the next node's `node_input`.
- `ctx.state["refund_case"] = ...` goes into the event's `state_delta`; the prompt reads `{refund_case}`.
- `audit_log(reply_text: str)` gets `reply_text` from state by name (the `output_key` of `write_reply`).
- `yield Event(message=...)`: `adk run` prints only message events. A plain `return` only sets output.
- Function nodes sign their events with the Workflow name (`refund_flow`). Filter on `event.node_info.path`.

## Errors to try

- Rename `reply_text` to `reply_txt` in `audit_log`:
  `WorkflowDataError: Missing value for parameter "reply_txt" ...`
- Change `write_reply` into a function typed `node_input: dict`:
  `GraphValidationError: ... Schema mismatch on edge check_policy -> write_reply ...`

Sources: https://adk.dev/graphs/ · https://adk.dev/graphs/data-handling/ ·
https://github.com/google/adk-python/tree/v2.13.0/contributing/samples/workflows/sequence
