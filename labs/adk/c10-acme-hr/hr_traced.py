# Lab 10 step 2: trace the guarded Acme HR app without PII in spans.
# Run from the parent folder of hr_agent/ (research-v2/adk/lab-prod.md, Lab 4).
import asyncio
import os

from opentelemetry import trace
from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.telemetry import google_cloud
from google.adk.telemetry.setup import maybe_set_otel_providers
from google.genai import types

os.environ.setdefault("OTEL_SERVICE_NAME", "acme-hr")
os.environ.setdefault("OTEL_RESOURCE_ATTRIBUTES", "deployment.environment=dev")
os.environ.setdefault("ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS", "false")  # no PII

hooks = ([google_cloud.get_gcp_exporters(enable_cloud_tracing=True)]
         if os.getenv("TO_CLOUD") else [])
maybe_set_otel_providers(otel_hooks_to_setup=hooks)  # + OTEL_EXPORTER_OTLP_* env

from hr_agent.agent import app  # noqa: E402  step 1: HrGuardPlugin + ModelArmorPlugin


async def main() -> None:
    runner = Runner(app=app, session_service=InMemorySessionService(),
                    auto_create_session=True)
    msg = types.Content(role="user", parts=[types.Part(text="What is my salary band?")])
    async for event in runner.run_async(
            user_id="E-1001", session_id="s1", new_message=msg,
            state_delta={"employee_id": "E-1001"}):  # the guard reads it
        if event.is_final_response():
            print("agent>", event.content.parts[0].text)
    tp = trace.get_tracer_provider()  # BatchSpanProcessor: flush before exit
    if hasattr(tp, "force_flush"):    # the default ProxyTracerProvider has none
        tp.force_flush()


asyncio.run(main())
