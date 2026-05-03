def remove_duplicates_preserve_order(values: list) -> list:
    """Return a new list with duplicates removed while preserving the order of first occurrence.

    Args:
        values: A list of hashable items.

    Returns:
        A list containing each unique item from `values` in the order they first appear.
    """
    if not isinstance(values, list):
        raise TypeError("Input must be a list")
    seen = set()
    result = []
    for item in values:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result
