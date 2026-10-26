# Hands-on labs: your first ADK 2.0 agents (google-adk 2.13.0)

Research date: 2026-10-23. Scope: `Agent`/`LlmAgent`, FunctionTools and docstrings, `Runner`/`InMemoryRunner`, sessions, state (`output_key`, `{state}` templating, prefixes), callbacks, structured output (`output_schema`), `adk web` / `adk run` / `adk api_server`, and the `App` class.

## 0. Versions and how this file was verified

| Package | Version | Evidence |
|---|---|---|
| `google-adk` | **2.13.0**, uploaded to PyPI 2026-10-23T18:26:31 UTC, `requires_python >=3.11` | https://pypi.org/pypi/google-adk/json (fetched today) |
| `google-genai` | **2.33.0** latest. ADK 2.13.0 pins `google-genai>=2.30,<3` | https://pypi.org/pypi/google-genai/json; `requires_dist` of google-adk |
| `pydantic` | ADK pins `pydantic>=2.12,<3` | `requires_dist` |
| `aiosqlite` | **core** dependency (`aiosqlite>=0.21`), so `SqliteSessionService` needs no extra | `requires_dist` |
| `sqlalchemy` | only with `google-adk[db]` (`sqlalchemy[asyncio]>=2,<3`, `sqlalchemy-spanner>=1.14`) | `requires_dist`, extra `db` |

**How it was verified.** pip and PyPI downloads are blocked on this machine, so nothing below was executed. Instead I cloned the source at tag `v2.13.0` (commit `d68ca857d5e3bab8e968d4e5f98ef028eb37dc87`, 2026-10-23) and read it. Every import path, class name, parameter, default and error string in the labs was checked against that tree.
- Citations take the form `path:line`, relative to `https://github.com/google/adk-python/blob/v2.13.0/src/google/adk/`.
- Every "Expected output" block is **illustrative**. Its shape follows the printing code in the source (`utils/_debug_output.py:41-88` for `run_debug`, `cli/cli.py:99-109,413` for `adk run`), but the model's wording will differ on your machine.

