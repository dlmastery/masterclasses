# 09 - Multimodal Handling in ADK 2.0 and Gemini (state as of 2026-10-23)

> Research brief for a university deck. Sources are primary: adk.dev (the ADK docs, which moved from google.github.io/adk-docs and now 301-redirect there), ai.google.dev (Gemini API), the github.com/google/adk-python source and samples, and Google Codelabs. Everything was fetched on 2026-10-23. Anything I could not confirm is marked **[UNVERIFIED]**.
> **Method caveat:** The session's web-search budget ran out before this task began. All facts below come from direct fetches of known primary URLs, and nothing comes from search-engine discovery. Some codelabs or blog posts from 2026 may therefore be missing.

---

## 0. The landscape changed a lot in 2026. Read this first.

The model names in many 2025 tutorials are now out of date. The Gemini API models page (https://ai.google.dev/gemini-api/docs/models, fetched 2026-10-23) lists the following:

- **Flagship:** `gemini-4-argon`, Stable, 1M-token context.
- **Current Flash:** `gemini-3.8-flash`, Stable. `gemini-3.6-flash` and `gemini-3.5-flash-lite` are Stable. `gemini-3.1-pro-preview` and `gemini-3-flash-preview` are still listed.
- **Live (voice):** `gemini-3.8-live` and `gemini-3.8-live-extended-thinking` are Stable. `gemini-3.1-flash-live-preview` is now "legacy preview". `gemini-2.5-flash-native-audio-preview-12-2025` is "limited access".
- **Image ("Nano Banana" family):**
  - `gemini-nano-banana-2.1`: Stable, and the recommended default.
  - `gemini-3.1-flash-image`: Nano Banana 2.
  - `gemini-3.1-flash-lite-image`: Nano Banana 2 Lite.
  - `gemini-3-pro-image`: Nano Banana Pro, up to 4K.
  - `gemini-2.5-flash-image`: the original Nano Banana, now "limited access / legacy".
- **Video:** `gemini-omni-1.1-flash` (Gemini Omni Flash). On the Gemini API, **Veo 3.1 (`veo-3.1-generate-preview`, `-fast-`, `-lite-`) was "shut down on October 22, 2026"** (https://ai.google.dev/gemini-api/docs/video).
- **Imagen:** `imagen-4.0-generate` is listed as **shut down**.
- **Embeddings:** `gemini-embedding-2-preview` is multimodal and accepts text, images, video, audio and PDF.
- **API surface:** The Gemini docs now default to the **Interactions API** (`client.interactions.create(...)`, `previous_interaction_id`). ADK still builds on `google.genai.types` (`Content`, `Part`, `Blob`, `FileData`). ADK can opt into Interactions with `Gemini(model=..., use_interactions_api=True)`, which has been supported since ADK Python v1.21.0 (https://adk.dev/agents/models/google-gemini/).

Not everything moved at the same pace. On the ADK side, the Live docs (https://adk.dev/live/models/) still list only two Live models: **`gemini-live-2.5-flash-native-audio`**, which is GA on "Agent Platform" (the renamed Vertex AI, now "Gemini Enterprise Agent Platform") and is `LlmAgent.DEFAULT_LIVE_MODEL`, and **`gemini-3.1-flash-live-preview`**, AI Studio preview only. The ADK docs lag the Gemini model catalog, so put that on a slide: always read the model ID from an environment variable.

**ADK 2.0 GA dates** (https://adk.dev/2.0/): Python on **2026-05-19**, Go on **2026-06-30**, TypeScript on **2026-08-21**. Java has no 2.0 release. The headline feature of 2.0 is the graph-based workflow engine. The 2.0 page lists no multimodal or live API changes. Those arrived in the 2.x point releases (see section 9).

---

## 1. The core primitive: `types.Part`

Every modality in ADK is a `google.genai.types.Part` inside a `types.Content(role=..., parts=[...])`. A Part carries exactly one payload kind:

| Payload | Field | When to use |
|---|---|---|
| Text | `Part(text=...)` | Prompts, transcripts |
| Raw bytes | `Part(inline_data=Blob(data=..., mime_type=...))` or `Part.from_bytes(data=, mime_type=)` | Small media, under the request limit |
| Reference | `Part(file_data=FileData(file_uri=..., mime_type=...))` or `Part.from_uri(file_uri=..., mime_type=...)` | Files API URIs, `gs://` (Vertex/Agent Platform), HTTPS, YouTube |
| Function call or response | `function_call` / `function_response` | Tools. Function responses can also carry images on Gemini 3 and later. |
| Thought | `thought=True` + `thought_signature` | Reasoning state. It must be round-tripped in stateless mode. |

The ADK artifacts doc states that these two lines are equivalent (https://adk.dev/artifacts/):

```python
pdf_artifact_alt_py = types.Part.from_bytes(data=pdf_bytes, mime_type=pdf_mime_type)
# == types.Part(inline_data=types.Blob(data=pdf_bytes, mime_type=pdf_mime_type))
```

Sample code from adk-python, `contributing/samples/multimodal/static_non_text_content/agent.py`, shows inline data with a display name. A `display_name` is what `SaveFilesAsArtifactsPlugin` uses as the artifact filename.

```python
types.Part(
    inline_data=types.Blob(
        data=SAMPLE_IMAGE_DATA,
        mime_type="image/png",
        display_name="sample_chart.png",
    )
),
```

The same sample's Vertex branch references PDFs by URI rather than inlining them: `"gs://cloud-samples-data/generative-ai/pdf/2507.06261.pdf"` and `file_uri="https://storage.googleapis.com/cloud-samples-data/generative-ai/pdf/2403.05530.pdf"`. It also places them in a **`static_instruction`** (`Agent(static_instruction=create_static_instruction_with_file_upload(), ...)`). Static content stays constant across turns and is therefore cacheable, so it is the right place for reference documents.

Sending a multimodal user turn into `runner.run_async`:

```python
# [illustrative, assembled from documented google.genai types; not a verbatim doc sample]
msg = types.Content(role="user", parts=[
    types.Part.from_bytes(data=open("receipt.jpg","rb").read(), mime_type="image/jpeg"),
    types.Part(text="Extract merchant, date, total as JSON."),
])
async for event in runner.run_async(user_id=uid, session_id=sid, new_message=msg):
    ...
```

### Inline data vs the Files API (Gemini Developer API)

From https://ai.google.dev/gemini-api/docs/files:

- **Size and storage:** files can be up to **2 GB** each, with **20 GB per project**.
- **Retention:** files are kept for **48 hours** and then deleted automatically.
- **Cost:** the Files API is **free**.
- **When to switch:** use the Files API "when the total request size ... is larger than **100 MB**". The threshold for PDFs is **50 MB**.

Older modality pages still say **20 MB** for inline requests (image-understanding, audio, and the video page). The video page itself shows both "<100MB" and "<20MB". **Teach this rule: inline under 20 MB is always safe. Above that, or whenever a file is reused, upload it.**

Upload code from the Files doc. The docs now use the Interactions API, and the snippet is verbatim:

```python
from google import genai
client = genai.Client()
myfile = client.files.upload(file="path/to/sample.mp3")
interaction = client.interactions.create(
    model="gemini-3.8-flash",
    input=[
        {"type": "text", "text": "Describe this audio clip"},
        {"type": "audio", "uri": myfile.uri, "mime_type": myfile.mime_type}
    ]
)
print(interaction.output_text)
```

In ADK, you would wrap that URI as `types.Part.from_uri(file_uri=myfile.uri, mime_type=myfile.mime_type)`. **[UNVERIFIED: no ADK doc page shows this exact Files-API-in-ADK line. It follows from the genai types API.]**

On Vertex / Agent Platform there is no Files API. Use `gs://` URIs that the service account can read. ADK's `SaveFilesAsArtifactsPlugin` only attaches `file_data` for schemes `{"gs", "https", "http"}` (source: `src/google/adk/plugins/save_files_as_artifacts_plugin.py`).

---

## 2. Per-modality limits and token costs

### Media resolution for Gemini 3 and Gemini 4

Source: https://ai.google.dev/gemini-api/docs/media-resolution

| Level | Image | Video / frame | Audio | PDF |
|---|---|---|---|---|
| unspecified (default) | 1120 | 70 | 25 tok/s | 560 |
| low | 280 | 70 | 25 tok/s | 280 + native text |
| medium | 560 | 70 | 25 tok/s | 560 + native text |
| high | 1120 | 280 | 25 tok/s | 1120 + native text |
| ultra_high (per-item only) | 2240 | n/a | n/a | n/a |

- **Recommended settings:** images on `high`, PDFs on `medium` (quality "typically saturates" there), and video on `low` or `medium`, both of which cost 70 tokens per frame. Use `high` for OCR or fine detail.
- **Per-item resolution:** you can set resolution per item and mix levels in one request: `{"type": "image", "uri": ..., "mime_type": ..., "resolution": "high"}`.

### Legacy (Gemini 2.x-era) per-modality pages, still live

- **Images** (https://ai.google.dev/gemini-api/docs/image-understanding):
  - Up to **3,600 images** per request.
  - An image of 384 px or less on both sides costs **258 tokens**. Larger images are tiled into 768x768 tiles at 258 tokens each. The crop unit is `floor(min(w,h)/1.5)`, so a 960x540 image becomes 6 tiles.
  - Supported MIME types: png, jpeg, webp, heic, heif.
  - Detection output is `box_2d` = `[ymin, xmin, ymax, xmax]`, normalized to **0-1000**.
  - Segmentation returns polygons, also normalized to 0-1000. The Gemini 3 guide says segmentation is **not supported on Gemini 3 Pro/Flash**, so use 2.5 Flash for it.
- **Video** (https://ai.google.dev/gemini-api/docs/video-understanding):
  - Sampling is 1 fps by default. Set a custom rate with `"fps": 0.5`, and clip with `start_offset` / `end_offset`.
  - Cost is about **100 tok/s** at default/low resolution (66 tokens per frame plus 32 tokens per second of audio) and about **300 tok/s** at high resolution.
  - A 1M-token context holds about **3 hours** of video at low resolution and **1 hour** at high.
  - YouTube URLs are supported (public videos only). The free tier allows 8 hours of YouTube per day.
  - Gemini 2.5 and later accept up to 10 videos per request. Timestamps use `MM:SS`.
- **Audio** (https://ai.google.dev/gemini-api/docs/audio):
  - **32 tokens/s** (1 minute = 1,920 tokens).
  - Up to **9.5 hours** per prompt.
  - Audio is downsampled to 16 Kbps and mixed to mono.
  - Formats: wav, mp3, aiff, aac, ogg, flac, mpeg, m4a, l16, opus, alaw, mulaw, webm.
  - The media-resolution page says 25 tok/s for Gemini 3 and 4. The difference between the two pages is a good exam question.
- **PDF** (https://ai.google.dev/gemini-api/docs/document-processing):
  - Limit: **50 MB or 1,000 pages**.
  - Cost: **258 tokens per page** on the legacy page. On Gemini 3 and later it depends on media resolution, 280 to 1120 tokens.
  - Pages larger than 3072x3072 are scaled down and pages smaller than 768x768 are scaled up.
  - Non-PDF documents (TXT, MD, HTML, XML) are read **as plain text only**, so charts and layout are lost. Only PDFs get visual understanding.
  - The single-page tip: put the prompt **after** the page.

### Gemini 3 notes

Source: https://ai.google.dev/gemini-api/docs/gemini-3. The page is now marked deprecated in favor of a "What's new in Gemini 3.8 Flash" guide.

- **Defaults changed:** default PDF token use may **increase** after migration, and video use may **decrease**.
- **Tuning:** try `media_resolution_high` for dense PDFs, and lower the resolution if you hit context limits.
- **Images:** Gemini 3 Flash can zoom, crop and annotate images via code execution.
- **Function responses can include images.** This is what multimodal tool results depend on.
- **`thinking_level`:** values are minimal, low, medium and high, with high as the default. Do not combine it with `thinking_budget`, or the request fails with a 400 error.
- **Temperature:** keep it at **1.0**. Lower values may cause looping.
- **Thought signatures:** they must be returned in stateless mode. Multi-turn image editing depends on them.

---

## 3. Artifacts: the binary-data layer of ADK

**Concept:** an artifact is a named, versioned `types.Part` (bytes plus MIME type) scoped to a session or a user. It keeps large blobs **out of the prompt history and out of session state**.

**Flow for a diagram:**

1. A tool or callback calls `context.save_artifact(filename, part)`.
2. The ArtifactService stores the Part (in memory or in GCS) and returns a version number (int, starting at 0).
3. The event's `actions.artifact_delta` records `{filename: version}`.
4. Later, `load_artifact(filename[, version])` returns the Part, or `None` if it does not exist.

Verbatim API from https://adk.dev/artifacts/:

```python
version = await context.save_artifact(filename=filename, artifact=report_artifact)
report_artifact = await context.load_artifact(filename=filename)
specific_version_artifact = await context.load_artifact(filename=filename, version=0)
available_files = await tool_context.list_artifacts()
```

**Scoping:**

- `"summary.txt"` is session-scoped.
- `"user:settings.json"` is user-scoped and shared across all of that user's sessions.
- The Go docs comment that namespacing is supported only with GCS. That conflicts with the Python docs, so verify it per SDK.

**Services** (verbatim):

```python
from google.adk.artifacts import InMemoryArtifactService
in_memory_service_py = InMemoryArtifactService()

from google.adk.artifacts import GcsArtifactService
gcs_service_py = GcsArtifactService(bucket_name="your-gcs-bucket-for-adk-artifacts")
# runner = Runner(..., artifact_service=gcs_service_py)
```

**How GCS stores artifacts:** each version is a separate object. Deletion is **not** exposed on the context, so use `artifact_service.delete_artifact` or bucket lifecycle rules. Since v2.9.0, `GcsArtifactService` has `get_authenticated_url` and `get_signed_url`, and concurrent saves get distinct versions (adk-python release notes).

**Getting artifacts into the model:**

- `load_artifacts` / `LoadArtifactsTool`: lists artifact names in the instruction. When the model asks for one, the tool **temporarily appends** the content to that LLM request. The content is not written back to history, so the model must reload it in later turns, which is a cost win.
- `LoadArtifactsTool(enable_spreadsheet_parsing=True)` parses xlsx/xls files, up to the first 100 rows per sheet.
- **`SaveFilesAsArtifactsPlugin`** (source: `src/google/adk/plugins/save_files_as_artifacts_plugin.py`):
  - It works in `on_user_message_callback` and replaces each user-uploaded `inline_data` Part with an artifact plus the placeholder `[Uploaded Artifact: "{display_name}"]`.
  - Files over **20 MB** are replaced with an error text part.
  - With `attach_file_reference`, it also adds a `file_data` Part, but only for gs, http or https canonical URIs.
  - It replaces the deprecated `RunConfig.save_input_blobs_as_artifacts`.

**Best practices** from the docs:

- Always set an accurate IANA `mime_type`. The MIME type decides how a file is handled, not the file extension.
- Use the `user:` prefix only for data that belongs to the user across sessions.
- Check for a `None` return.
- Expect a `ValueError` when no artifact_service is configured.
- Watch artifact size, because `InMemoryArtifactService` holds everything in RAM.

### Real sample: image generation tool + artifact

Source: adk-python `contributing/samples/multimodal/generate_image/agent.py`, verbatim and trimmed:

```python
from google.adk import Agent
from google.adk.tools import load_artifacts
from google.adk.tools.tool_context import ToolContext
from google.genai import types

async def generate_image(prompt: str, tool_context: 'ToolContext'):
  """Generates an image based on the prompt."""
  from google.genai import Client
  # Only Vertex AI supports image generation for now.
  client = Client()
  response = client.models.generate_images(
      model='imagen-3.0-generate-002',
      prompt=prompt,
      config={'number_of_images': 1},
  )
  if not response.generated_images:
    return {'status': 'failed'}
  image_bytes = response.generated_images[0].image.image_bytes
  await tool_context.save_artifact(
      'image.png',
      types.Part.from_bytes(data=image_bytes, mime_type='image/png'),
  )
  return {'status': 'success',
          'detail': 'Image generated successfully and stored in artifacts.',
          'filename': 'image.png'}

root_agent = Agent(name='root_agent',
    description="""An agent that generates images and answer questions about the images.""",
    instruction="""You are an agent whose job is to generate or edit an image based on the user's prompt.
""",
    tools=[generate_image, load_artifacts])
```

**Teaching point:** the tool returns a small JSON pointer (`filename`), not the bytes. The model reasons over the pointer. The UI (`adk web`) renders the artifact. **Caveat:** the sample still uses the 2024-era `imagen-3.0-generate-002`. The Gemini API now lists Imagen 4 as shut down, so swap in a Nano Banana model in class demos.

The sibling sample `multimodal/multimodal/agent.py` is the minimal "model is the tool" pattern. It is verbatim:

```python
from google.adk import Agent
root_agent = Agent(name='multimodal_agent', model='gemini-2.5-flash-image')
```

---

## 4. Multimodal tool results

Tools can return `types.Part` objects directly. The sample `contributing/samples/multimodal/multimodal_tool_results/agent.py` (verbatim, trimmed):

```python
from google.adk.agents import LlmAgent
from google.adk.apps.app import App
from google.adk.plugins.multimodal_tool_results_plugin import MultimodalToolResultsPlugin
from google.genai import types

def get_image():
  return [types.Part.from_uri(file_uri="gs://replace_with_your_image_uri")]

root_agent = LlmAgent(name="image_describing_agent", description="image describing agent",
    instruction="""Whatever the user says, get the image using the get_image tool, and describe it.""",
    tools=[get_image])

app = App(name="multimodal_tool_results", root_agent=root_agent,
          plugins=[MultimodalToolResultsPlugin()])
```

**How the plugin works** (source: `src/google/adk/plugins/multimodal_tool_results_plugin.py`):

- `after_tool_callback` stashes the returned Parts under `temp:PARTS_RETURNED_BY_TOOLS_ID`.
- `before_model_callback` appends them to the last content (`last_content.parts += temp_parts`) and then clears the state.
- Parts that the framework already carries in the `function_response` (media on models that support multimodal function responses) are dropped, so bytes are never sent twice.
- `retention: Literal["next_model_call", "session"] = "next_model_call"`. Opt-in session retention was added in v2.8.0. In `"session"` mode the parts are re-attached on later turns, **except `inline_data`**, which applies only to the turn in which it was returned.

**Flow for a diagram:**

1. The model emits function_call `get_image`.
2. The tool returns `[Part(file_data gs://...)]`.
3. `after_tool_callback` writes the Parts to temp state.
4. On the next LLM request, `before_model_callback` appends the Parts.
5. The model "sees" the image and describes it.

---

## 5. Image, video and audio generation inside agents

There are three integration patterns, from simplest to most controlled:

1. **The model is the agent.** `Agent(model='gemini-...-image')` (sample above). The agent's replies contain image Parts. This is simple, but you cannot use tools freely, and the outputs land in events rather than artifacts.
2. **A tool that calls a generation model and saves an artifact** (the `generate_image` sample). This pattern is best for production: you can version the outputs, a text-only reasoning model orchestrates, and you get a cost and safety checkpoint inside the tool.
3. **A sub-agent or AgentTool wrapping an image model.** A text planner calls an "illustrator" agent. **[UNVERIFIED: no official sample fetched for this exact pattern. It is a composition of documented AgentTool + model.]**

**Nano Banana facts** (https://ai.google.dev/gemini-api/docs/image-generation):

- **Modes:** text-to-image, text+image-to-image edit, and multi-turn editing via `previous_interaction_id`.
- **Output sizes:** **1K, 2K and 4K** (an uppercase "K" is required). 3.1 Flash Image also supports 512 px. Flash Lite supports 1K only.
- **Reference images:** up to **14** in total. Object images: 14 on Lite, 10 on 2.1 and 3.1 Flash, 6 on Pro. Character images: 4 on Lite, 5 on 2.1 and 3.1 Flash, none on Pro. Style images: 3, Pro only.
- **Grounding:** Google Search grounding is available on all models except Lite. Image Search grounding works on 2.1 and 3.1 Flash only.
- **Video-to-image:** supported on 2.1, 3.1 Flash and Lite.
- **Thinking:** Gemini 3 image models always think and can produce up to 2 interim images. Default thinking level is `medium` on 2.1 and `minimal` on 3.1 Flash.
- **Watermark:** every output carries **SynthID**.
- **Interleaved text and images:** `gemini-3-pro-image` can interleave them, so iterate `steps` rather than reading `output_image`.

**Codelab pattern:** "Way Back Home - Level 0: Identify Yourself" (https://codelabs.developers.google.com/way-back-home-level-0/instructions) uses `gemini-2.5-flash-image` through `client.chats.create()` with `response_modalities=["TEXT","IMAGE"]`. Generating the icon in the **same chat** keeps the character consistent with the portrait. A user photo is sent with `types.Part.from_bytes(..., mime_type="image/jpeg")`, and outputs are read from `part.inline_data`.

**Video** (https://ai.google.dev/gemini-api/docs/omni): **Gemini Omni Flash, `gemini-omni-1.1-flash`**, replaces Veo 3.1 on the Gemini API.

- **Inputs:** text-to-video with generated audio, image-to-video, first-and-last-frame interpolation, and subject references.
- **Editing:** stateful multi-turn editing, plus editing of uploaded videos of 10 s or less.
- **Extension:** extend by 3-10 s per step, up to 40 s in total.
- **Output:** 360p and 720p (the default), with 1080p and 4K upscaled. Aspect ratio 16:9 or 9:16.
- **Not supported:** system instructions, temperature, negative-prompt parameters and YouTube sources.
- **Watermark:** SynthID.
- **`store`:** setting `store=false` disables later edits.

Minimal code, condensed from the docs:

```python
interaction = client.interactions.create(model="gemini-omni-1.1-flash",
    input="A marble rolling fast on a chain reaction style track, continuous smooth shot.")
open("marble.mp4","wb").write(base64.b64decode(interaction.output_video.data))
```

In an ADK tool, save that video as an artifact with `mime_type="video/mp4"`. Video is the case where an artifact (GCS plus a signed URL) matters most, because an MP4 is far too large to sit in history. Note that the Veo shutdown applies to the **Gemini API** page. The Omni page links to Veo 3.1 docs on Agent Platform, so **Veo may remain on Agent Platform [UNVERIFIED]**.

**Audio and TTS:** `gemini-3.8-flash-tts` and `-lite-tts` are Stable, and Lyria 3.5 handles music. These are exposed the same way, as a tool plus a `audio/*` artifact.

---

## 6. Bidi streaming: voice and video agents with the Live API

**Mental model** (https://adk.dev/live/): an open, two-way connection in which the user can **interrupt** (barge in). `runner.run_live()` and `LiveRequestQueue` sit on top of the Gemini Live API. Of the streaming types, only bidi supports interruption. `StreamingMode.SSE` gives token streaming for `run_async`.

**Architecture flow** (draw as two lanes):

```
Browser mic(16kHz PCM)/cam(JPEG ~1fps) --WebSocket--> FastAPI
  upstream_task:  ws.receive -> live_request_queue.send_realtime(Blob)/send_content(Content)
  ADK Runner.run_live(user_id, session_id, live_request_queue, run_config)
      <-> Gemini Live API WebSocket (~10 min per connection; transparent resumption)
  downstream_task: async for event in run_live -> ws.send_text(event.model_dump_json(...))
Browser <- audio/pcm;rate=24000 chunks + transcriptions + interrupted/turn_complete
finally: live_request_queue.close()
```

**Lifecycle** (https://adk.dev/live/sessions/):

- **Once per process:** create the Agent, the SessionService and the Runner.
- **Once per session:** create the Session, a RunConfig and a **fresh** LiveRequestQueue.
- The session must already exist, or `run_live` raises "ValueError: Session not found".

**LiveRequestQueue API:**

- `send_content(content)`: sends a text turn and triggers a response. Send one text Part per call, because multi-part content may be treated as history seeding.
- `send_realtime(blob)`: streams audio, image or video bytes.
- `send_activity_start()` / `send_activity_end()`: manual turn boundaries, used only when VAD is disabled.
- `close()`: ends the session.

The send methods are synchronous and never block. The queue is FIFO and **unbounded**, so you must rate-limit high-rate media yourself.

**Custom server excerpts** (verbatim fragments from https://adk.dev/live/custom-server/):

```python
session_service = InMemorySessionService()
runner = Runner(app_name=APP_NAME, agent=agent, session_service=session_service)

run_config = RunConfig(
    response_modalities=response_modalities,
    input_audio_transcription=types.AudioTranscriptionConfig(),
    output_audio_transcription=types.AudioTranscriptionConfig(),
    session_resumption=types.SessionResumptionConfig()
)
live_request_queue = LiveRequestQueue()

# upstream
data: str = await websocket.receive_text()
content = types.Content(parts=[types.Part(text=data)])
live_request_queue.send_content(content)

# downstream
async for event in runner.run_live(
    user_id=user_id,
    session_id=session_id,
    live_request_queue=live_request_queue,
    run_config=run_config
):
    await websocket.send_text(
        event.model_dump_json(exclude_none=True, by_alias=True)
    )

# lifecycle
finally:
    live_request_queue.close()  # Always close, even on error.
await asyncio.gather(upstream_task(), downstream_task(), return_exceptions=True)
```

**Audio and video formats** (https://adk.dev/live/audio-video/):

- **Input audio:** 16-bit signed little-endian PCM, **16 kHz mono**, `audio/pcm;rate=16000`. ADK passes the bytes straight through and does no transcoding.
- **Chunk size:** 50-100 ms is recommended. 100 ms equals 3,200 bytes. Send continuously and do not wait for responses.
- **Output audio:** PCM at **24 kHz** mono, `audio/pcm;rate=24000`, delivered in `inline_data` parts and ready to play.
- **Video:** **JPEG frames, about 1 fps maximum, 768x768 recommended.** "There is no video codec: a video stream is a sequence of still frames."

```python
live_request_queue.send_realtime(types.Blob(mime_type="audio/pcm;rate=16000", data=audio_data))
# frames: types.Blob(mime_type="image/jpeg", data=jpeg_bytes)
```

**Events** (https://adk.dev/live/events/): the fields are `partial`, `turn_complete`, `interrupted`, `input_transcription`, `output_transcription` and `usage_metadata`. If you do not handle `interrupted`, the buffered audio keeps playing over the user. Transcripts arrive in fragments, so concatenate them. On 3.1 Live, a single event can carry several parts, so iterate over `event.content.parts` instead of reading `parts[0]`.

**RunConfig for live** (https://adk.dev/live/configuration/ and `src/google/adk/agents/run_config.py`):

- **Modalities:** `response_modalities=["AUDIO"]` is required, because Live models are **audio-only out**. Text comes from transcription.
- **Voice:** `speech_config=types.SpeechConfig(... prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Kore"))`.
- **Resumption and compression:** `session_resumption=types.SessionResumptionConfig()` and `context_window_compression=types.ContextWindowCompressionConfig(...)`.
- **Manual turn-taking:** `realtime_input_config=...AutomaticActivityDetection(disabled=True)`.
- **2.5-only features:** `proactivity=types.ProactivityConfig(proactive_audio=True)` and `enable_affective_dialog=True`. Neither is supported on 3.1 Live.
- **Transcription:** both transcription configs are on by default.
- **Saving audio:** `save_live_blob=True` persists audio at about **1.92 MB per minute per session**.
- **No cost ceiling:** **`max_llm_calls` (default 500) does NOT apply to `run_live()`**.
- **No-op setting:** in Python, `streaming_mode=StreamingMode.BIDI` "has no effect and fails silently".
- **Newer fields:** `avatar_config` (VIDEO sessions now default to a prebuilt avatar, since v2.11.0), `translation_config`, `explicit_vad_signal`, `history_config`, and `service_tier` (DEFERRED is not allowed with SSE).

**Limits** (https://ai.google.dev/gemini-api/docs/live-session):

- Without compression, **audio-only sessions last 15 minutes and audio+video sessions 2 minutes**.
- A connection lasts about **10 minutes**, and the server sends a `GoAway` with `timeLeft` before it closes.
- Resumption handles stay valid for **2 hours**.
- In ADK, enabling resumption caches handles and reconnects transparently, with **up to 5 consecutive retries**. Without resumption, the first drop propagates out of `run_live()`.
- Compression with `SlidingWindow` removes the duration limits. Trigger it at about 70-80% of the window and target about 60-70%.

**Live tools** (https://adk.dev/live/tools/):

- An **async-generator tool** (`AsyncGenerator[T, None]`) is non-blocking automatically. Add an `input_stream: LiveRequestQueue` parameter so it can watch video frames.
- `stop_streaming` is a reserved tool name that ADK intercepts, so the user can cancel a stream.
- `response_scheduling` takes `WHEN_IDLE`, `INTERRUPT` or `SILENT` (ADK Python 2.4 and later, 2.5 Live only). On 3.1, function calling is synchronous.

```python
async def query_sales_database(region: str) -> AsyncGenerator[str, None]:
    yield "Connecting to the warehouse..."
    await asyncio.sleep(4)
    yield "Aggregating by product line..."
```

**Production notes:**

- Use `DatabaseSessionService` or `VertexAiSessionService`, not in-memory.
- What persists: final transcriptions, usage metadata and function calls. What is ephemeral: raw audio and partial transcripts.
- Every user needs their own Live session, and concurrency is quota-capped. Count active sessions yourself, because a quota rejection surfaces as a connection failure.
- Telephony and WebRTC run through the LiveKit runner (v2.9.0).
- `CascadeLive` (v2.12/2.13) is a cascaded STT, LLM and TTS pipeline with barge-in, for models without native audio.
- Live models are not available at `GOOGLE_CLOUD_LOCATION=global`, so use a regional endpoint.

---

## 7. Codelabs (verified titles + URLs)

- **"Way Back Home - Building an ADK Bi-Directional Streaming Agent"**: https://codelabs.developers.google.com/way-back-home-level-3/instructions
  - Builds a React app that sends webcam frames (2 FPS JPEG) and mic audio over a WebSocket to FastAPI and ADK. The Live agent calls the `report_digit` tool when it sees a finger count of 1-5. Deployed on Cloud Run.
  - `MODEL_ID = os.getenv("MODEL_ID", "gemini-live-2.5-flash-native-audio")`.
  - Its RunConfig still sets `streaming_mode=StreamingMode.BIDI`, which the current docs say is a silent no-op in Python. That makes a nice "docs drift" teaching moment.
- **"Way Back Home - Live Bidirectional Multi-Agent system"** (Level 4, "Mission Bravo"): https://codelabs.developers.google.com/way-back-home-level-4/instructions
  - A Dispatch Live agent (native audio) works with an Architect agent over **A2A** (`RemoteA2aAgent` plus `AgentTool`), backed by Redis on Memorystore.
  - The `monitor_for_hazard` streaming tool watches the video and yields alerts.
  - The RunConfig enables proactivity.
- **"Way Back Home - Level 0: Identify Yourself"**: https://codelabs.developers.google.com/way-back-home-level-0/instructions. Nano Banana avatar generation with multi-turn chat consistency.
- **ADK docs tutorial "Build a streaming agent"**: https://adk.dev/live/get-started/streaming-python/ (`pip install google-adk`, `adk web`, google_search tool, and a `.env` with `GOOGLE_GENAI_USE_ENTERPRISE`).
- **Samples:**
  - https://github.com/google/adk-python/tree/main/contributing/samples/multimodal, with subfolders `computer_use`, `generate_image`, `multimodal`, `multimodal_tool_results` and `static_non_text_content`.
  - A sibling `contributing/samples/live` directory.
  - The former `adk-samples/python/agents/bidi-demo` URL now returns 404. **[UNVERIFIED: new location]**

---

## 8. Failure modes (and fixes)

1. **Request too large or a 400 on media.** Inline bytes exceed about 20 MB, or the request exceeds 100 MB. Fix: use the Files API (48 h retention, so re-upload long-lived files) or `gs://`.
2. **Context blow-up from re-sent media.** Bytes stored in session history are resent every turn. Fix: use artifacts with `load_artifacts`, which attaches them to one request only, plus `SaveFilesAsArtifactsPlugin` and the `next_model_call` retention mode.
3. **Wrong MIME type.** The model or UI misreads the bytes. The MIME type, not the extension, decides handling.
4. **Expired Files API URIs** in persisted sessions after 48 h. Persist artifacts in GCS and re-upload on demand.
5. **`None` from `load_artifact`, or a `ValueError`** because no artifact_service is configured on the Runner.
6. **Live audio sounds like chipmunks or noise.** The sample rate or format is wrong: input must be 16 kHz and output is 24 kHz, both 16-bit little-endian PCM. ADK does not transcode.
7. **Audio plays over the user.** The `interrupted` event is not handled. Flush the player buffer.
8. **Audio+video sessions die at 2 minutes and audio at 15 minutes.** Fix: enable context_window_compression. **Silent drops at about 10 minutes**: enable session_resumption.
9. **Zombie sessions consume quota.** `close()` was not called in a `finally` block.
10. **Runaway live cost.** `max_llm_calls` does not cap `run_live`, so add your own budgets or timers. The unbounded queue can also flood the model if you send too many video frames; keep to about 1 fps or less.
11. **Expecting TEXT from a Live model.** Live models are audio-only, so use transcription.
12. **Upgrading 2.5 to 3.1 Live breaks things.** Remove proactivity and affective dialog, `response_scheduling` is ignored, change `thinking_budget` to `thinking_level`, and iterate over all parts.
13. **Retired models in tutorials.** Imagen 3/4 and Veo 3.1 are shut down on the Gemini API, and `gemini-2.0-flash` is shut down. Read model IDs from env vars.
14. **Gemini 3 cost surprises.** PDF tokens rise under the new media resolution defaults, and `ultra_high` doubles image tokens. Set resolution per item.
15. **Segmentation requests on Gemini 3 Pro/Flash.** They are not supported, so route those to 2.5 Flash.
16. **Interactions API plus mixed tools.** You cannot combine custom function tools with built-ins. Use `GoogleSearchTool(bypass_multi_tools_limit=True)`.

---

## 9. ADK Python 2.x release notes with multimodal relevance

Source: https://github.com/google/adk-python/releases

| Version | Date (2026) | Multimodal / live / artifact change |
|---|---|---|
| v2.13.0 | Oct 23 | CascadeLive barge-in plus Gemini STT/TTS; helpers to pack and unpack visual frames |
| v2.12.0 | Oct 13 | Skill-script outputs persisted as artifacts; CascadeLive model and sample; InMemoryArtifactService isolated from caller mutation |
| v2.11.0 | Oct 2 | VIDEO live sessions default to a prebuilt avatar; `--avatar_config` |
| v2.10.0 | Sep 25 | Deferred service tier on Interactions; legacy live-audio modules deprecated in favor of `google.adk.live` |
| v2.9.0 | Sep 10 | LiveKit runner; GCS `get_signed_url` / `get_authenticated_url`; distinct versions for concurrent saves |
| v2.8.0 | Aug 26 | VIDEO allowed in the API server; `load_artifact_tool` handles spreadsheets; atomic file artifact versions; MultimodalToolResultsPlugin session retention; model callbacks run in live mode |
| v1.39.1 | Aug 27 | Backport of app-scoped file artifacts to the 1.x line |

---

## 10. Interview questions (crisp answers)

1. **Q: When should you use `inline_data` and when `file_data`?**
   A: Use `inline_data` for small, one-off media (keep the total request under about 20 MB). Use `file_data` URIs (Files API, `gs://`, HTTPS, YouTube) for large or reused files. The Files API allows 2 GB per file and 20 GB per project, keeps files for 48 h, and is free.
2. **Q: Why use Artifacts instead of session state for an image?**
   A: State is for small JSON values that are serialized into every event. Artifacts are versioned binary Parts held in a pluggable store (memory or GCS), referenced by filename, and loaded into a single request only when needed.
3. **Q: What does the `user:` prefix on an artifact do?**
   A: It scopes the artifact to app plus user rather than to the session, so every session for that user can access it.
4. **Q: How does a tool return an image to the model?**
   A: It returns `types.Part` or a list of Parts. Newer models carry media in the function_response. `MultimodalToolResultsPlugin` appends the Parts to the next LLM request through after_tool and before_model callbacks.
5. **Q: Which audio formats does ADK Live use?**
   A: Input is 16 kHz, 16-bit mono PCM and output is 24 kHz. Video is JPEG frames at about 1 fps, 768x768. There is no codec.
6. **Q: What is the difference between `send_content` and `send_realtime`?**
   A: `send_content` sends a turn-based text Content and triggers a response. `send_realtime` streams raw Blobs (audio or frames), and turn boundaries come from VAD or from activity_start and activity_end.
7. **Q: How do you make a live session last an hour?**
   A: Enable context_window_compression to remove the 15-minute audio and 2-minute video caps, and session_resumption to survive the roughly 10-minute connection resets (handles last 2 h). ADK reconnects transparently with up to 5 retries.
8. **Q: Why always call `live_request_queue.close()` in a finally block?**
   A: Otherwise zombie Live sessions keep counting against the concurrent-session quota.
9. **Q: Is a session the same as a connection?**
   A: No. The ADK Session is persistent storage. The Live API session is transient. A connection is the WebSocket, and one conversation can span many connections.
10. **Q: How many tokens is a minute of video on Gemini 3 at default settings?**
    A: Frames cost 70 tokens each at 1 fps, about 4,200 per minute, plus audio at 25 tok/s (1,500 per minute), so about 5.7k in total. On the legacy 2.x accounting it is about 100 tok/s, so about 6k.
11. **Q: Why can't my Live agent return TEXT?**
    A: Native-audio Live models output audio only. Read the text from output_audio_transcription.
12. **Q: Should image generation run in the agent's own model or in a tool?**
    A: Use a tool in production. The orchestrator stays a strong text and reasoning model, outputs become versioned artifacts, and you get policy and cost hooks. Making the model the agent suits simple demos.
13. **Q: What is a streaming tool?**
    A: An async-generator tool that yields intermediate results. It is non-blocking, can read live video through an `input_stream: LiveRequestQueue` parameter, and can be cancelled by the user through `stop_streaming`.
14. **Q: Which media resolution for PDFs vs. images?**
    A: Medium for PDFs, since quality saturates there. High for images. Ultra_high only per item, for fine detail.

---

## 11. Slide ideas (with animation)

1. **"Everything is a Part."** A central `types.Part` card fans out into text, inline_data, file_data, function_response and thought. *Animation:* each payload type flies in, then morphs into its Python constructor.
2. **"Inline vs Files API decision tree."** Branch on size under 20 MB, then reuse, then backend (Vertex: gs://). *Animation:* a file icon drops through the tree and lands in the right bucket. A 48 h timer appears on the Files API branch.
3. **"Token meter by modality."** Bar race across 1 image, 1 PDF page, 1 minute of audio and 1 minute of video, at each of the low, medium and high resolutions. *Animation:* the bars grow when a resolution slider moves.
4. **"Artifacts lifecycle."** save_artifact, then v0, v1, v2 stacked in GCS, then artifact_delta in the event, then load_artifact into a single request. *Animation:* version cards stack up, and one card slides into the LLM request and then fades out to show it does not stay in history.
5. **"Pointer, not payload."** The generate_image tool returns `{"filename": "image.png"}` while the bytes go to GCS. *Animation:* a split screen shows the context window filling up when bytes are inlined versus staying flat with a pointer.
6. **"Multimodal tool results plugin."** The after_tool, then temp state, then before_model sequence. *Animation:* a sequence diagram whose arrows light up in order, and the image thumbnail travels along them.
7. **"Bidi streaming architecture."** Browser to FastAPI (upstream and downstream tasks) to Runner.run_live to the Live API. *Animation:* continuous packet dots in both directions, then a red "barge-in" pulse that clears the audio buffer when `interrupted` fires.
8. **"Beating the clocks."** Timelines for the 10-minute connection, the 15-minute audio cap and the 2-minute video cap, then resumption and compression stretching them. *Animation:* a timeline bar snaps at 10 minutes and then reconnects seamlessly with a "handle" badge.
9. **"Model churn 2025 to 2026."** Imagen 3/4 and Veo 3.1 are greyed out, and Nano Banana 2.1, Omni Flash and 3.8 Live light up. *Animation:* a calendar flips to 2026-10-22, Veo stamps "shut down", and an env-var `MODEL_ID` badge pops in as the lesson.
10. **"Failure-mode bingo."** A 4x4 grid of the section 8 failures (chipmunk audio, zombie sessions, 2-minute video death and so on). *Animation:* the audience calls out the fix and each cell flips over to show it.

---

## Source index (all fetched 2026-10-23)

- ADK home: https://adk.dev/
- ADK 2.0: https://adk.dev/2.0/
- ADK artifacts: https://adk.dev/artifacts/
- ADK Live and voice agents: https://adk.dev/live/ (subpages /live/models/, /live/configuration/, /live/sessions/, /live/events/, /live/audio-video/, /live/tools/, /live/custom-server/, /live/get-started/streaming-python/)
- ADK Gemini models: https://adk.dev/agents/models/google-gemini/
- ADK context: https://adk.dev/context/
- adk-python releases: https://github.com/google/adk-python/releases
- adk-python multimodal samples: https://github.com/google/adk-python/tree/main/contributing/samples/multimodal
- adk-python plugin sources:
  - https://raw.githubusercontent.com/google/adk-python/main/src/google/adk/plugins/multimodal_tool_results_plugin.py
  - https://raw.githubusercontent.com/google/adk-python/main/src/google/adk/plugins/save_files_as_artifacts_plugin.py
  - https://raw.githubusercontent.com/google/adk-python/main/src/google/adk/agents/run_config.py
- Gemini API pages:
  - https://ai.google.dev/gemini-api/docs/models
  - https://ai.google.dev/gemini-api/docs/media-resolution
  - https://ai.google.dev/gemini-api/docs/files
  - https://ai.google.dev/gemini-api/docs/document-processing
  - https://ai.google.dev/gemini-api/docs/image-understanding
  - https://ai.google.dev/gemini-api/docs/video-understanding
  - https://ai.google.dev/gemini-api/docs/audio
  - https://ai.google.dev/gemini-api/docs/image-generation
  - https://ai.google.dev/gemini-api/docs/video
  - https://ai.google.dev/gemini-api/docs/omni
  - https://ai.google.dev/gemini-api/docs/live-session
  - https://ai.google.dev/gemini-api/docs/gemini-3
- Codelabs:
  - https://codelabs.developers.google.com/way-back-home-level-0/instructions
  - https://codelabs.developers.google.com/way-back-home-level-3/instructions
  - https://codelabs.developers.google.com/way-back-home-level-4/instructions
