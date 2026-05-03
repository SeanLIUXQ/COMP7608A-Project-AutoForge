from typing import Iterable, Hashable

def remove_duplicates_preserve_order(sequence: Iterable[Hashable]) -> list[Hashable]:
    """
    Return a list of unique elements from the input sequence, preserving the
    order of first occurrences.

    Elements must be hashable. Raises TypeError if the input is not iterable
    or contains unhashable items.

    Args:
        sequence: An iterable of hashable elements.

    Returns:
        A list of the unique elements in the order they first appeared.
        Returns an empty list if the input is empty.
    """
    # Validate that the input is iterable
    try:
        iterator = iter(sequence)
    except TypeError:
        raise TypeError("Input must be an iterable") from None

    seen = set()
    result = []

    for item in iterator:
        if item not in seen:
            seen.add(item)
            result.append(item)

    return result
