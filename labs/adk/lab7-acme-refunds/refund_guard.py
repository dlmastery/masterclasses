"""Step 6: one plugin enforces the $500 refund cap on every agent in the App."""
from typing import Any, Optional

from google.adk.plugins.base_plugin import BasePlugin
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext


class RefundGuardPlugin(BasePlugin):
    def __init__(self, max_amount: float = 500.0):
        super().__init__(name="refund_guard")
        self.max_amount = max_amount

    async def before_tool_callback(
        self, *, tool: BaseTool, tool_args: dict[str, Any], tool_context: ToolContext
    ) -> Optional[dict]:
        amount = float(tool_args.get("amount", 0) or 0)
        if amount > self.max_amount:     # a returned dict skips the tool
            return {"status": "blocked",
                    "reason": f"{amount} exceeds limit {self.max_amount}"}
        return None
