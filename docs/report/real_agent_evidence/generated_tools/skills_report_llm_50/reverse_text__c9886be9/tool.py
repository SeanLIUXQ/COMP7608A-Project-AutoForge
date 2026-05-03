def reverse_text(text: str) -> str:
    """Return the reversed string.

    Args:
        text: A string to reverse.

    Returns:
        The reversed string. If the input is empty, returns an empty string.

    Raises:
        TypeError: If `text` is not a string.
    """
    if not isinstance(text, str):
        raise TypeError("Input must be a string")
    if text == "":
        return ""
    return text[::-1]
