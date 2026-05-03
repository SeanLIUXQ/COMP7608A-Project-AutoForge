from urllib.parse import urlparse, parse_qs

def sorted_query_parameter_names(url: str) -> list[str]:
    """
    Extract query parameter names from a URL and return them as a sorted list.

    Args:
        url: A non-empty string representing a URL (can also be just a query string
             starting with '?').

    Returns:
        A list of unique query parameter names sorted alphabetically.  If the URL
        contains no query string, an empty list is returned.

    Raises:
        ValueError: If the input is not a non-empty string.
    """
    # Validate input
    if not isinstance(url, str) or not url:
        raise ValueError("Input must be a non-empty string.")

    # Parse the URL; if only query string given (starts with '?'), urlparse still
    # handles it correctly by treating it as a path-relative URL.
    parsed = urlparse(url)
    
    # Extract the query string and parse into key-value pairs
    query_dict = parse_qs(parsed.query, keep_blank_values=True)
    
    # Collect and sort the parameter names (keys)
    return sorted(query_dict.keys())
