import os
import re
import json
import httpx
import logging
from typing import Any
from uuid import uuid4

from google.adk.tools import ToolContext
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import MessageSendParams, SendMessageRequest, SendMessageSuccessResponse, Task

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- A2A (Agent to Agent)  ---

def _extract_json_from_markdown(text: str) -> str:
    """
    Extracts a JSON string from a markdown code block, which LLMs often return.
    """
    # Regex to find a JSON block, being lenient with the language specifier (e.g., ```json)
    match = re.search(r"```(?:json)?\s*({.*})\s*```", text, re.DOTALL)
    if match:
        return match.group(1)
    # If no markdown block is found, assume the whole string might be the JSON
    return text

async def _call_a2a_agent(
    base_url: str, prompt_text: str, httpx_client: httpx.AsyncClient
) -> Any:
    """
    A reusable helper to call an external A2A agent.

    Args:
        base_url: The base URL of the external agent.
        prompt_text: The full text prompt to send to the agent.
        httpx_client: An active httpx.AsyncClient instance.

    Returns:
        The response object from the agent.
    """
    resolver = A2ACardResolver(
        httpx_client=httpx_client,
        base_url=base_url,
    )

    try:

        http_args = {
            "timeout": 10.0,
        }
        
        # Preferred method: Fetch the full agent card for complete configuration.
        agent_card = await resolver.get_agent_card(http_kwargs=http_args)
        agent_card.url = base_url
        client = A2AClient(httpx_client=httpx_client, agent_card=agent_card)
    except Exception as e:
        # Fallback method: If fetching the card fails, create a client with minimal info.
        logger.warning(
            f"Warning: Could not fetch full agent card ({e}). "
            "Falling back to minimal client configuration.", exc_info=True
        )
        client = A2AClient(httpx_client=httpx_client, url=base_url)
    
    payload = {
        "message": {
            "role": "user",
            "parts": [{"type": "text", "text": prompt_text}],
            "messageId": uuid4().hex,
        },
        "configuration": {
            "accepted_output_modes": ["text"],
            "history_length": 1,
        },
    }

    params = MessageSendParams.model_validate(payload)
    request = SendMessageRequest(id=str(uuid4()), params=params)
    return await client.send_message(request)

async def validate_haiku_with_external_agent(haiku: str) -> dict:
    """
    Calls an external A2A agent to validate a haiku.
    """

    base_url = os.getenv("HAIKU_VALIDATOR_AGENT_URL")
    if not base_url:
        return {"status": "error", "message": "HAIKU_VALIDATOR_AGENT_URL environment variable is not set."}

    # For more advanced agents, or in future versions, this string can be augmented with additional context.
    prompt_for_validator = haiku

    try:
        async with httpx.AsyncClient() as httpx_client:
            # Call the reusable A2A helper function
            response = await _call_a2a_agent(
                base_url=base_url,
                prompt_text=prompt_for_validator,
                httpx_client=httpx_client,
            )

            # Following a robust response handling pattern
            logger.info("Validator response: %s", response.model_dump(mode='json', exclude_none=True))
            if not isinstance(response.root, SendMessageSuccessResponse):
                error_details = response.root.error.model_dump_json(indent=2)
                return {"status": "error", "message": f"Validator agent returned a non-success response: {error_details}"}

            task = response.root.result
            if not isinstance(task, Task):
                return {"status": "error", "message": "Validator agent response did not contain a valid Task object."}

            # Null-safe check for nested artifacts and parts before access.
            if not task.artifacts or not task.artifacts[0].parts:
                return {"status": "error", "message": "Validator agent response task did not contain any artifacts or parts.", "raw_response": response.model_dump_json()}

            validator_output_str = task.artifacts[0].parts[0].root.text

            if validator_output_str:
                try:
                    clean_json_str = _extract_json_from_markdown(validator_output_str)
                    validator_output_json = json.loads(clean_json_str)
                    return {"status": "success", "validation_result": validator_output_json}
                except json.JSONDecodeError:
                    return {"status": "error", "message": "Failed to parse JSON from validator agent's response.", "raw_response": validator_output_str}

            # If we reach here, the response was successful but the content was empty.
            return {"status": "error", "message": "Validator agent returned an empty response.", "raw_response": response.model_dump_json()}

    except httpx.RequestError as e:
        return {"status": "error", "message": f"Network error calling external validator agent: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"An unexpected error occurred while calling external validator agent: {e}"}