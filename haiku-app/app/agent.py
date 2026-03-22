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

import asyncio
import os

import google.auth
import google.genai.types as genai_types
from google import genai
from google.adk.agents import Agent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent, AGENT_CARD_WELL_KNOWN_PATH
from google.adk.tools import ToolContext
from google.genai.types import GenerateImagesConfig
from .sub_agents.haiku_validator.agent import haiku_validator_agent as validator_local_agent
from .sub_agents.poetry_lookup.agent import poetry_lookup_agent
from google.adk.tools.mcp_tool import MCPToolset, StreamableHTTPConnectionParams

_, project_id = google.auth.default()
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project_id)
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "global")
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")

validator_a2a_url = os.getenv("HAIKU_VALIDATOR_AGENT_URL", "http://localhost:8001")
utilities_a2a_url = os.getenv("HAIKU_UTILITIES_AGENT_URL", "http://localhost:8002")

validator_a2a_agent = RemoteA2aAgent(
    name="validator_a2a_agent",
    description="A remote A2A Agent that handles haiku validation.",
    agent_card=(
        f"{validator_a2a_url}/{AGENT_CARD_WELL_KNOWN_PATH}"
    ),
)

utilities_a2a_agent = RemoteA2aAgent(
    name="utilities_a2a_agent",
    description="A remote A2A Agent that handles haiku utility functions.",
    agent_card=(
        f"{utilities_a2a_url}/{AGENT_CARD_WELL_KNOWN_PATH}"
    ),
)

PROMPT = """
You are a haiku generator. 
Ask the user for a topic or an idea to create a haiku.
Do your best to follow the 5-7-5 syllable structure.

If the user asks you to validate the haiku, use the validator_agent.

If the user asks you to call any of the following utility functions,
use the utilities_a2a_agent (if available, otherwise, respond that the utility functions are not available):
- Louder: Convert the entire haiku to uppercase.
- Quieter: Convert the entire haiku to lowercase.
- Spooky Case: Alternate the case of all letters in the haiku.
- Make Choppy: Add a period after each word in the haiku.

If the user asks to look up poetry, find poems by a specific author, search for poems by title,
or wants random poem inspiration, use the poetry_lookup_agent.

You have access to a Haiku Store where you can save, browse, search, and delete haikus.
Use it to save haikus the user likes, retrieve previously saved haikus, or search by text or minimum score.

After generating a haiku, ask the user if they would like to validate it, generate a visual image inspired by it,
or save it to the Haiku Store.
If the user wants an image, craft a descriptive visual prompt capturing the haiku's imagery and mood,
then use the generate_haiku_image tool.
"""

# For our haiku validator, we can use this toggle to switch between our embedded sub-agent validator within the ADK app,
# or use an externally hosted A2A server
SHOULD_USE_EXTERNAL_A2A_VALIDATOR = False
validator_agent = validator_a2a_agent if SHOULD_USE_EXTERNAL_A2A_VALIDATOR else validator_local_agent

def louder_haiku(text: str) -> str:
    """Converts the entire text block to uppercase."""
    return text.upper()


async def generate_haiku_image(prompt: str, tool_context: ToolContext) -> dict:
    """Generate an image inspired by a haiku.

    Args:
        prompt: A descriptive visual prompt based on the haiku's imagery and mood.
    """
    try:
        client = genai.Client()
        response = await asyncio.to_thread(
            client.models.generate_images,
            model="imagen-3.0-generate-001",
            prompt=prompt,
            config=GenerateImagesConfig(number_of_images=1),
        )
        image_bytes = response.generated_images[0].image.image_bytes
        artifact = genai_types.Part.from_bytes(
            data=image_bytes, mime_type="image/png"
        )
        version = await tool_context.save_artifact(
            filename="haiku_image.png", artifact=artifact
        )
        return {"status": "success", "filename": "haiku_image.png", "version": version}
    except Exception as e:
        return {"status": "error", "message": f"Failed to generate image: {e}"}

root_agent = Agent(
    name="root_agent",
    model="gemini-2.5-flash",
    instruction=PROMPT,
    tools=[
        louder_haiku,
        generate_haiku_image,
        MCPToolset(
            connection_params=StreamableHTTPConnectionParams(
                url=os.getenv("MCP_HAIKU_STORE_SERVER_URL", "http://localhost:8075/mcp")
            )
        )
        ],
    sub_agents=[
        validator_agent,
        poetry_lookup_agent,

        # Uncomment when needed
        # utilities_a2a_agent
        ],
)
