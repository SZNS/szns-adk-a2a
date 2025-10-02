import os

import google.auth
from google.adk.agents import Agent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent, AGENT_CARD_WELL_KNOWN_PATH
from .sub_agents.haiku_validator.agent import haiku_validator_agent as validator_local_agent

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
"""

# For our haiku validator, we can use this toggle to switch between our embedded sub-agent validator within the ADK app,
# or use an externally hosted A2A server
SHOULD_USE_EXTERNAL_A2A_VALIDATOR = False
validator_agent = validator_a2a_agent if SHOULD_USE_EXTERNAL_A2A_VALIDATOR else validator_local_agent

def louder_haiku(text: str) -> str:
    """Converts the entire text block to uppercase."""
    return text.upper()

root_agent = Agent(
    name="root_agent",
    model="gemini-2.5-flash",
    instruction=PROMPT,
    tools=[
        # Uncomment when needed
        # louder_haiku,
        ],
    sub_agents=[
        validator_agent, 
        
        # Uncomment when needed
        # utilities_a2a_agent
        ],
)
