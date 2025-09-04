import requests
from scalestack_sdk import decorators
from pydantic import SecretStr
from structlog.stdlib import get_logger
from typing import Optional, Literal

PERPLEXITY_URL = "https://api.perplexity.ai/chat/completions"
HEADERS = {"Content-Type": "application/json"}
logger = get_logger()

@decorators.aws
def main(
    prompt: str,
    temperature: float,
    model: Literal["sonar", "sonar-pro", "sonar-deep-research", "sonar-reasoning", "sonar-reasoning-pro"],
    api_key: SecretStr,
    **kwargs
):
    # Convert temperature to ensure correct type with error handling
    try:
        temperature = float(temperature) if not isinstance(temperature, float) else temperature
    except (ValueError, TypeError):
        logger.error("Invalid temperature value", temperature=temperature)
        return {"response": "Error: Invalid temperature value"}
    
    # Validate temperature range (0-2 for Perplexity API)
    if not 0 <= temperature <= 2:
        logger.warning("Temperature out of range, clamping to valid range", temperature=temperature)
        temperature = max(0, min(2, temperature))
    
    # Prepare the request payload
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": temperature
    }
    
    headers = {
        **HEADERS,
        "Authorization": f"Bearer {api_key.get_secret_value()}"
    }
    
    try:
        response = requests.post(
            PERPLEXITY_URL,
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        # Extract the response content
        if data.get("choices") and len(data["choices"]) > 0:
            content = data["choices"][0].get("message", {}).get("content", "")
            
            # Also capture usage information if available
            usage = data.get("usage", {})
            
            logger.info(
                "Perplexity API call successful",
                model=model,
                temperature=temperature,
                prompt_tokens=usage.get("prompt_tokens"),
                completion_tokens=usage.get("completion_tokens")
            )
            
            return {
                "response": content,
                "model_used": model,
                "total_tokens": usage.get("total_tokens", 0)
            }
        else:
            logger.error("Unexpected response format from Perplexity API", response_data=data)
            return {"response": "Error: Unexpected response format from API"}
            
    except requests.exceptions.Timeout:
        logger.error("Request to Perplexity API timed out", prompt=prompt[:100])
        return {"response": "Error: Request timed out"}
    except requests.exceptions.HTTPError as e:
        logger.error("HTTP error from Perplexity API", status_code=e.response.status_code, error=str(e))
        return {"response": f"Error: API returned status code {e.response.status_code}"}
    except Exception as e:
        logger.error("Unexpected error calling Perplexity API", error=str(e))
        return {"response": f"Error: {str(e)}"}