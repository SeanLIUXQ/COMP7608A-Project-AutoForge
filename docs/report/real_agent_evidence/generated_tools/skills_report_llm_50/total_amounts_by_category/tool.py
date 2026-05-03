def total_amounts_by_category(
    rows: list[dict], 
    category_key: str = "category", 
    amount_key: str = "amount"
) -> dict:
    """
    Aggregate total amounts by category from a list of row dictionaries.

    Args:
        rows: A list of dictionaries. Each dictionary is expected to contain
            at least the fields specified by `category_key` and `amount_key`.
        category_key: The key that holds the category name (default "category").
        amount_key:   The key that holds the numeric amount (default "amount").

    Returns:
        A dictionary mapping each distinct category value to the sum of its amounts.

    Raises:
        TypeError: If `rows` is not a list.
        ValueError: If a row is not a dictionary, is missing the required keys,
            or the value for `amount_key` is not a numeric type (int or float,
            booleans are excluded).
    """
    if not isinstance(rows, list):
        raise TypeError("rows must be a list")

    totals: dict = {}
    for idx, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(
                f"Row at index {idx} must be a dictionary, got {type(row).__name__}"
            )
        if category_key not in row or amount_key not in row:
            missing = []
            if category_key not in row:
                missing.append(category_key)
            if amount_key not in row:
                missing.append(amount_key)
            raise ValueError(
                f"Row at index {idx} missing required keys: {missing}"
            )

        amount = row[amount_key]
        # Exclude booleans (which are a subclass of int) and any non-numeric type.
        if isinstance(amount, bool) or not isinstance(amount, (int, float)):
            raise ValueError(
                f"Amount at row {idx} must be int or float, "
                f"got {type(amount).__name__}: {amount!r}"
            )

        category = row[category_key]
        totals[category] = totals.get(category, 0) + amount

    return totals
