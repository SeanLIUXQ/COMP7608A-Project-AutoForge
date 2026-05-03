def count_vowels(text: str) -> int:
    """Return the number of vowels (a, e, i, o, u) in the input string, ignoring case."""
    if not isinstance(text, str):
        raise TypeError("Input must be a string.")
    lower = text.lower()
    vowels = {'a', 'e', 'i', 'o', 'u'}
    return sum(1 for ch in lower if ch in vowels)
