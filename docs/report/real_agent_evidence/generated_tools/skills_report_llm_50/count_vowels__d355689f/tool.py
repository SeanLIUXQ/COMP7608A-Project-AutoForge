def count_vowels(text: str) -> int:
    """
    Count the number of vowels (a, e, i, o, u) in the given string, case-insensitive.

    Args:
        text: The input string in which to count vowels.

    Returns:
        The integer count of vowel characters.

    Raises:
        TypeError: If `text` is not a string.
    """
    if not isinstance(text, str):
        raise TypeError("Input must be a string.")
    vowels = {'a', 'e', 'i', 'o', 'u'}
    return sum(1 for char in text.lower() if char in vowels)
