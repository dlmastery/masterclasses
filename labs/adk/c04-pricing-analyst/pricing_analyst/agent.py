# Lab 4, build: Acme back office competitor premiums.
# Each built-in tool lives alone in its own agent; the root calls them via AgentTool,
# so each subagent keeps its own context and control returns to the root.
from google.adk.agents import LlmAgent
from google.adk.code_executors import BuiltInCodeExecutor
from google.adk.tools import AgentTool, google_search

search_agent = LlmAgent(
    name="price_search",
    model="gemini-3.5-flash",
    description="Finds current retail prices for a product on the public web.",
    instruction="Search the web. Return a list of {retailer, price_usd, url}. Cite every url.",
    tools=[google_search],
)

calc_agent = LlmAgent(
    name="price_math",
    model="gemini-3.5-flash",
    description="Runs Python to compute statistics over a list of prices.",
    instruction="Write and run Python. Print mean, min, max and spread. Never guess numbers.",
    code_executor=BuiltInCodeExecutor(),   # runs in Gemini's sandbox, not locally
)

root_agent = LlmAgent(
    name="pricing_analyst",
    model="gemini-3.5-flash",
    instruction=(
        "1) Use price_search to collect prices. 2) Pass the numbers to price_math. "
        "3) Report the table, the stats, and the source urls."
    ),
    tools=[AgentTool(agent=search_agent), AgentTool(agent=calc_agent)],
)
