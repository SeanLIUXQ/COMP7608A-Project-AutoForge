def reverse_text(text: str) -> str:
    """Return the reversed version of the input string.

    Args:
        text: The string to reverse.

    Returns:
        The reversed string.

    Raises:
        TypeError: If `text` is not a string.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    # Empty string is handled correctly by slicing, yielding an empty string.
    return text[::-1]
