from typing import List, Union

def sort_numbers_ascending(numbers: List[Union[int, float]]) -> List[Union[int, float]]:
    """
    Sort a list of numbers (int or float) in ascending order and return a new sorted list.

    Args:
        numbers: A list containing only numeric values (int or float).

    Returns:
        A new list with the numbers sorted in ascending order.

    Raises:
        TypeError: If the input is not a list, or if any element is not an int or float.
    """
    if not isinstance(numbers, list):
        raise TypeError("Input must be a list")
    for idx, num in enumerate(numbers):
        if not isinstance(num, (int, float)):
            raise TypeError(
                f"Element at index {idx} is not a number (int/float): {type(num)}"
            )
    return sorted(numbers)
