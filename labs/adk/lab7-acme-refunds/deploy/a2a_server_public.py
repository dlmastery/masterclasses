"""Gotcha fix: on Cloud Run the card holds the public URL, not the container port.

Deploy so that uvicorn listens on $PORT (8080 by default):
    uvicorn deploy.a2a_server_public:a2a_app --host 0.0.0.0 --port $PORT
Replace refunds.example.com with your service's public host name.
"""
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from refund_core import refund_agent

a2a_app = to_a2a(refund_agent, host="refunds.example.com", protocol="https", port=443)
