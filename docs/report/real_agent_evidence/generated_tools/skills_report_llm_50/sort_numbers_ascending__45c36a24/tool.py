from numbers import Number
from typing import List, Union

def sort_numbers_ascending(numbers: List[Union[int, float]]) -> List[Union[int, float]]:
    """
    Sort a list of numbers in ascending order.

    Args:
        numbers: A list of integers or floats.

    Returns:
        A new list containing the numbers sorted in ascending order.

    Raises:
        TypeError: If the input is not a list.
        ValueError: If any element is not an int or float.
    """
    if not isinstance(numbers, list):
        raise TypeError("Input must be a list of numbers.")
    for item in numbers:
        if not isinstance(item, (int, float)):
            raise ValueError(f"All elements must be numeric (int or float). Found: {type(item).__name__}")
    return sorted(numbers)
