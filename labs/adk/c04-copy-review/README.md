# Lab 4 · step 3 · Acme ad-copy review (evaluator-optimizer loop)

`write_copy` drafts a 2-sentence ad, `review_copy` grades it against the compliance policy, and
`gate` routes: `done` -> `publish`, `retry` -> back to the same `write_copy`, or `escalate` to Legal
after `MAX_ROUNDS = 3`. A graph cycle is not bounded automatically: `gate` is the bound.

```
copy_review/
  __init__.py     # from . import agent
  agent.py
  .env            # copy from .env.example
```

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install "google-adk==2.13.0"
cp copy_review/.env.example copy_review/.env       # then set your key
```

## Environment (`copy_review/.env`)

| Variable | Value |
|---|---|
| `GOOGLE_GENAI_USE_ENTERPRISE` | `FALSE` (Gemini API key) or `TRUE` (Vertex AI, plus project and location) |
| `GOOGLE_API_KEY` | a key from https://aistudio.google.com/apikey |

## Run

From this folder (the parent of `copy_review/`):

```bash
adk run copy_review "a unit-linked savings policy for first-time investors" --jsonl | grep node_path
# Windows: ... --jsonl | findstr node_path
```

## Expected output (illustrative, not executed; trimmed to node_path)

```
copy_review@1/brief@1
copy_review@1/write_copy@1
copy_review@1/review_copy@1
copy_review@1/gate@1          needs_fix
copy_review@1/write_copy@2    @2 = second run of the node
copy_review@1/review_copy@2
copy_review@1/gate@2          compliant
copy_review@1/publish@1
```

If the reviewer never says `compliant`, `gate@3` routes to `escalate@1`.

## What to notice

- `{draft?}` and `{feedback?}`: `?` makes a state placeholder optional (empty in round 1).
  `{brief}` without `?` raises if the key is missing.
- `publish(draft)` and `escalate(draft, round)` read their parameters from `ctx.state` by name.
- Reuse the same `write_copy` object for the back-edge. Two ways to break it:
  - an unrouted back-edge: `GraphValidationError: Graph validation failed. Unconditional cycle detected: write_copy -> review_copy -> write_copy. ...`
  - a second `Agent(name="write_copy")`: `GraphValidationError: Graph validation failed. Duplicate node names found: ['write_copy']...`

Sources: https://github.com/google/adk-python/tree/v2.13.0/contributing/samples/workflows/loop ,
https://adk.dev/graphs/routes
