# Lab 2: the Acme claims API (chapter 2)

Typed claim intake with `output_schema`, an `App` with an audit plugin, the same App over
REST and SSE, state prefixes, and sessions in a SQLite file that survive a restart.

Tested against **google-adk 2.13.0** source (tag v2.13.0). Python 3.11 or newer.
Nothing here was executed by the course authors: every "expected output" below is **illustrative**.
The model's wording will differ on your machine.

## Install

```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install "google-adk==2.13.0"                       # or: pip install -r requirements.txt
```

## Environment variables

```bash
export GOOGLE_GENAI_USE_ENTERPRISE=0                   # 0 = AI Studio key, 1 = Agent Platform
export GOOGLE_API_KEY=your-ai-studio-key
# PowerShell: $env:GOOGLE_GENAI_USE_ENTERPRISE="0"; $env:GOOGLE_API_KEY="..."
```

`adk run`, `adk web` and `adk api_server` also read `agents/claims_api/.env`
(copy `.env.example` to `.env`). The plain Python scripts do not read `.env`: export the variables.

## Folder tree

```
lab2-claims-api/
  claims/
    email_77.txt          the loss email
    claim_intake.py       step 1: output_schema + output_key + check_claim
    claims_faq.py         build: app: / user: / temp: / no-prefix state
    claims_followup.py    build: SqliteSessionService, survives a restart
    mark_reviewed.py      gotcha: get_session returns a copy
  agents/
    claims_api/
      __init__.py         from . import agent
      agent.py            step 2: App + LoggingPlugin + AuditPlugin
      .env.example
    run_claims.py         the one App from Python, SQLite sessions
  rest_calls.sh           step 3: curl calls for /run, /run_sse, session GET
```

## Run, step by step (from this folder)

| Step | Command | Expected output (illustrative) |
|---|---|---|
| 1 | `python claims/claim_intake.py claims/email_77.txt` | `{"reasoning": "Rear-end, $6,400, no injury.", "claim_type": "auto_collision", "severity": "medium", "policy_number": "POL-448120", "estimated_loss_usd": 6400.0, "injuries_reported": false}` (no `incident_date` key: the email has no year, so the value is null and is dropped) |
| 2 | `adk run agents/claims_api`, then ask "What is my collision deductible on POL-448120?" | `[claims_assistant]: Your collision deductible on POL-448120 is $500.` and `audit_log = ["lookup_policy({'policy_number': 'POL-448120'})"]` in state |
| 3 | Terminal 1: `adk api_server agents --port 8000`. Terminal 2: `bash rest_calls.sh` | `["claims_api"]`, the new session, a JSON list of 3 events, 3 `data:` lines, then the session with 2 `audit_log` entries |
| 4 | `python claims/claims_faq.py` | `s2.state: {'app:company_name': 'Acme', 'user:customer_name': 'Tom', 'user:language': 'English', 'user:topics_asked': ['glass']}` |
| 5 | `python claims/claims_followup.py "My car is a 2024 Civic."` then `python claims/claims_followup.py "Which car did I say I have?"` | `(events stored: 2)`, then `You said you have a 2024 Civic.` and `(events stored: 4)` |
| 6 | `python claims/mark_reviewed.py` | `after the copy edit: None`, then `after state_delta: reviewed` |
| 7 | `cd agents && python run_claims.py` | `Yes, glass is covered on POL-448120.` (writes `agents/claims_sessions.db`) |

Delete `claims_sessions.db` to start fresh.

## Notes

- `output_key` stores `model_dump(exclude_none=True)`: a dict, and null fields are absent. Read optional keys with `.get()`.
- Put the schema in `output_schema`. `generate_content_config.response_schema` raises
  `Response schema must be set via LlmAgent.output_schema, not via generate_content_config.response_schema.`
- With an AI Studio key, a schema plus tools adds an internal `set_model_response` tool call. That is expected.
- Never pass `plugins=` to `Runner`: it is deprecated, and with `app=` it raises.
- On Windows, run `rest_calls.sh` in Git Bash or WSL.
- Postgres: `pip install "google-adk[db]==2.13.0" asyncpg` and use `DatabaseSessionService(db_url="postgresql+asyncpg://...")`.

## Sources

- Repo sample: https://github.com/google/adk-python/tree/v2.13.0/contributing/samples/core/input_output_schema
- Docs: https://adk.dev/apps/ , https://adk.dev/plugins/ , https://adk.dev/sessions/state/
- Codelab: "Building Stateful and Personalized Agents with ADK" https://codelabs.developers.google.com/codelabs/agent-memory/instructions
- Papers: arXiv 2608.08254 (schema text is a second prompt), arXiv 2609.23742 (valid JSON is not correct JSON)
