def reverse_text(text: str) -> str:
    """Reverse the given string and return the result.

    Args:
        text: A string to be reversed.

    Returns:
        The reversed string.

    Raises:
        TypeError: If the input is not a string.
    """
    if not isinstance(text, str):
        raise TypeError("Input must be a string")
    if len(text) == 0:
        return ""
    return text[::-1]
