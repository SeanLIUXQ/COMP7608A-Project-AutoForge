from typing import List, Union

def compute_moving_average(values: List[Union[int, float]], window: int) -> List[float]:
    """
    Compute the simple moving average of a list of numbers over a given window.

    Args:
        values: A list of integers or floats. Booleans are not accepted.
        window: A strictly positive integer window size, not larger than the
                length of values.

    Returns:
        A list of floats representing the moving averages, one for each valid
        window. The length of the output is len(values) - window + 1.

    Raises:
        TypeError: If values is not a list, contains non-numeric entries,
                   contains booleans, or window is not an integer (or is a bool).
        ValueError: If window is not positive or if it exceeds len(values).
    """
    # --- input validation ---
    if not isinstance(values, list):
        raise TypeError("values must be a list.")
    for x in values:
        if isinstance(x, bool):
            raise TypeError("values must contain only int or float, not bool.")
        if not isinstance(x, (int, float)):
            raise TypeError("values must contain only int or float.")
    if isinstance(window, bool):
        raise TypeError("window must be an int, not bool.")
    if not isinstance(window, int):
        raise TypeError("window must be an integer.")
    if window <= 0:
        raise ValueError("window must be a positive integer.")
    n = len(values)
    if window > n:
        raise ValueError("window must not exceed the length of values.")

    # --- sliding window computation ---
    result = []
    # initial window sum
    win_sum = sum(values[:window])
    result.append(win_sum / window)

    # slide the window, updating the sum in O(1) per step
    for i in range(1, n - window + 1):
        win_sum += values[i + window - 1] - values[i - 1]
        result.append(win_sum / window)

    return result
