# c03 · Build · Port a 1.x SequentialAgent to a 2.x Workflow

`v1/` is the Acme support pipeline written for 1.x (`SequentialAgent`). `v2/` is the same pipeline as a
`Workflow` with one chain tuple. Slides: `adk-c03-migrate*`.

## Install (pinned)

```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install "google-adk==2.13.0" pytest               # Python 3.11+
```

## Environment

Copy `.env.example` to `.env` in `v1/support_desk/` and `v2/support_desk/`:
`GOOGLE_GENAI_USE_ENTERPRISE=FALSE`, `GOOGLE_API_KEY=<AI Studio key>`.

## Folder

```
c03-migrate-sequential/
├── v1/                     <- run from here for the 1.x version
│   ├── support_desk/  __init__.py  agent.py  tools.py  .env
│   └── tests/test_import.py
└── v2/                     <- run from here for the 2.x version
    ├── support_desk/  __init__.py  agent.py  tools.py  .env
    └── tests/test_import.py
```

## Run

```bash
cd v2
adk run support_desk "refund A-1001 arrived broken"
python -W error::DeprecationWarning -m pytest tests/      # the CI gate: passes on v2

cd ../v1
python -W error::DeprecationWarning -m pytest tests/      # fails on v1
```

## Expected output (illustrative: not executed)

```
$ python -W error::DeprecationWarning -m pytest tests/      # in v1/
DeprecationWarning: SequentialAgent is deprecated in favor of Workflow and will be removed in a future version.
```

## The trap this lab shows

Inside a `Workflow`, `single_turn` agent nodes default to `include_contents='none'`. Without
`include_contents="default"`, `synthesizer_agent` gets only its system instruction plus the placeholder
user turn "Handle the requests as specified in the System Instruction." and answers
"Understood. Provide request" (google/adk-python issue #5780). Remove the `include_contents` line in
`v2/support_desk/agent.py` to see it.

## Modes

- `single_turn`: a one-shot worker (the default for an agent node in a graph).
- `task`: asks the user for missing slots, then exits with a typed result (`finish_task`).
- `chat`: free conversation, only right after `START`. Anywhere else:
  `GraphValidationError: The agent 'synthesizer_agent' has been added to the workflow with mode='chat' following node 'intake_agent'. This is not supported...`

Sources: https://github.com/google/adk-python/issues/5780 · https://adk.dev/2.0/
