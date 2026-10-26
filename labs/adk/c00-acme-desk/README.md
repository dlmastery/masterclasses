# c00 · Acme support desk (course opener, preview of Lab 3)

The graph from the first slide of the course as one runnable file:
`START -> intake -> classify -> pick -> {refund | answer} -> audit`.
`classify` is the only model call on the refund path. `pick` is plain code and picks the route.

## Setup (do this once, before Lab 1)

Python 3.11 or newer is required (google-adk 2.12.0 raised the minimum).

```bash
python3 --version                      # must be 3.11 or newer
python3 -m venv .venv                  # Windows: python, not python3
source .venv/bin/activate              # macOS / Linux
# .venv\Scripts\Activate.ps1           # Windows PowerShell (cmd.exe: .venv\Scripts\activate.bat)
pip install "google-adk==2.13.0"
pip show google-adk                    # Version: 2.13.0
adk --help                             # adk is on your PATH
```

## Environment

Copy `acme_desk/.env.example` to `acme_desk/.env` and set your key. `adk run` and `adk web` load it on
every OS, so you do not need `export` or `load_dotenv`. The `.gitignore` in this folder keeps `.env` out of git.

| Variable | Value |
|---|---|
| `GOOGLE_GENAI_USE_ENTERPRISE` | `FALSE` (use the API key, not a Cloud project) |
| `GOOGLE_API_KEY` | a key from https://aistudio.google.com/apikey |

Do not use the old name `GOOGLE_GENAI_USE_VERTEXAI`: it still works in google-adk 2.x but raises a
`DeprecationWarning` (`utils/env_utils.py`). If both are set, `GOOGLE_GENAI_USE_ENTERPRISE` wins.

## Run

From this folder (the parent of `acme_desk/`):

```bash
adk run acme_desk "Refund A-1001, broken"
adk run acme_desk "Do you ship to Canada?"
```

## Expected output (illustrative, not executed)

```
[acme_desk]: [audit] refund queued for A-1001
```

`intake`, `pick` and `refund` print nothing: only events with a `message` print, and function
nodes print under the workflow name. On the question path, `answer` replies under its own name and
`audit` then prints the answer it read from `session.state["outcome"]`.

## What to notice

- `output_schema=Ticket` keeps the label in a closed set (`Literal`).
- `{ticket}` in an instruction is read from `session.state`, where `intake` wrote it.
- `pick` yields `Event(route=..., output=...)`: `route` picks the edge, `output` becomes the next node's `node_input`.
- `audit(outcome: str)` gets `outcome` from state by parameter name: every parameter that is not `node_input`
  or `ctx` is read from `session.state`. A missing key raises `WorkflowDataError`.
- `edges`: a tuple of N nodes is a chain (`"START"` is allowed only there), a `(node, dict)` pair maps route
  labels to nodes, and a plain pair is one edge.
- A route label with no matching edge runs nothing and only logs a warning. Lab 3 adds `DEFAULT_ROUTE`.

Source: codelab "ADK 2 Orchestration" (https://codelabs.developers.google.com/adk2/instructions), https://adk.dev/graphs/
