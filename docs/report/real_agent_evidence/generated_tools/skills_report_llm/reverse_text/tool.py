def reverse_text(text: str) -> str:
    """Return the reversed version of the input string.

    Args:
        text: The string to be reversed.

    Returns:
        The reversed string.

    Raises:
        TypeError: If `text` is not a string.
    """
    if not isinstance(text, str):
        raise TypeError("Input must be a string")
    return text[::-1]
