from scalestack_sdk import decorators
from typing import Dict, Any
from structlog.stdlib import get_logger

logger = get_logger()

@decorators.aws
def main(input_data: str, **kwargs) -> Dict[str, Any]:
    """
    Tope module - Always returns ATTENZIONE!!!
    
    Args:
        input_data: Any input (will be ignored)
        **kwargs: Additional arguments
    
    Returns:
        Dict with the response "ATTENZIONE!!!"
    """
    logger.info("Tope module executed")
    
    return {
        "response": "ATTENZIONE!!!"
    }