# 1.x style: still runs on google-adk 2.13.0, but SequentialAgent is deprecated.
from google.adk.agents import LlmAgent, SequentialAgent
from support_desk.tools import lookup_order   # same tool used after the port

intake = LlmAgent(name="intake_agent", model="gemini-3.5-flash",
                  tools=[lookup_order],
                  instruction="Look up the order, then summarize the finding.")
synth = LlmAgent(name="synthesizer_agent", model="gemini-3.5-flash",
                 instruction="Write the customer reply from the intake finding.")
root_agent = SequentialAgent(name="support_pipeline", sub_agents=[intake, synth])
