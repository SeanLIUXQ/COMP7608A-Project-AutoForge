from typing import List, Any

def deduplicate_list_preserve_first(lst: List[Any]) -> List[Any]:
    """
    Return a new list with duplicate elements removed, preserving the order of first occurrence.

    Args:
        lst: A list of elements (must be hashable).

    Returns:
        A list containing only the first occurrence of each element, in original order.

    Raises:
        TypeError: If the input is not a list.
    """
    if not isinstance(lst, list):
        raise TypeError(f"Expected a list, got {type(lst).__name__}")

    seen = set()
    result = []
    for item in lst:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result
