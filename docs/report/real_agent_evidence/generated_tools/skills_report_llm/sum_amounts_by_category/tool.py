from typing import Dict, List, Union, Any

def sum_amounts_by_category(rows: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Sum 'amount' values grouped by 'category' for a list of dictionaries.

    Args:
        rows: A list of dicts, each expected to have 'category' and 'amount' keys.

    Returns:
        A dictionary mapping each category to the total sum of its amounts.

    Raises:
        TypeError: If rows is not a list, or an element is not a dict.
        ValueError: If a required key ('category' or 'amount') is missing,
                    or an amount is not a valid number (int, float, or numeric string).
    """
    if not isinstance(rows, list):
        raise TypeError("Input must be a list of dictionaries.")
    
    if not rows:
        return {}  # empty list yields empty result
    
    totals: Dict[str, float] = {}
    
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            raise TypeError(f"Item at index {i} is not a dictionary.")
        
        if "category" not in row:
            raise ValueError(f"Row at index {i} is missing 'category' key.")
        if "amount" not in row:
            raise ValueError(f"Row at index {i} is missing 'amount' key.")
        
        category = row["category"]
        amount = row["amount"]
        
        # Convert amount to float if it isn't already a number
        if isinstance(amount, (int, float)):
            value = float(amount)
        elif isinstance(amount, str):
            try:
                value = float(amount)
            except ValueError:
                raise ValueError(f"Invalid numeric string for amount at index {i}: {amount!r}")
        else:
            raise ValueError(f"Invalid amount type at index {i}: {type(amount).__name__} (expected number or numeric string)")
        
        totals[category] = totals.get(category, 0.0) + value
    
    return totals
