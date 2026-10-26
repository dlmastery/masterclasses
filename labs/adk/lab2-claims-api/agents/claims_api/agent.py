"""Lab 2, step 2: the claims App with a built-in and a custom plugin.

Run from the lab folder:
    adk run agents/claims_api
    adk api_server agents --port 8000
"""
from typing import Any, Optional

from google.adk import Agent
from google.adk.apps import App
from google.adk.plugins import LoggingPlugin
from google.adk.plugins.base_plugin import BasePlugin
from google.adk.tools import BaseTool, ToolContext


def lookup_policy(policy_number: str) -> dict:
    """Return coverage for a policy number like POL-448120."""
    return {"status": "success", "policy_number": policy_number,
            "collision_deductible_usd": 500,
            "coverage": ["collision", "glass", "liability"]}


class AuditPlugin(BasePlugin):
    """Records every tool call app-wide in state, for audit export."""

    def __init__(self) -> None:
        super().__init__(name="audit")

    async def before_tool_callback(
            self, *, tool: BaseTool, tool_args: dict[str, Any],
            tool_context: ToolContext) -> Optional[dict]:
        log = tool_context.state.get("audit_log", [])
        entry = f"{tool.name}({tool_args})"
        tool_context.state["audit_log"] = log + [entry]
        return None                     # None: the tool runs


root_agent = Agent(
    name="claims_assistant",
    model="gemini-3.5-flash",
    instruction=("Answer coverage questions. "
                 "Always call lookup_policy first."),
    tools=[lookup_policy],
)

# adk run / web / api_server use a variable named `app` when it exists
app = App(name="claims_api", root_agent=root_agent,
          plugins=[LoggingPlugin(), AuditPlugin()])
