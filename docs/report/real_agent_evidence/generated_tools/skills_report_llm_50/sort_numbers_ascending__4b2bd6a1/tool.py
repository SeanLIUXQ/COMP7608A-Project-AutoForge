from typing import List, Union

def sort_numbers_ascending(numbers: List[Union[int, float]]) -> List[Union[int, float]]:
    """
    Return a new list containing the numbers sorted in ascending order.

    Args:
        numbers: A list of numeric elements (integers or floats). Booleans are
            not accepted because they are not considered plain numbers.

    Returns:
        A new list with the elements sorted from smallest to largest.

    Raises:
        TypeError: If the input is not a list.
        ValueError: If any element is not an int or float (or is a bool).
    """
    if not isinstance(numbers, list):
        raise TypeError("Input must be a list")

    for i, val in enumerate(numbers):
        if isinstance(val, bool) or not isinstance(val, (int, float)):
            raise ValueError(
                f"Element at index {i} is {type(val).__name__}, expected int or float"
            )

    # sorted() returns a new list, leaving the original unchanged
    return sorted(numbers)
