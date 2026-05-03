def count_vowels(s: str) -> int:
    """
    Return the number of vowels (a, e, i, o, u) in the input string,
    treating uppercase and lowercase letters as equivalent.

    Args:
        s: The string to examine.

    Returns:
        The total count of vowel characters found.

    Raises:
        TypeError: If the input is not a string.
    """
    if not isinstance(s, str):
        raise TypeError("Input must be a string.")
    vowels = set("aeiou")
    return sum(1 for ch in s.lower() if ch in vowels)
