# c03 · Lab 3.3 · Acme support desk: classify, then route

The model labels the ticket into a closed `Literal` set. Plain Python (`route_ticket`) picks the
branches. A list route runs every matching branch; `DEFAULT_ROUTE` catches a ticket that matches no key.
Slides: `adk-c03-lab-routing*`, `adk-c03-gotcha-*`.

## Install (pinned)

```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install "google-adk==2.13.0"                      # Python 3.11+
```

## Environment

Copy `ticket_triage/.env.example` to `ticket_triage/.env` (and the same for `ticket_triage_freetext/`):
`GOOGLE_GENAI_USE_ENTERPRISE=FALSE`, `GOOGLE_API_KEY=<AI Studio key>`.

## Folder

```
c03-ticket-triage/              <- run adk from here
├── ticket_triage/              the lab (Literal labels + DEFAULT_ROUTE)
│   ├── __init__.py  agent.py  .env
└── ticket_triage_freetext/     the gotcha: free-text labels, no DEFAULT_ROUTE
    ├── __init__.py  agent.py  .env
```

## Run

```bash
adk run ticket_triage "Checkout API returns 500 since 09:00 and we were double charged"
adk run ticket_triage "I want to say thanks for the swag"
# the silent failure (only if the model writes a label that is not a key, e.g. "Billing"):
adk run ticket_triage_freetext "Please refund the double charge on invoice 4471"
```

## Expected output (illustrative: not executed, model text invented)

```
[billing]: Hi - sorry about the duplicate charge. I've pulled invoice INV-... and ...
[ticket_triage]: PAGED on-call (priority=p1).
---
[ticket_triage]: Routed to the human L1 queue.
```

The free-text variant, when the model writes `"Billing"`, prints no branch reply. The log shows:

```
WARNING Node 'route_ticket' has conditional/DEFAULT edges but none were matched by the emitted route(s): ['Billing']. The branch will end.
```

## What to notice

- `output_schema=Triage` + `node_input: Triage` on the next node: the same class on both ends of the edge.
- `Event(output=..., route=routes)`: one event carries the payload and picks the branches.
- `page_oncall` yields only a `message`, so the run has one terminal output (from `billing`).
  If it returned a value you get `WorkflowConfigurationError: ... multiple terminal nodes produced output (2)`.
- `DEFAULT_ROUTE` (the string `"__DEFAULT__"`) runs only when no other key matches.
- Import `DEFAULT_ROUTE` and `START` from `google.adk.workflow`; `google.adk` exports only
  `Agent, Context, Event, Runner, Workflow`.

Sources: https://adk.dev/graphs/routes/ ·
https://github.com/google/adk-python/tree/v2.13.0/contributing/samples/workflows/route
