from typing import TypeVar, Iterable, List
from collections.abc import Iterable as ABCIterable

T = TypeVar('T')

def deduplicate_preserving_order(iterable: Iterable[T]) -> List[T]:
    """
    Remove duplicate elements from an iterable, preserving the order of first occurrence.

    Args:
        iterable: An iterable containing hashable elements, possibly with duplicates.

    Returns:
        A list of unique elements in the order they first appear.

    Raises:
        TypeError: If the input is not an iterable.
    """
    if not isinstance(iterable, ABCIterable):
        raise TypeError("Input must be an iterable")
    seen = set()
    result: List[T] = []
    for item in iterable:
        if item not in seen:
            result.append(item)
            seen.add(item)
    return result
