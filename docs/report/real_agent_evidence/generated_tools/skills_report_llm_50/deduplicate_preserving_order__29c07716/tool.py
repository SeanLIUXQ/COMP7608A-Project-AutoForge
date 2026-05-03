from typing import Iterable, List, TypeVar, Any

T = TypeVar('T', bound=Any)

def deduplicate_preserving_order(seq: Iterable[T]) -> List[T]:
    """
    Remove duplicates from an iterable while preserving the original order 
    of first occurrences.

    Args:
        seq: An iterable of hashable elements.

    Returns:
        A list containing all unique elements in the order they first appeared.

    Raises:
        TypeError: If `seq` is not iterable.
    """
    try:
        iterator = iter(seq)
    except TypeError as exc:
        raise TypeError("Input must be an iterable") from exc

    seen = set()
    result = []
    for item in iterator:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result
