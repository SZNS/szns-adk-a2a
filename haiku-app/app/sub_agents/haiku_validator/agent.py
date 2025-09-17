from google.adk.agents import Agent

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

haiku_validator_agent = Agent(
    name="haiku_validator_agent",
    model="gemini-2.5-flash",
    instruction=PROMPT,
    output_key="haiku_validator_agent_output",
)