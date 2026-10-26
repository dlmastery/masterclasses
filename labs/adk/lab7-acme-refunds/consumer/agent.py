"""Step 1 (terminal 3, adk run consumer): an Acme front-line agent that calls the MCP tool."""
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import McpToolset, StreamableHTTPConnectionParams

root_agent = LlmAgent(
    name="cs_frontline",
    model="gemini-3.5-flash",
    instruction="For any refund question call the refund_agent tool.",
    tools=[McpToolset(
        connection_params=StreamableHTTPConnectionParams(
            url="http://127.0.0.1:8090/mcp",
            sse_read_timeout=120.0),       # the whole agent run is one call
        tool_filter=["refund_agent"])],    # tool name = agent name
)
