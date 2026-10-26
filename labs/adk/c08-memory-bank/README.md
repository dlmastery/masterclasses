# Lab 8 step 2: Memory Bank for the Acme support agent

On day 1 the customer says she is on the Family 4-line plan and wants SMS only.
On day 2, in a new session, the agent already knows.

## Install (pinned)

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
pip install "google-adk[gcp]==2.13.0" "google-cloud-agentplatform>=2.2,<3"
gcloud services enable aiplatform.googleapis.com
gcloud auth application-default login
```

Needs a Google Cloud project with billing on.

## Environment

```bash
export GOOGLE_GENAI_USE_ENTERPRISE=TRUE
export GOOGLE_CLOUD_PROJECT=my-proj
export GOOGLE_CLOUD_LOCATION=us-central1
export AGENT_ENGINE_ID=$(python create_bank.py)   # one-off, billed resource
```

## Files

```
c08-memory-bank/
  create_bank.py       # creates the Agent Runtime that holds the Memory Bank
  support_memory.py    # the agent: after_agent_callback writes, preload_memory reads
```

## Run

```bash
python support_memory.py day1 && python support_memory.py day2
# dev-UI alternative, no code change:
adk web . --memory_service_uri="agentengine://$AGENT_ENGINE_ID"
```

## Expected output (illustrative, not executed)

```
[day1] agent> Got it: Family 4-line, and SMS only.
[day2] agent> I'll review your Family 4-line bill and follow up by SMS.
```

## Notes

- Memories are scoped by `app_name` + `user_id`. A new user id looks like a stranger.
- "Forget me": call `delete_memory` (new in 2.13). `delete_session` does not remove memories.
- Delete the Agent Runtime in the console when you finish: it bills to your project.
- Codelab: https://codelabs.developers.google.com/next26/dev-keynote/enhancing-agents-with-memory
