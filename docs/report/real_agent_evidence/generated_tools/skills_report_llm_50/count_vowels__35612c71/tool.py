def count_vowels(text: str) -> int:
    """Return the number of vowels (a, e, i, o, u) in the given text, case-insensitive.
    
    Args:
        text: The input string to examine.
    
    Returns:
        The integer count of vowels found.
    
    Raises:
        TypeError: If the input is not a string.
    """
    if not isinstance(text, str):
        raise TypeError("Input must be a string")
    
    # Use lowercase for case-insensitive matching
    lower_text = text.lower()
    vowels = {'a', 'e', 'i', 'o', 'u'}
    count = 0
    for char in lower_text:
        if char in vowels:
            count += 1
    return count
