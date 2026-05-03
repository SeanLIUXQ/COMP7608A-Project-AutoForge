import urllib.parse

def get_sorted_query_param_names(url: str) -> list[str]:
    """
    Extract all unique query parameter names from a URL and return them sorted alphabetically.

    Args:
        url: A non-empty string representing a URL.

    Returns:
        A list of unique query parameter names in alphabetical order.

    Raises:
        ValueError: If the input is not a non-empty string.
    """
    if not isinstance(url, str) or not url:
        raise ValueError("Input must be a non-empty string.")

    parsed = urllib.parse.urlparse(url)
    query_string = parsed.query

    # parse_qs returns a dict mapping each parameter name to a list of values
    params = urllib.parse.parse_qs(query_string, keep_blank_values=True)

    return sorted(params.keys())
