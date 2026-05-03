from typing import Any, List

def deduplicate_ordered(values: List[Any]) -> List[Any]:
    """
    Remove duplicate values from a list while preserving the original order
    of first occurrences.

    Args:
        values: A list of hashable elements (strings, numbers, tuples, etc.).

    Returns:
        A new list containing only unique elements, in the order they first appeared.

    Raises:
        ValueError: If the input is not a list.
    """
    if not isinstance(values, list):
        raise ValueError("Input must be a list.")

    seen = set()
    result = []
    for item in values:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result
