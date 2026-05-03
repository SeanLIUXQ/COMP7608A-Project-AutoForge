def compute_moving_average(data: list[float | int], window_size: int) -> list[float]:
    """
    Compute the moving average of a numerical sequence.

    For each contiguous window of length `window_size`, the arithmetic mean
    of the values is calculated. The result contains one average for every
    valid window position, preserving the order of the original data.

    Args:
        data: A non-empty list of numeric values (int or float).
        window_size: A positive integer not exceeding the length of `data`.

    Returns:
        A list of float values representing the moving averages.

    Raises:
        TypeError: If `data` is not a list or contains non-numeric values,
                   or if `window_size` is not an integer.
        ValueError: If `data` is empty, `window_size` is non-positive, or
                    `window_size` exceeds the length of `data`.
    """
    # --- input validation ---
    if not isinstance(data, list):
        raise TypeError("data must be a list")
    if not all(isinstance(x, (int, float)) for x in data):
        raise TypeError("all elements in data must be int or float")
    if not isinstance(window_size, int):
        raise TypeError("window_size must be an integer")
    if window_size <= 0:
        raise ValueError("window_size must be a positive integer")
    if window_size > len(data):
        raise ValueError("window_size cannot exceed the length of data")

    # --- compute moving averages ---
    averages: list[float] = []
    # Loop from i = 0 to len(data) - window_size (inclusive)
    for i in range(len(data) - window_size + 1):
        window = data[i : i + window_size]
        avg = sum(window) / window_size
        averages.append(avg)

    return averages
