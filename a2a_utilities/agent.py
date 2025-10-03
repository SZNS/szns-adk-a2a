import os
from dotenv import load_dotenv
from google.adk import Agent
from google.adk.a2a.utils.agent_to_a2a import to_a2a

load_dotenv()

SERVICE_NAME = "a2a-utilities"

PROMPT = """
You are a haiku utilities agent.
You can perform a variety of text transformations on haikus, including:
- Louder: Convert the entire haiku to uppercase.
- Quieter: Convert the entire haiku to lowercase.
- Spooky Case: Alternate the case of all letters in the haiku.
- Make Choppy: Add a period after each word in the haiku.

You will be given a command and a haiku, and you must perform the requested transformation.
"""

def louder_haiku(text: str) -> str:
    """Converts the entire text block to uppercase."""
    return text.upper()

def quieter_haiku(text: str) -> str:
    """Converts the entire text block to lowercase."""
    return text.lower()

def spooky_case(s: str) -> str:
    """
    Alternates the case of all letters in a string.
    """
    return '\n'.join(
        ''.join(c.upper() if i % 2 == 1 else c.lower() for i, c in enumerate(line))
        for line in s.splitlines()
    )

def make_choppy(s: str) -> str:
    """
    Adds a period after each word in a string.
    """
    lines = s.splitlines()
    processed_lines = ['. '.join(line.split()) + '.' if line.strip() else '' for line in lines]
    return '\n'.join(processed_lines)

root_agent = Agent(
    name="haiku_utilities_agent",
    description="An ADK agent that can perform a variety of haiku-related tasks.",
    model="gemini-2.5-flash",
    instruction=PROMPT,
    tools=[
        louder_haiku,
        quieter_haiku,
        spooky_case,
        make_choppy,
    ],
    output_key="haiku_utilities_agent_output",
)

region = os.getenv('GOOGLE_CLOUD_REGION', 'us-central1')
project_number = os.getenv('GOOGLE_PROJECT_NUMBER')

# Determine if running locally or in Cloud Run
is_local = os.getenv('K_SERVICE') is None

if not is_local and not project_number:
    raise ValueError("GOOGLE_PROJECT_NUMBER must be set for Cloud Run deployments, it can be found on the GCP Console Dashboard.")

# If deploying to Cloud Run, pre-generate the host URL according to 
# Cloud Run's URL structure for use in the A2A Agent Card
protocol = "http" if is_local else "https"
host = "localhost" if is_local else f"{SERVICE_NAME}-{project_number}.{region}.run.app"

# Use port 8002 for local testing, and 443 for Cloud Run, since it uses HTTPS
port = 8002 if is_local else 443

a2a_app = to_a2a(root_agent, host=host, port=port, protocol=protocol)
