from typing import Iterable, Any


def deduplicate_preserve_order(sequence: Iterable[Any]) -> list[Any]:
    """
    Return a list of unique elements from the input iterable,
    preserving the order of first appearance.

    Elements must be hashable (e.g., numbers, strings, tuples of hashables);
    unhashable elements will cause a TypeError during insertion.

    Args:
        sequence: An iterable of hashable items.

    Returns:
        A new list containing each distinct element exactly once,
        in the order they first appear in the input.

    Raises:
        TypeError: If the input is not iterable or contains unhashable items.
    """
    try:
        it = iter(sequence)
    except TypeError:
        raise TypeError("Input must be an iterable") from None

    seen = set()
    result = []
    for item in it:
        if item not in seen:
            seen.add(item)
            result.append(item)

    return result
