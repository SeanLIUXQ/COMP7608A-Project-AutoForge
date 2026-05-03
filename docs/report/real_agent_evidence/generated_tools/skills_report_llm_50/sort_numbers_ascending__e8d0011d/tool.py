from typing import List, Union

def sort_numbers_ascending(numbers: List[Union[int, float]]) -> List[Union[int, float]]:
    """
    Return a new list containing the input numbers sorted in ascending order.

    Args:
        numbers: A list that must contain only integers or floats.

    Returns:
        A new sorted list (ascending).  If the input is empty, an empty list is
        returned.

    Raises:
        TypeError: If `numbers` is not a list, or if any element is not an
            instance of `int` or `float`.
    """
    if not isinstance(numbers, list):
        raise TypeError("Input must be a list")
    for idx, item in enumerate(numbers):
        if not isinstance(item, (int, float)):
            raise TypeError(
                f"Element at index {idx} is not int or float: "
                f"{type(item).__name__}"
            )
    return sorted(numbers)
