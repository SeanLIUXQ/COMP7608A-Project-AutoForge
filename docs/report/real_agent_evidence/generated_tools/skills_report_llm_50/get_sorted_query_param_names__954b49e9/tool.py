import urllib.parse
from typing import List


def get_sorted_query_param_names(url: str) -> List[str]:
    """
    Extract query parameter names from a URL and return them sorted alphabetically.

    Args:
        url: A non-empty string representing an absolute or relative URL.

    Returns:
        A list of parameter names (keys) from the query string, sorted in ascending
        alphabetical order.  If the URL contains no query string, an empty list is
        returned.

    Raises:
        ValueError: If `url` is not a non-empty string.
    """
    if not isinstance(url, str) or not url:
        raise ValueError("url must be a non-empty string")

    parsed = urllib.parse.urlparse(url)
    query_string = parsed.query

    # parse_qs gives a dict of key -> list[value]; keep_blank_values=True ensures
    # parameters like '?name' are still captured as a key with an empty string value.
    params = urllib.parse.parse_qs(query_string, keep_blank_values=True)

    # Return the unique parameter names sorted alphabetically.
    return sorted(params.keys())
