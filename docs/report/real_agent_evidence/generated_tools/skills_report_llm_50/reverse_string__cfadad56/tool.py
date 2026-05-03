def reverse_string(s: str) -> str:
    """Return the reversed version of the input string.

    Args:
        s: The string to reverse.

    Returns:
        The reversed string, using slicing `s[::-1]`.

    Raises:
        TypeError: If `s` is not a string.
    """
    if not isinstance(s, str):
        raise TypeError("Input must be a string")
    if len(s) == 0:
        return ""
    return s[::-1]
