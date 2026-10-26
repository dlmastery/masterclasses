# c03 · Lab 3.4 · The triage graph as YAML

The Lab 3.3 router, simplified (one label, three routes, no priority rule), as config:
topology and prompts in YAML (PM and legal review them as diffs), logic and schema in Python
(unit tests). Adapted from `contributing/samples/workflows/loop_config` (YAML loader sample).
Slides: `adk-c03-lab-yaml*`.

## Install (pinned)

```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install "google-adk==2.13.0"                      # Python 3.11+
```

## Environment

Copy `triage_yaml/.env.example` to `triage_yaml/.env`:
`GOOGLE_GENAI_USE_ENTERPRISE=FALSE`, `GOOGLE_API_KEY=<AI Studio key>`.

## Folder

```
c03-triage-yaml/            <- run adk from here (the parent folder)
└── triage_yaml/
    ├── root_agent.yaml     topology  (PR review)
    ├── classify.yaml       prompt    (legal review)
    ├── billing.yaml        prompt    (legal review)
    ├── agent.py            Triage schema + function nodes (unit tests)
    └── .env
```

No `__init__.py` is needed, the same as the `loop_config` sample.

## Run

```bash
adk run triage_yaml "We were charged twice for October"
adk web                    # the graph tab draws the YAML-defined workflow
```

## Expected output (illustrative: not executed, model text invented)

```
[billing]: Sorry about the duplicate October charge - I'm pulling up your invoice now ...
```

## Errors to try

- Run the same command from inside `triage_yaml/`:
  `ModuleNotFoundError: No module named 'triage_yaml'`. Run from the parent folder.
- Swap the two edges in `root_agent.yaml`:
  `ValueError: Unknown node 'route_ticket'. A node has to be defined by an earlier edge before another edge can name it.`

## What to notice

- `.agent.intake` resolves to `triage_yaml.agent.intake` and becomes a `FunctionNode`.
- A bare word (`route_ticket`) names a node from an earlier edge.
- Every `Triage.label` value has its own key, so no label goes unmatched.
  (`DEFAULT_ROUTE` is the string `"__DEFAULT__"`, but no official YAML sample uses that key yet.)
- Security: `name:` references import Python objects. Never build or load YAML from user input.

Source: https://github.com/google/adk-python/tree/v2.13.0/contributing/samples/workflows/loop_config
