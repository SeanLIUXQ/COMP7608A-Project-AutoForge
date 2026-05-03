def remove_duplicates_preserve_order(items: list) -> list:
    """
    Remove duplicates from a list while preserving the order of first occurrence.

    Supports any element type, including unhashable types like dicts and lists.

    Args:
        items: A list of elements. Must be a list.

    Returns:
        A new list with duplicates removed, maintaining the original order of
        first occurrence.

    Raises:
        ValueError: If `items` is not a list.
    """
    if not isinstance(items, list):
        raise ValueError("Input must be a list.")

    seen = []  # use a list to handle unhashable types via equality
    result = []
    for item in items:
        if item not in seen:
            seen.append(item)
            result.append(item)
    return result
