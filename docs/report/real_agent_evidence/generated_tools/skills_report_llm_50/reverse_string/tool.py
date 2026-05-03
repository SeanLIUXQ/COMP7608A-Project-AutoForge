from typing import Any

def reverse_string(text: str) -> str:
    """
    Return the reverse of the input string.

    Args:
        text: The string to reverse.

    Returns:
        The reversed string.

    Raises:
        TypeError: If the provided argument is not a string.
    """
    if not isinstance(text, str):
        raise TypeError(f"Expected a string, but got {type(text).__name__}.")
    return text[::-1]
