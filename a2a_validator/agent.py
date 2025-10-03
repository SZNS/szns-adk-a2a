import os
from dotenv import load_dotenv

from google.adk import Agent
from google.adk.a2a.utils.agent_to_a2a import to_a2a

load_dotenv()

SERVICE_NAME = "a2a-validator"

PROMPT = """
You are a haiku validator.
You will be given an input and must determine if it:
1. Has three lines
2. Follows the 5-7-5 syllable structure.

You will also judge the haiku on its literary excellence, and give it a score from 0 to 100, with 100 being the best.
Invalid haikus should receive a score of 0.

Return your response in the following format:
{
    "is_valid": true,
    "score": 85,
    "feedback": "This haiku is well-structured and follows the 5-7-5 syllable pattern."
}
"""

root_agent = Agent(
    name="haiku_validator_agent",
    description="An ADK agent that validates haikus based on structure and literary quality.",
    model="gemini-2.5-flash",
    instruction=PROMPT,
    output_key="haiku_validator_agent_output",
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

# Use port 8001 for local testing, and 443 for Cloud Run, since it uses HTTPS
port = 8001 if is_local else 443

a2a_app = to_a2a(root_agent, host=host, port=port, protocol=protocol)
