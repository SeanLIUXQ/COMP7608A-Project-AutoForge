from collections import defaultdict

def total_amounts_by_category(
    rows: list[dict],
    category_key: str = "category",
    amount_key: str = "amount",
) -> dict:
    """
    Aggregate amounts by category from a list of dictionaries.

    For each record, the value at `category_key` is used as the grouping key,
    and the value at `amount_key` (which must be numeric) is added to that
    category's total.  Returns a dictionary mapping each unique category to
    the sum of its amounts (as a float).

    Args:
        rows: A list of dictionaries representing the records.
        category_key: Key to extract the category from each row.
            Defaults to "category".
        amount_key: Key to extract the numeric amount from each row.
            Defaults to "amount".

    Returns:
        A dict mapping each distinct category to its total amount (float).

    Raises:
        TypeError: If `rows` is not a list, or `category_key`/`amount_key`
            are not strings.
        ValueError: If any element is not a dict, or if a row is missing a
            required key, or if an amount is not numeric (int/float).
    """
    if not isinstance(rows, list):
        raise TypeError("rows must be a list")
    if not isinstance(category_key, str):
        raise TypeError("category_key must be a string")
    if not isinstance(amount_key, str):
        raise TypeError("amount_key must be a string")

    totals = defaultdict(float)

    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"Row at index {i} is not a dictionary")
        if category_key not in row:
            raise ValueError(
                f"Row at index {i} is missing the category key '{category_key}'"
            )
        if amount_key not in row:
            raise ValueError(
                f"Row at index {i} is missing the amount key '{amount_key}'"
            )
        amount = row[amount_key]
        if not isinstance(amount, (int, float)):
            raise ValueError(
                f"Row at index {i} has a non-numeric amount for key "
                f"'{amount_key}': {amount!r}"
            )
        totals[row[category_key]] += float(amount)

    return dict(totals)
