from typing import Any

def sum_amounts_by_category(records: list[dict]) -> dict:
    """
    Sum the 'amount' values for each 'category' in a list of dictionaries.

    Args:
        records: A list of dictionaries. Each dictionary must contain a 'category' key
                 (used as the grouping key) and an 'amount' key whose value is numeric
                 (int or float, not bool).

    Returns:
        A dictionary mapping each unique category to the total sum of its amounts.

    Raises:
        TypeError: If records is not a list, any element is not a dict, or an 'amount'
                   value is not a valid numeric type (int/float, excluding bool).
        ValueError: If any dictionary is missing the required 'category' or 'amount' keys.
    """
    if not isinstance(records, list):
        raise TypeError("Input must be a list of dictionaries.")

    totals: dict[Any, float | int] = {}
    for idx, item in enumerate(records):
        if not isinstance(item, dict):
            raise TypeError(f"Expected dict at index {idx}, got {type(item).__name__}")

        if 'category' not in item:
            raise ValueError(f"Missing 'category' key at index {idx}")
        if 'amount' not in item:
            raise ValueError(f"Missing 'amount' key at index {idx}")

        amount = item['amount']
        if isinstance(amount, bool) or not isinstance(amount, (int, float)):
            raise TypeError(
                f"Amount at index {idx} must be int or float, got {type(amount).__name__}"
            )

        category = item['category']
        totals[category] = totals.get(category, 0) + amount

    return totals
