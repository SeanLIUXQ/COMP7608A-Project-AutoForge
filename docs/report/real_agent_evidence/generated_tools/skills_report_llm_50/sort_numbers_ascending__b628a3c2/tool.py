from typing import List, Union

def sort_numbers_ascending(numbers: list) -> List[Union[int, float]]:
    """Sort a list of numbers in ascending order.

    Args:
        numbers: A list of numbers (int or float).

    Returns:
        A new list containing the numbers sorted in ascending order.

    Raises:
        TypeError: If the input is not a list or if any element is not an int or float.
    """
    if not isinstance(numbers, list):
        raise TypeError(f"Input must be a list, got {type(numbers).__name__}")
    
    for idx, item in enumerate(numbers):
        # Booleans are a subclass of int but typically not considered a number for this purpose
        if isinstance(item, bool):
            raise TypeError(f"Element at index {idx} is bool, expected int or float")
        if not isinstance(item, (int, float)):
            raise TypeError(f"Element at index {idx} is {type(item).__name__}, expected int or float")
    
    return sorted(numbers)
