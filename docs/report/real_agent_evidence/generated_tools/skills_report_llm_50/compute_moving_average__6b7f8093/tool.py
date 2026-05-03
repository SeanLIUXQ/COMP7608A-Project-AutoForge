from typing import List, Union
import numbers

def compute_moving_average(series: List[Union[int, float]], window: int) -> List[float]:
    """Compute the simple moving average (SMA) for a series of numbers.

    Args:
        series: A list of numeric values (int or float).
        window: The number of consecutive elements to average (must be a positive integer).

    Returns:
        A list of floats representing the moving averages. If the window size
        exceeds the length of `series`, an empty list is returned.

    Raises:
        ValueError: If `series` is not a list of numbers or `window` is not a positive integer.
        TypeError: If any element in `series` is not numeric.
    """
    if not isinstance(series, list):
        raise ValueError("Series must be a list.")
    if not all(isinstance(x, (int, float)) for x in series):
        raise TypeError("All elements of series must be numbers (int or float).")
    if not isinstance(window, int) or window <= 0:
        raise ValueError("Window must be a positive integer.")

    if window > len(series):
        return []

    averages: List[float] = []
    for i in range(len(series) - window + 1):
        window_slice = series[i:i+window]
        averages.append(sum(window_slice) / window)

    return averages
