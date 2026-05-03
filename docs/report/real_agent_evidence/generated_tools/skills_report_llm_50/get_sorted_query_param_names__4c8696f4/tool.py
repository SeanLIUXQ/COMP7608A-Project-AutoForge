from urllib.parse import urlparse, parse_qs

def get_sorted_query_param_names(url: str) -> list[str]:
    """
    Extract query parameter names from a URL and return them sorted alphabetically.

    Args:
        url: A non-empty string representing a URL.

    Returns:
        A list of unique query parameter names, sorted as strings.
        If the URL has no query string, an empty list is returned.

    Raises:
        ValueError: If the input is not a non-empty string.
    """
    if not isinstance(url, str) or not url:
        raise ValueError("Input must be a non-empty string")

    parsed = urlparse(url)
    query_string = parsed.query

    if not query_string:
        return []

    # parse_qs returns a dict of lists; we only need the keys
    params_dict = parse_qs(query_string)
    return sorted(params_dict.keys())
