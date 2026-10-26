# Lab 5B: Acme payouts that retry, pause and resume in a new process

A flaky payment gateway node (`pay`) retries with exact backoff. The workflow pauses for an
analyst, the process exits, and a second process answers the pause from the SQLite session.
`side_effects.log` proves that finished nodes are replayed, not run again.
Slides: ADK deck, chapter 5. Pattern from `contributing/samples/workflows/retry`
(google/adk-python v2.13.0) and https://adk.dev/runtime/resume/.

## Install (pinned)

```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install "google-adk==2.13.0"                       # Python 3.11+
```

## Env vars

None. There is no LLM node, so no API key is needed.

## Folder

```
lab5b-payouts-durable/      run every command from here
└── payouts/
    ├── __init__.py         empty
    └── app.py              nodes, App, Runner and the driver main()
```

Files the run creates here: `payouts.db` (SQLite session), `pending.json` (both ids),
`side_effects.log`. For a fresh run, delete all three.

## Run

```bash
python -m payouts.app start "ACME-GmbH"   # process 1: kyc_lookup, analyst_review pauses, exit
python -m payouts.app resume yes          # process 2: a new interpreter answers the pause
cat side_effects.log                      # exactly one line
```

Crash test: press Ctrl-C during attempt 2 of `resume`, then

```bash
python -m payouts.app continue -          # run_async(invocation_id=...) with no new message
```

`continue` needs `ResumabilityConfig(is_resumable=True)`. Without it, the call fails with
`ValueError: Running an agent requires a new_message or a resumable app.`
The docs say this crash resume is not supported from `adk web` or `adk run`.

## Expected output (illustrative, not executed)

```
$ python -m payouts.app start "ACME-GmbH"
PAUSED -> pending.json
$ python -m payouts.app resume yes
[payouts] gateway attempt 1
[payouts] gateway attempt 2
[payouts] gateway attempt 3
OUTPUT: PAID idempotency_key=payout-e-9c1...
$ cat side_effects.log
kyc_lookup ACME-GmbH
```

With `jitter=0.0` the waits are exactly 0.5 s, then 1.0 s
(`initial_delay * backoff_factor ** (attempt - 1)`). The attempt counter is not persisted:
after a crash and `continue`, `pay` gets its full retry budget back.

## Notes

- `exceptions` matches class names along the MRO. A `timeout=2.0` failure raises
  `NodeTimeoutError`, so it is retried only because `"NodeTimeoutError"` is in the list.
- `RetryConfig()` with no arguments resolves to max_attempts=5, initial_delay=1.0,
  max_delay=60, backoff_factor=2.0, jitter=1.0: the wait before try 2 is anywhere in 0-2 s.
- Resume is at-least-once ("Tool call to resume needs to be idempotent"), so the gateway must
  dedupe on `payout-<invocation_id>`.
