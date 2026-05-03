from urllib.parse import urlparse, parse_qs

def sorted_query_param_names(url: str) -> list[str]:
    """
    Extracts all query parameter names from a URL and returns them sorted alphabetically.

    Args:
        url: A non-empty URL string.

    Returns:
        A list of unique query parameter names, sorted in ascending order.
        If the URL contains no query string, an empty list is returned.

    Raises:
        ValueError: If url is not a non-empty string.
    """
    if not isinstance(url, str) or not url.strip():
        raise ValueError("URL must be a non-empty string")

    parsed = urlparse(url)
    query = parsed.query

    if not query:
        return []

    # parse_qs handles percent-decoding and separates keys from values.
    # The resulting dictionary keys are the parameter names.
    params = parse_qs(query, keep_blank_values=True)   # keep keys even if value is empty
    return sorted(params.keys())
