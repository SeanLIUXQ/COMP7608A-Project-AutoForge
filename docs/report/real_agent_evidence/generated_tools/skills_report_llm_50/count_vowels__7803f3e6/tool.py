def count_vowels(text: str) -> int:
    r"""
    Count the number of vowels (a, e, i, o, u) in a string.

    The count is case-insensitive: both uppercase and lowercase vowels are included.
    Only the letters 'a', 'e', 'i', 'o', 'u' are considered vowels, not 'y' or others.

    Args:
        text: The input string to examine. Must not be None.

    Returns:
        An integer representing the total number of vowel characters found.

    Raises:
        TypeError: If the input is not a string.
    """
    if not isinstance(text, str):
        raise TypeError("Input must be a non-null string")
    cleaned = text.lower()
    vowels = set("aeiou")
    total = 0
    for ch in cleaned:
        if ch in vowels:
            total += 1
    return total
