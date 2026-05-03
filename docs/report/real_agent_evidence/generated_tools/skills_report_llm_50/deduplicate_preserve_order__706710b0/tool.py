from typing import Iterable, TypeVar

T = TypeVar('T')

def deduplicate_preserve_order(items: Iterable[T]) -> list[T]:
    """Remove duplicates from an iterable while preserving the order of first occurrence.
    
    Works for any element type that supports equality, including unhashable types
    such as dictionaries and lists.
    
    Args:
        items: An iterable of arbitrary elements.
        
    Returns:
        A list with duplicates removed, preserving the original order.
        
    Raises:
        TypeError: If `items` is not iterable.
    """
    try:
        iterator = iter(items)
    except TypeError:
        raise TypeError("Input must be an iterable")
    
    seen: list[T] = []   # list to remember encountered items
    result: list[T] = [] # result preserving first occurrence
    
    for item in iterator:
        # Check if an equal item has already been seen (supports unhashable types)
        if not any(item == x for x in seen):
            seen.append(item)
            result.append(item)
            
    return result
