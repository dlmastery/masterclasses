# Lab 4 · steps 1-2 · Acme claim checks (fan-out + JoinNode)

Three independent checks of one insurance claim run at the same time. A `JoinNode` waits for all
three, then `decide` gives one verdict. The graph has no model call, so it runs offline.

```
claim_checks/
  __init__.py   # from . import agent
  agent.py      # root_agent = Workflow(...)
```

## Setup

Python 3.11 or newer.

```bash
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install "google-adk==2.13.0"
```

## Environment

None. No LLM node, so no `.env` and no API key.

## Run

From this folder (the parent of `claim_checks/`). The query is a positional argument; without it
`adk run` opens an interactive prompt.

```bash
adk run claim_checks "POL-77 rear-end collision 4200"
adk run claim_checks "POL-77 total loss fire 18000"
adk run claim_checks "POL-99 hail 3000"
```

## Expected output (illustrative, not executed)

The graph has no LLM, so the code fixes the text.

```
[claim_checks]: APPROVE payout $3,490.00
[claim_checks]: REFER to SIU (fraud score 0.82)
[claim_checks]: DENY: policy inactive or payout 0
```

Approve: `min(4200 * 0.95 = 3,990, 20,000) - 500 = 3,490.00`.
Wall time is about 0.5 s (the slowest branch), not the 1.0 s sum, because the three async checks
overlap.

## What to notice

- The tuple `(policy_check, fraud_score, damage_estimate)` inside the chain makes the fan-out.
  `max_concurrency=3` is only a cap ("None or <= 0 means unlimited").
- `JoinNode` fires once, after all three predecessors. Its output is a dict keyed by node name.
- Remove `join_checks` and `decide` runs once per branch, with partial input (a `KeyError`).
- `decide` yields an `Event`: `adk run` prints only events with a `message`.

Sources: codelab "ADK 2 Orchestration: Graph, Collaborative & Dynamic Workflows", level L2a
(https://codelabs.developers.google.com/adk2/instructions); sample
https://github.com/google/adk-python/tree/v2.13.0/contributing/samples/workflows/fan_out_fan_in
