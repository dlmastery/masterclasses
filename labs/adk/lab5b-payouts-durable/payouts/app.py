# payouts/app.py  -  Lab 5B, Acme payouts: retry, pause, resume (google-adk 2.13.0)
# Run from the folder that contains payouts/:
#   python -m payouts.app start "ACME-GmbH"   # process 1: kyc_lookup, pause, exit
#   python -m payouts.app resume yes          # process 2: answers the pause
#   python -m payouts.app continue -          # after a crash: no new message
# No LLM node, so no API key is needed.
import asyncio, json, sys

from google.adk import Context, Event, Runner, Workflow
from google.adk.apps import App, ResumabilityConfig
from google.adk.events import RequestInput
from google.adk.sessions.sqlite_session_service import SqliteSessionService
from google.adk.workflow import RetryConfig, node
from google.genai import types


def kyc_lookup(node_input: str) -> dict:
  open("side_effects.log", "a").write(f"kyc_lookup {node_input}\n")
  return {"payee": node_input, "risk": "medium"}


def analyst_review(node_input: dict):   # hand-off pause
  yield RequestInput(message=f"Approve payout to {node_input['payee']} "
                             f"(risk {node_input['risk']})? yes/no")


@node(retry_config=RetryConfig(max_attempts=4, initial_delay=0.5,
                               backoff_factor=2.0, jitter=0.0,
                               exceptions=[ConnectionError,
                                           "NodeTimeoutError"]),
      timeout=2.0)
async def pay(ctx: Context, node_input: str):  # the analyst's reply
  yield Event(message=f"gateway attempt {ctx.attempt_count}")
  if node_input.strip().lower() != "yes":
    yield Event(output="CANCELLED"); return
  if ctx.attempt_count < 3:
    raise ConnectionError("gateway 503")   # attempts 1-2 fail, 3 pays
  key = "payout-" + ctx.invocation_id      # same key on every run
  yield Event(output=f"PAID idempotency_key={key}")


root = Workflow(name="payouts",
                edges=[("START", kyc_lookup, analyst_review, pay)])
app = App(name="payouts", root_agent=root,
          resumability_config=ResumabilityConfig(is_resumable=True))
runner = Runner(app=app,
                session_service=SqliteSessionService("payouts.db"))


async def main(cmd: str, arg: str):
  if cmd == "start":
    await runner.session_service.create_session(
        app_name="payouts", user_id="ops", session_id="s1")
    msg = types.Content(role="user", parts=[types.Part(text=arg)])
    inv = None
  elif cmd == "resume":                       # answer the open pause
    pending = json.load(open("pending.json"))
    inv = pending["invocation_id"]
    msg = types.Content(role="user", parts=[types.Part(
        function_response=types.FunctionResponse(
            id=pending["interrupt_id"], name="adk_request_input",
            response={"result": arg}))])
  else:                                       # "continue": after a crash
    inv = json.load(open("pending.json"))["invocation_id"]
    msg = None                                # needs ResumabilityConfig
  async for ev in runner.run_async(user_id="ops", session_id="s1",
                                   invocation_id=inv, new_message=msg):
    if ev.content and ev.content.parts and ev.content.parts[0].text:
      print(f"[{ev.author}] {ev.content.parts[0].text}")
    if ev.long_running_tool_ids:              # analyst_review paused
      json.dump({"invocation_id": ev.invocation_id,
                 "interrupt_id": next(iter(ev.long_running_tool_ids))},
                open("pending.json", "w"))
      print("PAUSED -> pending.json")
    if ev.output is not None and ev.node_info and \
        "/pay@" in (ev.node_info.path or ""):  # pay's output
      print("OUTPUT:", ev.output)


if __name__ == "__main__":
  asyncio.run(main(sys.argv[1], sys.argv[2]))
