def total_by_category(rows: list[dict]) -> dict:
    """
    Aggregates total amounts by category from a list of dictionaries.

    Args:
        rows (list[dict]): A list of dictionaries, each containing at least
                           the keys 'category' and 'amount'.

    Returns:
        dict: A dictionary mapping each category to the sum of its amounts.

    Raises:
        TypeError: If `rows` is not a list or any element is not a dictionary.
        ValueError: If any dictionary is missing 'category' or 'amount',
                    or if 'amount' cannot be converted to a number.
    """
    if not isinstance(rows, list):
        raise TypeError("Input must be a list.")

    # An empty list yields an empty aggregation.
    if not rows:
        return {}

    totals: dict[str, float] = {}

    for row in rows:
        if not isinstance(row, dict):
            raise TypeError("Each item in the list must be a dictionary.")
        if 'category' not in row:
            raise ValueError("Missing required key: 'category' in row.")
        if 'amount' not in row:
            raise ValueError("Missing required key: 'amount' in row.")

        category = row['category']
        try:
            amount = float(row['amount'])
        except (ValueError, TypeError) as ex:
            raise ValueError(f"Amount must be a number, got: {row['amount']!r}") from ex

        totals[category] = totals.get(category, 0) + amount

    return totals
