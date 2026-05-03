def add_two_numbers(a: int, b: int) -> int:
    """
    Returns the sum of two integers.

    Args:
        a: The first integer.
        b: The second integer.

    Returns:
        The sum of a and b as an integer.

    Raises:
        TypeError: If either input is not an integer.
    """
    if not isinstance(a, int) or not isinstance(b, int):
        raise TypeError("Both arguments must be integers")
    return a + b
