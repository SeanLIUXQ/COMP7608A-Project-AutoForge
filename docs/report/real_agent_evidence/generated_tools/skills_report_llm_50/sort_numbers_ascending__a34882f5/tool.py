from typing import List, Union

def sort_numbers_ascending(numbers: List[Union[int, float]]) -> List[Union[int, float]]:
    """
    Sort a list of numbers (int or float) in ascending order.

    Args:
        numbers: A list containing only integers and/or floats.

    Returns:
        A new list with the numbers sorted in ascending order.

    Raises:
        TypeError: If `numbers` is not a list or if any element is not an int or float.
    """
    if not isinstance(numbers, list):
        raise TypeError(f"Expected a list, got {type(numbers).__name__}")

    for i, x in enumerate(numbers):
        if not isinstance(x, (int, float)):
            raise TypeError(f"Element at index {i} is not a number: {x!r} (type {type(x).__name__})")

    return sorted(numbers)
