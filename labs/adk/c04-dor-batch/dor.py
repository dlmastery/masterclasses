# Lab 4, industry: the Palo Alto Networks "Document of Record" pattern on google-adk 2.13.0.
# The orchestrator is your code. Each question is one bounded agent call in a fresh
# session, five in flight at a time. The document lives in your process.
import asyncio
from google.adk.agents import LlmAgent
from google.adk.apps.app import App
from google.adk.runners import InMemoryRunner
from google.genai import types

answerer = LlmAgent(
    name="dor_answerer",
    model="gemini-3.5-flash",   # PANW used Gemini 2.5 Flash
    static_instruction="Answer ONE customer question from retrieved facts. "
                       "Return 'UNKNOWN' if the facts do not support an answer.",
    # tools=[rag_tool],   # e.g. a Vertex AI RAG Engine retrieval tool you supply
)
app = App(name="dor", root_agent=answerer)
runner = InMemoryRunner(app=app)
sem = asyncio.Semaphore(5)          # PANW: "batches of five"


async def answer(q: str) -> tuple[str, str]:
  async with sem:                   # at most 5 calls in flight
    s = await runner.session_service.create_session(
        app_name="dor", user_id="dor")         # fresh session
    msg = types.Content(role="user", parts=[types.Part(text=q)])
    final = ""
    async for ev in runner.run_async(
        user_id="dor", session_id=s.id, new_message=msg):
      if ev.is_final_response() and ev.content and ev.content.parts:
        final = "".join(p.text or "" for p in ev.content.parts)
    return q, final                 # context never grows


async def build_dor(questions: list[str]) -> dict[str, str]:
  return dict(await asyncio.gather(*(answer(q) for q in questions)))


if __name__ == "__main__":
  QUESTIONS = [
      "Which cloud providers does Acme use?",
      "How many security analysts does Acme employ?",
      "Which firewall vendor does Acme run today?",
      "When does Acme's current security contract renew?",
      "Who is Acme's CISO?",
      "Does Acme run a 24x7 security operations center?",
      "Which compliance frameworks must Acme follow?",
  ]
  dor = asyncio.run(build_dor(QUESTIONS))
  for q, a in dor.items():
    print(f"Q: {q}\nA: {a}\n")
