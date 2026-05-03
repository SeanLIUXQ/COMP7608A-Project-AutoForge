from urllib.parse import parse_qs, urlparse

def sorted_url_query_keys(url: str) -> list[str]:
    """
    Parse the query string of a URL and return the parameter names sorted alphabetically.

    Args:
        url: A URL string; must be non-empty.

    Returns:
        A list of query parameter names, sorted alphabetically.

    Raises:
        ValueError: If the input is not a non-empty string.
    """
    if not isinstance(url, str) or not url.strip():
        raise ValueError("Input must be a non-empty string.")

    parsed = urlparse(url)
    query = parsed.query
    params = parse_qs(query)
    return sorted(params.keys())
