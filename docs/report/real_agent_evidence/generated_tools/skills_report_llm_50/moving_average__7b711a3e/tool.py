from typing import List, Union

def moving_average(series: List[Union[int, float]], window: int) -> List[float]:
    """
    Compute the simple moving average (SMA) of a numerical series.

    The function slides a fixed-size window across `series` one step at a time
    and returns the equally weighted average for each window position.

    Args:
        series: A non-empty list of numbers (``int`` or ``float``).
        window: A positive integer specifying the window size. Must not exceed
                the length of `series`.

    Returns:
        A list of floats representing the moving averages.

    Raises:
        TypeError:  If `series` is not a list, contains non‑numeric elements,
                    or `window` is not an integer.
        ValueError: If `series` is empty, `window` is not positive,
                    or `window` exceeds the series length.
    """
    # --- Input validation ---
    if not isinstance(series, list):
        raise TypeError("series must be a list")

    if not series:
        raise ValueError("series must not be empty")

    for i, val in enumerate(series):
        # Reject booleans explicitly (bool is a subclass of int)
        if isinstance(val, bool) or not isinstance(val, (int, float)):
            raise TypeError(
                f"series must contain only int or float, got {type(val).__name__} at index {i}"
            )

    if isinstance(window, bool) or not isinstance(window, int):
        raise TypeError("window must be an integer")

    if window <= 0:
        raise ValueError("window must be a positive integer")

    if window > len(series):
        raise ValueError("window size must not exceed the length of the series")

    # --- Compute moving average ---
    result: List[float] = []
    # Pre‑compute total length minus window to avoid repeated length calls
    limit = len(series) - window + 1
    for i in range(limit):
        window_slice = series[i : i + window]
        avg = sum(window_slice) / window
        result.append(avg)

    return result
