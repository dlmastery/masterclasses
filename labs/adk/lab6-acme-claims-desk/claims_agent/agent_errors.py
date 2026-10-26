"""Plugin for MCP servers you cannot edit: drop human-only "next steps".

An error message is a prompt. "Run `cli login`" asks a tool-only agent for
something it cannot do. Keep the cause, delete the human-only sentence.
google-adk 2.13.0: BasePlugin.after_tool_callback(*, tool, tool_args,
tool_context, result); a non-None return replaces the result.
"""
import re

from google.adk.plugins.base_plugin import BasePlugin

HUMAN_STEP = re.compile(r"\b(Run|Open|Edit) [^.]*\.\s*")  # human-only


class AgentErrorPlugin(BasePlugin):
    def __init__(self):
        super().__init__(name="agent_errors")

    async def after_tool_callback(
            self, *, tool, tool_args, tool_context, result):
        text = str(result)
        if "error" not in text.lower():
            return None                     # normal results pass
        cleaned = HUMAN_STEP.sub("", text)  # keep the cause
        return {"result": cleaned} if cleaned != text else None


# register once: App(..., plugins=[AgentErrorPlugin()])
