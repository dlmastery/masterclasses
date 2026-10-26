"""Step 3 (terminal 3, adk web): Acme support triage delegates refunds over A2A."""
from google.adk.agents import LlmAgent
from google.adk.agents.remote_a2a_agent import (
    AGENT_CARD_WELL_KNOWN_PATH, RemoteA2aAgent)

refund_remote = RemoteA2aAgent(
    name="refund_agent",      # local name: the LLM transfers by it
    agent_card=f"http://localhost:8001{AGENT_CARD_WELL_KNOWN_PATH}",
    description="Remote refund-eligibility agent (Payments team).",
    timeout=60.0,             # default 600.0 seconds
)

root_agent = LlmAgent(
    name="support_triage",
    model="gemini-3.5-flash",
    instruction=("Classify the ticket. Refund or return questions: "
                 "transfer to refund_agent. Else answer yourself."),
    sub_agents=[refund_remote],
)
