# 10 - Multimodal Agent Design Patterns (2025 - Oct 2026)

> Research pack for the "Google ADK 2.0 and modern agent engineering" university deck. Compiled 2026-10-23.
>
> **Method and caveats.** The session's WebSearch budget ran out before this agent started, so every fact here comes from fetching known primary-source URLs directly (Google AI for Developers, adk.dev, GitHub `google/adk-python`, `google-gemini/computer-use-preview`, blog.google, voiceaiandvoiceagents.com, OSWorld). Pages were read through a summarizing fetcher. Code marked **[verbatim]** was asked for and returned as exact text. Code marked **[reconstructed]** was rebuilt from the page's description, or written for this deck. Anything not confirmed in a primary source is marked **[UNVERIFIED]**. Model IDs change quickly, so re-check the models page the day before you present.

---

## 0. The 30-second framing

A multimodal agent is still the ordinary loop of **perceive -> reason -> act -> observe**. What changes is the observation channel (pixels, audio frames, video frames, PDFs). That brings three engineering problems a text agent does not have:

1. **Token economics of perception.** One video frame costs 66-258 tokens, and a screenshot sits in context on every turn.
2. **Real-time constraints.** Voice needs about 1-1.5 s voice-to-voice latency and has to cope with barge-in.
3. **Grounding actions in pixels.** In computer use, the model outputs normalized coordinates and *your* code executes them.

ADK's answer is to keep one agent, tool and session abstraction and swap the transport. `runner.run_async()` handles request/response. `runner.run_live()` plus `LiveRequestQueue` handles bidirectional audio and video. `ComputerUseToolset` plus a `BaseComputer` implementation handles UI control.

---

## 1. State of the platform (as of 2026-10-22 docs)

Source: **"Gemini models"**, https://ai.google.dev/gemini-api/docs/models (last updated 2026-10-22 UTC).

| Category | Model IDs listed (status) |
|---|---|
| Text / multimodal | `gemini-4-argon` (Stable, New), `gemini-3.8-flash` (Stable, New), `gemini-3.6-flash`, `gemini-3.5-flash-lite`, `gemini-3.1-flash-lite`, `gemini-3-flash-preview`, `gemini-3.1-pro-preview` |
| Live / native audio | `gemini-3.8-live`, `gemini-3.8-live-extended-thinking` (Stable, New), `gemini-3.5-live-translate-preview`, `gemini-3.1-flash-live-preview` (legacy), `gemini-2.5-flash-native-audio-preview-12-2025` |
| Speech-to-text | `gemini-3.5-transcribe`, `gemini-3.5-transcribe-live` |
| TTS | `gemini-3.8-flash-tts`, `gemini-3.8-flash-lite-tts`, `gemini-3.1-flash-tts-preview` (legacy) |
| Image gen ("Nano Banana") | `gemini-nano-banana-2.1`, `gemini-3.1-flash-image`, `gemini-3.1-flash-lite-image`, `gemini-3-pro-image`, `gemini-2.5-flash-image` |
| Video | `gemini-omni-1.1-flash` |
| Embeddings | `gemini-embedding-2-preview`, `gemini-embedding-001` |
| Computer use | `gemini-2.5-computer-use-preview-10-2025`: **Shut down** |

**Key teaching point: computer use moved from a dedicated model into the mainline models.** The Oct 2025 launch shipped a separate model, `gemini-2.5-computer-use-preview-10-2025`. The Oct 2026 Computer Use docs list `gemini-3.8-flash` as "recommended for computer use", with `gemini-4-argon` for complex UI workflows and `gemini-3.5-flash-lite` as the low-latency option. The `google-gemini/computer-use-preview` reference repo now defaults to `gemini-3.6-flash`.

**Doc-lag warning (a real failure mode worth a slide).** At fetch time, three primary sources disagreed:

