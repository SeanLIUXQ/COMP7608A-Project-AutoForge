def reverse_text(s: str) -> str:
    """
    Return the input string with its characters in reverse order.

    Args:
        s: The string to reverse.

    Returns:
        The reversed string.

    Raises:
        TypeError: If the input is not a string.
    """
    if not isinstance(s, str):
        raise TypeError("Input must be a string")
    # Convert to a list of characters, reverse in place, then join back to a string
    chars = list(s)
    chars.reverse()
    return "".join(chars)
