from typing import List, Union

def sort_numbers_ascending(numbers: List[Union[int, float]]) -> List[Union[int, float]]:
    """
    Return a new list containing the numbers sorted in ascending order.
    
    The input must be a list of integers or floats. Booleans are not accepted 
    because they are not considered plain numbers. The original list is not modified.
    If the list is empty, an empty list is returned.
    
    Args:
        numbers: List of numeric values (int or float).
        
    Returns:
        A new list with the same numbers sorted in ascending order.
        
    Raises:
        TypeError: If the input is not a list or any element is not an int/float
                   (or is a boolean).
    """
    if not isinstance(numbers, list):
        raise TypeError("Input must be a list.")
    for idx, val in enumerate(numbers):
        if type(val) is bool or not isinstance(val, (int, float)):
            raise TypeError(
                f"Element at index {idx} is not a valid number (got {type(val).__name__})."
            )
    if not numbers:
        return []
    return sorted(numbers)