**Facts these labs rely on, all verified in source:**
- `from google.adk import Agent, Context, Event, Runner, Workflow` are the lazy top-level exports (`__init__.py`, `_LAZY_MEMBERS`). `Agent` is a `TypeAlias` for `LlmAgent` (`agents/llm_agent.py:1373`).
- The default model is `LlmAgent.DEFAULT_MODEL = 'gemini-3.5-flash'` (`agents/llm_agent.py:289`). `adk create` offers `gemini-3.5-flash` or `gemini-3.8-flash` (`cli/cli_create.py:172-181`). All labs pin `model="gemini-3.5-flash"`.
- `ToolContext = Context` and `CallbackContext = Context` are plain aliases (`tools/tool_context.py`, `agents/callback_context.py`).
- Backend selection: `GOOGLE_GENAI_USE_ENTERPRISE` is checked first. `GOOGLE_GENAI_USE_VERTEXAI` still works but raises `DeprecationWarning: GOOGLE_GENAI_USE_VERTEXAI is deprecated, please use GOOGLE_GENAI_USE_ENTERPRISE instead` (`utils/env_utils.py:82-98`). `adk create` writes `GOOGLE_GENAI_USE_ENTERPRISE=0|1` (`cli/cli_create.py:134-142`).
- **Python version conflict:** the quickstart page (https://adk.dev/get-started/python/, title "Python Quickstart for ADK") still says "Python 3.10 or newer", but the 2.13.0 wheel requires `>=3.11`. Teach 3.11+.

**Common setup for every lab.** Python 3.11+ and an AI Studio key.
```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install "google-adk==2.13.0"
# .env in the agent folder (adk web/run load it), or export in the shell:
GOOGLE_GENAI_USE_ENTERPRISE=0
GOOGLE_API_KEY=your-ai-studio-key
# Agent Platform (ex-Vertex) instead:
# GOOGLE_GENAI_USE_ENTERPRISE=1  GOOGLE_CLOUD_PROJECT=my-proj  GOOGLE_CLOUD_LOCATION=us-central1
```

---

## Lab 1: Refund-policy agent with FunctionTools, run with `adk run` and `adk web`

> **VERIFIED against google-adk 2.13.0 source (tag v2.13.0, commit d68ca857), re-checked by the verifier on 2026-10-23: every import path, class/function name and parameter in the code.** Expected-output blocks stay illustrative (nothing was executed).

**Goal.** Build a retail refund agent with two Python tools. See how the function name, docstring and type hints become the tool schema. Run it from the CLI and the dev UI.

**Prerequisites.** Common setup. Scaffold with `adk create refund_agent --model gemini-3.5-flash --api_key $GOOGLE_API_KEY`. This creates `refund_agent/{agent.py,__init__.py,.env}`; the template is at `cli/cli_create.py:29-38`. Replace `agent.py` with the code below.

Adapted from the official quickstart "Python Quickstart for ADK" (https://adk.dev/get-started/python/) and the repo sample `contributing/samples/core/runner_debug_example/agent.py`. The business scenario is changed to refunds.

```python
# refund_agent/agent.py
from typing import Annotated, Literal

from pydantic import Field
from google.adk import Agent

ORDERS = {
    "A-1001": {"email": "dana@example.com", "total_usd": 89.0, "days_since_delivery": 12, "category": "apparel"},
    "A-1002": {"email": "li@example.com", "total_usd": 1299.0, "days_since_delivery": 41, "category": "electronics"},
    "A-1003": {"email": "sam@example.com", "total_usd": 24.5, "days_since_delivery": 3, "category": "grocery"},
}
RETURN_WINDOW_DAYS = {"apparel": 30, "electronics": 30, "grocery": 0}


def lookup_order(order_id: Annotated[str, Field(description="Order ID, e.g. A-1001")]) -> dict:
    """Look up an order. Always call this before answering a refund question."""
    order = ORDERS.get(order_id.strip().upper())
    if order is None:
        return {"status": "error", "error_message": f"No order with ID {order_id}."}
    return {"status": "success", "order": order}


def check_refund_eligibility(
    order_id: str,
    reason: Literal["changed_mind", "damaged", "wrong_item"] = "changed_mind",
) -> dict:
    """Apply the refund policy: 30-day window; grocery is final sale unless damaged.

    Damaged or wrong items are always refundable, inside or outside the window.
    """
    order = ORDERS.get(order_id.strip().upper())
    if order is None:
        return {"status": "error", "error_message": f"No order with ID {order_id}."}
    if reason in ("damaged", "wrong_item"):
        return {"status": "success", "eligible": True, "rule": "defect_override"}
    window = RETURN_WINDOW_DAYS[order["category"]]
    eligible = order["days_since_delivery"] <= window
    return {"status": "success", "eligible": eligible, "window_days": window,
            "days_since_delivery": order["days_since_delivery"]}


root_agent = Agent(
    name="refund_agent",
    model="gemini-3.5-flash",
    description="Answers refund-eligibility questions for retail orders.",
    instruction=(
        "You are a refund desk assistant. Use lookup_order, then "
        "check_refund_eligibility. Quote the rule you applied. Never promise a "
        "refund the tool did not approve."
    ),
    tools=[lookup_order, check_refund_eligibility],
)
```

**Run it** from the folder that *contains* `refund_agent/`:
```bash
adk run refund_agent "Can I return order A-1002? I just changed my mind."   # one-shot query (positional QUERY arg)
adk run refund_agent                                                         # interactive; type exit to quit
adk run refund_agent --in_memory --jsonl "Is A-1003 refundable? It arrived damaged."
adk web --port 8000        # then open http://127.0.0.1:8000 and pick refund_agent
```
These flags are verified in `cli/cli_tools_click.py:1009-1100`: a positional `query`, `--in_memory`, `--jsonl`, `--state`, `--state_file`, `--timeout`, `--save_session` and `--replay`/`--resume`. For `adk web`, the default host is `127.0.0.1` and the default port is `8000` (`fast_api_common_options`).

**Expected output (illustrative):**
```
[user]: Can I return order A-1002? I just changed my mind.
[refund_agent]: I checked order A-1002 (electronics, $1,299.00). It was delivered 41 days ago,
and our policy allows change-of-mind returns within 30 days, so it is not eligible for a refund.
If the item is damaged or is the wrong item, it is refundable regardless of the window.
```

**Walk-through of the key lines:**
1. `Annotated[str, Field(description=...)]` gives the parameter its own description in the JSON schema. The JSON-schema function-declaration path (`FeatureName.JSON_SCHEMA_FOR_FUNC_DECL`) is STABLE and on by default (`features/_feature_registry.py:208-210`), and `Annotated` metadata is handled in `tools/_function_tool_declarations.py:305-307`.
2. **The docstring becomes the tool description verbatim.** `get_callable_doc()` returns the *cleaned whole docstring* (`utils/_callable_utils.py:177`; it is used at `_function_tool_declarations.py:564`). ADK does **not** parse an `Args:` section into per-parameter descriptions. Put the policy and the "when to call me" text in the docstring, and put per-parameter text in `Field(description=...)`.
3. `Literal[...]` becomes an enum in the schema, so the model cannot invent a reason such as `"broken"`.
4. A parameter with a default is optional. Without one it is mandatory, and when the model omits it, ADK returns an error dict to the model instead of raising: ``"Invoking `check_refund_eligibility()` failed as the following mandatory input parameters are not present: ..."`` (`tools/function_tool.py:491-500`). The model usually retries.
5. Return a `dict`. Any non-dict return value is wrapped as `{'result': value}` (`flows/llm_flows/tools/_caller.py:67`).
6. `name="refund_agent"` must be a Python identifier and must not be `"user"` (`agents/base_agent.py:728-740`).

**Common errors:**
| Exact message | Cause | Fix |
|---|---|---|
| ``Found invalid agent name: `refund-agent`. Agent name must be a valid identifier. It should start with a letter (a-z, A-Z) or an underscore (_), and can only contain letters, digits (0-9), and underscores.`` (`base_agent.py:729-734`) | Hyphen in `name=` | Use `refund_agent` |
| `Invalid agent name: 'refund-agent'. Agent names must be valid Python identifiers (letters, digits, and underscores only).` (`cli/utils/agent_loader.py:281-284`) | The **folder** has a hyphen (`adk create refund-agent`) | Rename the folder. It is imported as a Python package |
| `No root_agent found for 'refund_agent'. Searched in 'refund_agent.agent.root_agent', 'refund_agent.root_agent' and 'refund_agent/root_agent.yaml'.` (`agent_loader.py:398-402`) | The variable is called `agent`, or `__init__.py` lacks `from . import agent` | Name it `root_agent` (or `app`; see Lab 6) and keep the scaffolded `__init__.py` |
| `WARNING: The --reload flag is not supported on Windows because it forces Uvicorn to use SelectorEventLoop, which does not support subprocesses (needed for executing tools). Forcing --no-reload.` (`cli_tools_click.py:2243-2253`) | `adk web` on Windows | Expected. Restart the server after edits |

**Best practice.** Write each docstring as a *routing contract*: when to call the tool, what it returns, and what it will not do. Keep tool lists short and distinct. Two recent papers (§9) show that distractor tools and inflated descriptions do most of the damage to tool selection.

**Variation.** Add `async def` tools. FunctionTool awaits them (`tools/function_tool.py:623-636`). Or add `FunctionTool(issue_refund, require_confirmation=True)` for human-in-the-loop (Lab 8).

---

## Lab 2: Drive the agent from Python with `InMemoryRunner`, `run_debug` and `run_async`

> **VERIFIED against google-adk 2.13.0 source (tag v2.13.0, commit d68ca857), re-checked by the verifier on 2026-10-23: every import path, class/function name and parameter in the code.** Expected-output blocks stay illustrative (nothing was executed).

**Goal.** Run the Lab 1 agent from a script. Use the 2-line `run_debug` helper first, then the production `run_async` event loop, which shows tool calls, tool results, the final answer and session isolation.

**Prerequisites.** Lab 1's `refund_agent/` in the same directory. No extra installs.

Adapted from the repo sample `contributing/samples/core/runner_debug_example/main.py` and the docstring of `Runner.run_debug` (`runners.py:1852-1960`).

```python
# run_refund.py  (sits next to the refund_agent/ folder)
import asyncio

from google.adk.runners import InMemoryRunner
from google.genai import types

from refund_agent.agent import root_agent

APP = "refund_agent"   # match the folder name (see the errors table)


async def main() -> None:
    runner = InMemoryRunner(agent=root_agent, app_name=APP)

    # 1) Two-line debugging: creates session "debug_session_id" on first use.
    await runner.run_debug("Is order A-1001 refundable? Changed my mind.", verbose=True)

    # 2) Production loop: explicit session, event stream.
    session = await runner.session_service.create_session(app_name=APP, user_id="cust-dana")
    msg = types.UserContent(parts=[types.Part(text="And A-1003? It arrived damaged.")])
    async for event in runner.run_async(user_id="cust-dana", session_id=session.id, new_message=msg):
        for call in event.get_function_calls():
            print(f"  TOOL CALL  {call.name}({call.args})")
        for resp in event.get_function_responses():
            print(f"  TOOL RESULT {resp.name} -> {resp.response}")
        if event.is_final_response() and event.content and event.content.parts:
            print(f"[{event.author}] {''.join(p.text or '' for p in event.content.parts)}")

    # 3) Isolation: a new user/session does not see Dana's history.
    await runner.run_debug("What did I ask before?", user_id="cust-li", session_id="li-1")
    await runner.close()


if __name__ == "__main__":
    asyncio.run(main())
```

**Run:**
```bash
python run_refund.py
```

**Expected output (illustrative; the line format comes from `utils/_debug_output.py:59,79-88`):**
```
refund_agent > [Calling tool: lookup_order({'order_id': 'A-1001'})]
refund_agent > [Tool result: {'status': 'success', 'order': {'email': 'dana@example.com', ...}}]
refund_agent > [Calling tool: check_refund_eligibility({'order_id': 'A-1001', 'reason': 'changed_mind'})]
refund_agent > [Tool result: {'status': 'success', 'eligible': True, 'window_days': 30, 'days_since_delivery': 12}]
refund_agent > Yes. A-1001 (apparel) was delivered 12 days ago, inside our 30-day window, so it is eligible.
  TOOL CALL  lookup_order({'order_id': 'A-1003'})
  TOOL RESULT lookup_order -> {'status': 'success', 'order': {...}}
  TOOL CALL  check_refund_eligibility({'order_id': 'A-1003', 'reason': 'damaged'})
  TOOL RESULT check_refund_eligibility -> {'status': 'success', 'eligible': True, 'rule': 'defect_override'}
[refund_agent] A-1003 is groceries, which are normally final sale, but damaged items are always refundable.
refund_agent > I don't have any earlier messages from you in this conversation.
```

**Walk-through of the key lines:**
1. `InMemoryRunner(agent=..., app_name=APP)` bundles `InMemorySessionService`, `InMemoryArtifactService` and `InMemoryMemoryService` (`runners.py:2390-2430`). If you omit `app_name`, it defaults to `'InMemoryRunner'`.
2. `run_debug(user_messages, *, user_id='debug_user_id', session_id='debug_session_id', quiet=False, verbose=False)` gets or creates the session, wraps your string in `types.UserContent`, prints the events and returns `list[Event]` (`runners.py:1852-1960`). Its docstring says it is "for debugging and experimentation only".
3. `run_async(*, user_id, session_id, invocation_id=None, new_message=None, state_delta=None, run_config=None, yield_user_message=False, abort_signal=None)` (`runners.py:1129-1140`) is the production entry point. `run()` is a sync wrapper that is "only for local testing" (`runners.py:1008-1020`).
4. `event.get_function_calls()` / `get_function_responses()` come from `LlmResponse` (`models/llm_response.py:196,205`). `is_final_response()` is false while function calls are pending (`events/event.py:286-305`).
5. `await runner.close()` (`runners.py:2326`) closes plugins. The runner is also an async context manager (`__aenter__`/`__aexit__`, `runners.py:2362-2371`).

**Common errors:**
| Exact message | Cause | Fix |
|---|---|---|
| `Session not found: <id>` (raised as `SessionNotFoundError`, a subclass of `ValueError`; `runners.py:1004-1005`, `errors/session_not_found_error.py`) | You called `run_async` with a session ID you never created, or created it under a different `app_name` | Call `create_session(app_name=runner.app_name, ...)` first, or construct `Runner(..., auto_create_session=True)` (`runners.py:293`) |
| `App name mismatch detected. The runner is configured with app name "InMemoryRunner", but the root agent was loaded from ".../refund_agent", which implies app name "refund_agent".` (warning, `runners.py:498-509`). A later "Session not found" then carries the hint `...set auto_create_session=True when constructing the runner.` | You omitted `app_name` for an agent that lives in a package folder | Pass `app_name="refund_agent"`, the folder name |
| `app_name is required when agent is provided without app.` (`runners.py:419-422`) | You used plain `Runner(agent=..., session_service=...)` without `app_name` | Add `app_name=` or pass `app=App(...)` |
| ``Max number of llm calls limit of `500` exceeded`` (`LlmCallsLimitExceededError`, `agents/invocation_context.py:91-93`) | A tool-call loop | Fix the tool's error messages. Set a lower cap with `RunConfig(max_llm_calls=20)` or the `ADK_MAX_LLM_CALLS` env var (`agents/run_config.py:38-50`) |

**Best practice.** Production code should consume `run_async` and log every function call and response, not only the final text. Today most agent failures show up in the trajectory, not in the answer (arXiv 2608.11274, §9).

**Variation.** Pass `abort_signal=asyncio.Event()` to `run_async` and `set()` it from a timeout task to cancel a runaway turn. The parameter was added in v2.11.0 (`runners.py:1139`).

---

## Lab 3: HR-policy assistant with state, `output_key`, `{state}` templating and the four prefixes

> **VERIFIED against google-adk 2.13.0 source (tag v2.13.0, commit d68ca857), re-checked by the verifier on 2026-10-23: every import path, class/function name and parameter in the code.** Still [UNVERIFIED]: `state_schema` end-to-end on an `LlmAgent` (field inherited from `BaseNode`, not run). Expected-output blocks stay illustrative (nothing was executed).

**Goal.** Personalise an HR policy agent from session state. Write state from a tool and through `output_key`. Prove which scopes survive into a second session.

**Prerequisites.** Common setup only.

Adapted from the docs page "State" (https://adk.dev/sessions/state/) and the codelab **"Building Stateful and Personalized Agents with ADK"** (https://codelabs.developers.google.com/codelabs/agent-memory/instructions). The scenario is changed to HR.

```python
# hr_state_lab.py
import asyncio

from google.adk import Agent
from google.adk.runners import InMemoryRunner
from google.adk.tools import ToolContext
from google.genai import types

POLICIES = {"parental_leave": "16 weeks paid for all parents", "remote_work": "3 remote days per week",
            "pto": "25 days per year, max carry-over 5"}


def get_policy(topic: str, tool_context: ToolContext) -> dict:
    """Return the official HR policy text for a topic: parental_leave, remote_work or pto."""
    tool_context.state["temp:last_topic"] = topic                  # this invocation only
    asked = tool_context.state.get("user:topics_asked", [])
    tool_context.state["user:topics_asked"] = asked + [topic]      # every session of this user
    text = POLICIES.get(topic)
    return {"status": "success", "policy": text} if text else {"status": "error", "error_message": "unknown topic"}


hr_agent = Agent(
    name="hr_policy_agent",
    model="gemini-3.5-flash",
    instruction=(
        "You are the HR assistant for {app:company_name}. You are talking to "
        "{user:employee_name} in the {user:office?} office. Reply in {user:language?} "
        "(default English). Quote policy text exactly from get_policy."
    ),
    tools=[get_policy],
    output_key="last_hr_answer",                                   # final text -> session state
)


async def main() -> None:
    runner = InMemoryRunner(agent=hr_agent, app_name="hr_app")
    svc = runner.session_service
    s1 = await svc.create_session(app_name="hr_app", user_id="emp-17", state={
        "app:company_name": "Acme Corp", "user:employee_name": "Priya", "user:office": "Dublin"})
    msg = types.UserContent(parts=[types.Part(text="How much parental leave do I get?")])
    async for _ in runner.run_async(user_id="emp-17", session_id=s1.id, new_message=msg,
                                    state_delta={"user:language": "English"}):
        pass
    s1 = await svc.get_session(app_name="hr_app", user_id="emp-17", session_id=s1.id)
    print("session 1 state:", s1.state)
    s2 = await svc.create_session(app_name="hr_app", user_id="emp-17")   # new chat, same user
    print("session 2 state:", s2.state)


asyncio.run(main())
```

**Run:**
```bash
python hr_state_lab.py
```

**Expected output (illustrative values; the key set follows the source logic cited below):**
```
session 1 state: {'app:company_name': 'Acme Corp', 'user:employee_name': 'Priya', 'user:office': 'Dublin',
  'user:language': 'English', 'user:topics_asked': ['parental_leave'],
  'last_hr_answer': 'Hi Priya, at Acme Corp parental leave is "16 weeks paid for all parents".'}
session 2 state: {'app:company_name': 'Acme Corp', 'user:employee_name': 'Priya', 'user:office': 'Dublin',
  'user:language': 'English', 'user:topics_asked': ['parental_leave']}
```
Note what is missing: `temp:last_topic` appears in neither session, and `last_hr_answer` (no prefix, so session-scoped) is absent from session 2.

**Walk-through of the key lines:**
1. **Prefixes** are `State.APP_PREFIX="app:"`, `USER_PREFIX="user:"` and `TEMP_PREFIX="temp:"` (`sessions/state.py:96-98`). `InMemorySessionService` keeps separate `app_state[app]` and `user_state[app][user]` dicts and merges them back into each session it returns (`sessions/in_memory_session_service.py:86-88,136-143,241-253`). That is why session 2 sees `user:*` and `app:*` keys.
2. **`temp:`** is applied to the live session for the rest of the invocation, then trimmed from the event before commit (`sessions/base_session_service.py:_apply_temp_state`, `_trim_temp_delta_state`). It is never persisted.
3. **`{user:office?}`.** The template regex is `(?<![\$\{\\]){+[^{}]*}+` (`flows/llm_flows/prompt/_instructions_utils.py:45`). A trailing `?` makes the key optional (missing becomes `''`). A missing key without `?` raises `KeyError` (line 196). Valid names are identifiers or `app:|user:|temp:` + identifier (`_is_valid_state_name`). Anything else, such as JSON like `{"a": 1}`, is left untouched.
4. **`output_key="last_hr_answer"`** writes the joined non-thought text of the agent's final response into `event.actions.state_delta` (`agents/llm_agent.py:1113-1147`). It is skipped in `mode="task"`. During streaming with tool calls, ADK accumulates text across the turn (`llm_agent.py:1151-1188`).
5. **`state_delta=`** on `run_async` writes state *through an event*. This is the legal way to inject per-turn context such as locale or channel.
6. **`get_session` returns a copy** (`_copy_session` deep-copies by default, `in_memory_session_service.py:55-59`). Mutating `s1.state[...]` afterwards does nothing. Write through `state_delta`, tools or callbacks.

**Common errors:**
| Exact message | Cause | Fix |
|---|---|---|
| ``KeyError: "Context variable not found: `user:employee_name` in agent 'hr_policy_agent'."`` (`_instructions_utils.py:196-197`) | The template references a key that is not in state on the first turn | Seed it in `create_session(state=...)`, or make it optional: `{user:employee_name?}` |
| The literal text `${user:office}` shows up in the prompt (no error) | Since v2.10.0, `${var}` is not substituted. The lookbehind `(?<![\$...])` excludes it | Use `{var}` |
| `{{customer}}` is still substituted, though you meant a literal | `{+...}+` matches doubled braces too | For literal braces or Jinja-style logic, pass an `InstructionProvider` and call `inject_session_state(template, ctx, use_jinja2=True)` (`_instructions_utils.py:54-110`). That needs `pip install jinja2`, or you get `Rendering an instruction with Jinja2 requires the optional jinja2 package. Install it with: pip install jinja2` |
| The state change "disappears" | You mutated `session.state` on an object returned by `get_session` | Write through `state_delta`, `tool_context.state` or `callback_context.state` |

**Best practice.** Put durable personalisation (name, language, entitlements) in `user:`. Put tenant config in `app:`. Put scratch values in `temp:`. Leave unprefixed keys for per-conversation results such as `output_key`. Never store secrets in state: it is printed by `adk web` and returned by `GET /apps/.../sessions/...`.

**Variation (2.x only).** Declare a typed state contract. `BaseNode.state_schema: type[BaseModel] | None` is inherited by every agent (`workflow/_base_node.py:139-147`). Writes to unprefixed keys are then validated, and violations raise `StateSchemaError` (`sessions/state.py`). Colon-prefixed keys bypass the check. [UNVERIFIED end-to-end on `LlmAgent`: the field is inherited, but I did not run it.]

---

## Lab 4: Support-ticket triage with all four callback types (guardrail, policy gate, redaction, metering)

> **VERIFIED against google-adk 2.13.0 source (tag v2.13.0, commit d68ca857), re-checked by the verifier on 2026-10-23: every import path, class/function name and parameter in the code.** Still [UNVERIFIED]: the exact `TypeError` text for a wrong callback argument name. Expected-output blocks stay illustrative (nothing was executed).

**Goal.** Add deterministic controls around the LLM and the tools without touching the prompt:
- `before_model_callback` blocks payment-card numbers before they reach the model.
- `before_tool_callback` enforces a refund cap.
- `after_tool_callback` redacts emails from tool output.
- `after_model_callback` meters tokens into state.

**Prerequisites.** Common setup.

Adapted from the repo sample `contributing/samples/core/callbacks/agent.py` and the docs page "Types of callbacks" (https://adk.dev/callbacks/types-of-callbacks/).

```python
# triage_callbacks.py
import asyncio
import re
from typing import Any, Optional

from google.adk import Agent, Context
from google.adk.models import LlmRequest, LlmResponse
from google.adk.runners import InMemoryRunner
from google.adk.tools import BaseTool, ToolContext
from google.genai import types

CARD = re.compile(r"\b(?:\d[ -]?){13,16}\b")
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")


def lookup_customer(ticket_id: str) -> dict:
    """Fetch the customer record attached to a support ticket."""
    return {"status": "success", "name": "Dana Ruiz", "email": "dana@example.com", "plan": "Pro"}


def issue_refund(ticket_id: str, amount_usd: float) -> dict:
    """Refund the customer on a ticket. Use only after confirming the amount."""
    return {"status": "success", "refund_id": f"RF-{ticket_id}", "amount_usd": amount_usd}


def block_card_numbers(callback_context: Context, llm_request: LlmRequest) -> Optional[LlmResponse]:
    last = llm_request.contents[-1] if llm_request.contents else None
    text = " ".join(p.text or "" for p in (last.parts or [])) if last else ""
    if CARD.search(text):
        return LlmResponse(content=types.Content(role="model", parts=[types.Part.from_text(
            text="For your security, please don't share card numbers here. I've flagged the ticket.")]))
    return None                                            # None = call the model


def refund_cap(tool: BaseTool, args: dict[str, Any], tool_context: ToolContext) -> Optional[dict]:
    cap = tool_context.state.get("app:refund_cap_usd", 100)
    if tool.name == "issue_refund" and args.get("amount_usd", 0) > cap:
        return {"status": "error", "error_message": f"Refunds over ${cap} need a supervisor."}
    return None                                            # None = run the tool


def redact_pii(tool: BaseTool, args: dict, tool_context: ToolContext, tool_response: dict) -> Optional[dict]:
    if tool.name == "lookup_customer":
        return {k: EMAIL.sub("[email redacted]", v) if isinstance(v, str) else v for k, v in tool_response.items()}
    return None


def meter_tokens(callback_context: Context, llm_response: LlmResponse) -> Optional[LlmResponse]:
    if llm_response.usage_metadata:
        used = callback_context.state.get("tokens_used", 0)
        callback_context.state["tokens_used"] = used + (llm_response.usage_metadata.total_token_count or 0)
    return None                                            # None = keep the model's response


triage = Agent(name="ticket_triage", model="gemini-3.5-flash",
               instruction="Triage support tickets. Look up the customer, then act.",
               tools=[lookup_customer, issue_refund],
               before_model_callback=block_card_numbers, before_tool_callback=refund_cap,
               after_tool_callback=redact_pii, after_model_callback=meter_tokens)


async def main() -> None:
    runner = InMemoryRunner(agent=triage, app_name="triage_app")
    await runner.run_debug(["Ticket T-88: refund $250 please.", "My card is 4111 1111 1111 1111"], verbose=True)
    s = await runner.session_service.get_session(app_name="triage_app", user_id="debug_user_id", session_id="debug_session_id")
    print("tokens_used =", s.state.get("tokens_used"))

asyncio.run(main())
```

**Run:**
```bash
python triage_callbacks.py
```

**Expected output (illustrative):**
```
ticket_triage > [Calling tool: lookup_customer({'ticket_id': 'T-88'})]
ticket_triage > [Tool result: {'status': 'success', 'name': 'Dana Ruiz', 'email': '[email redacted]', 'plan': 'Pro'}]
ticket_triage > [Calling tool: issue_refund({'ticket_id': 'T-88', 'amount_usd': 250.0})]
ticket_triage > [Tool result: {'status': 'error', 'error_message': 'Refunds over $100 need a supervisor.'}]
ticket_triage > I can't issue a $250 refund directly; refunds over $100 need a supervisor. I've escalated T-88.
ticket_triage > For your security, please don't share card numbers here. I've flagged the ticket.
tokens_used = 2875
```

**Walk-through of the key lines:**
1. **Return-value semantics** (docstrings, `agents/llm_agent.py:494-600`):
   - Model callbacks stop the chain on a *truthy* result. A truthy `before_model` result skips the LLM.
   - Tool callbacks stop on any *non-None* result, "including an empty dict". A non-None `before_tool` result skips the tool; a non-None `after_tool` result replaces the tool's result.
2. **Order:** plugin callbacks run first. If a plugin returns a value, the agent's callback is skipped (`flows/llm_flows/core/_finalizer.py:170-189`, `flows/llm_flows/tools/_caller.py:505-519`).
3. **Argument names.** ADK calls agent callbacks with keywords (`callback_context=`, `llm_request=`, `tool=`, `args=`, `tool_context=`, `tool_response=`). In 2.13 it falls back to positional order in the canonical sequence `tool, args, tool_context, response, tool_response, callback_context, llm_request, llm_response, error` when the names don't bind (`utils/_callback_pipeline.py:17-77`). Keep the canonical names anyway; plugins get **no** fallback (see Lab 6).
4. `callback_context.state[...] = ...` inside a callback goes into the event's `state_delta`, so it is persisted like any other state write.
5. `LlmResponse(content=types.Content(role="model", parts=[types.Part.from_text(text=...)]))` is the exact short-circuit shape used in the official sample. `from google.adk.models import LlmRequest, LlmResponse` is verified (`models/__init__.py:26-27`).
6. Each `*_callback` field also accepts a **list**, run in order until the stop condition is met.

**Common errors:**
| Exact message / symptom | Cause | Fix |
|---|---|---|
| The refund still happens | `refund_cap` returned `{}` or `False` | A `before_tool` callback that returns `{}` *does* skip the tool. `False`/`None` do not. Return a clear error dict |
| The guardrail never fires on multi-part messages | You inspected only `parts[0]` | Join all parts, as in the code above. A user turn can carry several text or file parts |
| `TypeError: ... got an unexpected keyword argument 'tool_args'` [UNVERIFIED exact text] | A plugin-style signature (`tool_args`) on an *agent* callback, or the reverse | Agent callback: `(tool, args, tool_context)`. Plugin hook: `(self, *, tool, tool_args, tool_context)` (`plugins/base_plugin.py:297-303`) |
| The guardrail is bypassed by a tool result | `before_model` only sees the request. Injected text can arrive inside a tool response | Also check `after_tool_callback`, or use a plugin such as Model Armor |

**Best practice.** Put **policy in code, not prompts**. Caps, PII rules and allow-lists belong in `before_tool_callback` or a plugin, so they hold even when the model is persuaded otherwise. This is the "runtime contract" position of arXiv 2608.11274 (§9).

**Variation.** Add `on_tool_error_callback(tool, args, tool_context, error)` to turn a CRM timeout into `{"status": "error", "error_message": "CRM unavailable, retry later"}`. Note that it is also called with `asyncio.CancelledError` when a parallel call fails (`llm_agent.py:574-600`).

---

## Lab 5: Insurance-claim intake with `output_schema` (structured output) and `output_key`

> **VERIFIED against google-adk 2.13.0 source (tag v2.13.0, commit d68ca857), re-checked by the verifier on 2026-10-23: every import path, class/function name and parameter in the code.** Expected-output blocks stay illustrative (nothing was executed).

**Goal.** Turn a free-text first-notice-of-loss email into a validated `ClaimIntake` record in session state, ready for a downstream system.

**Prerequisites.** Common setup. `pydantic>=2.12` comes with ADK.

Adapted from the repo samples `contributing/samples/core/input_output_schema/agent.py` and `contributing/samples/tools/output_schema_with_tools/agent.py`.

```python
# claim_intake.py
import asyncio
import json
from typing import Literal, Optional

from pydantic import BaseModel, Field
from google.adk import Agent
from google.adk.runners import InMemoryRunner


class ClaimIntake(BaseModel):
    """First notice of loss, extracted from a customer email."""
    reasoning: str = Field(description="One sentence: which facts in the email decided claim_type and severity.")
    claim_type: Literal["auto_collision", "auto_glass", "home_water", "home_theft", "other"]
    severity: Literal["low", "medium", "high"] = Field(description="high = injury or > $10k estimated loss")
    policy_number: Optional[str] = Field(default=None, description="Format POL-######, or null if absent")
    incident_date: Optional[str] = Field(default=None, description="ISO 8601 date, or null if not stated")
    estimated_loss_usd: Optional[float] = None
    injuries_reported: bool


intake_agent = Agent(
    name="claim_intake",
    model="gemini-3.5-flash",
    instruction="Extract a ClaimIntake record from the email. Never guess a policy number.",
    output_schema=ClaimIntake,
    output_key="claim",
)

EMAIL = ("Hi, this is Tom Becker, policy POL-448120. On Oct 19 a delivery van rear-ended me on Route 9. "
         "Bumper and tailgate are crushed, the body shop quoted about $6,400. Nobody was hurt.")


async def main() -> None:
    runner = InMemoryRunner(agent=intake_agent, app_name="claims")
    await runner.run_debug(EMAIL, quiet=True)
    s = await runner.session_service.get_session(app_name="claims", user_id="debug_user_id",
                                                 session_id="debug_session_id")
    claim = s.state["claim"]                       # already a dict, validated by pydantic
    print(type(claim).__name__, json.dumps(claim, indent=2))
    ClaimIntake.model_validate(claim)              # round-trip check for downstream code


asyncio.run(main())
```

**Run:**
```bash
python claim_intake.py
```

**Expected output (illustrative):**
```
dict {
  "reasoning": "Rear-end collision with a van, $6,400 quote and no injuries, so auto_collision with medium severity.",
  "claim_type": "auto_collision",
  "severity": "medium",
  "policy_number": "POL-448120",
  "incident_date": "2026-10-19",
  "estimated_loss_usd": 6400.0,
  "injuries_reported": false
}
```

**Walk-through of the key lines:**
1. `output_schema=ClaimIntake` accepts a `BaseModel`, `list[BaseModel]`, `list[primitive]`, a raw `dict` schema or a genai `Schema` (`agents/llm_agent.py:449-462`).
2. With `output_key`, the final text is parsed by `validate_schema()`. For a BaseModel that is `model_validate_json(...).model_dump(exclude_none=True)`, after code fences are stripped (`utils/_schema_utils.py:235-260`, `llm_agent.py:1139-1147`). State therefore holds a **dict, not a model instance**, and **`None` fields are dropped**. Read optional keys with `.get()`.
3. The `reasoning` field comes *first*. arXiv 2608.08254 (§9) found that a required intermediate reasoning field placed before the label raised schema-only accuracy by 15-24 points.
4. Field `description=` text is a second prompt channel. The same paper found that a wrong schema description can override the system prompt (accuracy drops of 5-45 points). Keep the prompt and the schema consistent.
5. Put the schema in `output_schema`, never in `generate_content_config.response_schema`. Doing that raises the error shown in the table below.

**Common errors:**
| Exact message | Cause | Fix |
|---|---|---|
| `Response schema must be set via LlmAgent.output_schema, not via generate_content_config.response_schema. Move your schema to LlmAgent(output_schema=...).` (`llm_agent.py:1309-1314`) | Old genai habit | Use `output_schema=` |
| `temperature is a GenerateContentConfig field. Pass generate_content_config=types.GenerateContentConfig(temperature=...) instead.` (wrapped in a pydantic `ValidationError`; `llm_agent.py:1255-1277`) | `Agent(temperature=0)` | `generate_content_config=types.GenerateContentConfig(temperature=0)` |
| `KeyError: 'policy_number'` in your downstream code | `exclude_none=True` dropped the null field | `claim.get("policy_number")`, or `ClaimIntake.model_validate(claim)` |
| pydantic `ValidationError` on the final turn (illustrative: `1 validation error for ClaimIntake claim_type Input should be 'auto_collision', ...`) | The model emitted an enum value outside the schema, or truncated JSON | Lower `max_output_tokens` pressure, add an `"other"` bucket, and catch the error in an `after_model_callback` |

**Best practice.** Validate *semantics* as well as syntax. arXiv 2609.23742 (§9) shows that constrained decoding fixes 100% of structural failures but not semantic ones. Add a deterministic check after extraction, such as "`severity == 'high'` requires `injuries_reported` or a loss over $10k".

**Variation: schema plus tools.** Add `tools=[lookup_policy]`. When the model can't natively combine a schema with tools, ADK injects an internal `set_model_response` tool and the instruction "IMPORTANT: You have access to other tools, but you must provide your final response using the set_model_response tool..." (`flows/llm_flows/prompt/_schema.py:37-68`). For Gemini, native support requires the **Agent Platform / Vertex backend**: `gemini_output_schema_and_tools()` returns true only when `GOOGLE_GENAI_USE_ENTERPRISE` is on (`models/_capabilities.py:30-51`). With an AI Studio key you will therefore see an extra `set_model_response` tool call in traces. That is expected, not a bug.

---

## Lab 6: Package it as an `App` with plugins, then call it over REST with `adk api_server`

> **VERIFIED against google-adk 2.13.0 source (tag v2.13.0, commit d68ca857), re-checked by the verifier on 2026-10-23: every import path, class/function name and parameter in the code.** Correction applied: the `plugins=` deprecation text is now quoted exactly. Expected-output blocks stay illustrative (nothing was executed).

**Goal.** Wrap the claims agent in an `App` with a built-in `LoggingPlugin` and a custom audit plugin. Serve it with `adk api_server`, then create a session and run turns with `curl`, including SSE streaming.

**Prerequisites.** Common setup. Folder layout: `agents/claims_api/{__init__.py, agent.py}`, with `__init__.py` containing `from . import agent`.

Adapted from the repo sample `contributing/samples/core/app/agent.py` and the docs page "Apps" (https://adk.dev/apps/).

```python
# agents/claims_api/agent.py
from typing import Any, Optional

from google.adk import Agent
from google.adk.apps import App
from google.adk.plugins import LoggingPlugin
from google.adk.plugins.base_plugin import BasePlugin
from google.adk.tools import BaseTool, ToolContext


def lookup_policy(policy_number: str) -> dict:
    """Return coverage for a policy number like POL-448120."""
    return {"status": "success", "policy_number": policy_number, "collision_deductible_usd": 500,
            "coverage": ["collision", "glass", "liability"]}


class AuditPlugin(BasePlugin):
    """Records every tool call app-wide in state, for audit export."""

    def __init__(self) -> None:
        super().__init__(name="audit")

    async def before_tool_callback(self, *, tool: BaseTool, tool_args: dict[str, Any],
                                   tool_context: ToolContext) -> Optional[dict]:
        log = tool_context.state.get("audit_log", [])
        tool_context.state["audit_log"] = log + [f"{tool.name}({tool_args})"]
        return None


root_agent = Agent(
    name="claims_assistant",
    model="gemini-3.5-flash",
    instruction="Answer coverage questions. Always call lookup_policy first.",
    tools=[lookup_policy],
)

app = App(name="claims_api", root_agent=root_agent, plugins=[LoggingPlugin(), AuditPlugin()])
```

**Run the server and call it (bash; on Windows PowerShell use `curl.exe`):**
```bash
adk api_server agents --port 8000                   # add --with_ui to also serve the dev UI
curl -s localhost:8000/list-apps                    # -> ["claims_api"]
curl -s -X POST localhost:8000/apps/claims_api/users/u-tom/sessions \
     -H "Content-Type: application/json" -d '{"sessionId":"claim-77","state":{"channel":"email"}}'
curl -s -X POST localhost:8000/run -H "Content-Type: application/json" -d '{
  "appName":"claims_api","userId":"u-tom","sessionId":"claim-77",
  "newMessage":{"role":"user","parts":[{"text":"What is my collision deductible on POL-448120?"}]}}'
curl -N -X POST localhost:8000/run_sse -H "Content-Type: application/json" -d '{
  "appName":"claims_api","userId":"u-tom","sessionId":"claim-77","streaming":true,
  "newMessage":{"role":"user","parts":[{"text":"Is glass covered?"}]}}'
curl -s localhost:8000/apps/claims_api/users/u-tom/sessions/claim-77    # inspect state incl. audit_log
```
Routes are verified in `cli/api_server.py`: `/list-apps` (1658), `POST /apps/{app_name}/users/{user_id}/sessions` (1755) with body `CreateSessionRequest{session_id, state, events, options}`, `/run` (2088) and `/run_sse` (2180). `RunAgentRequest` fields (`api_server.py:651-667`) are `app_name, user_id, session_id, new_message, streaming, state_delta, invocation_id, custom_metadata, service_tier`. They are accepted in **camelCase** because of the `alias_generator=to_camel, populate_by_name=True` setting (`cli/utils/common.py`).

**Expected output (illustrative, abbreviated).** `/run` returns a JSON **list of Events**:
```json
[{"author":"claims_assistant","content":{"role":"model","parts":[{"functionCall":{"name":"lookup_policy","args":{"policy_number":"POL-448120"}}}]}, ...},
 {"author":"claims_assistant","content":{"role":"user","parts":[{"functionResponse":{"name":"lookup_policy","response":{"status":"success","collision_deductible_usd":500, ...}}}]}, ...},
 {"author":"claims_assistant","content":{"role":"model","parts":[{"text":"Your collision deductible on POL-448120 is $500."}]}, ...}]
```
The server console shows `LoggingPlugin` lines for each callback point. `/run_sse` emits `data: {...event...}` lines as they arrive.

**Walk-through of the key lines:**
1. `App` is a pydantic model with `extra="forbid"`. Its fields are `name`, `root_agent` (any `BaseNode`), `plugins`, `events_compaction_config`, `context_cache_config` and `resumability_config` (`apps/app.py:53-97`). That's all: there are **no** startup/shutdown hook fields in 2.13.0, which corrects earlier research.
2. **The loader prefers `app` over `root_agent`.** `agent_loader.py:130-140,183-189` checks for a module attribute `app` that is an `App` first. Expose both if you like; `adk web`, `adk run` and `api_server` will use `app` and its plugins.
3. **The server uses the folder name as the app name.** `_wrap_loaded_agent` and `_create_runner(agentic_app, app_name)` pass `app_name` from the folder (`api_server.py:1120-1136,1193-1203`). Name the App the same as the folder (`claims_api`) so programmatic runners and the server agree.
4. **Plugin hooks are keyword-only and use different names:** `before_tool_callback(self, *, tool, tool_args, tool_context)`, and `before_model_callback(self, *, callback_context, llm_request)` (`plugins/base_plugin.py:233-303`). Plugins run before agent callbacks, and the first non-None plugin result wins (`plugins/plugin_manager.py:277-312`).
5. `plugins=` on `Runner` is deprecated. It warns ``The `plugins` argument is deprecated. Please use the `app` argument to provide plugins instead.`` (`DeprecationWarning`; exact text verified), and passing it together with `app=` raises (`runners.py:398-409`).

**Common errors:**
| Exact message | Cause | Fix |
|---|---|---|
| `Invalid app name 'claims api': must start with a letter and can only consist of letters, digits, underscores, and hyphens.` (`apps/app.py:42-48`) | A space in `App(name=...)` | Use `claims_api`. `App` allows hyphens but agent folders do not, so prefer underscores everywhere |
| pydantic `Extra inputs are not permitted` for field `agent` | `App(name=..., agent=...)` | The field is `root_agent=` |
| `When app is provided, plugins should not be provided and should be provided in the app instead.` (`runners.py:401-403`) | `Runner(app=app, plugins=[...])` | Move the plugins into `App(plugins=[...])` |
| HTTP 404 `{"detail":"Session not found: claim-77"}` from `/run` (`SessionNotFoundError` mapped to 404 at `api_server.py:2135-2136`) | The session was never created | `POST /apps/{app}/users/{user}/sessions` first, or start the server with `--auto_create_session` (`cli_tools_click.py` api_server options) |

**Best practice.** Treat `App` as the **deployable unit**. Cross-cutting concerns (audit, logging, PII, rate limits) go in plugins, registered once, so every agent in the tree gets them. Test against `adk api_server` locally before `adk deploy cloud_run`/`agent_engine`/`gke`. Those are the same FastAPI routes.

**Variation.** Inject a plugin without code changes: `adk web --extra_plugins=my_pkg.audit.AuditPlugin` (option listed in `fast_api_common_options`). Or cap cost per request with `adk api_server --max_llm_calls 25`, which feeds `RunConfig(max_llm_calls=...)` per `/run` (`api_server.py:2103-2114`).

---

## Lab 7: Sessions that survive a restart (SQLite, then Postgres)

> **VERIFIED against google-adk 2.13.0 source (tag v2.13.0, commit d68ca857), re-checked by the verifier on 2026-10-23: every import path, class/function name and parameter in the code.** Still [UNVERIFIED]: an `asyncpg` version pin. Expected-output blocks stay illustrative (nothing was executed).

**Goal.** Swap the in-memory session store for a persistent one, so a support conversation continues after the process restarts.

**Prerequisites.** Common setup. SQLite needs nothing extra (`aiosqlite` is core). Postgres needs `pip install "google-adk[db]==2.13.0" asyncpg`. The asyncpg version is up to you [UNVERIFIED pin].

```python
# persistent_support.py   usage: python persistent_support.py "message"
import asyncio
import sys

from google.adk import Agent, Runner
from google.adk.apps import App
from google.adk.sessions.sqlite_session_service import SqliteSessionService
from google.genai import types

support_agent = Agent(
    name="support_agent",
    model="gemini-3.5-flash",
    instruction="You are a helpdesk agent for ticket {ticket_id}. Remember details the user gave earlier.",
)
app = App(name="support_app", root_agent=support_agent)
sessions = SqliteSessionService(db_path="support_sessions.db")
# Postgres instead (needs google-adk[db]):
# from google.adk.sessions import DatabaseSessionService
# sessions = DatabaseSessionService(db_url="postgresql+asyncpg://adk:pw@localhost:5432/adk")


async def main(text: str) -> None:
    runner = Runner(app=app, session_service=sessions, auto_create_session=True)
    sid, uid = "ticket-4521", "cust-88"
    existing = await sessions.get_session(app_name="support_app", user_id=uid, session_id=sid)
    delta = None if existing else {"ticket_id": "T-4521"}           # seed state on first contact
    msg = types.UserContent(parts=[types.Part(text=text)])
    async for ev in runner.run_async(user_id=uid, session_id=sid, new_message=msg, state_delta=delta):
        if ev.is_final_response() and ev.content and ev.content.parts:
            print(f"[{ev.author}] {ev.content.parts[0].text}")
    s = await sessions.get_session(app_name="support_app", user_id=uid, session_id=sid)
    print(f"(events stored: {len(s.events)})")
    await runner.close()


asyncio.run(main(sys.argv[1]))
```

**Run (two separate processes):**
```bash
python persistent_support.py "My laptop model is ZX-14 and the fan rattles."
python persistent_support.py "What model did I say I have?"
# same store from the dev tools:
adk web --session_service_uri sqlite:///support_sessions.db
```

**Expected output (illustrative):**
```
[support_agent] Thanks. A rattling fan on a ZX-14 is often a loose fan shroud. Is it under warranty?
(events stored: 2)
[support_agent] You told me you have a ZX-14 laptop, with a rattling fan (ticket T-4521).
(events stored: 4)
```

**Walk-through of the key lines:**
1. `SqliteSessionService(db_path: str)` (`sessions/sqlite_session_service.py:202-215`) stores events as JSON "to allow for schema flexibility as event fields evolve". It is imported from its module path; it is not re-exported in `google.adk.sessions.__all__`.
2. `auto_create_session=True` (`runners.py:293,999`) creates the session on first contact instead of raising `SessionNotFoundError`.
3. `state_delta={"ticket_id": ...}` on the first turn seeds `{ticket_id}` for the template, through an event, so it is persisted.
4. `DatabaseSessionService(db_url=..., **engine_kwargs)` or `DatabaseSessionService(db_engine=AsyncEngine)` (`sessions/database_session_service.py:313-345`) uses async SQLAlchemy drivers. The ADK CLI also recognises `postgresql+asyncpg` and `sqlite+aiosqlite` URLs (`cli/service_registry.py:403-405`).
5. CLI URIs (`cli/service_registry.py:268-296`):
   - `memory://`
   - `sqlite://<path>`. The leading `/` after `sqlite://` is stripped, so `sqlite:///support_sessions.db` is a relative file.
   - `postgresql://...` and `mysql://...` go to `DatabaseSessionService`.
   - `agentengine://<id>` goes to Agent Platform Sessions.
   Without a URI, `adk web` and `adk run` default to local `.adk` storage, falling back to in-memory when the directory is not writable (`cli_tools_click.py:956-967`).

**Common errors:**
| Exact message | Cause | Fix |
|---|---|---|
| `The 'sqlalchemy' package is required to use this feature. Please install it by running: pip install google-adk[db]` (`sessions/__init__.py:51-54`, `utils/_dependency.py:27-30`) | You imported `DatabaseSessionService` without the extra | `pip install "google-adk[db]"`, or use `SqliteSessionService` |
| `Invalid database URL format or argument '<redacted-url>'.` (`database_session_service.py:404-407`) | A malformed URL such as `postgres://` | Use `postgresql+asyncpg://user:pw@host:5432/db` |
| `--use_local_storage/--no_use_local_storage cannot be used with --session_service_uri or --artifact_service_uri.` (`cli_tools_click.py`, `adk_services_options`) | Both flags set | Pick one |
| Old 1.x code cannot read 2.x sessions | 2.0 added `node_info`/`output` to events. Per https://adk.dev/2.0/, only 1.28+ can read 2.0 sessions | Upgrade every reader. Use `adk migrate session` (the `migrate` command group in `cli_tools_click.py:2772-2830`) for DB schemas |

**Best practice.** Make the session ID a business key (`ticket-4521`, `claim-77`). Retries and channel switches then land in the same conversation, and support staff can find it. Use `get_user_state(app_name=..., user_id=...)` (`sessions/base_session_service.py:126-165`) to read `user:` data before a session exists. It raises `NotImplementedError` on services that don't support it.

**Variation.** Point at managed storage on Agent Platform: `VertexAiSessionService(project=..., location=...)` (needs `google-adk[gcp]`), or `adk web --session_service_uri agentengine://<resource-id>`.

---

## Lab 8: Human approval for high-value refunds (tool confirmation, HITL)

> **VERIFIED against google-adk 2.13.0 source (tag v2.13.0, commit d68ca857), re-checked by the verifier on 2026-10-23: every import path, class/function name and parameter in the code.** Still [UNVERIFIED]: the docs URL slug and the user-facing request-input HITL API. Expected-output blocks stay illustrative (nothing was executed).

**Goal.** Require a human "yes" before `issue_refund` runs, but only when the amount is over $200. Test it from the `adk run` terminal, which renders the confirmation prompt.

**Prerequisites.** Common setup. Folder `refund_hitl/` containing `__init__.py` (`from . import agent`) and the `agent.py` below.

Adapted from the docs page "Tool confirmation" (https://adk.dev/tools-custom/confirmation/) [UNVERIFIED URL slug]. The API is verified in `tools/function_tool.py:166-190,405-423,503-528`.

```python
# refund_hitl/agent.py
from google.adk import Agent
from google.adk.tools import FunctionTool, ToolContext

APPROVAL_THRESHOLD_USD = 200.0


def issue_refund(order_id: str, amount_usd: float, tool_context: ToolContext) -> dict:
    """Issue a refund to the original payment method. Irreversible."""
    issued = tool_context.state.get("refunds_issued", [])
    tool_context.state["refunds_issued"] = issued + [{"order_id": order_id, "amount_usd": amount_usd}]
    return {"status": "success", "refund_id": f"RF-{order_id}", "amount_usd": amount_usd}


def needs_approval(order_id: str, amount_usd: float, tool_context: ToolContext) -> bool:
    """Same parameters as issue_refund: ADK calls this with the tool's arguments."""
    return amount_usd > APPROVAL_THRESHOLD_USD


root_agent = Agent(
    name="refund_hitl",
    model="gemini-3.5-flash",
    instruction=(
        "You process refunds. Call issue_refund with the order ID and amount. "
        "If the tool says the call was rejected, tell the customer a supervisor declined it."
    ),
    tools=[FunctionTool(issue_refund, require_confirmation=needs_approval)],
)
```

**Run:**
```bash
adk run refund_hitl
```

**Expected output (illustrative; the prompt lines come from `cli/cli.py:156-161`, and the hint text from `function_tool.py:513-518`):**
```
Running agent refund_hitl, type exit to exit.
[user]: Refund $80 on order A-1001
[refund_hitl]: Done. Refund RF-A-1001 for $80.00 has been issued.
[user]: Refund $1299 on order A-1002
[HITL confirm] Please approve or reject the tool call issue_refund() by responding with a FunctionResponse with an expected ToolConfirmation payload.
  Type "yes" to confirm, anything else to reject.
[user]: no
[refund_hitl]: I'm sorry, a supervisor declined the $1,299 refund for order A-1002.
```

**Walk-through of the key lines:**
1. `FunctionTool(func, *, require_confirmation: bool | Callable[..., bool] = False)` (`function_tool.py:166-190`). `True` gates every call; a callable gates per call.
2. **The callable gets the tool's own arguments.** `check_require_confirmation` prepares the same `args_to_call` (including the injected `tool_context` when the tool declares it) and calls your function with those keywords (`function_tool.py:405-422`). There is no keyword filtering (`utils/_sync_runner.py:214-232`), so the predicate must accept exactly the same parameter names.
3. On the first call ADK runs `tool_context.request_confirmation(hint=...)`, sets `skip_summarization`, and returns `{"error": "This tool call requires confirmation, please approve or reject."}`. A rejection returns `{"error": "This tool call is rejected."}` (`function_tool.py:503-528`).
4. `adk run` detects the pending long-running confirmation call and replies with a `FunctionResponse` whose payload is `{"confirmed": true|false}`. `y`, `yes`, `true` and `confirm` count as yes (`cli/cli.py:140-188`). `adk web` shows a confirm dialog instead.
5. The tool itself still writes state through `tool_context`, so approved refunds are auditable in `refunds_issued`.

**Common errors:**
| Exact message / symptom | Cause | Fix |
|---|---|---|
| `TypeError: needs_approval() got an unexpected keyword argument 'tool_context'` (standard Python wording) | The predicate's signature differs from the tool's | Give the predicate the same parameters as the tool, or accept `**kwargs` |
| The model "pretends" the refund went through after a rejection | The instruction doesn't cover the error dict | Tell the model explicitly what to say when the tool reports a rejection (see the instruction above) |
| The confirmation never appears in your own client | Your client ignores the long-running function call | Look for `event.long_running_tool_ids` and send back a `FunctionResponse` with the same `id` and `{"confirmed": ...}`, as `cli/cli.py:118-188` does |

**Best practice.** Gate **irreversible** actions (money, email, deletes) behind confirmation or a `before_tool_callback` threshold. Never rely on a prompt instruction like "ask before refunding". Make the threshold data-driven, for example `app:` state, so ops can change it without a deploy.

**Variation.** For richer approvals (an approver name or a partial amount), ADK also has a request-input HITL path, which `adk run` renders as `[HITL input] ... Schema: {...}` (`cli/cli.py:148-155`). The user-facing API for it is [UNVERIFIED in this pass].

---

## 9. Insights from arXiv papers, 2026-07-23 to 2026-10-23 (abstracts read on arxiv.org/abs)

| arXiv | Date | Title | What it means for these labs |
|---|---|---|---|
| **2608.08254** | 2026-08-08 | *Your Prompt Is Not the Only Prompt: How Much Do LLMs Weight Structured-Output Schema Descriptions?* (Sin-Ying Lin) | **Lab 5.** Schema field descriptions are a second instruction channel. Conflicting schema text cut accuracy by 5-45 points (Claude Haiku 4.5 fell from 52.5% to 7%). A required reasoning field placed *before* the label raised schema-only accuracy by 15-24 points |
| **2609.23742** | 2026-09-20 | *Constrained Decoding Eliminates Structural Failures in Small LLMs but Reveals a Scale-Dependent Semantic Gap* (Akash Chavan) | **Lab 5.** Constrained decoding brought schema validity to 100% (from 78.6-92.9%), but semantic errors remained, especially multi-step function calling. Validate meaning after `output_schema` |
| **2610.23342** | 2026-10-16 | *Robust Function Calling for LLM Agents Under Interface Drift* (Chattopadhyay et al.) | **Labs 1 and 4.** Tool descriptions and candidate lists drift after deployment. A training-free validate-retry-repair layer (SchemaShield-Lite) raised BFCL-200 accuracy from 0.580 to 0.805 on Qwen3.5-9B. **Distractor tools caused most of the damage.** Keep tool lists small, and validate arguments in `before_tool_callback` |
| **2610.28454** | 2026-10-20 | *Toolflation: Seller Agents Distort Tool Markets Through Spontaneous Generative Engine Optimization* (Tang et al.) | **Lab 1.** When descriptions over-claim, buyer agents fall back to picking tools by list position, and task success dropped from 89% to about 30% under one model. Write honest, specific docstrings, and review third-party tool descriptions |
| **2610.25372** | 2026-10-18 | *SEAL: Towards Persistent Tool Poisoning Attack against LLM Agents via Prefix-Eliciting Trigger* (Zhou et al.) | **Labs 1 and 6.** Malicious text in tool descriptions can persist across multi-round sessions. Pin and review the tool descriptions you load, and audit tool calls in a plugin |
| **2608.11274** | 2026-08-11 | *Agent Safety Should Be a Runtime Contract* (Ng, Han, Zhang) | **Labs 4 and 8.** Safety enforced by the harness has two faces: preventive gates (permission gates, filters) and evidential proof (logs, diffs). In ADK these map to callbacks/plugins/confirmation and to event logs/state audit trails |
| **2610.14346** | 2026-10-09 | *Evaluating LLMs as Agentic Workflow Executors in Real-World Customer Support Skills* (Laskar et al.) | **Labs 2 and 4.** Narrow, stateful, tool-constrained support workflows are the realistic target. Judge agreement on pass/fail was only Kappa 0.524 across judge pairs, so pair LLM judges with deterministic checks (tool coverage, hallucinated tools) |

## 10. Slide-ready gotchas (one line each, all sourced above)

1. `pip install google-adk` 2.13.0 needs **Python 3.11+**, though the quickstart still says 3.10.
2. The docstring becomes the tool description **verbatim**. `Args:` is *not* parsed, so use `Annotated[..., Field(description=)]` for per-parameter text.
3. Agent and agent-folder names must be identifiers: `refund_agent`, not `refund-agent`.
4. `{key}` raises when the key is missing, `{key?}` doesn't, `${key}` is ignored (since 2.10), and `{{key}}` is *still* substituted.
5. `output_key` + `output_schema` puts a **dict with None fields dropped** into state.
6. Schema plus tools on an AI Studio key runs through an injected `set_model_response` tool; native support is on the Agent Platform backend.
7. `temperature=` on `Agent` is rejected, so use `generate_content_config`. Tools, system instruction and response_schema each have their own field.
8. `get_session()` returns a copy. Write state only through `state_delta`, tools or callbacks.
9. `temp:` lives for one invocation, `user:` follows the user across sessions, and `app:` is global.
10. Plugins run before agent callbacks, and plugin hooks use `tool_args` where agent callbacks use `args`.
11. `adk web` uses the **folder name** as the app name, so name your `App` the same. The loader prefers a module-level `app` over `root_agent`.
12. `--reload` is forced off on Windows.
13. The default cap is **500 LLM calls** per invocation (`ADK_MAX_LLM_CALLS`).
14. A `require_confirmation` predicate must take the same parameters as the tool.
15. `GOOGLE_GENAI_USE_VERTEXAI` is deprecated in favour of `GOOGLE_GENAI_USE_ENTERPRISE`.

## Sources

- Source tree: https://github.com/google/adk-python/tree/v2.13.0 (commit d68ca85), read locally. The files are cited inline.
- PyPI JSON: https://pypi.org/pypi/google-adk/json, https://pypi.org/pypi/google-genai/json
- Docs: "Python Quickstart for ADK" https://adk.dev/get-started/python/; State https://adk.dev/sessions/state/; Apps https://adk.dev/apps/; Callbacks https://adk.dev/callbacks/types-of-callbacks/; ADK 2.0 https://adk.dev/2.0/
- Codelab: "Building Stateful and Personalized Agents with ADK" https://codelabs.developers.google.com/codelabs/agent-memory/instructions
- Repo samples: `contributing/samples/core/{app,callbacks,input_output_schema,runner_debug_example}`, `contributing/samples/tools/output_schema_with_tools`, `contributing/samples/context_management/session_state_agent`
- arXiv: https://arxiv.org/abs/2608.08254, /2609.23742, /2610.23342, /2610.28454, /2610.25372, /2608.11274, /2610.14346
