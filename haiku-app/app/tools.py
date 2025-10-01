import os
import re
import json
import httpx
import logging
from typing import Any
from uuid import uuid4, UUID

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

async def _invoke_a2a_agent(
    base_url: str, prompt_text: str, httpx_client: httpx.AsyncClient
) -> dict:
    """Agnostic helper to call any external A2A agent and handle responses.
    A reusable helper to call an external A2A agent.

    Args:
        base_url: The base URL of the external agent.
        prompt_text: The full text prompt to send to the agent.
        httpx_client: An active httpx.AsyncClient instance.

    Returns:
        A dictionary with the result or an error message.
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
    response = await client.send_message(request)

    # --- Robust Response Handling ---
    logger.info("A2A response: %s", response.model_dump(mode='json', exclude_none=True))
    if not isinstance(response.root, SendMessageSuccessResponse):
        error_details = response.root.error.model_dump_json(indent=2)
        return {"status": "error", "message": f"Agent returned a non-success response: {error_details}"}

    task = response.root.result
    if not isinstance(task, Task):
        return {"status": "error", "message": "Agent response did not contain a valid Task object."}

    # Null-safe check for nested artifacts and parts before access.
    if not task.artifacts or not task.artifacts[0].parts:
        return {"status": "error", "message": "Agent response task did not contain any artifacts or parts.", "raw_response": response.model_dump_json()}

    # Return the raw text content for the specific handlers to parse.
    return {"status": "success", "content": task.artifacts[0].parts[0].root.text}

async def _generic_a2a_tool_handler(
    env_var_name: str, prompt_text: str, response_parser: callable
) -> dict:
    """
    A generic handler for calling an external A2A tool.

    This function encapsulates the logic for:
    1. Reading the agent URL from an environment variable.
    2. Making the A2A call using the agnostic _invoke_a2a_agent helper.
    3. Handling common errors (network, unexpected exceptions).
    4. Passing the successful response content to a specific parser function.

    Args:
        env_var_name: The name of the environment variable holding the agent's URL.
        prompt_text: The text to send to the external agent.
        response_parser: A function that takes the raw text response and processes it.

    Returns:
        A dictionary with the final result or an error.
    """
    base_url = os.getenv(env_var_name)
    if not base_url:
        return {"status": "error", "message": f"{env_var_name} environment variable is not set."}

    try:
        async with httpx.AsyncClient() as httpx_client:
            result = await _invoke_a2a_agent(base_url, prompt_text, httpx_client)

        return response_parser(result)
    except httpx.RequestError as e:
        return {"status": "error", "message": f"Network error calling agent at {env_var_name}: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"An unexpected error occurred calling agent at {env_var_name}: {e}"}

async def validate_haiku_with_external_agent(haiku: str) -> dict:
    """
    Calls an external A2A agent to validate a haiku.
    """
    base_url = os.getenv("HAIKU_VALIDATOR_AGENT_URL", "http://localhost:8002")
    if not base_url:
        return {"status": "error", "message": "HAIKU_VALIDATOR_AGENT_URL environment variable is not set."}

    def _parse_validator_response(result: dict) -> dict:
        """Parses the JSON response from the validator agent."""
        if result["status"] != "success":
            return result
        validator_output_str = result.get("content")
        if not validator_output_str:
            return {"status": "error", "message": "Validator agent returned an empty response.", "raw_response": result}
        try:
            clean_json_str = _extract_json_from_markdown(validator_output_str)
            return {"status": "success", "validation_result": json.loads(clean_json_str)}
        except json.JSONDecodeError:
            return {"status": "error", "message": "Failed to parse JSON from validator agent's response.", "raw_response": validator_output_str}

    return await _generic_a2a_tool_handler("HAIKU_VALIDATOR_AGENT_URL", haiku, _parse_validator_response)

async def call_utility_a2a(prompt: str) -> dict:
    """Calls the external A2A utility agent with a given prompt."""
    base_url = os.getenv("HAIKU_UTILITIES_AGENT_URL", "http://localhost:8002")
    if not base_url:
        return {"status": "error", "message": "HAIKU_UTILITIES_AGENT_URL environment variable is not set."}
    
    def _parse_utility_response(result: dict) -> dict:
        """Handles the plain-text response from the utility agent."""
        if result["status"] != "success":
            return result
        return {"status": "success", "result_text": result.get("content", "")}

    return await _generic_a2a_tool_handler("HAIKU_UTILITIES_AGENT_URL", prompt, _parse_utility_response)