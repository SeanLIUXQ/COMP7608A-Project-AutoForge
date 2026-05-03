from typing import List

def moving_average(values: List[float], window: int) -> List[float]:
    """
    Compute the moving average of a list of numbers over a given window.

    Args:
        values: A list of numeric values (int or float).
        window: Positive integer specifying the number of consecutive elements
                to average at each step.

    Returns:
        A list of moving averages (floats). Each element is the arithmetic mean
        of a window of size `window`. If `window > len(values)`, an empty list
        is returned.

    Raises:
        TypeError: If `values` is not a list, contains non-numeric elements,
                   or `window` is not an integer.
        ValueError: If `window` is not positive.
    """
    # --- input validation ---
    if not isinstance(values, list):
        raise TypeError("values must be a list")
    if not isinstance(window, int):
        raise TypeError("window must be an integer")
    if window <= 0:
        raise ValueError("window must be a positive integer")

    # check that all elements are int or float
    for i, x in enumerate(values):
        if not isinstance(x, (int, float)):
            raise TypeError(
                f"Element at index {i} is not a number (int or float), "
                f"got {type(x).__name__}"
            )

    n = len(values)
    if window > n:
        return []

    # --- compute moving averages ---
    result: List[float] = []
    for i in range(n - window + 1):
        window_sum = sum(values[i:i + window])
        result.append(window_sum / window)

    return result
