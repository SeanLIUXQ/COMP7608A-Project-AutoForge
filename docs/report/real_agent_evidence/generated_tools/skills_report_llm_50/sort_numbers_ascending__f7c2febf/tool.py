import numbers
from typing import List, Union

def sort_numbers_ascending(values: List[Union[int, float]]) -> List[Union[int, float]]:
    """
    Return a new list containing the given numbers sorted in ascending order.

    Args:
        values: A list of numbers (int or float). Must not be empty; all
                elements must be numeric and the list itself must be a list.

    Returns:
        A new list with the numbers sorted from smallest to largest.

    Raises:
        TypeError: If the input is not a list or if any element is not
                   an int or float.
    """
    if not isinstance(values, list):
        raise TypeError(f"Expected a list, got {type(values).__name__}")

    for i, item in enumerate(values):
        if not isinstance(item, (int, float)):
            raise TypeError(
                f"Element at index {i} is {type(item).__name__}, "
                f"expected int or float"
            )

    return sorted(values)
