from typing import Any

def count_vowels(text: str) -> int:
    """
    Count the number of vowel characters (a, e, i, o, u) in a string,
    case-insensitively.

    Args:
        text: The input string to examine.

    Returns:
        The integer count of vowels present in the string.

    Raises:
        TypeError: If the input is not a string.
    """
    if not isinstance(text, str):
        raise TypeError(f"Expected a string, got {type(text).__name__}")
    # case-insensitive counting
    lowered = text.lower()
    vowels = {'a', 'e', 'i', 'o', 'u'}
    return sum(1 for char in lowered if char in vowels)
