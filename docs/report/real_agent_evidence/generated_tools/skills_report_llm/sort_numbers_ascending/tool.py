from typing import List, Union

def sort_numbers_ascending(numbers: List[Union[int, float]]) -> List[Union[int, float]]:
    """Sort a list of numbers in ascending order.

    Args:
        numbers: A list containing integers and/or floats.

    Returns:
        A new list with the numbers sorted in ascending order.

    Raises:
        TypeError: If the input is not a list or if any element is not an int or float.
    """
    if not isinstance(numbers, list):
        raise TypeError("Input must be a list.")

    for i, item in enumerate(numbers):
        if not isinstance(item, (int, float)):
            raise TypeError(
                f"Element at index {i} is of type {type(item).__name__}, "
                f"expected int or float."
            )

    return sorted(numbers)
