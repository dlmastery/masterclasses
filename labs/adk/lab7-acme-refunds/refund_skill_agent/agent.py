"""Step 5 (adk web): the refund policy as an Agent Skill, loaded on demand."""
import pathlib

from google.adk.agents import LlmAgent
from google.adk.code_executors import UnsafeLocalCodeExecutor
from google.adk.skills import load_skill_from_dir
from google.adk.tools.skill_toolset import SkillToolset
from refund_core import lookup_order    # A-300: $120, day 42

HERE = pathlib.Path(__file__).parent

skills = SkillToolset(
    skills=[load_skill_from_dir(HERE / "skills" / "refund-policy")],
    additional_tools=[lookup_order],          # supplies the function
    code_executor=UnsafeLocalCodeExecutor(),  # DEV ONLY: exec() in-process
)

root_agent = LlmAgent(
    name="refund_skill_agent",
    model="gemini-3.5-flash",
    instruction="Use skills when they match the request.",
    tools=[skills],
)
