import ast
import csv
import io
import re
from collections import Counter, defaultdict
from datetime import datetime
from urllib.parse import parse_qs, urlparse


def _extract_quoted_strings(query: str) -> list[str]:
    matches = re.findall(r"'([^']*)'|\"([^\"]*)\"", query)
    return [left or right for left, right in matches]


def _extract_balanced(query: str, opener: str, closer: str) -> str | None:
    start = query.find(opener)
    if start == -1:
        return None
    depth = 0
    for index in range(start, len(query)):
        char = query[index]
        if char == opener:
            depth += 1
        elif char == closer:
            depth -= 1
            if depth == 0:
                return query[start:index + 1]
    return None


def _to_python_literal(text: str):
    normalized = re.sub(r"\bnull\b", "None", text, flags=re.IGNORECASE)
    normalized = re.sub(r"\btrue\b", "True", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\bfalse\b", "False", normalized, flags=re.IGNORECASE)
    return ast.literal_eval(normalized)


def _extract_first_list(query: str):
    fragment = _extract_balanced(query, "[", "]")
    if fragment is None:
        raise ValueError("Missing list literal")
    return _to_python_literal(fragment)


def _extract_first_dict(query: str):
    fragment = _extract_balanced(query, "{", "}")
    if fragment is None:
        raise ValueError("Missing dict literal")
    return _to_python_literal(fragment)


def _extract_decimal_places(query: str, default: int = 2) -> int:
    lowered = query.lower()
    match = re.search(r"(\d+)\s*(?:decimal|decimals|dp)", lowered)
    if match:
        return int(match.group(1))
    if "one decimal" in lowered:
        return 1
    if "two decimals" in lowered:
        return 2
    if "three decimals" in lowered:
        return 3
    return default


def _extract_numeric_value(query: str, pattern: str):
    match = re.search(pattern, query, flags=re.IGNORECASE)
    if not match:
        raise ValueError(f"Pattern not found: {pattern}")
    raw = match.group(1)
    return float(raw) if "." in raw else int(raw)


def _extract_tail_words(query: str, marker: str) -> str:
    lowered = query.lower()
    index = lowered.find(marker.lower())
    if index == -1:
        raise ValueError(f"Missing marker: {marker}")
    return query[index + len(marker):].strip(" ?.:\"'")


def _parse_csv_text(csv_text: str):
    reader = csv.DictReader(io.StringIO(csv_text))
    return list(reader)


def _parse_json_lines(lines):
    records = []
    for line in lines:
        records.append(_to_python_literal(line))
    return records


def _sum_by_category(rows):
    grouped = defaultdict(int)
    for row in rows:
        category = row.get("cat") or row.get("category")
        amount = row.get("amt", row.get("amount", 0))
        grouped[category] += amount
    return dict(grouped)


def _filter_names_by_score(rows, threshold):
    return [row["name"] for row in rows if float(row.get("score", 0)) >= float(threshold)]


def solve_structured_query(query: str):
    lowered = query.lower()

    if "keys" in lowered and ("sorted" in lowered or "alphabetically" in lowered or "sort" in lowered):
        obj = _extract_first_dict(query)
        return sorted(obj.keys())

    if "sum field" in lowered or "total for field" in lowered or "add up field" in lowered or "total field" in lowered:
        rows = _extract_first_list(query)
        if any(not isinstance(row, dict) for row in rows):
            raise ValueError("Field summation expects row dictionaries")
        field_match = re.search(
            r"(?:sum field|field|total field)\s+([a-zA-Z_][a-zA-Z0-9_]*)",
            query,
            flags=re.IGNORECASE,
        )
        field_name = field_match.group(1) if field_match else "x"
        return sum(row[field_name] for row in rows if field_name in row)

    if (("return names" in lowered or "list names" in lowered or "output names" in lowered or "names only" in lowered or "keep names" in lowered) and ">=" in lowered):
        rows = _extract_first_list(query)
        threshold = _extract_numeric_value(query, r">=\s*(\d+(?:\.\d+)?)")
        return _filter_names_by_score(rows, threshold)

    if "first letter" in lowered or "first-letter" in lowered:
        words = _extract_first_list(query)
        grouped = defaultdict(list)
        for word in words:
            grouped[str(word)[0].lower()].append(word)
        return dict(sorted(grouped.items()))

    if "contains key" in lowered or "contain key" in lowered or "exists in json" in lowered or ("check key" in lowered and "inside" in lowered):
        quoted = _extract_quoted_strings(query)
        if len(quoted) < 2:
            raise ValueError("Expected JSON text and key")
        json_text = quoted[0]
        key = quoted[-1]
        for item in quoted:
            if item.strip().startswith("{"):
                json_text = item
                break
        for item in quoted:
            if not item.strip().startswith("{"):
                key = item
                break
        obj = _to_python_literal(json_text)
        return key in obj

    if (
        "aggregate total by category" in lowered
        or "aggregate totals by category" in lowered
        or "category totals" in lowered
        or "total amount by category" in lowered
        or "amounts by category" in lowered
    ):
        rows = _extract_first_list(query)
        return _sum_by_category(rows)

    raise ValueError("Unsupported structured query")


def structured_data_query_tool(query: str):
    """Solve dict, JSON, grouping, filtering, and category aggregation tasks."""
    return solve_structured_query(query)
