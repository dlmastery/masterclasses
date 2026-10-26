# Lab 8 step 3: run_live voice billing for Acme

The Acme billing desk answers a balance question through the Live API.
Audio comes back as PCM (saved to `answer.wav`) plus a text transcript.

## Install (pinned)

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
pip install "google-adk==2.13.0"
```

## Environment

Agent Platform (Vertex), model `gemini-live-2.5-flash-native-audio`:

```bash
GOOGLE_GENAI_USE_ENTERPRISE=TRUE
GOOGLE_CLOUD_PROJECT=my-proj
GOOGLE_CLOUD_LOCATION=us-central1    # regional, NOT global
```

AI Studio instead: `GOOGLE_GENAI_USE_ENTERPRISE=FALSE`, `GOOGLE_API_KEY=...`, and the preview
model `gemini-3.1-flash-live-preview` in `live_billing.py`.

## Run

```bash
python live_billing.py
# mic in the browser (Windows needs --no-reload):
export SSL_CERT_FILE=$(python -m certifi)
adk web --no-reload .
```

## Expected output (illustrative, not executed)

```
agent: Your balance on A-3310 is 84 dollars 20, due November 5th.
answer.wav written · 153,600 bytes
```

153,600 bytes is 3.2 s of 24 kHz 16-bit mono audio.

## Notes

- `RunConfig(streaming_mode=StreamingMode.BIDI)` does not start live mode. Only `runner.run_live()` does.
- Break on `turn_complete`, then `close()` the queue. Use one queue per call.
- Voice agents fail on numbers (arXiv 2610.17619): re-confirm account numbers in the tool.
- Source: https://github.com/google/adk-python/blob/v2.13.0/src/google/adk/runners.py
