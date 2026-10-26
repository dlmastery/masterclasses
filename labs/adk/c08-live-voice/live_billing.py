"""Lab 8 step 3: Acme billing answers by voice with run_live (Live API, native audio).

Text stands in for the microphone so the loop is easy to read. A real call streams
16 kHz PCM with q.send_realtime(blob) and adds input_audio_transcription.
Tested against google-adk 2.13.0 source. Output in README.md is illustrative.
"""
import asyncio
import wave

from google.adk import Agent, Runner
from google.adk.agents.live_request_queue import LiveRequestQueue
from google.adk.agents.run_config import RunConfig
from google.adk.sessions import InMemorySessionService
from google.genai import types


def get_balance(account_id: str) -> dict:
    """Returns balance and due date for an Acme account."""
    return {"status": "success", "account_id": account_id,
            "balance_usd": 84.20, "due": "2026-11-05"}


agent = Agent(name="voice_billing", tools=[get_balance],
    model="gemini-live-2.5-flash-native-audio",       # DEFAULT_LIVE_MODEL in 2.13.0
    instruction="Acme billing. Be brief. No new-plan prices.")

cfg = RunConfig(
    response_modalities=["AUDIO"],                                   # audio-only out
    output_audio_transcription=types.AudioTranscriptionConfig(),     # text comes from here
    session_resumption=types.SessionResumptionConfig())              # reconnect on limits


def save_wav(pcm: bytes) -> None:
    """Native-audio output is 24 kHz, 16-bit, mono PCM."""
    with wave.open("answer.wav", "wb") as w:
        w.setparams((1, 2, 24000, 0, "NONE", None))
        w.writeframes(pcm)


async def main() -> None:
    sessions = InMemorySessionService()
    runner = Runner(agent=agent, app_name="acme_voice", session_service=sessions)
    # run_live needs the session first, or: ValueError: Session not found
    await sessions.create_session(app_name="acme_voice", user_id="cust-42",
                                  session_id="call-1")
    q = LiveRequestQueue()                    # one queue per call
    q.send_content(types.Content(role="user", parts=[
        types.Part(text="What's my balance on account A-3310?")]))
    pcm = bytearray()
    try:
        async for ev in runner.run_live(user_id="cust-42",
                session_id="call-1", live_request_queue=q,
                run_config=cfg):
            t = ev.output_transcription
            if t and t.text: print("agent:", t.text)
            for p in (ev.content.parts if ev.content else []):
                if p.inline_data: pcm += p.inline_data.data
            if ev.turn_complete: break
    finally: q.close()
    save_wav(bytes(pcm))
    print(f"answer.wav written · {len(pcm):,} bytes")


if __name__ == "__main__":
    asyncio.run(main())
