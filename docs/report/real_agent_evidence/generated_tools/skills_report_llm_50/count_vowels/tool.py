def count_vowels(s: str) -> int:
    """
    Count the number of vowels (a, e, i, o, u) in a string, case-insensitively.

    Args:
        s: The input string to analyze.

    Returns:
        The integer count of vowel characters.

    Raises:
        TypeError: If the input is not a string.
    """
    if not isinstance(s, str):
        raise TypeError("Input must be a string")
    lower = s.lower()
    vowels = {'a', 'e', 'i', 'o', 'u'}
    count = 0
    for ch in lower:
        if ch in vowels:
            count += 1
    return count
