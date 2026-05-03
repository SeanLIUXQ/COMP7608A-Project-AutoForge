def reverse_text(text: str) -> str:
    """
    Return the reversed version of the input string.
    
    Args:
        text: The string to reverse.
        
    Returns:
        The reversed string. Returns an empty string if the input is empty.
        
    Raises:
        TypeError: If the input is not a string.
    """
    if not isinstance(text, str):
        raise TypeError("Input must be a string")
    if text == "":
        return ""
    return text[::-1]
