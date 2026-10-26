# Lab 4 · step 4 · Acme expense audit (orchestrator-workers with ctx.run_node)

The number of expense lines is known only at run time. `orchestrate` splits the input and starts one
`auditor` run per line with `ctx.run_node` inside `asyncio.gather`. A deterministic `policy_math`
node re-checks hotel lines that the model flagged.

```
expense_audit/
  __init__.py     # from . import agent
  agent.py
  .env            # same as Lab 4 step 3 (copy_review/.env)
```

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install "google-adk==2.13.0"
```

## Environment (`expense_audit/.env`)

```
GOOGLE_GENAI_USE_ENTERPRISE=FALSE
GOOGLE_API_KEY=<key from Google AI Studio>
```

## Run

From this folder (the parent of `expense_audit/`). Quote the input so the shell keeps the `$`:

```bash
adk run expense_audit 'Team dinner 4 people $260; Hotel Berlin 1 night $240; Wine for client $90'
```

## Expected output (illustrative, not executed; model text is invented)

```
[expense_audit]: Auditing 3 lines in parallel.
[expense_audit]: OK   Team dinner 4 people $260 — $65/person, under the $75 cap.
OK   Hotel Berlin 1 night $240 — Within hotel cap per deterministic check.
FLAG Wine for client $90 — Alcohol is not reimbursable.
```

## What to notice

- `@node(rerun_on_resume=True)` is required on any node that calls `ctx.run_node`. Without it:
  `ValueError: A node must have rerun_on_resume=True. ...`. On resume the parent re-runs from the
  top and finished children are replayed from history, so keep the parent thin.
- `use_sub_branch=True` isolates the parallel runs, so one auditor does not see another's events.
- Await children directly or through `asyncio.gather`. With `asyncio.create_task`, "errors are
  silently swallowed".
- `@node(parameter_binding="node_input")`: the dict keys `line` and `limit` bind to the parameters.
- A custom `run_id` must contain a non-numeric character, e.g. `f"line-{i}"`, not `"1"`.
- For an agent child, `node_input` becomes the user message, so the instruction has no placeholder.

Sources: https://adk.dev/graphs/dynamic/ ; codelab "ADK 2 Orchestration", level L4b
(https://codelabs.developers.google.com/adk2/instructions); samples `workflows/dynamic_fan_out_fan_in`
and `workflows/dynamic_nodes` at google/adk-python v2.13.0.
