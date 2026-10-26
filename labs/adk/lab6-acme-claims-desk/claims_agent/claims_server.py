"""Acme claims MCP server (stdio). mcp 2.3.0.

McpToolset starts this file as a child process. Never write to stdout:
over stdio, stdout carries the JSON-RPC stream. Log to stderr instead.
"""
import logging
import os
import sys

from mcp.server.mcpserver import MCPServer

# stdout carries JSON-RPC: log to stderr only
logging.basicConfig(stream=sys.stderr, level=logging.INFO)
mcp = MCPServer("claims-server")

CLAIMS = {
    "CLM-1001": {"policy": "AUTO-77", "status": "open", "amount": 1800.0},
    "CLM-1002": {"policy": "HOME-12", "status": "open", "amount": 420.0},
}
SESSION = {"valid": False}  # the claims-system session starts expired


@mcp.tool()
def login() -> dict:
    """Start a claims session. Call it when a session expired."""
    SESSION["valid"] = True
    return {"status": "ok"}


@mcp.tool()
def get_claim(claim_id: str) -> dict:
    """Return policy, status and claimed amount (USD) for a claim id like CLM-1001."""
    if not SESSION["valid"]:
        # written for the agent: the next step is a tool call it can make
        return {"status": "error", "message": "Session expired. Call "
                "claims_login, then call claims_get_claim again."}
    if claim_id not in CLAIMS:
        return {"status": "error",
                "message": f"Unknown claim {claim_id}."}
    return {"status": "ok", "claim_id": claim_id, **CLAIMS[claim_id]}


@mcp.tool()
def approve_claim(claim_id: str, approved_amount: float) -> dict:
    """Approve a claim and pay approved_amount USD."""
    claim = CLAIMS.get(claim_id)
    if claim is None or approved_amount > claim["amount"]:  # rule
        return {"status": "error",
                "message": "Unknown claim or amount too high."}
    claim["status"] = "approved"
    logging.info("approved %s for %.2f", claim_id, approved_amount)
    return {"status": "ok", "paid": approved_amount}


@mcp.tool()
def purge_claim(claim_id: str) -> dict:
    """Permanently delete a claim record (admin role only)."""
    if os.environ.get("CLAIMS_ROLE") != "admin":  # role check
        return {"status": "error", "message": "Needs the admin role."}
    purged = CLAIMS.pop(claim_id, None) is not None
    return {"status": "ok", "purged": purged}


if __name__ == "__main__":
    mcp.run()  # transport defaults to "stdio"
