"""Gotcha fix: security_schemes on the card is metadata only.

Enforce auth in front of the server (Cloud Run IAM, an API gateway or
middleware) and send a token from the client. Data, not state, crosses.
Needs:  export REFUNDS_ID_TOKEN=<an identity token for the service>
"""
import os

from google.adk.agents.remote_a2a_agent import AGENT_CARD_WELL_KNOWN_PATH, RemoteA2aAgent
from google.adk.tools.openapi_tool.auth.auth_helpers import token_to_scheme_credential

URL = "https://refunds.example.com"   # replace with your public host

# the server enforces auth in front: Cloud Run IAM, a gateway or middleware
scheme, cred = token_to_scheme_credential(
    "oauth2Token", "header", "Authorization",
    os.environ["REFUNDS_ID_TOKEN"])
refund_remote = RemoteA2aAgent(name="refund_agent", timeout=60.0,
    agent_card=f"{URL}{AGENT_CARD_WELL_KNOWN_PATH}",
    auth_scheme=scheme, auth_credential=cred)   # data, not state, crosses
