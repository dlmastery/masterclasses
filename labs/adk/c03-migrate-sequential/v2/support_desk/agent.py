# google-adk 2.13.0: the same pipeline as a Workflow.
from google.adk import Agent, Workflow
from support_desk.tools import lookup_order   # same tool as 1.x

intake = Agent(name="intake_agent", mode="single_turn",
               model="gemini-3.5-flash", tools=[lookup_order],
               instruction="Look up the order, then "
                           "summarize the finding.")
synth = Agent(name="synthesizer_agent", mode="single_turn",
              model="gemini-3.5-flash",
              instruction="Write the customer reply from the "
                          "intake finding.",
              include_contents="default")   # sees upstream turns

root_agent = Workflow(name="support_workflow",
                      edges=[("START", intake, synth)])
# Run it through the Runner (adk run / adk web / Runner.run_async).
# Do not call workflow.run(ctx=...) yourself: that skips the Runner
# event-queue consumer that saves tool-call events.
