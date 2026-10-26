# ADK 2.x gotchas and open challenges (research for the hands-on deck)

Research date: 2026-10-23. Baseline: `google-adk` 2.13.0 (PyPI 2026-10-23).
Method: GitHub API (`gh api`) over `google/adk-python` issues from May to Oct 2026 (bodies, maintainer comments and closing commits), the raw `CHANGELOG.md` on `main` (each fix is mapped to the release that ships it), adk.dev pages (`/2.0/index.md`, `/deploy/cloud-run/index.md`), the Gemini 3 developer guide, and arXiv abstract pages for papers from 2026-07-23 to 2026-10-23.
Nothing here was run locally, because pip is blocked on this machine. The "repro" lines come from the issue authors' scripted, offline reproductions (most use a scripted `BaseLlm` and need no API key).
Already covered in `research-adk-platform/05-adk2-yaml-plugins.md` §5 and not repeated here: the YAML-config gotchas, the `after_agent` extra event, plugin `RuntimeError`, the BigQuery plugin `batch_size`, and the `${var}` templating change.

**Legend.** "Fixed in vX" means the CHANGELOG entry for vX closes that issue or names the fix. "Open" means the issue is open on 2026-10-23. [UNVERIFIED] marks anything I could not confirm against a primary source.

**One rule for every slide:** pin `google-adk==2.13.0` (and `a2a-sdk`, `mcp`, `litellm`) in both the local and the deployed requirements. More than a third of the items below are "fixed in a minor release". 2.x ships about every 1–2 weeks, and an unpinned deployment changes behaviour underneath you.

---

## A. Migration 1.x → 2.0

### A1. A SequentialAgent → Workflow port loses the conversation context
- **Symptom:** After you migrate `SequentialAgent(sub_agents=[a, b])` to `Workflow(edges=[("START", a, b)])`, agent `a` calls an AgentTool and then "restarts" with only its system instruction. It replies "Understood. Provide request". LiteLLM logs show the injected placeholder user turn "Handle the requests as specified in the System Instruction."
- **Root cause:** Inside a `Workflow`, LlmAgent nodes default to `mode="single_turn"` with `include_contents="none"`. A second bug also played a part: the current-turn slice dropped the query once a function-response event sat in the trail. That bug was fixed in v2.9.0.
- **Fix (maintainer answer, 2026-09-23):**
```python
from google.adk import Agent, Workflow
specialist = Agent(name="inventory_specialist", mode="single_turn", model="gemini-2.5-flash",
                   description="Checks warehouse stock.", tools=[query_warehouse_db])
intake = Agent(name="intake_agent", mode="single_turn", model="gemini-2.5-flash",
               sub_agents=[specialist],            # replaces AgentTool(...)
               instruction="Call inventory_specialist, then summarize.")
synth = Agent(name="synthesizer_agent", mode="single_turn", model="gemini-2.5-flash",
              include_contents="default",          # sees upstream conversation
              instruction="Write the customer reply from the intake finding.")
root_agent = Workflow(name="inventory_workflow", edges=[("START", intake, synth)])
# Run it through Runner. Do not call workflow.run(ctx=Context(ctx), ...) yourself:
# that bypasses the Runner event-queue consumer that persists tool-call events.
```
- **Detect early:** Write a golden test that asserts the second LLM request's `contents` still holds the original user text, using a scripted `BaseLlm` that records `llm_request.contents`.
- **Source:** https://github.com/google/adk-python/issues/5780

