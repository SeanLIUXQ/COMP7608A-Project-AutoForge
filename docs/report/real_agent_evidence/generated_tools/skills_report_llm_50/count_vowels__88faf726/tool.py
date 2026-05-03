import unicodedata
from typing import Any

def count_vowels(s: str) -> int:
    """
    Count the number of vowels in a string (case-insensitive).

    Vowels considered: a, e, i, o, u.
    Handles basic ASCII vowels; Unicode letters are normalized to
    their base form for counting (e.g., accented vowels decompose).

    Args:
        s: The input string.

    Returns:
        An integer count of vowels found.

    Raises:
        TypeError: If the input is not a string.
    """
    if not isinstance(s, str):
        raise TypeError("Input must be a string")

    # Normalize to NFKD to decompose accented characters, then convert to ASCII
    # so that letters like 'é' are reduced to 'e' before counting.
    normalized = unicodedata.normalize('NFKD', s)
    ascii_text = normalized.encode('ascii', 'ignore').decode('ascii')
    
    lower_text = ascii_text.lower()
    vowels = {'a', 'e', 'i', 'o', 'u'}
    return sum(1 for ch in lower_text if ch in vowels)
