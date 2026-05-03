from typing import Union

def moving_average(series: list[Union[int, float]], window: int) -> list[float]:
    """
    Compute the simple moving average of a numeric series.

    The function slides a window of the given size across the series and
    returns the arithmetic mean of each window.

    Args:
        series: A list of numbers (int or float).
        window: Window size (non‑negative integer). A window of 0 returns an
                empty list. Must not exceed len(series) when series is non‑empty.

    Returns:
        A list of moving averages as floats.  Returns an empty list if the
        series is empty or window is 0.

    Raises:
        TypeError: If *series* is not a list or *window* is not an integer.
        ValueError: If the series contains non‑numeric values, or if *window*
                    is negative, or if *window* > len(series) for a non‑empty series.
    """
    # --- Input validation -------------------------------------------------
    if not isinstance(series, list):
        raise TypeError("series must be a list")
    if not all(isinstance(x, (int, float)) for x in series):
        raise ValueError("series must contain only numbers (int or float)")
    if not isinstance(window, int):
        raise TypeError("window must be an integer")
    if window < 0:
        raise ValueError("window must be non-negative")

    # --- Edge cases -------------------------------------------------------
    if not series or window == 0:
        return []
    if window > len(series):
        raise ValueError("window size cannot exceed length of series")

    # --- Compute moving averages ------------------------------------------
    result = []
    for i in range(len(series) - window + 1):
        window_slice = series[i : i + window]
        avg = sum(window_slice) / window
        result.append(avg)

    return result
