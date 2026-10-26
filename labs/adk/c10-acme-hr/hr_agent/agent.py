# Lab 10 step 1: the Acme HR assistant with two guard layers.
# Verified against google-adk 2.13.0 source (research-v2/adk/lab-prod.md, Lab 3).
import os
import re
from typing import Any, Optional

from google.adk import Agent
from google.adk.apps import App
from google.adk.integrations.model_armor import ModelArmorConfig, ModelArmorPlugin
from google.adk.models import LlmRequest, LlmResponse
from google.adk.plugins import BasePlugin
from google.adk.tools import BaseTool, ToolContext
from google.genai import types

SSN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")


class HrGuardPlugin(BasePlugin):
    def __init__(self) -> None:
        super().__init__(name="hr_guard")

    async def before_model_callback(self, *, callback_context,
                                    llm_request: LlmRequest) -> Optional[LlmResponse]:
        for content in llm_request.contents or []:
            for part in content.parts or []:
                if part.text and SSN.search(part.text):
                    # mutate, then continue
                    part.text = SSN.sub("[REDACTED-SSN]", part.text)
        return None

    async def before_tool_callback(self, *, tool: BaseTool, tool_args: dict[str, Any],
                                   tool_context: ToolContext) -> Optional[dict]:
        caller = tool_context.state.get("employee_id")
        if tool.name == "get_salary_band" and tool_args.get("employee_id") != caller:
            return {"status": "error",
                    "error_message": "You can only view your own salary band."}
        return None


def get_salary_band(employee_id: str) -> dict:
    """Returns the salary band for an employee id such as E-1001."""
    return {"status": "success", "employee_id": employee_id, "band": "L5"}


root_agent = Agent(
    name="hr_agent",
    model="gemini-3.5-flash",
    instruction=("Answer Acme HR policy questions. "
                 "Use get_salary_band only for the caller."),
    tools=[get_salary_band],
)

template = os.environ["MA_TEMPLATE"]  # full resource name, see README
app = App(name="hr_agent", root_agent=root_agent, plugins=[
    HrGuardPlugin(),
    ModelArmorPlugin(config=ModelArmorConfig(
        prompt_template_name=template,
        response_template_name=template,
        tool_output_template_name=template,
        block_on_screening_failure=True)),
])
