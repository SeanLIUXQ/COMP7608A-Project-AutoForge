from typing import Any, Iterable, List

def deduplicate(items: Iterable[Any]) -> List[Any]:
    """
    Remove duplicates from an iterable while preserving the order of first occurrence.

    The function works with any objects that support equality comparison, including
    unhashable types like lists and dictionaries.

    Args:
        items: An iterable of elements to deduplicate.

    Returns:
        A list of unique elements in the order they first appear.

    Raises:
        TypeError: If *items* is not iterable.
    """
    # Validate that the input is iterable.
    try:
        iter(items)
    except TypeError:
        raise TypeError("items must be iterable")

    seen: list[Any] = []      # list to track elements we have already seen
    result: list[Any] = []    # final list preserving original order

    for item in items:
        # Check whether the item is already in the seen list.
        # Using `in` on a list performs equality checks, which works for
        # both hashable and unhashable objects.
        if item not in seen:
            seen.append(item)
            result.append(item)

    return result
