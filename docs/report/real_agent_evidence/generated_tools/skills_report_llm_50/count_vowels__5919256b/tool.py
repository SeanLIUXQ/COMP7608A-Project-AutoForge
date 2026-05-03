def count_vowels(text: str) -> int:
    """
    Count the number of vowels (a, e, i, o, u) in a given string.

    Args:
        text: The input string to analyze.

    Returns:
        The integer count of vowels found, case-insensitive.

    Raises:
        TypeError: If the input is not a string.
    """
    if not isinstance(text, str):
        raise TypeError("Input must be a string")

    vowels = {'a', 'e', 'i', 'o', 'u'}
    lower_text = text.lower()
    count = 0
    for char in lower_text:
        if char in vowels:
            count += 1
    return count
