from scalestack_sdk import decorators

@decorators.aws
def main(first_number: int, second_number: int, **kwargs):
    # Convert to ensure correct types with error handling
    try:
        first_number = int(first_number) if not isinstance(first_number, int) else first_number
    except (ValueError, TypeError):
        return {"error": "Invalid first_number value"}
    
    try:
        second_number = int(second_number) if not isinstance(second_number, int) else second_number
    except (ValueError, TypeError):
        return {"error": "Invalid second_number value"}
    
    # Calculate the sum
    result = first_number + second_number
    
    return {"sum": result}