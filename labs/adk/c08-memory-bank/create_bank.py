"""One-off: create an empty Agent Runtime that holds the Memory Bank. Prints AGENT_ENGINE_ID.

Needs google-cloud-agentplatform>=2.2 (older SDKs only expose Client.agent_engines).
The Agent Runtime is a billed resource: delete it in the console when you finish.
"""
import os

import agentplatform

client = agentplatform.Client(project=os.environ["GOOGLE_CLOUD_PROJECT"],
                              location=os.environ["GOOGLE_CLOUD_LOCATION"])
runtime = client.runtimes.create()                 # same call `adk deploy agent_engine` uses
print(runtime.api_resource.name.split("/")[-1])    # -> AGENT_ENGINE_ID
