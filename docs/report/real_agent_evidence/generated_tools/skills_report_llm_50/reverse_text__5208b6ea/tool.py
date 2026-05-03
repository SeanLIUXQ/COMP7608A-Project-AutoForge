def reverse_text(s: str) -> str:
    """Reverse the given string.

    Args:
        s: The string to be reversed.

    Returns:
        The reversed string. For an empty string, an empty string is returned.

    Raises:
        TypeError: If `s` is not a string.
    """
    if not isinstance(s, str):
        raise TypeError("Input must be a string")
    return s[::-1]
