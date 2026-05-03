from urllib.parse import urlparse, parse_qs

def sorted_query_param_names(url: str) -> list[str]:
    """
    Extract the query parameter keys from a URL string, sort them lexicographically,
    and return the sorted list.

    If the URL has no query string, an empty list is returned.

    Args:
        url: A string representing the URL to parse.

    Returns:
        A sorted list of unique query parameter names (ignoring values).

    Raises:
        TypeError: If `url` is not a string.
    """
    if not isinstance(url, str):
        raise TypeError("Input must be a string")

    parsed = urlparse(url)
    query = parsed.query
    if not query:
        return []

    # parse_qs returns a dict of key -> list of values; keep_blank_values preserves keys with empty values
    params = parse_qs(query, keep_blank_values=True)
    keys = list(params.keys())
    keys.sort()
    return keys
