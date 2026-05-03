from typing import Any, List

def deduplicate_preserve_order(lst: list) -> list:
    """
    Return a new list containing the unique elements of `lst` in their first occurrence order.

    The function preserves the original order and removes all but the first occurrence
    of each element. Elements must be hashable; otherwise a TypeError will be raised
    during membership testing.

    Args:
        lst: Input list of elements.

    Returns:
        A new list of unique elements in the order they first appear.

    Raises:
        TypeError: If `lst` is not a list.
    """
    if not isinstance(lst, list):
        raise TypeError("Input must be a list.")
    seen = set()
    result: List[Any] = []
    for item in lst:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result
