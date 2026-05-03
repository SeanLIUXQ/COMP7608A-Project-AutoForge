def sum_amounts_by_category(
    rows: list[dict],
    category_field: str = "category",
    amount_field: str = "amount"
) -> dict:
    """Aggregate sum of a numeric field grouped by a category field.

    Args:
        rows: List of dictionaries containing category and amount data.
        category_field: Name of the key identifying the category (default 'category').
        amount_field: Name of the key holding the numeric amount (default 'amount').

    Returns:
        A dictionary mapping each distinct category to the total sum of amounts
        for that category. Returns an empty dictionary if rows is empty.

    Raises:
        TypeError: If `rows` is not a list or any row is not a dictionary.
        KeyError: If a row is missing the expected category or amount key.
        ValueError: If an amount is not numeric (int or float).
    """
    if not isinstance(rows, list):
        raise TypeError("rows must be a list")
    totals: dict = {}
    for row in rows:
        if not isinstance(row, dict):
            raise TypeError("Each row must be a dictionary")
        category = row[category_field]
        amount = row[amount_field]
        if not isinstance(amount, (int, float)):
            raise ValueError(f"Amount for category '{category}' must be numeric")
        totals[category] = totals.get(category, 0) + amount
    return totals
