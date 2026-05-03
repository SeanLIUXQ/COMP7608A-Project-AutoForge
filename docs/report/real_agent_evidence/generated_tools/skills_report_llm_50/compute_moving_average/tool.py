import statistics
from typing import Union


def compute_moving_average(values: list[Union[int, float]], window: int) -> list[float]:
    """Compute the moving average of a list of numbers using a sliding window.

    Args:
        values: A non-empty list of numbers (int or float).
        window: A positive integer window size, must not exceed len(values).

    Returns:
        A list of floats representing the arithmetic mean of each sliding window.

    Raises:
        ValueError: If values is empty, window is not a positive integer,
                    or window exceeds the length of values.
        TypeError: If values contains non-numeric elements.
    """
    # Validate values is a non-empty list
    if not isinstance(values, list):
        raise TypeError("values must be a list")
    if len(values) == 0:
        raise ValueError("values must be a non-empty list")

    # Validate all elements are numbers
    for i, v in enumerate(values):
        if not isinstance(v, (int, float)) or isinstance(v, bool):
            raise TypeError(
                f"All elements in values must be int or float, got {type(v).__name__} at index {i}"
            )

    # Validate window is a positive integer
    if not isinstance(window, int) or isinstance(window, bool):
        raise TypeError("window must be an integer")
    if window < 1:
        raise ValueError("window must be a positive integer (>= 1)")

    # Validate window does not exceed series length
    if window > len(values):
        raise ValueError(
            f"window ({window}) must not exceed the length of values ({len(values)})"
        )

    # Compute moving averages using sliding window
    result: list[float] = []
    for i in range(len(values) - window + 1):
        window_slice = values[i:i + window]
        result.append(statistics.mean(window_slice))

    return result
