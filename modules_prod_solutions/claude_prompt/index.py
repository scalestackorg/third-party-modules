import requests
from scalestack_sdk import decorators
from pydantic import SecretStr
from structlog.stdlib import get_logger
from typing import Optional, Literal

logger = get_logger()

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"

@decorators.aws(default_secret="ANTHROPIC_API_KEY")
def main(
    prompt: str,
    system_prompt: Optional[str] = None,
    model: Literal[
        "claude-3-5-sonnet-20241022",
        "claude-3-5-haiku-20241022", 
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307"
    ] = "claude-3-5-haiku-20241022",
    max_tokens: int = 1024,
    temperature: float = 0.7,
    api_key: SecretStr = None,
    **kwargs
) -> dict:
    """
    Send a generic prompt to Claude and return the response.
    
    Args:
        prompt: The user prompt to send to Claude
        system_prompt: Optional system message to guide Claude's behavior
        model: The Claude model to use
        max_tokens: Maximum tokens in the response
        temperature: Controls randomness (0-1, higher = more creative)
        api_key: Anthropic API key
    
    Returns:
        dict: Contains the Claude response and metadata
    """
    
    # Type conversion with error handling
    try:
        max_tokens = int(max_tokens) if not isinstance(max_tokens, int) else max_tokens
    except (ValueError, TypeError):
        logger.error("Invalid max_tokens value", max_tokens=max_tokens)
        return {"error": "Invalid max_tokens value"}
    
    try:
        temperature = float(temperature) if not isinstance(temperature, float) else temperature
        temperature = max(0.0, min(1.0, temperature))  # Clamp between 0 and 1
    except (ValueError, TypeError):
        logger.error("Invalid temperature value", temperature=temperature)
        return {"error": "Invalid temperature value"}
    
    if not api_key:
        logger.error("No API key provided")
        return {"error": "API key is required"}
    
    headers = {
        "x-api-key": api_key.get_secret_value(),
        "anthropic-version": ANTHROPIC_VERSION,
        "content-type": "application/json"
    }
    
    # Build the request payload
    payload = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    
    # Add system prompt if provided
    if system_prompt:
        payload["system"] = system_prompt
    
    try:
        logger.info(
            "Sending request to Claude",
            model=model,
            prompt_length=len(prompt),
            has_system_prompt=bool(system_prompt)
        )
        
        response = requests.post(
            ANTHROPIC_API_URL,
            headers=headers,
            json=payload,
            timeout=60
        )
        
        response.raise_for_status()
        data = response.json()
        
        # Extract the response content
        if "content" in data and len(data["content"]) > 0:
            response_text = data["content"][0].get("text", "")
        else:
            response_text = ""
            logger.warning("Empty response from Claude")
        
        # Extract usage information
        usage = data.get("usage", {})
        
        logger.info(
            "Successfully received response from Claude",
            response_length=len(response_text),
            input_tokens=usage.get("input_tokens"),
            output_tokens=usage.get("output_tokens")
        )
        
        return {
            "response": response_text,
            "model_used": data.get("model"),
            "input_tokens": usage.get("input_tokens"),
            "output_tokens": usage.get("output_tokens"),
            "total_tokens": usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
            "stop_reason": data.get("stop_reason")
        }
        
    except requests.exceptions.Timeout:
        logger.error("Request to Claude timed out")
        return {"error": "Request timed out"}
    
    except requests.exceptions.HTTPError as e:
        error_msg = f"HTTP error: {e.response.status_code}"
        try:
            error_data = e.response.json()
            error_msg = f"{error_msg} - {error_data.get('error', {}).get('message', '')}"
        except:
            pass
        logger.error("HTTP error from Claude", error=error_msg, status_code=e.response.status_code)
        return {"error": error_msg}
    
    except Exception as e:
        logger.error("Unexpected error calling Claude", error=str(e))
        return {"error": f"Unexpected error: {str(e)}"}