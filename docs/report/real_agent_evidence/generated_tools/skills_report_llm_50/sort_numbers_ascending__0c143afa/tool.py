import typing

def sort_numbers_ascending(numbers: list[int | float]) -> list[int | float]:
    """
    Return a new list containing all numbers from the input, sorted in ascending order.

    Args:
        numbers: A list of numbers (int or float).

    Returns:
        A new list of numbers sorted in ascending order.

    Raises:
        TypeError: If the input is not a list or if any element is not an int or float.
    """
    if not isinstance(numbers, list):
        raise TypeError(f"Input must be a list, got {type(numbers).__name__}")
    # Validate each element
    for i, val in enumerate(numbers):
        if not isinstance(val, (int, float)):
            raise TypeError(
                f"Element at index {i} is not a number (int or float): {type(val).__name__}"
            )
    # Create a shallow copy and sort it
    sorted_copy = sorted(numbers)
    return sorted_copy
