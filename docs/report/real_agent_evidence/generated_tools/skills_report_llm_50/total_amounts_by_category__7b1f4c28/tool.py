from typing import List, Dict, Union

def total_amounts_by_category(rows: List[Dict[str, Union[str, float, int]]]) -> Dict[str, Union[int, float]]:
    """Calculate total amounts grouped by category from a list of dictionaries.

    Each dictionary must contain the keys 'category' and 'amount'.
    The 'amount' value must be numeric (int or float).

    Args:
        rows: A list of dictionaries, each with 'category' (str) and 'amount' (int or float).

    Returns:
        A dictionary mapping each category string to the sum of its amounts.

    Raises:
        TypeError: If rows is not a list, if any element is not a dict,
                   or if an 'amount' is not numeric (int/float).
        KeyError: If a row is missing the 'category' or 'amount' key.
    """
    if not isinstance(rows, list):
        raise TypeError("Input must be a list of dictionaries.")
    
    totals: Dict[str, Union[int, float]] = {}
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            raise TypeError(f"Each item must be a dictionary; got {type(row)} at index {i}.")
        
        if 'category' not in row:
            raise KeyError(f"Missing 'category' key in row at index {i}.")
        if 'amount' not in row:
            raise KeyError(f"Missing 'amount' key in row at index {i}.")
        
        category = row['category']
        amount = row['amount']
        
        if not isinstance(amount, (int, float)):
            raise TypeError(f"'amount' must be int or float, got {type(amount)} at index {i}.")
        
        # setdefault ensures a float/int zero when first encountering a category
        totals.setdefault(category, 0)
        totals[category] += amount
    
    return totals
