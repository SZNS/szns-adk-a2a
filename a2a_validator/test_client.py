"""
A client script to send a haiku for validation to a remote agent.

This script initializes an A2AClient, fetches the agent's capabilities
from its "agent card," and then sends a haiku as a text message.
The agent's response is printed to the console.

Usage:
    python haiku_validator_client.py --base-url <AGENT_BASE_URL>
"""

import argparse
import asyncio
import json
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


async def validate_haiku_with_agent(haiku_text: str, base_url: str) -> None:
    """
    Initializes a client, sends a haiku to the agent, and prints the response.

    Args:
        haiku_text: The haiku to send to the agent for validation.
        base_url: The base URL of the deployed agent.
    """
    async with httpx.AsyncClient() as httpx_client:
        resolver = A2ACardResolver(httpx_client=httpx_client, base_url=base_url)
        agent_card_to_use = await fetch_and_select_agent_card(resolver, base_url)

        logger.info(f'Initializing A2AClient with agent card: {agent_card_to_use.name}')
        client = A2AClient(httpx_client=httpx_client, agent_card=agent_card_to_use)

        message_payload: dict[str, Any] = {
            'message': {
                'role': 'user',
                'parts': [{'type': 'text', 'text': haiku_text}],
                'messageId': uuid4().hex,
            },
        }
        request = SendMessageRequest(
            id=str(uuid4()), params=MessageSendParams(**message_payload)
        )

        logger.info(f"Sending haiku for validation:\n---\n{haiku_text}\n---")
        response = await client.send_message(request)

        # --- Process and Summarize Response ---
        print("\n--- Validation Result ---")
        if not isinstance(response.root, SendMessageSuccessResponse):
            error_details = response.root.error.model_dump_json(indent=2)
            print(f"❌ Failure: Agent returned an error.\nDetails: {error_details}")
            return

        task = response.root.result
        if not isinstance(task, Task) or not task.artifacts or not task.artifacts[0].parts:
            print(f"❌ Failure: Agent response was malformed or empty.")
            print(f"Raw Response: {response.model_dump_json(indent=2)}")
            return

        result_text = task.artifacts[0].parts[0].root.text
        try:
            # The model may wrap the JSON in markdown, so we extract it.
            if "```" in result_text:
                result_text = result_text.split("```")[1].strip("json\n")

            validation_data = json.loads(result_text)
            is_valid = validation_data.get("is_valid")
            status_icon = "✅" if is_valid else "⚠️"

            print(f"{status_icon} Validation Status: {'Valid' if is_valid else 'Invalid'}")
            print(f"   - Score: {validation_data.get('score', 'N/A')}")
            print(f"   - Feedback: {validation_data.get('feedback', 'N/A')}")
        except (json.JSONDecodeError, IndexError) as e:
            print(f"❌ Failure: Could not parse JSON from agent response.\nError: {e}")
            print(f"Raw Text Received: {result_text}")
        finally:
            print("-------------------------\n")


async def main() -> None:
    """
    Parses command-line arguments and runs the haiku validation.
    Usage:
        python test_client.py --base-url http://localhost:8001
    """
    parser = argparse.ArgumentParser(description='Send a haiku to an A2A agent for validation.')
    parser.add_argument(
        '--base-url',
        required=True,
        help='The base URL of the deployed haiku validator agent.',
    )
    args = parser.parse_args()

    # A classic haiku by Matsuo Bashō to test the agent.
    haiku_to_validate = (
        "An old silent pond...\n"
        "A frog jumps into the pond—\n"
        "Splash! Silence again."
    )

    await validate_haiku_with_agent(haiku_text=haiku_to_validate, base_url=args.base_url)


if __name__ == '__main__':
    asyncio.run(main())
