import string

def count_vowels(text: str) -> int:
    """
    Return the number of vowel characters (a, e, i, o, u) in the given string.

    The function performs a case-insensitive count, treating both uppercase
    and lowercase vowels equally. Only standard English vowels are counted.
    Non-alphabetical characters are ignored.

    Args:
        text: The input string in which to count vowels.

    Returns:
        The total count of vowel characters as an integer.

    Raises:
        TypeError: If `text` is not a string.
    """
    if not isinstance(text, str):
        raise TypeError(f"Expected a string, got {type(text).__name__}")

    vowels = {'a', 'e', 'i', 'o', 'u'}
    lowercase_text = text.lower()

    return sum(1 for char in lowercase_text if char in vowels)