### A2. A `mode="chat"` agent inside a Workflow never hands off
- **Symptom:** The next node never runs. The graph appears to hang after the chat node.
- **Root cause:** A chat-mode agent never calls `finish_task` and never emits a node `output`, so the scheduler gets no completion signal ("Do **not** use `mode="chat"` inside a sequential workflow", maintainer, #5780).
- **Fix:** Make the chat agent the **root** `Agent(mode="chat")` and give it `mode="task"` sub-agents. Don't put chat agents in the graph.
- **Detect:** Write a test with a timeout per node run. A graph test that never reaches a terminal event is this bug.
- **Source:** https://github.com/google/adk-python/issues/5776 , #5780

### A3. `Workflow` cannot be used as a `sub_agent`, even though the deprecation tells you to "use Workflow instead"
- **Symptom:** `Agent(sub_agents=[pipeline])` fails because `issubclass(Workflow, BaseAgent)` is `False`. `Workflow` is a `BaseNode` only.
- **Fix:** Since v2.4.0 you can pass the workflow as a **tool**: `Agent(tools=[pipeline])`. It is wrapped as a `NodeTool`. `pipeline.description` must be set, or you get a `ValueError`. Since v2.13.0, NodeTool infers the input schema from the START successors. The trade-off is that the LLM decides when to call it, so it is no longer a deterministic step.
- **Detect:** Make `-W error::DeprecationWarning` a CI gate so you find every `SequentialAgent/ParallelAgent/LoopAgent` before the classes are removed.
- **Source:** https://github.com/google/adk-python/issues/5872 ; CHANGELOG 2.4.0, 2.13.0 (NodeTool)

### A4. `_run_async_impl` / `generate_content` overrides are silently ignored
- **Symptom:** Custom telemetry or state logic in an overridden 1.x method never runs inside a graph. You see no error.
- **Root cause:** The Workflow graph engine bypasses the 1.x overrides (adk.dev/2.0: calls are "silently ignored").
- **Fix:** Move the logic to `before_agent_callback` / `after_agent_callback`, or write it as a `@node` function.
- **Detect:** Run `grep -rn "_run_async_impl\|def generate_content" src/` in the migration PR checklist.
- **Source:** https://adk.dev/2.0/

### A5. Rigid session schemas break on 2.0 events, and older 1.x readers break on 2.0 sessions
- **Symptom:** Custom `BaseSessionService` inserts or deserializes fail. Strict JSON validators (`additionalProperties: false`) reject events.
- **Root cause:** 2.0 adds `node_info` and `output` to `Event` (TS adds 4 fields, Go adds 5). The PyPI 2.0.0 description says sessions written by 2.0 "are readable by ADK 1.28+ … but are incompatible with older 1.x versions".
- **Fix:** Upgrade **all readers** first (≥1.28), then the writers. Use JSON-blob storage instead of per-field columns.
- **Detect:** Add a contract test that round-trips a 2.0 event through your storage and validator.
- **Source:** https://adk.dev/2.0/ ; https://pypi.org/pypi/google-adk/2.0.0/json

### A6. `adk migrate session` shifts v0 timestamps by your UTC offset
- **Symptom:** Migrated events carry timestamps that are off by hours. The two migration paths give different results for the same DB.
- **Root cause:** `migrate_from_sqlalchemy_pickle` (the one the CLI calls) reads naive v0 datetimes as **local** time. The SQLite path reads them as **UTC**. Before commit 1b8ed3d9 (2026-08-13), v0 wrote local time; after it, v0 writes UTC.
- **Fix:** Run the migration with `TZ=UTC` on the host that wrote the v0 DB [workaround inferred from the root cause; UNVERIFIED]. Spot-check a few events against known wall-clock times. The issue was closed on 2026-10-14, but the reporter says the fix (#7299) does not touch timestamp conversion.
- **Detect:** After migration, assert that the newest event's timestamp is ≤ now and ≥ the session `create_time`.
- **Also:** #5634, "Unsafe pickle.loads() in v0 schema runtime path and migration tool". Only migrate DB files you trust.
- **Source:** https://github.com/google/adk-python/issues/7300 , https://github.com/google/adk-python/issues/5634

### A7. `LlmAgent(temperature=0.1)` fails at construction
- **Symptom:** `ValidationError: 1 validation error for LlmAgent temperature Extra inputs are not permitted [type=extra_forbidden ...]`
- **Fix:** `generate_content_config=types.GenerateContentConfig(temperature=0.1)`. Since v2.9.0 the error message points you there. (For Gemini 3, see G2 before you lower temperature at all.)
- **Source:** https://github.com/google/adk-python/issues/6836 ; CHANGELOG 2.9.0

### A8. Minor 2.x releases contain real breaking changes
- 2.6.0: "**artifacts:** namespace file artifacts by app". Existing `FileArtifactService` paths move.
- 2.7.0: "`pyarrow` left the `gcp` extra". `BigQueryAgentAnalyticsPlugin` needs `pip install google-adk[bigquery-analytics]`.
- 2.12.0: `requires_python >=3.11` (it was 3.10 through 2.11).
- 2.13.0: telemetry defaults to OTel GenAI semconv v2 (`otel_semconv_1_44`), and the `call_llm` span is removed. Opt out with `ADK_TELEMETRY_SCHEMA_VERSION_OPT_IN=otel_semconv_1_36`.
- **Detect:** Read the "Breaking changes" block of every CHANGELOG entry in the upgrade PR. Dashboards keyed on `call_llm` go to zero silently.
- **Source:** https://github.com/google/adk-python/blob/main/CHANGELOG.md

---

## B. Workflow graphs (resume, retry, HITL, parallelism)

### B1. `retry_config` re-runs a sibling that already finished, so the side effect happens twice (Open)
- **Symptom:** A fan-out has a `JoinNode`. One branch fails once and retries. The other branch, `send_email`, runs **again** under the same run id `body@1/send_email@1`. No error is raised. Reporter's output: `[sqlite] node executions: {'flaky': 2, 'send_email': 2} emails sent: ['email #1', 'email #2']`.
- **Root cause:** The completed sibling's output event is still being persisted (async `append_event`, real I/O, or a ~1 ms plugin `on_event_callback`) when the failure cancels the batch, so replay does not see it. InMemory passes, SQLite fails.
- **Fix/workaround (maintainer):** Put `retry_config` on the **flaky node itself**, not on the enclosing Workflow. PR #7526 adds a persist barrier and is not merged yet.
- **Detect:** Run every resume and retry test against the **same session backend you use in prod**, not InMemory, and count side-effect calls.
- **Source:** https://github.com/google/adk-python/issues/7524

### B2. `RuntimeError: Replay divergence detected: Timed out waiting for sequence key '…' to be unblocked.`
- **Two root causes in 2026:**
  1. Events with **equal timestamps** reload out of append order. Sqlite and Database services order by `(timestamp, id)` and ids are random. This is common on Windows, where Python 3.12 ticks every 15.6 ms. Fixed for `SqliteSessionService` in v2.12.0 ("preserve append order for tied timestamps"). `DatabaseSessionService` [UNVERIFIED].
  2. **Repeated HITL** in a review/revise loop deadlocks on the 3rd resume. Fixed in v2.10.0 ("stop a re-emitted output echo from reordering the replay sequence").
- **Fix:** Upgrade to ≥2.12. Tests can force ties with `google.adk.platform.time.set_time_provider` (the reporter's technique).
- **Detect:** Run a soak test that loops wait → classify → answer 10+ times with a coarse clock.
- **Source:** https://github.com/google/adk-python/issues/7286 , https://github.com/google/adk-python/issues/7027

### B3. Resume re-runs failed nodes, and Pub/Sub redelivery re-runs the whole agent
- **Symptom:** A payment or email is sent twice after a crash or a 500. The ambient-agents docs say "Each redelivery creates a new session." `trigger_routes.py` creates `session_id = str(uuid.uuid4())` per delivery.
- **Fix:** Make every side-effecting tool idempotent, keyed on a stable id. Since v2.12.0 the trigger delivery id is exposed so tools can detect redeliveries ("expose trigger delivery id so tools can detect redeliveries"). The recommended pattern (#7325 docstring): "provider key first, atomic reservation if it's a store and a 409 is raised rather than handed back to the model".
- **Detect:** Write a chaos test that injects an exception after the tool returns and before the run ends, then redelivers. Assert there is exactly one side effect.
- **Source:** https://github.com/google/adk-python/issues/7322 ; CHANGELOG 2.12.0

### B4. Parallel tool calls: a raising sibling erases finished siblings, which the model then re-runs
- **Symptom:** The model calls `create_ticket` and `notify_oncall` in parallel. `notify_oncall` raises. On the next turn the model creates the ticket **again**.
- **Root cause:** The merged response event was built only after `_gather_or_cancel`. The finished results were then dropped, and `drop_orphaned_function_calls` stripped the call. Related bugs: `parts[0]` indexing dropped parallel tool responses, fixed in v2.10.0; and a never-executed parallel call was not replayed, fixed in v2.11.0.
- **Fix:** Upgrade to ≥2.13.0 ("keep finished parallel tool results when a sibling raises"). Until then, add an `on_tool_error_callback` that returns a dict, so nothing raises.
- **Source:** https://github.com/google/adk-python/issues/7428 , https://github.com/google/adk-python/issues/6603 , https://github.com/google/adk-python/issues/7108

### B5. Parallel `single_turn` agents see each other's inputs and outputs
- **Symptom:** Worker B's context contains worker A's "order 1" output.
- **Root cause:** `_get_current_turn_contents` scanned backwards from the tail of the **shared** session event list. A related bug: a shallow `session.model_copy(deep=False)` shared the `events` list, so node-input events (including inline PDF bytes) leaked into the root agent's request (#7227, fixed in v2.11.0).
- **Fix:** ≥2.12.0 (node-path fix 097ae1e and tool sub-branch fix 2e06fdc).
- **Detect:** Write a test that fans out two workers with distinct sentinel strings and asserts each request contains only its own sentinel.
- **Source:** https://github.com/google/adk-python/issues/7488 , https://github.com/google/adk-python/issues/5961 , https://github.com/google/adk-python/issues/7227

### B6. A `single_turn` sub-agent that pauses on a tool confirmation takes over the conversation
- **Symptom:** After a `require_confirmation=True` tool pauses inside a single_turn sub-agent, every later user turn goes to the sub-agent. The root's model is never called again.
- **Fix:** v2.13.0 ("route the turn after a paused single_turn sub-agent to its delegator", closes #7602).
- **Source:** https://github.com/google/adk-python/issues/7602

### B7. A task-mode root agent forgets the original request after it asks a clarifying question (Open)
- **Symptom:** With root `LlmAgent(mode="task")` (the server shape behind `to_a2a`), the turn after the question shows the user's **answer twice** and the original request is gone. A second task in the same session reuses scope `<agent>@1`.
- **Fix:** None merged. Workaround: keep a `mode="chat"` root and put task agents underneath it (see A2).
- **Source:** https://github.com/google/adk-python/issues/7384

### B8. `output_schema` results are not JSON-serializable (Decimal, datetime, UUID, Enum)
- **Symptom:** Persisting or serializing `Event.output` fails, or `when_used="json"` serializers are skipped.
- **Root cause:** `BaseNode._validate_schema` used `model_dump()` (python mode), although its docstring says it keeps output JSON-serializable. Also open: #7280, where `validate_schema` does **not validate** `list[str]`, `dict[...]`, raw JSON Schema or `types.Schema` (bare `safe_json_loads`).
- **Fix:** Fix PR #6750 (`mode="json"`) [release UNVERIFIED]. Until then, use `BaseModel` schemas only, and give them JSON-native field types.
- **Source:** https://github.com/google/adk-python/issues/6747 , https://github.com/google/adk-python/issues/7280

### B9. A `before_agent_callback` that only changes state ends the turn with an empty event (Open)
- **Symptom:** A callback writes `callback_context.state[...]` and the agent returns an empty event instead of running.
- **Root cause:** `base_agent.py` treats "state delta present" as an early-exit output. This is not documented on the callbacks page; docs PR adk-docs#2245.
- **Fix/workaround:** Do state setup in a preceding `@node` function or in `before_model_callback` [workaround inferred; UNVERIFIED].
- **Source:** https://github.com/google/adk-python/issues/7078

### B10. FunctionNodes are invisible to plugins and analytics
- **Symptom:** `BigQueryAgentAnalyticsPlugin` writes rows for agents but **none** for FunctionNodes.
- **Root cause:** `NodeRunner` did not dispatch plugin callbacks (`rg plugin_manager src/google/adk/workflow/` gave 0 matches at the time), and the plugin read `event.content`, not `Event.output`. Since v2.11.0 the release notes say "run plugin tool callbacks around ToolNode calls". Native node lifecycle callbacks remain deferred (maintainer note, 2026-08-11).
- **Detect:** In staging, assert one analytics row per graph node.
- **Source:** https://github.com/google/adk-python/issues/6529

---

## C. Sessions, state, memory

### C1. `list_sessions()` has no order, so `sessions[-1]` is not the latest
- **Symptom:** Users randomly get a 3-day-old session, and the app creates orphan sessions ("losing all conversation history").
- **Fix:** v2.7.0 orders by update time for Database and Sqlite. Never rely on position. Sort by `last_update_time` yourself.
- **Source:** https://github.com/google/adk-python/issues/6272

### C2. Mixing `SqliteSessionService` and `DatabaseSessionService` on one file
- **Symptom:** `TypeError: fromisoformat: argument must be str`, raised from `sqlalchemy/cyextension/processors.pyx … str_to_datetime`.
- **Root cause:** The REAL-affinity float timestamps written by one service are read as strings by the other.
- **Fix:** v2.5.0 handles floats. Maintainer: "if SQLite is your main database we recommend just use the SqliteSessionService." Use one service per DB.
- **Source:** https://github.com/google/adk-python/issues/6352

### C3. Redis session keys collide across tenants (Open)
- **Symptom:** `("billing","tenant:victim","fixed")` and `("billing","tenant","victim:fixed")` map to the same key `{prefix}billing:tenant:victim:fixed`. The reporter reproduced cross-user read, append and delete on 2.8.0.
- **Fix:** PR #7563 (new key format) is open. Until then, **reject `:` in `user_id`/`session_id`** at your API edge, or hash the ids.
- **Detect:** Add a property test over ids that contain separators.
- **Source:** https://github.com/google/adk-python/issues/7464

### C4. `delete_session()` does not delete what was copied into memory
- **Symptom:** After the session is deleted, `search_memory()` still returns `my-passport-number-is-AB1234567` verbatim.
- **Fix:** v2.13.0 adds `BaseMemoryService.delete_memory` (with a `NotImplementedError` default; `MemoryEntry.id` is set for InMemory, Firestore and Memory Bank, but not RAG). Wire it into your GDPR/erasure path. For backends that don't implement it, delete in the backend directly.
- **Source:** https://github.com/google/adk-python/issues/7109 ; CHANGELOG 2.13.0

### C5. Session state does not cross a `RemoteA2aAgent` boundary, in either direction
- **Symptom:** `output_key="findings"` on the remote worker means the caller reads `None`. A caller-side `state_delta` never reaches the remote. Everything works in-process, so CI passes.
- **Fix:** Pass data explicitly in the message or the artifact, and treat A2A as a network boundary. Since v2.12.0 ADK warns when state is dropped.
- **Detect:** Write an integration test that runs the remote agent behind a real `to_a2a()` server, not in-process.
- **Source:** https://github.com/google/adk-python/issues/6854

### C6. `output_key` + SSE streaming keeps only the text after the last tool call
- **Symptom:** "60-70% of agent responses being discarded" (1.32.0, LlmAgent wrapped as an AgentTool).
- **Fix:** Closed 2026-06-19 [fixing release UNVERIFIED]. Have the agent emit its final answer as a single last response (e.g. `output_schema`), and test with streaming on.
- **Source:** https://github.com/google/adk-python/issues/5590

### C7. A replacement `LlmResponse` from `after_model_callback` turns every streamed delta into a final event
- **Symptom:** The session history fills with fragments. The client sees N "final" responses.
- **Root cause:** `partial` defaults to `None`, which means final. The Runner persists every non-partial event.
- **Fix:** v2.10.0 copies the streaming flags across. On older versions, copy `partial` and `turn_complete` from the original response by hand.
- **Source:** https://github.com/google/adk-python/issues/7035

### C8. A session is "permanently poisoned" by an orphaned function response
- **Symptom:** Every turn raises `ValueError` from `_rearrange_events_for_latest_function_response`. The agent never answers again. `before_model_callback` cannot help, because the raise happens earlier in `_preprocess_async`. One way this happens: progressive SSE marks the delegation FunctionCall chunk `partial=True`, the wrapper dispatches on it, and the FC is never persisted (#6583).
- **Fix:** Both issues are closed (PR #6638 adds a `partial` gate). Operationally, keep a "reset session" path and alert on repeated identical exceptions per session.
- **Source:** https://github.com/google/adk-python/issues/6582 , https://github.com/google/adk-python/issues/6583

---

## D. Tools, MCP, A2A, auth, HITL

### D1. MCP toolset dies forever after the server restarts or scales to zero
- **Symptom:** Every call fails with `Session terminated` / 404 "Session not found". `@retry_on_errors` retries the **same cached session**. With `_MCP_GRACEFUL_ERROR_HANDLING` (default on) you get a dict, `{"error": "MCP tool execution failed: Session terminated"}`, instead of an exception, so app code can't tell it from a normal result.
- **Root cause:** `_is_session_disconnected()` only checked the local stream flags.
- **Fix:** v2.10.0 ("rebuild a session the server reports it no longer holds"), plus v2.11.0 ("detect a dead MCP session whose transport sits behind a dispatcher"). #6822 is still open as a report against 2.7.1.
- **Detect:** Write an e2e test that restarts the MCP container between two tool calls. Alert on the tool-result error string, not only on exceptions.
- **Source:** https://github.com/google/adk-python/issues/7060 , https://github.com/google/adk-python/issues/6822

### D2. `to_mcp_server` leaks one ADK session per tool call in stateless mode
- **Symptom:** Session storage grows linearly with traffic behind Cloud Run (stateless streamable HTTP builds a fresh transport per request).
- **Root cause:** A `WeakKeyDictionary` drops the mapping, but nothing calls `session_service.delete_session`.
- **Fix:** PR #7155. The issue closed 2026-10-21 [shipping release UNVERIFIED; not in the 2.13.0 notes]. Until then, run a TTL cleanup job on the session store.
- **Source:** https://github.com/google/adk-python/issues/7154

### D3. MCP Python SDK 2.0 (2026-07-28) and the ADK pin
- **Symptom:** `pip` conflicts: ADK pinned `mcp>=1.24,<2`. The breaking renames include `McpError` → `MCPError`, `inputSchema` → `input_schema`, and a float `read_timeout_seconds`.
- **Fix:** v2.9.0/2.10.0 widen the bound to `<3` and run on either major (via `IS_MCP_SDK_V2`). v2.11.0 adds "an opt-in modern-protocol connect path for MCP SDK 2.x". **Gotcha:** the OTel instrumentor is built for httpx 1.x, so under MCP 2.x "mcp calls go untraced rather than breaking" (maintainer, 2026-09-11). Also, every `crewai` release pins `mcp~=1.28.1`.
- **Source:** https://github.com/google/adk-python/issues/6532

### D4. HITL confirmation can be forged by an A2A peer or an unauthenticated `/run` caller (Open)
- **Symptom:** A remote peer sends a `function_response` DataPart `{confirmed: true}` for a pending `adk_request_confirmation`, and `ExecuteBashTool` runs.
- **Root cause:** The only trust check is `event.author == "user"`, and inbound A2A messages become `role='user'`. The v2.8.0 guard (9e9eaa6) **was reverted on 2026-08-20** (9a32eba, "revert the A2A guard that broke every HITL tool confirmation"). The replacement, #7134, is open.
- **Fix:** Put authentication in front of `adk api_server` (it has none by default). Don't expose confirmation-gated tools on an A2A-served agent.
- **Source:** https://github.com/google/adk-python/issues/6461

### D5. "Decline" did not stop a custom `BaseTool`
- **Symptom:** The user clicks Decline and the custom tool's side effect still happens (2.9.1).
- **Root cause:** The resume path never read `ToolConfirmation.confirmed`. Only the built-in tools checked it.
- **Fix:** v2.10.0 enforces the gate centrally (`apply_confirmation_gate()`). Verified by the reporter: Decline → 0 executions, `{'error': 'This tool call is rejected.'}`.
- **Source:** https://github.com/google/adk-python/issues/7148

### D6. A `require_confirmation` predicate that returns `None` skips the gate (Open, PR #7012)
- **Root cause:** `cast(bool, ...)` does nothing at runtime, and a predicate that falls off a branch returns `None`, which is falsy.
- **Fix:** Always `return bool(...)` and add an explicit `return True` default:
```python
def needs_ok(amount: float, **_) -> bool:
    if amount > 100:
        return True
    return False          # never fall through
FunctionTool(transfer, require_confirmation=needs_ok)
```
- **Source:** https://github.com/google/adk-python/issues/7010

### D7. OAuth/OIDC `RestApiTool`: a 401 traps the session in a loop
- **Symptom:** Every turn returns `Status Code: 401`. The user is never re-prompted. Repeated 401s can trip WAF rate-limits. `ToolContextCredentialStore.remove_credential()` crashed with `AttributeError: __delitem__`.
- **Fix:** v2.10.0 ("handle HTTP 401 in RestApiTool and recover stale OAuth2 credentials").
- **Related:** #7182, where an OIDC auth request raised by a **sub-agent's** tool never shows the popup. Closed 2026-10-13; the cause was found on the reporter's side [details UNVERIFIED].
- **Source:** https://github.com/google/adk-python/issues/7085 , https://github.com/google/adk-python/issues/7182

### D8. SkillToolset hallucination loop on `run_skill_script`
- **Symptom:** An instruction-only skill (no `scripts/`) leads the model to call `run_skill_script` repeatedly with made-up args. `tool_filter=["list_skills","load_skill"]` alone did not help, because the injected system instruction still advertised the tool.
- **Fix:** v2.9.0 (the instruction respects `tool_filter`) and v2.10.0 ("hide run_skill_script when no skill has a script").
- **Source:** https://github.com/google/adk-python/issues/6281

### D9. `RemoteA2aAgent` refuses plaintext http inside a service mesh (Open)
- **Exact errors:** `Agent card URL must use https, or http on a loopback host: <url>` / `Agent card RPC URL must use https, or http on a loopback host: <url>`. There is no opt-out flag (2.9.1).
- **Fix:** Expose https endpoints, or use a loopback sidecar address. An opt-in PR is pending.
- **Source:** https://github.com/google/adk-python/issues/7139

### D10. A2A streaming quirks
- Against a deployed Agent Engine, `message:stream` stops after `TASK_STATE_WORKING`, or fails with `append=True for nonexistent artifact_id='<uuid>' … The artifact must be created (append=False) before appending parts to it.` `message:send` works. Fixed in v2.12.0 ("keep streamed artifacts when a Task snapshot arrives mid-stream"). https://github.com/google/adk-python/issues/6680
- The default streaming executor delivers the final text **twice** (once as `thought=True`) and `adk_request_confirmation` twice with the same id (Open). https://github.com/google/adk-python/issues/7247
- `RemoteA2aAgent(mode="task")` delegating to a **non-ADK** peer never closes on `TASK_STATE_COMPLETED`, because it waits for ADK's `finish_task` (Open; PR #7251). https://github.com/google/adk-python/issues/7248
- A Workflow's `output_schema` result was dropped by `to_a2a()`, because the converters only read `event.content`, not `Event.output` (PR #6777) [release UNVERIFIED]. https://github.com/google/adk-python/issues/6762
- **Detect:** Run a cross-SDK contract test against a plain `a2a-sdk` server as well as an ADK server.

### D11. Sync tools block the event loop
- **Symptom:** BigQuery `execute_sql` froze the whole process: "heartbeat ran 3 times, longest gap between heartbeats: 2.108s".
- **Fix:** v2.11.0 makes the BigQuery tools coroutines. For your own tools, write `async def` and use `await asyncio.to_thread(blocking_call, ...)`. (v2.13.0 also lets synchronous workflow nodes use `tool_thread_pool_config`.)
- **Detect:** Run a heartbeat-task test like the reporter's, or enable asyncio debug mode (`slow_callback_duration`).
- **Source:** https://github.com/google/adk-python/issues/7160

### D12. Live (bidi) streaming tools re-invoke themselves forever
- **Symptom:** Each `yield` from an async-generator tool makes the model call the same tool again.
- **Root cause:** Results are sent with `send_client_content(..., turn_complete=True)`.
- **Fix:** Closed 2026-07-06 [fix release UNVERIFIED]. Add a duplicate-in-flight guard keyed on tool+args, and test live tools explicitly.
- **Source:** https://github.com/google/adk-python/issues/5947

---

## E. Deployment (Cloud Run, Agent Runtime / Agent Engine)

### E1. Cloud Run without `--session_service_uri` loses sessions
- **Docs:** "the deployed container falls back to the in-memory session and artifact services … sessions and artifacts are lost whenever a Cloud Run instance is recycled."
- **Fix:**
```bash
adk deploy cloud_run --project=$P --region=$R \
  --session_service_uri="agentengine://$AGENT_ENGINE_ID" \
  --artifact_service_uri="gs://$BUCKET" ./my_agent
```
  (Any SQLAlchemy URL is also accepted; the `gs://` artifact form is [UNVERIFIED] on that page.) Don't ship `--with_ui` to production, and answer **n** to unauthenticated access.
- **Source:** https://adk.dev/deploy/cloud-run/

### E2. Long Gemini Enterprise conversations hit `429 RESOURCE_EXHAUSTED … 'Session Event Append Requests per minute per region'`
- **Root cause:** Agent Engine `_init_session` replays every prior event through individual `append_event` calls. Each retry burns more quota.
- **Status:** Closed without a merged fix (PR #5720 unreviewed). The maintainer says "the underlying bug is still live". Request a quota increase and keep hand-off histories short.
- **Source:** https://github.com/google/adk-python/issues/5714

### E3. `adk deploy agent_engine` and capability mismatches
- `:asyncQuery` failed with `FAILED_PRECONDITION: The reasoning engine resource [...] does not support AsyncQueryReasoningEngine API`. A backend fix rolled out "in some regions" (2026-07-14). https://github.com/google/adk-python/issues/6220
- With Agent Gateway enabled, the generated Dockerfile ignored the `AGENT_GATEWAY_ROOT_CERTIFICATES` build arg, so every outbound TLS call failed. Resolved by #7048 (commit 2ba3e2d, 2026-10-15). https://github.com/google/adk-python/issues/6427
- `'AgentEngine' object has no attribute 'async_create_session'` came from `agents-cli`, not ADK, and was fixed in agents-cli v1.4.0 (2026-08-18). https://github.com/google/adk-python/issues/6369
- `SystemError` at startup from a mismatched `pydantic`/`pydantic_core`. The reporter's root cause was `extra_packages=["./"]` shipping the local venv. https://github.com/google/adk-python/issues/6041
- `AttributeError: 'LlmAgent' object has no attribute 'mode'. Did you mean: 'model'?` came from version skew between the deployed ADK and the agent code (`google-adk>=1.20.0` resolved differently in the cloud). The maintainer's advice is to pin versions. https://github.com/google/adk-python/issues/6156
- **Detect:** Run a post-deploy smoke test that calls `async_create_session` + `async_stream_query` and one tool call. Fail the pipeline if the stream ends without a final event.

### E4. A worker dies with no traceback on the second model call (2.7.0 on Agent Engine)
- **Symptom:** The stream ends after 2 events. The uvicorn worker is replaced silently. Reverting to 2.6.2 fixes it.
- **Status:** Closed as stale. The root cause was never published [UNVERIFIED].
- **Lesson:** Canary every minor upgrade. Keep the previous image deployable.
- **Source:** https://github.com/google/adk-python/issues/6757

### E5. A client disconnect skips `after_run_callback` (2.11.0 regression)
- **Symptom:** Per-run plugins (billing, analytics flush) get no callback when `/run` cancels `worker_task`. `on_run_error_callback` is also skipped, because `CancelledError` is not an `Exception`.
- **Fix:** v2.12.0 ("run after_run_callback when an aborted run is cancelled"). Prefer `abort_signal` (2.11.0) over task cancellation.
- **Source:** https://github.com/google/adk-python/issues/7394

### E6. A shared agent instance leaks a capability across invocations
- **Symptom:** One request with `RunConfig(support_cfc=True)` left `code_executor = BuiltInCodeExecutor()` on the shared `LlmAgent`, so later requests got code execution too.
- **Fix:** v2.10.0 (f8282da). Lesson: treat agents as immutable after construction, and never mutate them per request.
- **Source:** https://github.com/google/adk-python/issues/7224

### E7. Observability dashboards read 0 after an upgrade
- 2.2.0 emitted the `cloud.resource.id` attribute instead of the OTel `cloud.resource_id`, so every Agent Engine dashboard panel showed 0. Fixed in v2.4.0. https://github.com/google/adk-python/issues/6247
- 2.13.0 removes the `call_llm` span (see A8).
- Under MCP SDK 2.x, MCP calls are untraced (see D3).
- **Detect:** Add a synthetic canary query per deployment plus an alert on "spans ingested > 0 but dashboard metric = 0".

---

## F. Evals

### F1. An eval that evaluates **zero** cases passes
- **Symptom:** `eval_cases=[]` or `num_runs=0` gives a green run.
- **Fix:** v2.10.0 raises `ValueError`. Also assert the number of evaluated cases in CI.
- **Source:** https://github.com/google/adk-python/issues/6951

### F2. `safety_v1` silently became `safety_v3`, which scores in the opposite direction
- **Symptom:** Benign answers fail the safety gate and harmful ones pass. The `threshold` cannot fix it.
- **Root cause:** `PrebuiltMetric.SAFETY` was unversioned and resolved to "latest" in the aiplatform SDK. It depends on the aiplatform version, not on ADK.
- **Fix:** v2.10.0 ("pin the specific version for safety_v1"). Lesson: keep a known-bad and a known-good fixture in **every** eval gate.
- **Source:** https://github.com/google/adk-python/issues/7258

### F3. A lower-is-better custom metric fails even when its evaluator says PASSED
- **Root cause:** `AgentEvaluator` used `overall_score >= threshold` and ignored `eval_status`.
- **Fix:** On main since 2026-10-14 (5bf7f12, PR #6739) [shipping release UNVERIFIED]. Until then, invert the metric (e.g. 1 − error_rate).
- **Source:** https://github.com/google/adk-python/issues/7414

### F4. Rubric verdicts dropped when the judge paraphrases (non-English)
- **Symptom:** `... not found in the rubrics provided to the metric.` then `Expected 0.7, but got None.` (Japanese 長音符/kanji variants).
- **Fix:** v2.6.0 ("match rubric verdicts by echoed id"). Open follow-up #7659: duplicate rubric verdicts let one judge sample outvote two.
- **Source:** https://github.com/google/adk-python/issues/6171

### F5. Editing an eval case in `adk web` fails with `422 Unprocessable Entity`
- **Root cause:** The Web UI sends view-model fields `invocationIndex`/`toolUseIndex`, and `InvocationEvent` forbids extras. A second cause was `RubricContent.text_property` lacking a default (#7026).
- **Fix:** Edit the eval-set JSON in git, not in the UI [workaround; UNVERIFIED as fixed in 2.13].
- **Source:** https://github.com/google/adk-python/issues/7019

---

## G. Gemini model quirks (as seen through ADK)

### G1. `Function call is missing a thought_signature in functionCall parts.`
- **Symptom:** Gemini 3 returns 400 on the request after a tool call. Seen with `LiteLlm(..., stream=True)` against the Vertex OpenAI-compatible endpoint.
- **Root cause:** The streamed tool-call reassembly dropped `thought_signature`. Non-streaming was already fixed.
- **Fix:** v2.12.0 ("keep Gemini thought signatures on streamed LiteLlm tool calls"), v2.13.0 ("keep a streamed thought signature sent without the call's name"). Native `Gemini` path: v2.7.0 keeps signatures in history. On older versions, turn streaming off.
- **Rule:** Never rebuild or filter history parts by hand (callbacks, compaction, custom session stores), because you will drop signatures.
- **Source:** https://github.com/google/adk-python/issues/7438

### G2. Lowering temperature on Gemini 3 causes looping
- **Docs:** "Changing the temperature (setting it below 1.0) may lead to unexpected behavior, such as looping or degraded performance". Keep the default `1.0`. (The page is now marked deprecated in favour of the Gemini 3.8 Flash guide, and it lists 3.x model ids.)
- **Also:** You "cannot use both `thinking_level` and the legacy `thinking_budget` parameter in the same request" (400). `thinking_level` defaults to `high` (it is `minimal` on 3.1 Flash-Lite), so latency and cost rise unless you set it.
- **Detect:** Add a tool-loop counter metric and set `RunConfig(max_llm_calls=...)` as a budget.
- **Source:** https://ai.google.dev/gemini-api/docs/gemini-3

### G3. `output_schema` + tools on non-native Gemini paths loop
- **Symptom:** 4–19 model calls per turn on `openrouter/google/gemini-3.1-flash-lite`.
- **Root cause:** `LiteLlm.capabilities` hard-coded `output_schema_and_tools=True`, so the `SetModelResponseTool` fallback never engaged.
- **Fix:** PR #6955: "2 calls per turn instead of 4-19" (verified by the reporter on one model only).
- **Source:** https://github.com/google/adk-python/issues/6954

### G4. An aborted LiteLLM stream mid-tool-call raises an unhandled `JSONDecodeError`
- **Root cause:** The truncation guard only covered `finish_reason == "length"`.
- **Fix:** PR #6937 (closed 2026-08-13) [release UNVERIFIED]. Wrap model calls with `on_model_error_callback`.
- **Source:** https://github.com/google/adk-python/issues/6716

### G5. Default model drift
- `DEFAULT_MODEL = 'gemini-3.5-flash'` in `llm_agent.py` (critic file C23). The docs snippets use the alias `gemini-flash-latest`. Both move under you, so pin an explicit model id per agent in production and record it in eval results.

---

## 10 open challenges (not solved in the field as of 2026-10-23)

1. **Exactly-once side effects in a resumable agent graph.** ADK added replay, resume, retry and delivery ids, but #7524 (open) shows a completed sibling re-running under retry on a real DB backend, and #7322 needed a docstring recipe for idempotency. Durable-execution semantics for LLM tools (two-phase commit, reservations) are still the developer's job.
2. **Human approval as a security boundary.** In ADK the HITL guard against forged A2A approvals was **reverted** (#6461, open via #7134). In research, *From Approval to Abuse* (arXiv 2610.22987, 2026-10-16) shows injected repo context gets Claude Code and Codex CLI to request broad allow-rules in 58% of instances, with 81.0% silent goal completion once approved. Approval fatigue turns HITL into a privilege-escalation channel.
3. **Prompt-injection defense for tool agents.** *Ignored, Not Refused* (2610.23254) reports that a system prompt alone moves InjecAgent attack success rate from 0.2% to 43%. *The Window Is in the Reasoning* (2610.24048) finds that with thinking on, the decision to follow an injection forms during reasoning (0.62 of variance fixed at read time vs 0.91 without thinking). *One Word Opens the Gate* (2610.12292) shows six lines of irrelevant log text raise an LLM guardrail's fail-open rate from 0% to 63%, and a deterministic rule beats the model. Lesson for ADK: deterministic `before_tool_callback` policy checks, not LLM judges, should make the allow/deny decision (see also open FR #7520).
4. **Persistent and memory-borne attacks.** *CarryoverBench* (2610.28425, 2026-10-20) shows injections stored in long-term memory or scheduled tasks re-fire across five rounds "without measurable decay" on five frontier models. ADK only got `delete_memory` in 2.13.0 (#7109), and `MemoryEntry.id` is not set for RAG memory. Memory provenance and quarantine are unsolved.
5. **Multi-agent ≠ better, and failures hide inside successes.** *Does Multi-Agent Collaboration Pay When Agents Serve Users?* (2610.27655) finds a centralized MAS worse than a single agent in 12 of 13 τ²-bench cells (~7,950 conversations). *MASIF* (2610.25852) finds "implicit failures" in 54.3% of **successful** traces. Outcome-only evals (ADK `final_response_match`, rubric metrics) cannot see them.
6. **Cross-boundary (A2A) trust and state.** *Why Do Agent Teams Fail Across Boundaries?* (2610.19342; 2,500+ runs, 20 failure modes) finds that no agent independently verifies a peer's factual claims, so the system is only as reliable as its least reliable participant. ADK evidence: state does not cross `RemoteA2aAgent` (#6854), non-ADK peers never close task delegations (#7248), and streaming duplicates replies (#7247).
7. **Silent communication faults.** *When Messages Go Wrong* (2610.15459; 29,000+ executions) finds 20.7% of failures give no immediate signal (76.2% for partial-content faults), and sequential and hierarchical topologies collapse to ~3% success under faults vs 53.0% for flat. ADK parallels: MCP graceful-error dicts hide dead sessions (D1), and the A2A stream truncates after WORKING (D10).
8. **Eval reliability.** Single runs disagree with reruns up to 35% for thinking agents (2610.24048). ADK's own eval stack shipped a gate inversion (`safety_v1`→`v3`, #7258), a silent pass on zero cases (#6951), polarity bugs (#7414) and duplicate-verdict voting (#7659). pass^k-style repeated runs plus known-good and known-bad fixtures are needed, and nobody has made them cheap.
9. **Version churn vs production stability.** 13 minor releases in 5 months (2.0.0 2026-05-19 → 2.13.0 2026-10-23), each with fixes to core semantics such as routing, replay and confirmation. Regressions came with them: #7394 (2.11.0), #6757 (2.7.0), #6247 (2.2.0). Many issues are auto-closed as "stale" without a fix (#5714, #6757, #6198). Teams need canaries, pinned stacks and upgrade evals, and there is no LTS line.
10. **Observability of graph-native agents.** FunctionNodes were invisible to plugins (#6529), the telemetry schema changed twice (cloud.resource_id, then semconv v2 in 2.13.0), MCP 2.x calls are untraced, and the open #7494 reports that error spans other than tool spans don't set `error.type`. The OTel GenAI conventions for agents and graph nodes are still moving. Process-level signals (MASIF-style implicit failures) have no standard span model.

---

## Slide-ready "gotcha → guardrail" checklist (one slide)
- Pin `google-adk`, `a2a-sdk`, `mcp` and `litellm`. Canary every minor upgrade. Read the CHANGELOG "Breaking changes" block.
- Workflow nodes: `mode="single_turn"` + `include_contents="default"` when a node needs history. No chat agents inside graphs.
- Side-effecting tools: idempotency key + `retry_config` on the flaky node, not on the parent.
- Test resume and retry on your **production** session backend, not InMemory.
- Don't put `:` in Redis ids. Sort sessions yourself. Wire up `delete_memory` for erasure.
- Put auth in front of `api_server`. Don't expose confirmation-gated tools over A2A. Predicates return a real `bool`.
- Use `async` tools and `asyncio.to_thread` for blocking clients.
- Gemini 3: keep temperature 1.0, set `thinking_level`, never hand-edit history parts (thought signatures).
- Evals: assert the number of evaluated cases, keep known-good and known-bad fixtures per gate, run k > 1 times.
