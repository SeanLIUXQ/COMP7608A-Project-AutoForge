from typing import List, Union

def sort_numbers_ascending(numbers: List[Union[int, float]]) -> List[Union[int, float]]:
    """
    Sort a list of numbers in ascending order.

    Args:
        numbers: A list containing only integers and/or floats.

    Returns:
        A new list with the elements sorted in ascending order.

    Raises:
        TypeError: If the input is not a list, or if any element is not a number.
    """
    if not isinstance(numbers, list):
        raise TypeError(f"Expected a list, but got {type(numbers).__name__}")

    for i, item in enumerate(numbers):
        if not isinstance(item, (int, float)):
            raise TypeError(
                f"All elements must be int or float, but element at index {i} "
                f"is {type(item).__name__}"
            )

    # `sorted` returns a new list; booleans are a subclass of int and considered numbers
    return sorted(numbers)
