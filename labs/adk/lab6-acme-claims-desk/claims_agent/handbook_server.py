"""Acme claims handbook MCP server (streamable HTTP, port 3000). mcp 2.3.0.

Run it in its own terminal: python claims_agent/handbook_server.py
"""
from mcp.server.mcpserver import MCPServer

mcp = MCPServer("claims-handbook-server")

POLICIES = {
    "glass": "Glass repair: no deductible on comprehensive policies.",
    "rental": "Rental car covered up to 30 days at $40 per day.",
    "towing": "Towing covered up to 50 miles per incident.",
}


@mcp.tool()
def search_policy(topic: str) -> str:
    """Search the claims handbook. topic: glass, rental or towing."""
    return POLICIES.get(topic.lower(), f"No policy for '{topic}'.")


@mcp.tool()
def list_topics() -> list[str]:
    """List claims-handbook topics that search_policy understands."""
    return sorted(POLICIES)


if __name__ == "__main__":
    # mcp 2.x: host and port go to run(); the path defaults to /mcp
    mcp.run(transport="streamable-http", host="127.0.0.1", port=3000)
