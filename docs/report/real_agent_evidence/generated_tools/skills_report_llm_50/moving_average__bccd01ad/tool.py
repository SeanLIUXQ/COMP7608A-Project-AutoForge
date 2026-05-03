def moving_average(series: list[float], window: int) -> list[float]:
    """
    Compute the simple moving average of a numeric series.

    Args:
        series: A non-empty list of numbers (int or float).
        window: A positive integer window size.

    Returns:
        A list of floats representing the moving averages of each
        window slice. The length is len(series) - window + 1.

    Raises:
        ValueError: If series is empty, window is not a positive integer,
                    or window is larger than the series length.
        TypeError: If series contains non-numeric values or window is not an integer.
    """
    # Validate series is a non-empty list of numbers
    if not isinstance(series, list) or len(series) == 0:
        raise ValueError("series must be a non-empty list of numbers")
    
    # Ensure all elements are numeric (int or float)
    for i, val in enumerate(series):
        if not isinstance(val, (int, float)):
            raise TypeError(f"All elements in series must be numeric; got {type(val).__name__} at index {i}")

    # Validate window is a positive integer
    if not isinstance(window, int) or isinstance(window, bool):
        raise TypeError(f"window must be an integer, got {type(window).__name__}")
    if window <= 0:
        raise ValueError("window must be a positive integer")

    # Check window size does not exceed series length
    n = len(series)
    if window > n:
        raise ValueError(f"window size ({window}) cannot be larger than series length ({n})")

    # Compute the moving average using a sliding window sum
    # Use a running sum to avoid repeated sum() calls for better performance
    result = []
    current_sum = sum(series[:window])
    result.append(current_sum / window)

    for i in range(window, n):
        current_sum += series[i] - series[i - window]
        result.append(current_sum / window)

    return result
