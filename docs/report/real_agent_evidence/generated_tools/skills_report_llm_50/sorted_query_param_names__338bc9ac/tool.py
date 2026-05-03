import urllib.parse
from typing import List

def sorted_query_param_names(url: str) -> List[str]:
    """
    Extract and return sorted unique query parameter names from a URL or query string.

    Args:
        url: A full URL (e.g., 'http://example.com/path?key1=val1&key2=val2')
             or a raw query string (e.g., 'key1=val1&key2=val2').

    Returns:
        A list of parameter names sorted in ascending lexicographic order.

    Raises:
        TypeError: If the input is not a string.
        ValueError: If the input is empty or the query string contains invalid percent encoding.
    """
    if not isinstance(url, str):
        raise TypeError("Input must be a string")
    if not url:
        raise ValueError("Input must be a non-empty string")

    # Isolate the query string component
    if '?' in url:
        query = url.split('?', 1)[1]
    else:
        query = url

    try:
        # parse_qs handles percent-decoding and returns a dict of lists
        params = urllib.parse.parse_qs(query)
    except Exception as e:
        raise ValueError(f"Invalid query string: {e}") from e

    return sorted(params.keys())
