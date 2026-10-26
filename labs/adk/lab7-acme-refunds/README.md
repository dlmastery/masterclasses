# Lab 7: the Acme refund team (MCP, A2A, Skills, Plugins)

One Acme refund agent (`refund_core.py`) is reused four ways:

| Step | What | Files | Process |
|---|---|---|---|
| 1 | The agent as one MCP tool | `refund_mcp_server.py`, `consumer/` | terminal 1 + terminal 3 |
| 2 | The agent as an A2A service with an agent card | `refund_service/a2a_server.py` | terminal 2 |
| 3 | Support triage delegates over A2A | `triage/` | terminal 3 (`adk web`) + terminal 2 |
| 4-5 | The refund policy as an Agent Skill | `refund_skill_agent/` | `adk web` |
| 6 | One plugin caps refunds at $500 for every agent | `refund_guard.py`, `guarded_app.py` | `python` |
| extra | Preselect top-k skills (arXiv 2610.18522) | `refund_skill_agent/preselect.py` | `python -m` |
| extra | Variable pinning (Rippling pattern) | `pinning.py` | import as tools |
| extra | Gotcha fixes: public card URL, client token | `deploy/` | reference |

Tested on google-adk 2.13.0, mcp 2.3.0, a2a-sdk 1.2.3, Python 3.11+.

## Install (every terminal)

```bash
cd labs/adk/lab7-acme-refunds
pip install "google-adk[mcp,a2a]==2.13.0" "mcp==2.3.0"
export GOOGLE_GENAI_USE_ENTERPRISE=0
export GOOGLE_API_KEY=your-key
export ADK_SUPPRESS_EXPERIMENTAL_FEATURE_WARNINGS=1   # to_mcp_server is EXPERIMENTAL
```

`python` and `uvicorn` do not read an agent folder's `.env` file, so export the variables in each terminal.

Test orders (in `refund_core.py`):

| id | category | days | amount |
|---|---|---|---|
| A-100 | apparel | 12 | $79 |
| A-200 | electronics | 45 | $640 |
| A-300 | apparel | 42 | $120 |

## Step 1: MCP

```bash
# terminal 1
python refund_mcp_server.py          # serves http://127.0.0.1:8090/mcp
# terminal 3
adk run consumer
```

Expected output (illustrative):

```
[user]: Can order A-200 be refunded?
[cs_frontline]: call refund_agent {"request": "Can order A-200 be refunded?"}
  -> "NOT_REFUNDABLE: electronics have a 14-day window; A-200 is 45 days old."
```

## Step 2: A2A server

```bash
# terminal 2
uvicorn refund_service.a2a_server:a2a_app --host localhost --port 8001
curl -s http://localhost:8001/.well-known/agent-card.json
```

Expected card keys (illustrative; the exact A2A 1.0 layout can differ):

```
{"name": "refund_agent", "url": "http://localhost:8001/",
 "capabilities": {"streaming": true},
 "skills": [{"id": "refund_agent", ...}, {"id": "refund_agent-lookup_order", ...}]}
```

## Step 3: A2A client

```bash
# terminal 3 (stop adk run consumer first), keep uvicorn from step 2 running
adk web .            # pick "triage"
```

Prompt: `I want to return order A-100, it doesn't fit.` Expected (illustrative):

```
[support_triage]: transfer_to_agent -> refund_agent
[refund_agent]: REFUNDABLE: A-100 is apparel (30-day window) and was bought 12 days ago.
```

## Steps 4-5: Agent Skill

```bash
cd refund_skill_agent/skills/refund-policy
python scripts/prorate.py --amount 120 --days 42      # prints 72.0
cd ../../..
adk web .            # pick "refund_skill_agent"
```

Prompt: `Order A-300 is a jacket I bought 42 days ago. Can I get money back?` Expected tool trace (illustrative):

```
list_skills {}  -> [{"name": "refund-policy", ...}]
load_skill {"skill_name": "refund-policy"}  -> SKILL.md body
lookup_order {"order_id": "A-300"}  -> {"days_since_purchase": 42, "amount": 120.0, ...}
load_skill_resource {..., "file_path": "references/policy.md"}
run_skill_script {..., "file_path": "scripts/prorate.py", "args": {"amount": 120.0, "days": 42}}
  -> stdout "72.0"
[agent]: PARTIAL_REFUND 72.00 - past 30 days, inside 60 days.
```

`UnsafeLocalCodeExecutor` runs scripts with `exec()` in your process and `script_timeout` does not apply. Use it on a laptop only; use `ContainerCodeExecutor` or `GkeCodeExecutor` in production.

## Step 6: plugin

```bash
python guarded_app.py
# or, with no code change:
adk web --extra_plugins=refund_guard.RefundGuardPlugin .
```

Expected (illustrative):

```
User > Refund $79 on A-100  -> refunds: {"status": "ok", "refunded": 79.0}
User > Partner-store order: refund $640 on A-200
  -> partner_refunds: {"status": "blocked", "reason": "640.0 exceeds limit 500.0"}
```

## Extras

```bash
python -m refund_skill_agent.preselect    # one short-lived agent per ticket, top-3 skills
```

`SkillLifecycleMode.BOUNDED` caps active skills at 3. Evicted skill text leaves the request (and `unload_skill` appears) only with `ADK_ENABLE_SKILL_LIFECYCLE=1`.

## Sources

- Codelab: Getting Started with MCP, ADK and A2A — https://codelabs.developers.google.com/getting-started-mcp-a2a-adk
- Docs: A2A Exposing — https://adk.dev/a2a/quickstart-exposing/ · A2A Consuming — https://adk.dev/a2a/quickstart-consuming/
- Docs: Skills for ADK agents — https://adk.dev/skills/ · Spec: https://agentskills.io/specification
- Docs: Plugins — https://adk.dev/plugins/
