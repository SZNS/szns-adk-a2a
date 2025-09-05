# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

import google.auth
from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools.mcp_tool import MCPToolset, StreamableHTTPConnectionParams

_, project_id = google.auth.default()
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project_id)
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "global")
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")

from .sub_agents.haiku_validator.agent import haiku_validator_agent

from .tools import (
   validate_haiku_with_external_agent
)

PROMPT = """
You are a haiku generator. 
Ask the user for a topic or an idea to create a haiku.
Do your best to follow the 5-7-5 syllable structure.
If the user asks you to say or repeat the haiku in a louder voice, use the louder_haiku tool.

If the user asks you to validate the haiku, use the haiku_validator_agent tool.
"""

# For our haiku validator, we can use this toggle to switch between our embedded sub-agent validation within the ADK app,
# or use an externally hosted A2A server, which we can call with a function tool
SHOULD_USE_EXTERNAL_A2A_VALIDATOR = False
haiku_validator_agent = validate_haiku_with_external_agent if SHOULD_USE_EXTERNAL_A2A_VALIDATOR else AgentTool(agent=haiku_validator_agent)


def louder_haiku(text: str) -> str:
    """Converts the entire text block to uppercase."""
    return text.upper()


root_agent = Agent(
    name="root_agent",
    model="gemini-2.5-flash",
    instruction=PROMPT,
    tools=[
        louder_haiku,
        
        # Uncomment when ready
        
        # haiku_validator_agent,
        
        # Uncomment when ready
        
        # MCPToolset(
        #     connection_params=StreamableHTTPConnectionParams(
        #         url=os.getenv("MCP_HAIKU_STORE_SERVER_URL", "http://localhost:8075/mcp")
        #     )
        # )
        ],
)
