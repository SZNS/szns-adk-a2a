import asyncio
import os
from dotenv import load_dotenv

from google.adk import Agent
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.a2a.utils.agent_card_builder import AgentCardBuilder

load_dotenv()

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
    Alternates the case of all letters in a string, preserving newlines.
    
    Args:
        s: The input string.
        
    Returns:
        A new string with alternating lowercase and uppercase letters.
        Example: "hello world\\nnew line" -> "hElLo wOrLd\\nnEw lInE"
    """
    return '\n'.join(
        ''.join(c.upper() if i % 2 == 1 else c.lower() for i, c in enumerate(line))
        for line in s.splitlines()
    )

def make_choppy(s: str) -> str:
    """
    Adds a period after each word in a string, preserving newlines.
    
    Args:
        s: The input string.
        
    Returns:
        A new string with a period appended to each word.
        Example: "Hello world\\nAnother line" -> "Hello. world.\\nAnother. line."
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

port = int(os.getenv('PORT', '8002'))

a2a_app = to_a2a(root_agent, port=port)
