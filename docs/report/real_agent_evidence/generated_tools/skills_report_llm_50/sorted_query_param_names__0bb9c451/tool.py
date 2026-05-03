from urllib.parse import urlparse, parse_qs
from typing import List


def sorted_query_param_names(url: str) -> List[str]:
    """
    Extract all unique query parameter names from a URL and return them sorted.

    Args:
        url: A non-empty URL string (e.g. "http://example.com?a=1&b=2").

    Returns:
        A list of parameter names sorted lexicographically.

    Raises:
        ValueError: If the input is not a non-empty string.
    """
    if not isinstance(url, str) or not url.strip():
        raise ValueError("Input must be a non-empty string")

    parsed = urlparse(url)
    query = parsed.query
    # parse_qs handles duplicate keys and percent-encoded characters, yielding a dict
    params = parse_qs(query)
    return sorted(params.keys())
