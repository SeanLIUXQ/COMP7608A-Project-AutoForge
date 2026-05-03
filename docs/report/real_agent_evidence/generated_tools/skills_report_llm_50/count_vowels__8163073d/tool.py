from typing import Set

def count_vowels(s: str) -> int:
    """
    Count the number of vowel characters (a, e, i, o, u) in the input string,
    ignoring case. Non-letter characters are not counted.

    Args:
        s: A string to analyze.

    Returns:
        The count of vowels as an integer.

    Raises:
        TypeError: If the input is not a string.
    """
    if not isinstance(s, str):
        raise TypeError(f"Expected a string, got {type(s).__name__}")
    
    vowels: Set[str] = {'a', 'e', 'i', 'o', 'u'}
    return sum(1 for ch in s.lower() if ch in vowels)
