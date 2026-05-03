def reverse_text(text: str) -> str:
    """
    Return the reversed version of the input string.

    Args:
        text: A string to be reversed.

    Returns:
        The reversed string.

    Raises:
        TypeError: If `text` is not a string.
    """
    if not isinstance(text, str):
        raise TypeError(f"Expected a string, got {type(text).__name__}")
    return text[::-1]
