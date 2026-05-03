def reverse_string(s: str) -> str:
    """Reverse a given string.

    Args:
        s: The string to reverse.

    Returns:
        The reversed string.

    Raises:
        TypeError: If `s` is not a string.
    """
    if not isinstance(s, str):
        raise TypeError(f"Expected a string, got {type(s).__name__}")
    return s[::-1]
