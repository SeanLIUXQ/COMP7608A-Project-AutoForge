from typing import List, Dict, Union, Any


def sum_by_category(
    rows: List[Dict[str, Any]],
    category_field: str = "cat",
    value_field: str = "amt",
) -> Dict[str, Union[int, float]]:
    """
    Aggregate numeric values per category from a list of dictionaries.

    Args:
        rows: List of dictionaries, each containing a category field (string)
              and a numeric value field.
        category_field: Key in each dict whose value is the category name.
        value_field: Key in each dict whose value is the numeric amount.

    Returns:
        Dictionary mapping category strings to the sum of their associated values.

    Raises:
        TypeError: If rows is not a list, or if an element is not a dict, or
                   if a value is not numeric.
        ValueError: If a row is missing the required field.
    """
    if not isinstance(rows, list):
        raise TypeError("rows must be a list of dictionaries")

    totals: Dict[str, Union[int, float]] = {}

    for idx, row in enumerate(rows):
        if not isinstance(row, dict):
            raise TypeError(f"Item at index {idx} is not a dictionary")

        if category_field not in row or value_field not in row:
            missing = [f for f in (category_field, value_field) if f not in row]
            raise ValueError(
                f"Row {idx} is missing required field(s): {', '.join(missing)}"
            )

        category = row[category_field]
        if not isinstance(category, str):
            raise TypeError(
                f"Category field '{category_field}' in row {idx} must be a string, "
                f"got {type(category).__name__}"
            )

        amount = row[value_field]
        if not isinstance(amount, (int, float)):
            raise TypeError(
                f"Value field '{value_field}' in row {idx} must be numeric, "
                f"got {type(amount).__name__}"
            )

        totals[category] = totals.get(category, 0) + amount

    return totals
