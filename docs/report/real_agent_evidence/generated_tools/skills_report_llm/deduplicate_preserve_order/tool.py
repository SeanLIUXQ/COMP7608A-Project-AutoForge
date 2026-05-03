from typing import Iterable, TypeVar, List

T = TypeVar('T')

def deduplicate_preserve_order(sequence: Iterable[T]) -> List[T]:
    """
    Remove duplicates from an iterable while preserving the order of first occurrence.

    Args:
        sequence: An iterable (e.g., list, tuple, string) whose elements are hashable.

    Returns:
        A list of unique elements in the order they first appeared.

    Raises:
        TypeError: If the input is not iterable.
    """
    # Validate that the input is iterable
    if not hasattr(sequence, '__iter__'):
        raise TypeError("Input must be an iterable (list, tuple, string, etc.)")

    seen = set()
    result: List[T] = []

    for item in sequence:
        if item not in seen:
            result.append(item)
            seen.add(item)

    return result