- The ADK Computer Use page and the ADK sample still use `gemini-2.5-computer-use-preview-10-2025`, which the models page marks as shut down.
- The ADK Live "Supported models" page (https://adk.dev/live/models/) lists only `gemini-2.5-flash-native-audio-preview-12-2025` / `gemini-live-2.5-flash-native-audio` and `gemini-3.1-flash-live-preview`. It calls `gemini-live-2.5-flash-native-audio` ADK's `LlmAgent.DEFAULT_LIVE_MODEL` and "the only Live model that is publicly available."
- The Gemini API Live guide already uses `gemini-3.8-live`.

Lesson for students: pin model IDs in config, not in code, and run a smoke test against the models page in CI.

[UNVERIFIED]: no launch blog post for Gemini 4 Argon / 3.8 Flash / 3.8 Live was fetched, so release dates for these models are not confirmed here.

---

## 2. Pattern: Vision-grounded computer use (screenshot -> action loop)

### 2.1 Launch facts (Oct 2025)

Source: **"Introducing the Gemini 2.5 Computer Use model"**, blog.google, **2025-10-07**, https://blog.google/technology/google-deepmind/gemini-computer-use-model/

- Specialized model "built on Gemini 2.5 Pro's visual understanding and reasoning". Exposed as a `computer_use` tool and run in a loop whose inputs are the request, the screenshot and the action history.
- Optimized for browsers, "promising" on mobile, and **not yet optimized for desktop OS-level control** (at launch).
- Claimed to outperform alternatives on **Online-Mind2Web, WebVoyager, AndroidWorld**. The numeric scores appear only in a chart image. The scatterplot alt text reads "70%+ accuracy, ~225 sec latency" on the Browserbase harness for Online-Mind2Web.
- Safety design: (a) safety training in the model, (b) a **per-step safety service**, an out-of-model check on every proposed action before it runs, and (c) system instructions to refuse or confirm high-stakes actions.
- Used internally for UI testing and in **Project Mariner, the Firebase Testing Agent, and agentic features in AI Mode in Search**. A public demo is hosted by **Browserbase**.

### 2.2 Current API contract (Oct 2026)

Source: **"Computer use"**, https://ai.google.dev/gemini-api/docs/computer-use (updated 2026-10-22)

- **Environments:** `ENVIRONMENT_BROWSER`, `ENVIRONMENT_MOBILE`, `ENVIRONMENT_DESKTOP`. Desktop is now listed, which is new compared with the launch.
- **Browser actions:** click, double_click, triple_click, middle_click, right_click, mouse_down, mouse_up, move, type, drag_and_drop, wait, press_key, key_down, key_up, hotkey, take_screenshot, scroll, go_back, navigate, go_forward.
- **Mobile actions:** open_app, click, list_apps, wait, go_back, type, drag_and_drop, long_press, press_key, take_screenshot.
- **Desktop actions:** the browser set minus navigate, go_back and go_forward.
- **Coordinates:** normalized integers on a **0-999 grid** (a "1000x1000" space). The client denormalizes with `pixel = value/1000 * screen_dim`. The model does not need the screen size.
- Each function call carries an **`intent`** field and may carry a **`safety_decision`** (`explanation`, `decision`): allowed, `require_confirmation`, or blocked. When the user confirms, the client returns `safety_acknowledgement` in the `function_result`.
- **Safety policy categories:** FINANCIAL_TRANSACTIONS, SENSITIVE_DATA_MODIFICATION, COMMUNICATION_TOOL, ACCOUNT_CREATION, DATA_MODIFICATION, USER_CONSENT_MANAGEMENT, LEGAL_TERMS_AND_AGREEMENTS. These can be relaxed with `disabled_safety_policies`, but that only sets a preference. The model may still return `require_confirmation`.
- **`excluded_predefined_functions`** removes built-in actions. You can add custom functions, for example a `yield_to_user` human handoff.
- **`enable_prompt_injection_detection`**: opt-in, default false, available on 3.5 Flash-Lite and later. It scans screenshots for hidden adversarial instructions and blocks execution.
- Docs guidance: run in a sandboxed VM, container or limited browser profile, and avoid irreversible or sensitive tasks. Pop-ups and layout shifts confuse the model.

### 2.3 Architecture flow (diagram in words)

`User goal` -> **Agent** (model + `computer_use` tool) receives the goal and screenshot #0 -> returns `function_call(s)` with normalized (x, y), `intent` and an optional `safety_decision` -> **Policy gate** (client): if blocked, stop; if `require_confirmation`, ask the human -> **Executor** (Playwright / Browserbase / ADB) denormalizes and acts -> waits for load plus about 0.5-1 s -> **Observer** takes screenshot #n and records the URL -> `function_result` [text JSON{url, error?}, image/png] -> back to the Agent -> loop until there are no function calls (final text) or the turn limit is hit.

Animation idea: a cursor dot jumps across a mock page while a 0-999 grid overlay fades in and out, and a red "confirm?" shield pops up at the "Buy" button.

### 2.4 Code: raw Gemini API loop [verbatim, excerpt]

Source: https://ai.google.dev/gemini-api/docs/computer-use (Apache 2.0)

```python
def denormalize_x(x: int, screen_width: int) -> int:
    """Convert normalized x coordinate (0-1000) to actual pixel coordinate."""
    return int(x / 1000 * screen_width)

# ... first call
interaction = client.interactions.create(
    model='gemini-3.8-flash',
    input=[
        {"type": "text", "text": USER_PROMPT},
        {"type": "image", "data": base64.b64encode(initial_screenshot).decode("utf-8"), "mime_type": "image/png"}
    ],
    tools=[{
        "type": "computer_use",
        "environment": "browser",
        "enable_prompt_injection_detection": True
    }]
)

# Agent Loop
turn_limit = 5
for i in range(turn_limit):
    has_function_calls = any(step.type == "function_call" for step in interaction.steps)
    if not has_function_calls:
        break
    results = execute_function_calls(interaction, page, SCREEN_WIDTH, SCREEN_HEIGHT)
    function_responses = get_function_responses(page, results)   # text JSON + PNG screenshot
    interaction = client.interactions.create(
        model='gemini-3.8-flash',
        previous_interaction_id=interaction.id,
        input=function_responses,
        tools=[{"type": "computer_use", "environment": "browser",
                "enable_prompt_injection_detection": True}]
    )
```

Note that the current docs use the **Interactions API** (`client.interactions.create`, `previous_interaction_id`), so server-side conversation state replaces resending the full history. The page's helper clears fields with `Meta+A`, a macOS shortcut. That is a classic cross-platform bug and makes a good slide.

### 2.5 Code: ADK `ComputerUseToolset` [verbatim]

Source: **"Gemini API Computer Use tool for ADK"**, https://adk.dev/integrations/computer-use/ (ADK Python >= **v1.17.0**, Preview)

```python
from google.adk import Agent
from google.adk.tools.computer_use.computer_use_toolset import ComputerUseToolset

from .playwright import PlaywrightComputer

root_agent = Agent(
    model='gemini-2.5-computer-use-preview-10-2025',   # docs-lag: swap for a current CU-capable model
    name='hello_world_agent',
    description=(
        'computer use agent that can operate a browser on a computer to finish'
        ' user tasks'
    ),
    instruction='you are a computer use agent',
    tools=[
        ComputerUseToolset(computer=PlaywrightComputer(screen_size=(1280, 936)))
    ],
)
```

The `BaseComputer` implementation is the seam where *you* own execution. From https://github.com/google/adk-python/blob/main/contributing/samples/multimodal/computer_use/playwright.py **[verbatim excerpt]**:

```python
  async def current_state(self) -> ComputerState:
    await self._page.wait_for_load_state()
    # Even if Playwright reports the page as loaded, it may not be so.
    # Add a manual sleep to make sure the page has finished rendering.
    await asyncio.sleep(0.5)
    screenshot_bytes = await self._page.screenshot(type="png", full_page=False)
    return ComputerState(screenshot=screenshot_bytes, url=self._page.url)
```

Every action (`click_at`, `type_text_at`, ...) returns `ComputerState(screenshot, url)`, so **each action is also an observation**. Setup: `pip install playwright==1.52.0 browserbase==1.3.0 termcolor==3.1.0 rich`, then `playwright install-deps chromium && playwright install chromium`, then `adk web contributing/samples`. Sample: https://github.com/google/adk-python/tree/main/contributing/samples/multimodal/computer_use. The sample README's install path omits `multimodal/`, a small doc bug.

Reference CLI: https://github.com/google-gemini/computer-use-preview runs `python main.py --query="..." --env="playwright"|"browserbase" --highlight_mouse`. Known issue: Playwright cannot capture OS-rendered `<select>` dropdowns. The workarounds are Browserbase or injecting a custom-select script.

### 2.6 Benchmarks to cite

- **OSWorld**: 369 tasks (361 without the Google Drive tasks), human performance about **72.36%**. OSWorld-Verified upgrade on 2025-07-28. **OSWorld 2.0 announced 2026-06-26**. Source: http://osworld-v1.xlang.ai/. Live leaderboard numbers were not captured [UNVERIFIED].
- Online-Mind2Web, WebVoyager and AndroidWorld (Google claims, Oct 2025). Exact scores [UNVERIFIED] (chart only).

### 2.7 Failure modes (computer use)

1. **Render race.** "Loaded" is not the same as painted, hence the `sleep(0.5)` in the ADK sample. The fix is load-state plus a settle delay, or a DOM-stable check.
2. **Coordinate drift.** A DPI or viewport mismatch between screenshot and executor (Retina 2x, a zoomed browser) makes clicks land in the wrong place.
3. **OS-rendered widgets** (`<select>`, file pickers, native dialogs) never appear in screenshots.
4. **Platform hotkeys** (`Meta+A` vs `Control+A`).
5. **Prompt injection in pixels**: hidden text on a web page. Mitigations: `enable_prompt_injection_detection`, a sandboxed profile, and an allow-list of domains.
6. **Over-autonomy on irreversible actions.** Use `require_confirmation` together with a custom `yield_to_user` tool.
7. **Context bloat.** Every turn adds a screenshot. Keep only the last N screenshots, or rely on server-side state through `previous_interaction_id`.
8. **Model deprecation.** The dedicated CU preview model is already shut down (see section 1).

---

## 3. Pattern: Voice agents - cascaded vs native audio

### 3.1 Two architectures (diagram in words)

**Cascaded:** Mic -> WebRTC/Opus -> **VAD + turn detector** -> **STT** (streaming partials) -> **LLM** (text, tools) -> sentence aggregator -> **TTS** (streaming) -> Opus -> speaker. Every arrow is a cancellation point.

**Native audio (speech-to-speech):** Mic -> 16 kHz PCM chunks -> **one Live model** over WebSocket (server VAD, interruption, tools, optional transcripts) -> 24 kHz PCM -> speaker. ADK's Live docs: native models take audio in and produce audio out "end to end, with no intermediate text-to-speech stage".

Source for the trade-offs: **"Voice AI & Voice Agents: An Illustrated Primer"**, Kwindla Hultman Kramer (Pipecat), updated **June 2026**, https://voiceaiandvoiceagents.com/

| | Cascaded | Native speech-to-speech |
|---|---|---|
| Latency | A well-tuned cascade is "faster than current speech-to-speech APIs" (primer) | Lower in theory |
| Control | Better instruction following, function calling and context editing | Less flexible context manipulation |
| Transcripts | Reliable (compliance, evals, UI) | Weaker. The transcript is a by-product. |
| Voice quality and nuance | Depends on the TTS | More natural. Handles prosody and code-switching. |
| Cost | ~2.5 cents/min in the primer's self-hosted example (Deepgram + GPT-4o + Cartesia) | ~$0.20+/min. "Roughly 3-5x" more than GPT-4.1 in the primer's comparison |

Primer cost split for the cascaded example: about 1/4 STT, 1/4 LLM, 1/2 TTS, hosting under 1%. Optimized at-scale deployments run about $0.02/min. Ops rule of thumb: one agent per VM CPU, and 2x the max RAM seen in dev.

### 3.2 Latency budget (use this table on a slide)

From the primer, a voice-to-voice round trip in a cascaded pipeline:

| Stage | ms |
|---|---|
| Mic input (macOS) | 40 |
| Opus encode | 21 |
| Network + transit | 10 |
| Packet handling | 2 |
| Jitter buffer | 40 |
| Opus decode | 1 |
| **STT + endpointing** | **300** |
| **LLM TTFB** | **650** |
| Sentence aggregation | 20 |
| **TTS TTFB** | **120** |
| Return path (encode, net, jitter, decode, speaker) | ~89 |
| **Total** | **~1,293** (the text says "about 1,200") |

- **Target: 1,500 ms voice-to-voice.** "It is critical, though, not to have latency spikes." A cascade co-located on one GPU cluster has reached about 500 ms.
- TTFB metrics hide endpointing delay, network and OS overhead. Measure **mic-to-speaker** (voice-to-voice), not model TTFB.
- STT, LLM and TTS make up about 83% of the budget. The LLM's time to first token is the biggest single lever.

### 3.3 Turn detection and barge-in

Turn detection approaches (primer):

- **VAD alone** (for example Silero) is "no longer sufficient" by itself.
- **Push-to-talk** is unambiguous but unnatural, and impossible on the phone.
- **Smart Turn**: a small native-audio model that runs in parallel with STT and decides in about 250 ms.
- **LLM single-token tagging**: the response starts with ✓ (respond now), ○ (wait ~5 s) or ◐ (wait ~10 s).
- The primer recommends combining VAD, Smart Turn and tagging.

Interruption rules (primer):

- Every stage must be cancellable, and client playout must stop at once.
- Spurious barge-ins come from transient noise, AEC failure at speech onset, and background talkers. Tune the VAD start length and confidence, and use speaker isolation.
- **After an interruption, context must reflect what the user actually heard.** Truncate the assistant turn using TTS word timestamps.

**Gemini Live API knobs** (https://ai.google.dev/gemini-api/docs/live-guide) **[verbatim]**:

```python
"automatic_activity_detection": {
    "disabled": False, # default
    "start_of_speech_sensitivity": types.StartSensitivity.START_SENSITIVITY_LOW,
    "end_of_speech_sensitivity": types.EndSensitivity.END_SENSITIVITY_LOW,
    "prefix_padding_ms": 20,
    "silence_duration_ms": 100,
}
# barge-in signal
if response.server_content.interrupted is True: ...
# manual VAD (push-to-talk / own endpointing)
await session.send_realtime_input(activity_start=types.ActivityStart())
await session.send_realtime_input(activity_end=types.ActivityEnd())
```

More Live guide facts:

- **Audio format:** raw little-endian 16-bit PCM, **16 kHz in, 24 kHz out**.
- **Session limits:** **15 min audio-only, 2 min audio+video**.
- **Context window:** 128k tokens on native-audio models, 32k on others.
- **Feature options:** `enable_affective_dialog=True` (adapts to the user's tone) and `proactivity={'proactive_audio': True}` (the model may choose not to respond). Both need `v1beta` and are not supported on 3.1 Flash Live.
- **Thinking:** `gemini-3.8-live` rejects `thinkingLevel`; `-extended-thinking` and the 3.1 models accept it.

### 3.4 ADK bidi-streaming architecture

Source: **"Live and voice agents"**, https://adk.dev/live/ (Python v0.5.0+, Java v0.2.0 experimental)

Diagram in words:

- Browser/phone -> WebSocket or WebRTC -> **FastAPI server** with two concurrent tasks:
  - **upstream**: client -> `LiveRequestQueue.send_realtime(Blob)` / `send_content(Content)`
  - **downstream**: `runner.run_live(...)` events -> client
- ADK talks to the **Gemini Live API**. It runs tools automatically, handles session resumption, and persists the session (SQL, Agent Platform, or in-memory).

What ADK adds over the raw Live API (from the page's comparison table):

| Concern | Raw Live API | ADK |
|---|---|---|
| Tool execution | manual | automatic |
| Reconnection | manual | session resumption |
| Events | custom structures | unified event model |
| Session persistence | manual | built in |
| Multi-agent | not available | sub-agents and transfer |

**Server skeleton [reconstructed from https://adk.dev/live/custom-server/; the docs' own example is longer]:**

```python
queue = LiveRequestQueue()                          # one per connected session
async def upstream():
    while True:
        text = await ws.receive_text()
        queue.send_content(types.Content(parts=[types.Part(text=text)]))
async def downstream():
    async for event in runner.run_live(user_id=user_id, session_id=session_id,
                                       live_request_queue=queue, run_config=cfg):
        await ws.send_text(event.model_dump_json(exclude_none=True, by_alias=True))
try:
    await asyncio.gather(upstream(), downstream(), return_exceptions=True)
finally:
    queue.close()   # docs: must run on every exit path
```

The docs say that running upstream and downstream sequentially "lose[s] interruption".

**Media rules** (https://adk.dev/live/audio-video/):

- **Audio in:** `audio/pcm;rate=16000` mono. Use 50-100 ms chunks (100 ms = **3,200 bytes**), 10-20 ms for ultra-low latency. Keep chunk sizes consistent, and do not wait for a model response before sending the next chunk.
- **Audio out:** `audio/pcm;rate=24000` mono, arriving as `inline_data`.
- **Video:** individual **JPEG frames, about 1 fps max, 768x768**. There is no video codec. This handles scene context but not motion or action recognition.
- **Recording:** `save_live_blob=True` persists audio (not video) to the artifact service.

**Events for barge-in** (https://adk.dev/live/events/):

- `partial`, `turn_complete`, `interrupted`
- `input_transcription` / `output_transcription` (`.text`, `.finished`)
- `usage_metadata`

When `interrupted` is true, the client must **flush its playback queue and stop the current audio source**. Otherwise the agent "talks over" the user.

**RunConfig for live** (https://adk.dev/live/configuration/, https://adk.dev/live/sessions/) **[verbatim]**:

```python
run_config = RunConfig(
    context_window_compression=types.ContextWindowCompressionConfig(
        trigger_tokens=100000,  # Start compressing near ~78% of the window.
        sliding_window=types.SlidingWindow(
            target_tokens=80000,  # Compress down to ~62%, keeping recent turns.
        ),
    )
)
run_config = RunConfig(session_resumption=types.SessionResumptionConfig())
```

- **Connections and resumption:** the Live API closes each WebSocket after about 10 min. ADK caches resumption handles, reconnects on `go_away`, and allows at most 5 *consecutive* failed reconnects.
- **Compression:** removes the session-duration cap, at the cost of a lossy summary of old turns. Guidance: trigger at 70-80% of the window, target 60-70%.
- **No cost ceiling:** `max_llm_calls` (default 500) **does not apply to `run_live()`**, so live sessions have no automatic cost limit. That is a production gotcha.
- **Agent Platform limits:** up to 1,000 concurrent sessions per project on PAYG, and a 10-min default session cap. Live models are **not available in `location=global`**.

**Tools in live sessions** (https://adk.dev/live/tools/):

- Async-generator **streaming tools** `yield` progress. They can take `input_stream: LiveRequestQueue` to watch the video stream, for example the people-counting `monitor_video_stream` sample. The reserved `stop_streaming` tool cancels them.
- `response_scheduling` (ADK Python >= 2.4): `WHEN_IDLE` (wait for a pause), `INTERRUPT` (deliver now, for alarms), `SILENT` (add to context only). It is supported on 2.5 Live. On 3.1 Live, function calling is synchronous.

**ADK 2.0 graph workflows live** (https://adk.dev/live/workflows/) **[verbatim excerpt]**:

```python
greeter  = Agent(model=LIVE_MODEL, name='greeter',  mode='task', instruction='...')
verifier = Agent(model=LIVE_MODEL, name='verifier', mode='task', instruction='...')
root_agent = Workflow(name='intake', edges=[(START, greeter), (greeter, verifier)])
```

Constraints:

- Every speaking node needs `mode='task'` or `mode='chat'`. Otherwise it falls back to `single_turn` and the caller hears nothing.
- Each node gets its own Live session, and transfers reset resumption handles.
- Use one queue and one `run_live` loop for the whole graph.
- `LoopAgent` and `ParallelAgent` raise `NotImplementedError` under `run_live()`. `SequentialAgent` works, through an injected `task_completed` tool.

**Guardrails** (https://adk.dev/live/guardrails/):

- Spoken input is screened on the *transcript*, after the model already heard the audio. Blocking it restarts the live session to drop the reply in flight.
- An `after_model_callback` returning an `LlmResponse` halts output and clears the turn.
- Live audio cannot pause for interactive approval. Validate privileged arguments in `before_tool_callback`, or hand off to a human.
- Keep validators fast, because they run inline with the audio loop.
- Conflict to flag: the Python quickstart says "model callbacks don't run on the streaming path". Verify against your ADK version.

**Telephony:** **LiveKit integration** (https://adk.dev/integrations/livekit/).

- `LiveKitRunner` bridges a LiveKit room (WebRTC and SIP) to the ADK runner. It handles barge-in, captions and call control, and `LiveKitToolset()` adds hang-up and transfer.
- SIP callers join as participants, and `livekit_caller_phone_number` lands in session state. Keypad digits are buffered into one turn.
- Each job runs in its own process, so use a durable session service, never `InMemoryRunner`.

### 3.5 Failure modes (voice)

1. **Talk-over after barge-in**: the client did not flush its audio buffer.
2. **Phantom interruptions**: echo or AEC failure, coughs, a TV in the background.
3. **Context desync**: the model "remembers" saying words the user never heard because playback was cut.
4. **Tool-call silence**: two inference passes plus a slow backend. Use filler speech, `WHEN_IDLE` scheduling or streaming tools.
5. **Entities over audio**: emails, phone numbers, addresses and names are the primer's top error class.
6. **Silent session death** at the 10-15 min limits without resumption or compression.
7. **Runaway cost**: no `max_llm_calls` guard on `run_live`.
8. **Wrong region**: `global` endpoint has no Live models.
9. **Sample-rate mismatch**: playing 24 kHz audio at 16 kHz gives the "chipmunk or slow-mo" bug.

---

## 4. Pattern: Video understanding pipelines

Source: **"Video understanding"**, https://ai.google.dev/gemini-api/docs/video-understanding

- **Sampling:** 1 fps by default. Custom rate through `"processing": {"fps": 0.5}`. Clipping through `start_offset` / `end_offset` (static mode).
- **Token costs:**
  - 258 tokens/frame by default, 66 at low `media_resolution`
  - about 100 tokens/s (low) to about 300 tokens/s (high), plus 32 tokens/s for audio
- **Capacity:** about 3 h of video at low resolution, or about 1 h at high, on 1M-context models.
- **Timestamps:** `MM:SS`.
- **YouTube URLs:** public videos only. Up to 10 videos per request on 2.5+. Free tier allows 8 h/day.
- **Files API:** up to 20 GB paid, 2 GB free. Use it for files over 100 MB, videos over 10 min, or reusable media.
- **Models:** examples use `gemini-3.8-flash`. "Agentic processing" is listed for 4 Argon, 3.8 Flash, 3.6 Flash and 3.5 Flash-Lite.

**Pipeline (diagram in words):** Ingest (upload to Files API / GCS) -> **Coarse pass** (low-res, 0.5-1 fps, whole video -> scene list with MM:SS) -> **Router** picks segments -> **Fine pass** (high res, clipped `start/end_offset`, higher fps) -> structured JSON (events, timestamps, entities) -> index for RAG, or hand to downstream agents. This "zoom" pattern can cut cost about 3-4x compared with a uniform high-res pass. That figure is derived from the docs' token rates: ~100 vs ~300 tokens/s.

**Live video is different.** ADK Live sends at most about 1 fps of 768x768 JPEG frames, which is fine for "what am I looking at" and fails at motion. For motion, record a clip and use the batch path.

**Failure modes:**

- Fast events falling between 1 fps samples
- Hallucinated timestamps (ask the model to quote the visual evidence)
- Inline-upload size confusion: the docs say 20 MB in prose and 100 MB in a table
- The audio track is silently ignored by the embedding model (see section 5)

---

## 5. Pattern: Multimodal RAG for agents

Source: **"Embeddings"**, https://ai.google.dev/gemini-api/docs/embeddings (page updated 2026-10-09. gemini-embedding-2 "latest update April 2026")

**`gemini-embedding-2`** maps **text, images, video, audio and PDF into one embedding space** across 100+ languages.

- **Input limit:** 8,192 tokens total. Inputs over the limit are **silently truncated**.
- **Per-modality limits:**

  | Modality | Limit |
  |---|---|
  | Images | ≤6 per request, PNG or JPEG |
  | Audio | ≤180 s, MP3 or WAV |
  | Video | ≤120 s, MP4 or MOV, ≤32 frames sampled, **audio track not processed** |
  | PDF | 1 file, ≤6 pages, 258 tokens/page, OCR always on |

- **Dimensions:** 128-3072 (default 3072; recommended 768, 1536 or 3072). Trained with Matryoshka representation learning (MRL) and auto-renormalized when truncated.
- **No `task_type` field.** Put the task in a text prefix instead: `task: search result | query: {content}` for queries, `title: {title} | text: {content}` for documents.
- **Batching gotcha:** several inputs inside one `Content` produce **one aggregated vector**. Wrap each input in its own `Content` to get separate vectors.
- **Migration:** the embedding spaces of `gemini-embedding-001` (text-only, 2,048 tokens) and v2 are incompatible, so the whole corpus must be re-embedded.

**[verbatim]**

```python
result = client.models.embed_content(
    model="gemini-embedding-2",
    contents="What is the meaning of life?",
    config=types.EmbedContentConfig(output_dimensionality=768)
)
```

**Agentic multimodal RAG (diagram in words):**

1. **Index:** chunk PDFs into 6-page windows, video into overlapping ≤120 s clips, audio into ≤180 s clips. Embed each chunk natively (no captioning step), store the vector, the media URI and the timestamps or page numbers.
2. **Query:** the agent's `retrieve` tool embeds the text query with a task prefix and pulls top-k mixed-modality hits.
3. **Read:** the agent loads the original media (an ADK artifact or GCS URI) into a Gemini call, so it reasons on pixels, not on the embedding.
4. **Answer** with citations (page number or MM:SS).
5. **Critic** checks that every claim is grounded in a retrieved item.

ADK plumbing:

- Media moves as `types.Part.from_bytes(data=..., mime_type=...)` artifacts through `tool_context.save_artifact()` / `load_artifact()`. Versions are automatic (0, 1, 2...), the `user:` prefix gives cross-session scope, and `GcsArtifactService` handles persistence (https://adk.dev/artifacts/).
- Why this design: embed natively, then **re-read the raw media at answer time**. Embeddings route; the generator verifies.

[UNVERIFIED in this pack]: late-interaction visual retrievers (ColPali-family) and their 2026 benchmark numbers were not fetched. Mention them only as an alternative design ("page-image patch embeddings") without numbers.

**Failure modes:**

- Silent truncation over 8,192 tokens
- Accidental aggregation of a batch into one vector
- Speech content inside videos is lost (no audio track). Add a separate audio or transcript embedding.
- Mixing v1 and v2 vectors in one index
- OCR cannot be disabled for scanned PDFs on the Developer API

---

## 6. Pattern: Image generation with critique loops

Source: **"Image generation (Nano Banana)"**, https://ai.google.dev/gemini-api/docs/image-generation

**Models:**

| Name | ID | Notes |
|---|---|---|
| Nano Banana 2.1 | `gemini-nano-banana-2.1` | recommended |
| Nano Banana 2 | `gemini-3.1-flash-image` | previous workhorse |
| Nano Banana 2 Lite | `gemini-3.1-flash-lite-image` | cheapest |
| Nano Banana Pro | `gemini-3-pro-image` | most complex tasks |
| Nano Banana (legacy) | `gemini-2.5-flash-image` | migrate to 2 Lite |

**Reference images:** up to **14** total.

| Model | Objects | Characters | Styles |
|---|---|---|---|
| Lite | 14 | - | - |
| 2.1 / 3.1 Flash | 10 | 4 | - |
| Pro | 6 | 5 | 3 |

**Other features:**

- **Resolution:** 1K, 2K or 4K (uppercase K). 512px only on 3.1 Flash. Lite is 1K only.
- **Thinking is always on for Gemini 3 image models.** Up to two interim images are produced, and the last one is final.
- **Grounding:** Google Search grounding (not on Lite). Image Search grounding on 2.1 and 3.1 Flash, where you must display the returned search suggestions.
- **Inputs and outputs:** video-to-image (YouTube or Files API) for posters. Interleaved text and image output on Pro (iterate over the steps).
- **SynthID watermark on every image.**
- **Multi-turn edits:** use `previous_interaction_id`. Lite is not optimized for multi-turn or multi-reference work.

**Generate -> critique -> refine (diagram in words):**

1. **Brief** (spec plus brand rules).
2. **Generator** (Nano Banana 2.1) writes the image artifact v0.
3. **Critic** (a strong vision LLM, for example `gemini-3.8-flash`) scores the image against a rubric: text legibility, brand colors, character consistency, policy. It returns JSON `{pass: bool, issues: [...]}`.
4. **Router**: if pass, go to DONE. Otherwise go to the **Editor**, which runs a multi-turn edit with `previous_interaction_id` and the critic's issues as instructions, producing artifact v(n+1). Then back to the Critic.
5. Stop at max N iterations, or escalate to a human.

**ADK 2.0 loop wiring.** The graph route syntax is from https://adk.dev/graphs/routes/. A back-edge creates the loop, and **cycles are not automatically bounded**: the docs recommend a dynamic workflow when you need an explicit bound.

```python
# [reconstructed - pattern code for the deck, not copied from a single source page]
def critic_router(verdict: dict):
    return Event(route="DONE" if verdict["pass"] else "REVISE")

root_agent = Workflow(
    name="image_studio",
    edges=[
        ("START", generator, critic, critic_router),
        (critic_router, {"REVISE": editor, "DONE": publish}),
        (editor, critic),                      # back-edge = loop; bound it yourself
    ],
)
```

The legacy equivalent is `LoopAgent(sub_agents=[critic, refiner], max_iterations=5)` with an `exit_loop` tool that sets `tool_context.actions.escalate = True`. That is verbatim from https://adk.dev/agents/workflow-agents/loop-agents/, which also notes that **graph-based workflows supersede templated workflows in ADK 2.0**. Store each version with `save_artifact("poster.png", part)` to get version history for free.

**Failure modes:**

- **Self-grading bias**: use a different model, or a rubric with checkable items such as OCR on the rendered text.
- **Edit drift**: identity or character changes across turns. Mitigate with character reference images and by limiting edits per turn.
- **Unbounded loops**
- **Cost**: thinking cannot be turned off, so each iteration is expensive.
- **Search-grounding display obligations** ignored
- **Rights**: users must own uploaded references.

---

## 7. Multimodal evals

- **ADK voice evals** (https://adk.dev/live/evaluation/):
  - An `llm_audio` user simulator, where one model writes the user's turn and a TTS model speaks it. Vary `voice_name` and `language_code` to test accents.
  - The agent runs over a real live session, and the transcript is scored.
  - Criteria: `rubric_based_final_response_quality_v1`, `rubric_based_tool_use_quality_v1`, `rubric_based_multi_turn_trajectory_quality_v1`, `tool_trajectory_avg_score`.
  - Config: `live_model_config.timeout_seconds` (default 300).
  - Run with `adk eval <agent> <live.evalset.json> --config_file_path test_config.json`, or with `AgentEvaluator` in CI. `adk web` has a Standard | Live toggle with playable audio per turn.
  - Key insight from the docs: **feeding text to a voice agent skips VAD, turn-taking, STT and TTS**, so text evals miss voice bugs.
  - The page defines **no latency metric**. Add your own mic-to-speaker p50/p95 instrumentation.
- **Primer evals guidance:** results are probabilistic ("8/10 acceptable for some, 9.99/10 for others"), simulated users are needed, and a spreadsheet plus an LLM judge is a fine start. Vendors named: Cekura, Coval, Bluejay. Top failure areas: time-to-first-speech, transcription errors, entities (emails, phones, names, addresses), interruptions.
- **Computer-use evals:** OSWorld (369 tasks, human 72.36%, OSWorld 2.0 June 2026), Online-Mind2Web, WebVoyager, AndroidWorld. Report **success rate and latency together**. Google's own chart plots accuracy against seconds per task.
- **Image-gen evals:** rubric-graded vision judge plus deterministic checks (OCR'd text matches the brief, color histogram vs palette, face or character similarity to the references) [pattern; no primary source fetched].
- **Video and RAG evals:** timestamp accuracy (within ±N s of the gold label), citation precision, and retrieval recall@k per modality [pattern].

---

## 8. Real products and case studies (verified mentions only)

- **Project Mariner, Firebase Testing Agent, AI Mode in Search** run on versions of the Gemini Computer Use model (blog.google, 2025-10-07).
- **Browserbase**: hosted demo and cloud browser backend for the CU reference implementation.
- **LensMosaic**: ADK Live visual-shopping demo. App at https://lens-mosaic-nhhfh7g7iq-uc.a.run.app, source at https://github.com/kazunori279/lens-mosaic (linked from adk.dev/live).
- **LiveKit**: WebRTC and SIP transport for ADK live agents (adk.dev/integrations/livekit).
- **Pipecat**: open-source cascaded voice framework used throughout the primer.
- Named customer metrics (for example deflection rates, % time saved) were **not found in the fetched pages** [UNVERIFIED]. Do not cite numbers for them.

**Tutorials and further reading** (titles and URLs as linked from adk.dev; no codelabs.developers.google.com page was fetched, so codelab titles are [UNVERIFIED]):

- "Build a Live Streaming Agent with Python": https://adk.dev/live/get-started/streaming-python/
- "ADK Bidi-streaming: A Visual Guide to Real-time Multimodal AI Agent Development" (Medium, Google Cloud): https://medium.com/google-cloud/adk-bidi-streaming-a-visual-guide-to-real-time-multimodal-ai-agent-development-62dd08c81399
- "Google ADK + Vertex AI Live API" (Medium, Google Cloud): https://medium.com/google-cloud/google-adk-vertex-ai-live-api-125238982d5e
- Computer use sample: https://github.com/google/adk-python/tree/main/contributing/samples/multimodal/computer_use
- Reference CU agent: https://github.com/google-gemini/computer-use-preview

---

## 9. Interview questions (crisp answers)

1. **Why does a computer-use model output 0-999 coordinates instead of pixels?** It makes the model independent of resolution. The client denormalizes with `v/1000*dim`, so the same policy works on any viewport. Bugs come from DPI or viewport mismatch between the screenshot and the executor.
2. **Who executes actions in Gemini computer use?** Your client (Playwright, Browserbase, ADB). The model only proposes function calls with an `intent` and an optional `safety_decision`. In ADK you implement `BaseComputer`.
3. **How do you handle a `require_confirmation` safety decision?** Pause, show the explanation to a human, and on approval return `safety_acknowledgement` in the `function_result`. Otherwise terminate. Disabling a safety policy only sets a preference.
4. **Cascaded or native audio: when would you pick each?** Pick cascaded when you need precise tool use, auditable transcripts, context editing or cost control (~$0.02-0.10/min). Pick native when naturalness, prosody, code-switching and simplicity matter more (~$0.20+/min).
5. **What is a realistic voice latency target, and where does the time go?** About 1.5 s voice-to-voice with no spikes. Roughly 300 ms STT plus endpointing, 650 ms LLM TTFB and 120 ms TTS TTFB, out of about 1.2-1.3 s total.
6. **What must happen on barge-in?** Server: cancel generation (the `interrupted` event). Client: flush the playback queue and stop the current source. Context: truncate the assistant turn to what was actually heard.
7. **Why run upstream and downstream as concurrent tasks in an ADK live server?** If they run sequentially, the server cannot receive user audio while streaming output, so interruption is lost (the ADK docs say exactly this).
8. **How do you keep a Live session alive past 10-15 minutes?** Use `session_resumption` to cross the ~10 min connection resets (ADK reconnects on `go_away`), plus `context_window_compression` with trigger ≈ 78% and target ≈ 62% to lift the duration cap.
9. **Why can't you use `LoopAgent` for a live critique loop?** `LoopAgent` and `ParallelAgent` raise `NotImplementedError` under `run_live()`. Use a graph `Workflow` with `mode='task'` live nodes on a single path, or run the loop offline.
10. **How do you cap the cost of a live session?** `max_llm_calls` does not apply to `run_live()`. Enforce your own token budget from `usage_metadata`, wall-clock limits, and platform session caps.
11. **What does video cost in tokens?** About 258 tokens/frame by default (66 at low resolution), or about 100-300 tokens/s plus 32 tokens/s for audio, at 1 fps by default. Use a coarse low-res pass, then clip and zoom.
12. **Give two traps in multimodal embeddings with gemini-embedding-2.** Silent truncation at 8,192 tokens, and several parts in one `Content` producing a single aggregated vector. Bonus: video audio is ignored, and v1 and v2 spaces are incompatible.
13. **How do you stop a generate-critique loop from running forever in ADK 2.0?** Graph cycles are not bounded automatically. Use a dynamic workflow with an explicit counter, or legacy `LoopAgent(max_iterations=N)` plus `exit_loop` with `escalate=True`.
14. **Why are voice evals with text input insufficient?** They skip VAD, turn-taking, STT, TTS and transcription. ADK's `llm_audio` simulator speaks the user turns through TTS over a real live session.
15. **What is prompt injection in a computer-use context, and how do you mitigate it?** Instructions hidden in rendered pages or screenshots. Mitigate with `enable_prompt_injection_detection`, a sandboxed browser profile, domain allow-lists, a confirmation gate on sensitive categories, and a `yield_to_user` tool.

---

## 10. Slide ideas (with animation)

1. **"Same loop, new senses."** Perceive -> reason -> act -> observe ring. *Animation:* the "observe" node swaps icons from text to screenshot to waveform to film strip while the ring keeps spinning.
2. **"From a dedicated model to a built-in tool."** Timeline: Oct 2025 `gemini-2.5-computer-use-preview-10-2025`, then 2026 CU in 3.5 Flash-Lite, 3.6 Flash and 3.8 Flash, then the old ID marked "Shut down". *Animation:* the old model card grays out and the stamp "SHUT DOWN" slams on.
3. **"The screenshot-action loop."** Diagram from section 2.3. *Animation:* a 0-999 grid overlays a web page, a dot denormalizes to pixel coordinates, a click ripples, a new screenshot slides in, and the loop repeats.
4. **"Safety gate per step."** Action stream passing through the allowed / require_confirmation / blocked filter. *Animation:* three cards fly toward a gate: two pass, one turns amber and waits for a human thumbs-up.
5. **"Where 1.3 seconds go."** Stacked horizontal bar of the latency table. *Animation:* segments grow left to right in real time; the STT, LLM and TTS segments pulse red as "the 83%".
6. **"Cascade vs native."** Two pipelines side by side, with a cost per minute and control-vs-naturalness slider. *Animation:* audio packets race through both pipes, then the cost meters tick up at different speeds.
7. **"Barge-in, done right."** Waveform timeline: agent speaking, user interrupts, `interrupted` event, buffer flush, transcript truncated to the words heard. *Animation:* the unheard words of the agent's sentence fade out of the context box.
8. **"ADK live architecture."** Browser -> FastAPI (upstream / downstream) -> `LiveRequestQueue` / `run_live` -> Gemini Live, with resumption handles around a 10-min connection. *Animation:* the connection snaps at 10:00 and instantly reattaches with a "resumption handle" key icon.
9. **"Zoom pipeline for video."** Coarse 1 fps low-res scan -> segment picks -> high-res clipped pass. *Animation:* a film strip blurs, then a magnifier zooms into 02:14-02:40 and the frames sharpen.
10. **"Generate -> Critique -> Refine."** ADK 2.0 graph with a back-edge, plus artifact versions v0, v1, v2. *Animation:* the poster improves at each loop, a rubric checklist ticks green, and the loop exits at DONE (with a max-N guard drawn as a fuse).

---

## Source index (all fetched 2026-10-23)

- Gemini models: https://ai.google.dev/gemini-api/docs/models
- Computer use (Gemini API): https://ai.google.dev/gemini-api/docs/computer-use
- Blog, "Introducing the Gemini 2.5 Computer Use model" (2025-10-07): https://blog.google/technology/google-deepmind/gemini-computer-use-model/
- ADK Computer Use integration: https://adk.dev/integrations/computer-use/
- ADK CU sample: https://github.com/google/adk-python/tree/main/contributing/samples/multimodal/computer_use
- Reference CU repo: https://github.com/google-gemini/computer-use-preview
- Live API guide: https://ai.google.dev/gemini-api/docs/live-guide
- ADK Live pages:
  - Overview: https://adk.dev/live/
  - Audio and video: https://adk.dev/live/audio-video/
  - Supported models: https://adk.dev/live/models/
  - Events: https://adk.dev/live/events/
  - Sessions: https://adk.dev/live/sessions/
  - Configuration: https://adk.dev/live/configuration/
  - Tools: https://adk.dev/live/tools/
  - Workflows: https://adk.dev/live/workflows/
  - Guardrails: https://adk.dev/live/guardrails/
  - Evaluation: https://adk.dev/live/evaluation/
  - Custom server: https://adk.dev/live/custom-server/
  - Python quickstart: https://adk.dev/live/get-started/streaming-python/
- LiveKit integration: https://adk.dev/integrations/livekit/
- Graph routes: https://adk.dev/graphs/routes/
- LoopAgent: https://adk.dev/agents/workflow-agents/loop-agents/
- Artifacts: https://adk.dev/artifacts/
- Video understanding: https://ai.google.dev/gemini-api/docs/video-understanding
- Image generation: https://ai.google.dev/gemini-api/docs/image-generation
- Embeddings: https://ai.google.dev/gemini-api/docs/embeddings
- "Voice AI & Voice Agents: An Illustrated Primer" (K. Hultman Kramer, June 2026 update): https://voiceaiandvoiceagents.com/
- OSWorld: http://osworld-v1.xlang.ai/
- Not retrievable: OpenAI "Introducing gpt-realtime" (HTTP 403). No OpenAI claims are included.
