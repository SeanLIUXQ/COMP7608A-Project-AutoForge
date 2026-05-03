def count_vowels(text: str) -> int:
    """
    Return the number of vowel characters (a, e, i, o, u) in the given string,
    ignoring case.

    Args:
        text: Input string to analyze.

    Returns:
        Integer count of vowels found.

    Raises:
        TypeError: If `text` is not a string.
    """
    if not isinstance(text, str):
        raise TypeError(f"Expected a string, got {type(text).__name__}")

    vowels = {'a', 'e', 'i', 'o', 'u'}
    count = 0
    for char in text.lower():
        if char in vowels:
            count += 1
    return count
