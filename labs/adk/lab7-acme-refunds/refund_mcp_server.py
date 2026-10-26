"""Step 1 (terminal 1): publish refund_agent as one MCP tool on :8090/mcp."""
from google.adk.tools.mcp_tool import to_mcp_server
from refund_core import refund_agent   # the shared agent

server = to_mcp_server(
    refund_agent,
    # a public hint for the MCP host, not the agent's instruction=
    instructions=("Ask about refund eligibility by order id, "
                  "e.g. 'Can A-100 be refunded?'"),
    runner=None,   # default: in-memory sessions, lost on restart
)

if __name__ == "__main__":
    server.run(transport="streamable-http", host="127.0.0.1", port=8090)
