def count_vowels(s: str) -> int:
    """
    Count the number of English vowel characters in a string.

    Args:
        s: Input string to examine.

    Returns:
        Integer count of characters that are vowels (a, e, i, o, u), 
        case-insensitive.

    Raises:
        TypeError: If s is not a string.
    """
    if not isinstance(s, str):
        raise TypeError("Input must be a string")

    lower_s = s.lower()
    vowels = {'a', 'e', 'i', 'o', 'u'}
    return sum(1 for ch in lower_s if ch in vowels)
