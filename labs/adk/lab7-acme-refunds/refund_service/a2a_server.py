"""Step 2 (terminal 2): serve refund_agent over A2A with an agent card on :8001.

Run from lab7-acme-refunds/:
    uvicorn refund_service.a2a_server:a2a_app --host localhost --port 8001
"""
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from refund_core import refund_agent   # same agent as step 1

# to_a2a WRITES host and port into the card URL.
# uvicorn BINDS the socket. Both must say 8001.
a2a_app = to_a2a(refund_agent, host="localhost", port=8001)
