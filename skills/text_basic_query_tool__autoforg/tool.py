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


def solve_text_query(query: str):
    lowered = query.lower()
    quoted = _extract_quoted_strings(query)

    if "vowel" in lowered:
        if quoted:
            target = quoted[0]
        else:
            target = query.strip().split()[-1].strip("?.")
        return sum(1 for char in target.lower() if char in "aeiou")

    if "reverse" in lowered or "backwards" in lowered:
        if quoted:
            target = quoted[0]
        elif " of " in lowered:
            target = _extract_tail_words(query, " of ")
        elif " string " in lowered:
            target = _extract_tail_words(query, " string ")
        else:
            target = query.strip().split()[-1].strip("?.")
        return target[::-1]

    if "title case" in lowered or "title-case" in lowered:
        target = quoted[-1] if quoted else _extract_tail_words(query, " to ")
        return " ".join(part.capitalize() for part in target.split())

    if "phone" in lowered and ("digits" in lowered or "digits only" in lowered or "digit-only" in lowered):
        target = quoted[0] if quoted else query
        return "".join(char for char in target if char.isdigit())

    if "top" in lowered and "token" in lowered:
        token_text = quoted[0] if quoted else _extract_tail_words(query, " in ")
        top_n = _extract_numeric_value(query, r"top\s+(\d+)") if "top " in lowered else 2
        counts = Counter(token_text.split())
        ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        return [item[0] for item in ordered[:top_n]]

    raise ValueError("Unsupported text query")


def text_basic_query_tool(query: str):
    """Solve string reversal, vowel counting, title case, phone cleanup, and token frequency tasks."""
    return solve_text_query(query)
