def reverse_text(text: str) -> str:
    """
    Return the reversed copy of the input string.

    Args:
        text: The string to reverse. Must be a `str`.

    Returns:
        A new string containing the characters of `text` in reverse order.
        If `text` is empty, an empty string is returned.

    Raises:
        TypeError: If `text` is not a string.
    """
    if not isinstance(text, str):
        raise TypeError("Input must be a string")
    return text[::-1]
