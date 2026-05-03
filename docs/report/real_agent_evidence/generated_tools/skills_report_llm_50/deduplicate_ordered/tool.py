from typing import Iterable, List, TypeVar

T = TypeVar("T")

def deduplicate_ordered(seq: Iterable[T]) -> List[T]:
    """Remove duplicates from an iterable while preserving the order of first occurrence.

    Works for any iterable, including those containing unhashable elements
    (e.g., lists, dicts, sets).

    Args:
        seq: An iterable of elements.

    Returns:
        A new list containing the first occurrence of each distinct element,
        in the order they first appeared.

    Raises:
        TypeError: If *seq* is not iterable.
    """
    # Validate that seq is iterable
    try:
        iterator = iter(seq)
    except TypeError:
        raise TypeError(f"Input must be an iterable, got {type(seq)}")

    # Use a list instead of a set to support unhashable types
    seen: List[T] = []
    result: List[T] = []

    for item in seq:
        if item not in seen:
            seen.append(item)
            result.append(item)

    return result
