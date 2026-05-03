def remove_duplicates_preserve_order(iterable):
    """
    Remove duplicate elements from an iterable, preserving the order of first occurrence.

    Args:
        iterable: An iterable of hashable items.

    Returns:
        A list containing each unique item in the original order.

    Raises:
        TypeError: If the input is not iterable.
    """
    # Validate that the input is iterable
    try:
        iterator = iter(iterable)
    except TypeError:
        raise TypeError("Input must be an iterable")

    seen = set()
    result = []
    for item in iterator:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result
