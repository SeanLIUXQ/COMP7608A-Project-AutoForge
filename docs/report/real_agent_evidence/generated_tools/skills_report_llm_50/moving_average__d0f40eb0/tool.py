from typing import List, Union

def moving_average(values: List[Union[float, int]], window: int) -> List[float]:
    """
    Compute the simple moving average of a series using a sliding window.

    Args:
        values: A non-empty list of numeric values (int or float).
        window: A positive integer window size, not larger than len(values).

    Returns:
        A list of moving average values, each as a float. The length is
        len(values) - window + 1.

    Raises:
        ValueError: if values is empty, window <= 0, or window > len(values).
        TypeError: if any element in values is not an int or float, or if
                   window is not an integer.
    """
    # Validate inputs thoroughly
    if not isinstance(values, list):
        raise TypeError("values must be a list")
    if not values:
        raise ValueError("values must not be empty")

    if not isinstance(window, int):
        raise TypeError("window must be an integer")
    if window <= 0:
        raise ValueError("window must be a positive integer")
    if window > len(values):
        raise ValueError(f"window ({window}) cannot be larger than the number of values ({len(values)})")

    for i, val in enumerate(values):
        if not isinstance(val, (int, float)):
            raise TypeError(f"values[{i}] must be int or float, got {type(val).__name__}")

    # Compute moving averages using a list comprehension and slicing
    n = len(values)
    return [sum(values[i:i + window]) / window for i in range(n - window + 1)]
