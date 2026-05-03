def sort_numbers_ascending(numbers: list[float]) -> list[float]:
    """Sort a list of numbers in ascending order.

    Args:
        numbers: A list of numeric values (integers or floats).

    Returns:
        A new list containing the input numbers sorted in ascending order.

    Raises:
        TypeError: If the input is not a list or if any element is not an int or float.
    """
    if not isinstance(numbers, list):
        raise TypeError("Input must be a list.")
    for item in numbers:
        # Allow int and float, but exclude bool (which is a subclass of int)
        if not (isinstance(item, (int, float)) and not isinstance(item, bool)):
            raise TypeError("All elements must be numbers (int or float).")
    return sorted(numbers)
