"""
A client script to send a command to the haiku utility agent.

This script initializes an A2AClient, fetches the agent's capabilities
from its "agent card," and then sends a prompt as a text message.
The agent's response is printed to the console.

Usage:
    python test_client.py --base-url <AGENT_BASE_URL>
"""

import argparse
import asyncio
import logging
from typing import Any
from uuid import uuid4

import httpx

from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    AgentCard,
    MessageSendParams,
    SendMessageSuccessResponse,
    SendMessageRequest,
    Task,
)
from a2a.utils.constants import (
    AGENT_CARD_WELL_KNOWN_PATH,
    EXTENDED_AGENT_CARD_PATH,
)

# Configure logging for clear output
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def fetch_and_select_agent_card(resolver: A2ACardResolver, base_url: str) -> AgentCard:
    """
    Fetches the public agent card and, if supported, the extended agent card.

    It prioritizes the extended card if available, otherwise falls back to the public one.

    Args:
        resolver: An instance of A2ACardResolver.
        base_url: The base URL of the agent.

    Returns:
        The selected AgentCard to use for client initialization.

    Raises:
        RuntimeError: If the public agent card cannot be fetched.
    """
    try:
        logger.info(f'Fetching public agent card from: {base_url}{AGENT_CARD_WELL_KNOWN_PATH}')
        public_card = await resolver.get_agent_card()
        logger.info('Successfully fetched public agent card.')

        # The agent card from the remote server may incorrectly point to localhost.
        # We override it here to ensure it points to the correct public URL.
        if public_card.url != base_url:
            logger.info(f"Overriding agent card URL from '{public_card.url}' to '{base_url}'")
            public_card.url = base_url

        if public_card.supports_authenticated_extended_card:
            logger.info('Public card supports an extended card. Attempting to fetch...')
            try:
                auth_headers = {'Authorization': 'Bearer dummy-token-for-extended-card'}
                extended_card = await resolver.get_agent_card(
                    relative_card_path=EXTENDED_AGENT_CARD_PATH,
                    http_kwargs={'headers': auth_headers},
                )
                logger.info('Successfully fetched extended agent card. Using it for the client.')
                return extended_card
            except Exception as e:
                logger.warning(
                    f'Failed to fetch extended agent card: {e}. Falling back to public card.'
                )
        else:
            logger.info('Public card does not support an extended card. Using public card.')

        return public_card

    except Exception as e:
        logger.error(f'Critical error fetching public agent card: {e}', exc_info=True)
        raise RuntimeError('Failed to fetch the public agent card. Cannot continue.') from e


async def call_utility_agent(prompt_text: str, base_url: str) -> str:
    """
    Initializes a client, sends a prompt to the agent, and prints the response.

    Args:
        prompt_text: The prompt to send to the agent.
        base_url: The base URL of the deployed agent.
    Returns:
        The text content of the agent's response, or an error message.
    """
    async with httpx.AsyncClient() as httpx_client:
        resolver = A2ACardResolver(httpx_client=httpx_client, base_url=base_url)
        agent_card_to_use = await fetch_and_select_agent_card(resolver, base_url)

        logger.info(f'Initializing A2AClient with agent card: {agent_card_to_use.name}')
        client = A2AClient(httpx_client=httpx_client, agent_card=agent_card_to_use)

        message_payload: dict[str, Any] = {
            'message': {
                'role': 'user',
                'parts': [{'type': 'text', 'text': prompt_text}],
                'messageId': uuid4().hex,
            },
        }
        request = SendMessageRequest(
            id=str(uuid4()), params=MessageSendParams(**message_payload)
        )

        logger.info(f"Sending prompt to utility agent:\n---\n{prompt_text}\n---")
        response = await client.send_message(request)

        # Extract the text from the response
        if isinstance(response.root, SendMessageSuccessResponse) and isinstance(response.root.result, Task):
            task = response.root.result
            if task.artifacts and task.artifacts[0].parts:
                result_text = task.artifacts[0].parts[0].root.text
                logger.info(f"Received response: {result_text[:100]}...")
                return result_text

        return f"Error: Failed to get a valid text response. Full response: {response.model_dump_json()}"


async def main() -> None:
    """
    Parses command-line arguments and runs the haiku utility agent test.
    Usage:
        python test_client.py --base-url http://localhost:8002
    """
    parser = argparse.ArgumentParser(description='Send a command to the A2A haiku utility agent.')
    parser.add_argument(
        '--base-url',
        required=True,
        help='The base URL of the deployed haiku utility agent.',
    )
    args = parser.parse_args()

    # A classic haiku by Matsuo Bashō and a command to test the agent.
    haiku = (
        "An old silent pond...\n"
        "A frog jumps into the pond—\n"
        "Splash! Silence again."
    )

    test_cases = [
        {"name": "Spooky Case", "prompt": f"Please transform the following haiku into Spooky Case:\n\n{haiku}"},
        {"name": "Louder", "prompt": f"Please make this haiku louder:\n\n{haiku}"},
        {"name": "Quieter", "prompt": f"Can you make this haiku quieter?\n\n{haiku}"},
        {"name": "Make Choppy", "prompt": f"Please make the following haiku choppy:\n\n{haiku}"},
    ]

    results = []
    for case in test_cases:
        print(f"\n{'='*20} RUNNING TEST: {case['name'].upper()} {'='*20}")
        result_text = await call_utility_agent(prompt_text=case['prompt'], base_url=args.base_url)
        results.append({"name": case['name'], "output": result_text})
        # A small delay between requests to make the log output easier to read
        await asyncio.sleep(1)

    print(f"\n\n{'='*25} ALL TESTS COMPLETE {'='*25}")
    print("Aggregating results into a summary table...")

    # --- Print Results Table ---
    # Determine column widths
    max_name_len = max((len(r['name']) for r in results), default=0)
    col_width_name = max(max_name_len, len("Transformation")) + 2

    # Header
    print("\n" + "-" * 80)
    print(f"| {'Transformation'.ljust(col_width_name)}| {'Result'.ljust(80 - col_width_name - 4)} |")
    print(f"|{'-' * (col_width_name + 1)}|{'-' * (80 - col_width_name - 3)}|")

    # Rows
    for res in results:
        # Replace newlines in the output for clean table formatting
        cleaned_output = res['output'].replace('\n', ' ')
        print(f"| {res['name'].ljust(col_width_name)}| {cleaned_output.ljust(80 - col_width_name - 4)} |")
    print("-" * 80 + "\n")


if __name__ == '__main__':
    asyncio.run(main())
