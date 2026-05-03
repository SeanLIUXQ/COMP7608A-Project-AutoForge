from typing import List, Union

def sort_numbers_ascending(numbers: List[Union[int, float]]) -> List[Union[int, float]]:
    """
    Sort a list containing only numbers (int or float) in ascending order.

    This function strictly accepts int and float values; booleans (which are a
    subclass of int) are rejected to avoid unintended input.  An empty list
    returns an empty list.

    Args:
        numbers: List of numbers (int and float only).

    Returns:
        A new list with the numbers sorted in ascending order.

    Raises:
        TypeError: If `numbers` is not a list, or if any element is not an
                   int or float (including bool).
    """
    if not isinstance(numbers, list):
        raise TypeError("Input must be a list.")

    # Early exit for empty list
    if len(numbers) == 0:
        return []

    # Validate all elements, explicitly rejecting bool
    for x in numbers:
        if type(x) not in (int, float):
            raise TypeError(
                f"Element {x!r} is not an int or float. "
                "Only int and float values are allowed."
            )

    # Return a new sorted list (sorted() already creates a copy)
    return sorted(numbers)
