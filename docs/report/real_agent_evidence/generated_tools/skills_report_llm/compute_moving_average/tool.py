from typing import List, Union

def compute_moving_average(series: List[Union[int, float]], window: int) -> List[float]:
    """
    Compute the moving average of a numeric series using a sliding window.

    Args:
        series: A non-empty list of numeric values (integers or floats).
        window: A positive integer specifying the window size. Must not exceed
                the length of the series.

    Returns:
        A list of floats representing the arithmetic mean of each consecutive
        window of the given size.

    Raises:
        ValueError: If series is empty, window is not a positive integer, or
                    window is larger than the series length.
        TypeError: If any element in series is not an int or float.
    """
    # Validate series
    if not series:
        raise ValueError("series must be non-empty")
    for i, val in enumerate(series):
        if not isinstance(val, (int, float)):
            raise TypeError(
                f"All elements in series must be int or float, got {type(val).__name__} at index {i}"
            )

    # Validate window
    if not isinstance(window, int) or window <= 0:
        raise ValueError("window must be a positive integer")
    if window > len(series):
        raise ValueError(
            f"window ({window}) must not exceed the length of the series ({len(series)})"
        )

    # Compute moving averages
    result: List[float] = []
    for i in range(len(series) - window + 1):
        segment = series[i : i + window]
        avg = sum(segment) / window
        result.append(avg)

    return result
