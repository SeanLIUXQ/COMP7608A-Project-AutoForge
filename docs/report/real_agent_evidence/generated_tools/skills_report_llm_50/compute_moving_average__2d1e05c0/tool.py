from typing import List, Union

def compute_moving_average(series: List[Union[int, float]], window_size: int) -> List[float]:
    """Calculate the simple moving average of a numeric series.

    Args:
        series: A list of numeric values (int or float).
        window_size: Positive integer specifying the number of consecutive elements
                     to average at each step. Must not exceed len(series).

    Returns:
        A list of floats representing the moving averages,
        computed for each window of length window_size from left to right.

    Raises:
        ValueError: If series is empty, contains non-numeric values,
                    or window_size is not a positive integer <= len(series).
    """
    # Validate series type and elements
    if not isinstance(series, list):
        raise ValueError("series must be a list.")
    for val in series:
        if not isinstance(val, (int, float)):
            raise ValueError(
                f"All series elements must be int or float, got {type(val)}"
            )
    
    # Validate window_size
    if not isinstance(window_size, int) or window_size <= 0:
        raise ValueError("window_size must be a positive integer.")
    if window_size > len(series):
        raise ValueError("window_size cannot exceed the length of series.")

    # Compute moving averages
    averages: List[float] = []
    for i in range(len(series) - window_size + 1):
        window = series[i : i + window_size]
        averages.append(sum(window) / window_size)

    return averages
