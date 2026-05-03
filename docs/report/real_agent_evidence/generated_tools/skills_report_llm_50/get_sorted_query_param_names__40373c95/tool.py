import urllib.parse
from typing import List

def get_sorted_query_param_names(url: str) -> List[str]:
    """
    Extract unique query parameter names from a URL, sorted lexicographically.
    
    Args:
        url: A string representing a URL. May contain a '?' followed by a query
             string, and optionally a '#' fragment.
    
    Returns:
        A list of unique parameter names, sorted in ascending string order.
        Returns an empty list if the URL contains no query string or is empty.
    
    Raises:
        TypeError: If `url` is not a string.
    """
    if not isinstance(url, str):
        raise TypeError("url must be a string")
    
    # Empty string or no query separator → no parameters
    if not url or '?' not in url:
        return []
    
    # Extract query component: after '?' and before any fragment '#'
    query_start = url.find('?') + 1
    raw_query = url[query_start:]
    fragment_pos = raw_query.find('#')
    if fragment_pos != -1:
        raw_query = raw_query[:fragment_pos]
    
    # Parse query string into dict of parameter name → list of values
    parsed = urllib.parse.parse_qs(raw_query)
    
    # Return sorted unique parameter names
    return sorted(parsed.keys())
