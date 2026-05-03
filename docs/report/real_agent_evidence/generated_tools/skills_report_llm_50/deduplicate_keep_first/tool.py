from typing import Any

def deduplicate_keep_first(lst: list) -> list:
    """
    Return a new list containing the unique elements of `lst` in the order they first appear.

    Works with both hashable (e.g., int, str, tuple) and unhashable elements (e.g., list, dict).
    Raises TypeError if `lst` is not a list.
    """
    if not isinstance(lst, list):
        raise TypeError("Input must be a list.")
    
    output = []
    seen_set = set()          # for hashable elements
    seen_unhashable = []      # for unhashable elements (compared by equality)
    
    for item in lst:
        try:
            if item not in seen_set:
                seen_set.add(item)
                output.append(item)
        except TypeError:
            # item is unhashable (e.g., dict, list)
            # use linear scan over previously seen unhashable items
            if item not in seen_unhashable:
                seen_unhashable.append(item)
                output.append(item)
                
    return output
