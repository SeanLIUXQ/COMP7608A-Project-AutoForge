from __future__ import annotations

import json
from pathlib import Path


def _sample_id(counters: dict[int, int], difficulty: int) -> str:
    counters[difficulty] += 1
    return f"L{difficulty}_{counters[difficulty]:03d}"


def _append(
    output: list[dict],
    counters: dict[int, int],
    difficulty: int,
    query: str,
    paraphrases: list[str],
    expected_output,
    expected_output_type: str,
    tool_family: str,
) -> None:
    output.append(
        {
            "sample_id": _sample_id(counters, difficulty),
            "difficulty": difficulty,
            "query": query,
            "paraphrases": paraphrases,
            "expected_output": expected_output,
            "expected_output_type": expected_output_type,
            "tool_family": tool_family,
        }
    )


def build_dataset() -> list[dict]:
    counters = {1: 0, 2: 0, 3: 0, 4: 0}
    rows: list[dict] = []

    # Difficulty 1
    for word in ["AutoForge", "evaluation"]:
        _append(
            rows,
            counters,
            1,
            f"Count vowels in the string '{word}'",
            [
                f"Return vowel count for '{word}'",
                f"How many vowels are in '{word}'?",
                f"Count vowels for '{word}'",
            ],
            sum(1 for char in word.lower() if char in "aeiou"),
            "numeric",
            "string_ops",
        )

    for text in ["streamlit", "benchmark"]:
        _append(
            rows,
            counters,
            1,
            f"Reverse the text '{text}'",
            [
                f"Return the reverse of '{text}'",
                f"Write '{text}' backwards",
                f"Reverse '{text}'",
            ],
            text[::-1],
            "exact",
            "string_ops",
        )

    for values in ([5, 1, 9, 2], [8, 3, 8, 1]):
        _append(
            rows,
            counters,
            1,
            f"Sort numbers {values} ascending",
            [
                f"Return ascending sort for {values}",
                f"Sort {values} from small to large",
                f"Order {values} ascending",
            ],
            sorted(values),
            "exact",
            "list_ops",
        )

    for values in ([10, 20, 30, 40], [4, 6, 8, 10]):
        _append(
            rows,
            counters,
            1,
            f"Compute average of {values}",
            [
                f"Return the mean of {values}",
                f"Average the numbers in {values}",
                f"What is the average for {values}?",
            ],
            sum(values) / len(values),
            "numeric",
            "math_ops",
        )

    for text in ["hello world", "auto forge dashboard"]:
        _append(
            rows,
            counters,
            1,
            f"Convert '{text}' to title case",
            [
                f"Return '{text}' in title case",
                f"Title-case '{text}'",
                f"Convert '{text}' into title case",
            ],
            " ".join(part.capitalize() for part in text.split()),
            "exact",
            "string_ops",
        )

    for values in ([1, 2, 2, 3, 1, 4], [5, 5, 2, 5, 3, 2]):
        ordered = []
        seen = set()
        for value in values:
            if value in seen:
                continue
            seen.add(value)
            ordered.append(value)
        _append(
            rows,
            counters,
            1,
            f"Remove duplicates from {values} preserving order",
            [
                f"Deduplicate {values} while preserving order",
                f"Keep first occurrences only from {values}",
                f"Remove duplicates but preserve order for {values}",
            ],
            ordered,
            "exact",
            "list_ops",
        )

    for values, decimals in [([1.0, 2.5, 3.5], 1), ([2.25, 3.25, 4.25], 2)]:
        _append(
            rows,
            counters,
            1,
            f"For values {values}, compute sum rounded to {decimals} decimal",
            [
                f"Return the sum of {values} rounded to {decimals} dp",
                f"Add {values} and keep {decimals} decimal",
                f"Compute rounded sum for {values} with {decimals} decimal",
            ],
            round(sum(values), decimals),
            "numeric",
            "math_ops",
        )

    for raw_bytes in [1048576, 1572864]:
        _append(
            rows,
            counters,
            1,
            f"Convert {raw_bytes} bytes to megabytes with 2 decimals",
            [
                f"Return {raw_bytes} bytes in megabytes with 2 dp",
                f"How many megabytes is {raw_bytes} bytes with 2 decimals?",
                f"Convert {raw_bytes} bytes into MB with 2 decimals",
            ],
            round(raw_bytes / (1024 * 1024), 2),
            "numeric",
            "unit_conversion",
        )

    for word in ["retrieval", "automation"]:
        _append(
            rows,
            counters,
            1,
            f"Count vowels in the string '{word}'",
            [
                f"Return vowel count for '{word}'",
                f"How many vowels are in '{word}'?",
                f"Count vowels for '{word}'",
            ],
            sum(1 for char in word.lower() if char in "aeiou"),
            "numeric",
            "string_ops",
        )

    for values in ([3, 1, 3, 2, 1], [9, 7, 7, 5, 9, 3]):
        ordered = []
        seen = set()
        for value in values:
            if value in seen:
                continue
            seen.add(value)
            ordered.append(value)
        _append(
            rows,
            counters,
            1,
            f"Remove duplicates from {values} preserving order",
            [
                f"Deduplicate {values} while preserving order",
                f"Keep first occurrences only from {values}",
                f"Remove duplicates but preserve order for {values}",
            ],
            ordered,
            "exact",
            "list_ops",
        )

    # Difficulty 2
    for phone in ["+852 9123-4567", "+1 (415) 555-0100"]:
        _append(
            rows,
            counters,
            2,
            f"Normalize phone '{phone}' to digits only",
            [
                f"Keep digits only from phone '{phone}'",
                f"Return phone digits for '{phone}'",
                f"Convert phone '{phone}' to digits only",
            ],
            "".join(char for char in phone if char.isdigit()),
            "exact",
            "phone_cleanup",
        )

    for obj in [
        {"name": "Ada", "age": 20, "city": "HK"},
        {"product": "Book", "price": 18, "stock": 7},
    ]:
        _append(
            rows,
            counters,
            2,
            f"Extract keys from object {obj} sorted alphabetically",
            [
                f"Return sorted keys for {obj}",
                f"List the keys in {obj} alphabetically",
                f"Sort the keys from {obj}",
            ],
            sorted(obj.keys()),
            "exact",
            "json_processing",
        )

    for field_name, records in [
        ("x", [{"x": 1}, {"x": 3}, {"x": 5}]),
        ("score", [{"score": 4}, {"score": 6}, {"score": 10}]),
    ]:
        _append(
            rows,
            counters,
            2,
            f"Given list {records}, sum field {field_name}",
            [
                f"Return the total for field {field_name} in {records}",
                f"Compute sum field {field_name} for {records}",
                f"Add up field {field_name} from {records}",
            ],
            sum(row[field_name] for row in records),
            "numeric",
            "json_processing",
        )

    for threshold, records in [
        (80, [{"name": "A", "score": 70}, {"name": "B", "score": 90}, {"name": "C", "score": 85}]),
        (75, [{"name": "Tom", "score": 75}, {"name": "May", "score": 88}, {"name": "Eve", "score": 60}]),
    ]:
        _append(
            rows,
            counters,
            2,
            f"Filter rows {records} where score >= {threshold} and return names",
            [
                f"Return names from {records} with score >= {threshold}",
                f"Keep rows in {records} where score >= {threshold} and list names",
                f"Filter {records} by score >= {threshold} and output names",
            ],
            [row["name"] for row in records if row["score"] >= threshold],
            "exact",
            "table_filter",
        )

    for words in [
        ["apple", "ape", "banana", "boat"],
        ["cat", "car", "dog", "dove"],
    ]:
        grouped: dict[str, list[str]] = {}
        for word in words:
            grouped.setdefault(word[0].lower(), []).append(word)
        _append(
            rows,
            counters,
            2,
            f"Group words {words} by first letter",
            [
                f"Return first-letter groups for {words}",
                f"Bucket words {words} by first letter",
                f"Group the words in {words} using their first letter",
            ],
            dict(sorted(grouped.items())),
            "exact",
            "text_grouping",
        )

    for json_text, key in [
        ('{"a":1,"b":2}', "b"),
        ('{"name":"Ada","region":"HK"}', "region"),
    ]:
        _append(
            rows,
            counters,
            2,
            f"Check whether JSON text '{json_text}' contains key '{key}'",
            [
                f"Return whether key '{key}' exists in JSON text '{json_text}'",
                f"Does JSON text '{json_text}' contain key '{key}'?",
                f"Check key '{key}' inside '{json_text}'",
            ],
            key in json.loads(json_text),
            "exact",
            "json_processing",
        )

    for url in [
        "https://example.com/path?a=1&b=2",
        "https://demo.org/search?page=2&sort=desc",
    ]:
        _append(
            rows,
            counters,
            2,
            f"Parse URL '{url}' and return query parameter names sorted",
            [
                f"Return sorted query parameter names for '{url}'",
                f"List query parameter names in '{url}' alphabetically",
                f"Extract sorted query keys from '{url}'",
            ],
            sorted(part.split("=")[0] for part in url.split("?", 1)[1].split("&")),
            "exact",
            "url_processing",
        )

    for timestamps in [
        ["2025-01-01T00:00:00Z", "2025-01-01T01:30:00Z"],
        ["2025-03-10T10:15:00Z", "2025-03-10T11:30:00Z"],
    ]:
        _append(
            rows,
            counters,
            2,
            f"Given ISO timestamps {timestamps}, return interval in minutes",
            [
                f"Return the interval in minutes for {timestamps}",
                f"Compute difference in minutes for {timestamps}",
                f"Find the minute interval between {timestamps}",
            ],
            int(
                (
                    __import__("datetime").datetime.fromisoformat(timestamps[1].replace("Z", "+00:00"))
                    - __import__("datetime").datetime.fromisoformat(timestamps[0].replace("Z", "+00:00"))
                ).total_seconds()
                / 60
            ),
            "numeric",
            "datetime_ops",
        )

    for json_text, key in [
        ('{"team":"ml","status":"ready"}', "team"),
        ('{"owner":"Lyu","metric":"trr","value":0.7}', "metric"),
    ]:
        _append(
            rows,
            counters,
            2,
            f"Check whether JSON text '{json_text}' contains key '{key}'",
            [
                f"Return whether key '{key}' exists in JSON text '{json_text}'",
                f"Does JSON text '{json_text}' contain key '{key}'?",
                f"Check key '{key}' inside '{json_text}'",
            ],
            key in json.loads(json_text),
            "exact",
            "json_processing",
        )

    for url in [
        "https://autoforge.local/tools?mode=fast&limit=5",
        "https://example.net/data?format=json&retry=2",
    ]:
        _append(
            rows,
            counters,
            2,
            f"Parse URL '{url}' and return query parameter names sorted",
            [
                f"Return sorted query parameter names for '{url}'",
                f"List query parameter names in '{url}' alphabetically",
                f"Extract sorted query keys from '{url}'",
            ],
            sorted(part.split("=")[0] for part in url.split("?", 1)[1].split("&")),
            "exact",
            "url_processing",
        )

    # Difficulty 3
    for top_n, text in [(2, "a b c a b a"), (3, "red blue red green red blue yellow")]:
        tokens = text.split()
        counts: dict[str, int] = {}
        for token in tokens:
            counts[token] = counts.get(token, 0) + 1
        ordered = [item[0] for item in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:top_n]]
        _append(
            rows,
            counters,
            3,
            f"Find top {top_n} frequent tokens in '{text}'",
            [
                f"Return top {top_n} tokens for '{text}'",
                f"Compute top {top_n} frequent tokens in '{text}'",
                f"List the top {top_n} tokens from '{text}'",
            ],
            ordered,
            "exact",
            "text_stats",
        )

    for rows_data, percent in [
        ([{"item": "A", "price": 10}, {"item": "B", "price": 20}], 20),
        ([{"item": "Pen", "price": 5}, {"item": "Book", "price": 12}], 15),
    ]:
        _append(
            rows,
            counters,
            3,
            f"From rows {rows_data}, increase price by {percent}%",
            [
                f"Increase price by {percent}% for rows {rows_data}",
                f"Apply a {percent}% price increase to {rows_data}",
                f"Raise the price field in {rows_data} by {percent}%",
            ],
            [round(row["price"] * (1 + percent / 100.0), 4) for row in rows_data],
            "exact",
            "csv_pipeline",
        )

    for records in [
        [{"cat": "food", "amt": 30}, {"cat": "book", "amt": 20}, {"cat": "food", "amt": 15}],
        [{"cat": "travel", "amt": 100}, {"cat": "food", "amt": 25}, {"cat": "travel", "amt": 50}],
    ]:
        grouped: dict[str, int] = {}
        for row in records:
            grouped[row["cat"]] = grouped.get(row["cat"], 0) + row["amt"]
        _append(
            rows,
            counters,
            3,
            f"Aggregate total by category for {records}",
            [
                f"Return category totals for {records}",
                f"Aggregate totals by category in {records}",
                f"Compute total amount by category for {records}",
            ],
            grouped,
            "exact",
            "aggregation_pipeline",
        )

    for records in [
        [{"v": 1}, {"v": None}, {"v": 3}],
        [{"v": 2}, {"v": None}, {"v": 4}, {"v": 6}],
    ]:
        values = [row["v"] for row in records if row["v"] is not None]
        _append(
            rows,
            counters,
            3,
            f"Given rows {records}, drop null v and return mean",
            [
                f"Drop null v from {records} and return mean",
                f"Filter null v values in {records} then compute mean",
                f"Return the mean after dropping null v in {records}",
            ],
            sum(values) / len(values),
            "numeric",
            "data_cleaning_pipeline",
        )

    for csv_text, threshold in [
        ("name,score\nA,80\nB,90\nC,70", 80),
        ("name,score\nAna,91\nBo,85\nCy,60", 90),
    ]:
        rows_csv = [line.split(",") for line in csv_text.splitlines()]
        names = []
        for name, score in rows_csv[1:]:
            if int(score) >= threshold:
                names.append(name)
        _append(
            rows,
            counters,
            3,
            f"From CSV text '{csv_text}', keep score>={threshold} and return names joined by comma",
            [
                f"Filter CSV text '{csv_text}' with score>={threshold} and join names",
                f"Return comma-joined names from '{csv_text}' where score>={threshold}",
                f"Keep score>={threshold} in CSV text '{csv_text}' and join matching names",
            ],
            ",".join(names),
            "exact",
            "csv_pipeline",
        )

    for lines, field_name in [
        (['{"x":1}', '{"x":2}', '{"y":3}'], "x"),
        (['{"score":4}', '{"score":6}', '{"skip":1}'], "score"),
    ]:
        total = 0
        for line in lines:
            row = json.loads(line)
            if field_name in row:
                total += row[field_name]
        _append(
            rows,
            counters,
            3,
            f"Read JSON lines {lines}, keep {field_name} records and return sum {field_name}",
            [
                f"Return sum {field_name} from JSON lines {lines}",
                f"Keep JSON lines with {field_name} and sum {field_name} for {lines}",
                f"Read {lines} and total field {field_name}",
            ],
            total,
            "numeric",
            "jsonl_pipeline",
        )

    for payload, window in [
        ({"prices": [10.0, 11.0, 12.0, 13.0]}, 3),
        ({"prices": [2.0, 4.0, 6.0, 8.0]}, 2),
    ]:
        output = []
        prices = payload["prices"]
        for index in range(len(prices) - window + 1):
            chunk = prices[index:index + window]
            output.append(round(sum(chunk) / len(chunk), 4))
        _append(
            rows,
            counters,
            3,
            f"Given payload {payload}, compute {window}-point moving average",
            [
                f"Return the {window}-point moving average for {payload}",
                f"Compute {window}-point moving average from {payload}",
                f"Calculate {window}-point moving average using {payload}",
            ],
            output,
            "exact",
            "timeseries_pipeline",
        )

    for lines in [
        ["apple,3", "banana,1", "apple,2"],
        ["cat,2", "dog,5", "cat,1", "dog,1"],
    ]:
        grouped: dict[str, int] = {}
        for line in lines:
            key, raw_value = line.split(",", 1)
            grouped[key] = grouped.get(key, 0) + int(raw_value)
        ordered = [[key, value] for key, value in sorted(grouped.items(), key=lambda item: (-item[1], item[0]))]
        _append(
            rows,
            counters,
            3,
            f"Take text lines {lines}, aggregate counts and return descending pairs",
            [
                f"Aggregate counts from text lines {lines} and return descending pairs",
                f"Return descending aggregated pairs for {lines}",
                f"Group and sum the text lines {lines}, then return descending pairs",
            ],
            ordered,
            "exact",
            "text_etl_pipeline",
        )

    for top_n, text in [(2, "tool rag tool forge rag"), (3, "fast slow fast agent slow fast")]:
        tokens = text.split()
        counts: dict[str, int] = {}
        for token in tokens:
            counts[token] = counts.get(token, 0) + 1
        ordered = [item[0] for item in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:top_n]]
        _append(
            rows,
            counters,
            3,
            f"Find top {top_n} frequent tokens in '{text}'",
            [
                f"Return top {top_n} tokens for '{text}'",
                f"Compute top {top_n} frequent tokens in '{text}'",
                f"List the top {top_n} tokens from '{text}'",
            ],
            ordered,
            "exact",
            "text_stats",
        )

    for payload, window in [
        ({"prices": [5.0, 7.0, 9.0, 11.0, 13.0]}, 4),
        ({"prices": [3.0, 6.0, 9.0, 12.0]}, 3),
    ]:
        prices = payload["prices"]
        output = []
        for index in range(len(prices) - window + 1):
            chunk = prices[index:index + window]
            output.append(round(sum(chunk) / len(chunk), 4))
        _append(
            rows,
            counters,
            3,
            f"Given payload {payload}, compute {window}-point moving average",
            [
                f"Return the {window}-point moving average for {payload}",
                f"Compute {window}-point moving average from {payload}",
                f"Calculate {window}-point moving average using {payload}",
            ],
            output,
            "exact",
            "timeseries_pipeline",
        )

    # Difficulty 4
    for rows_data, threshold in [
        ([{"name": "Kai", "score": 88}, {"name": "Li", "score": 91}, {"name": "Mo", "score": 79}, {"name": "Jo", "score": 85}], 85),
        ([{"name": "Nia", "score": 92}, {"name": "Oli", "score": 68}, {"name": "Pia", "score": 95}, {"name": "Qin", "score": 89}], 90),
    ]:
        _append(
            rows,
            counters,
            4,
            f"Filter rows {rows_data} where score >= {threshold} and return names",
            [
                f"Keep names from {rows_data} with score >= {threshold}",
                f"Return rows in {rows_data} where score >= {threshold} as names only",
                f"Filter {rows_data} using score >= {threshold} and output names",
            ],
            [row["name"] for row in rows_data if row["score"] >= threshold],
            "exact",
            "table_filter",
        )

    for records in [
        [{"cat": "food", "amt": 12}, {"cat": "travel", "amt": 40}, {"cat": "food", "amt": 18}, {"cat": "books", "amt": 25}],
        [{"cat": "ops", "amt": 30}, {"cat": "ops", "amt": 50}, {"cat": "sales", "amt": 45}, {"cat": "sales", "amt": 20}],
    ]:
        grouped: dict[str, int] = {}
        for row in records:
            grouped[row["cat"]] = grouped.get(row["cat"], 0) + row["amt"]
        _append(
            rows,
            counters,
            4,
            f"Aggregate total by category for {records}",
            [
                f"Compute category totals for {records}",
                f"Return aggregated category totals for {records}",
                f"Sum the amounts by category in {records}",
            ],
            grouped,
            "exact",
            "aggregation_pipeline",
        )

    for records in [
        [{"v": 2}, {"v": None}, {"v": 4}, {"v": 6}, {"v": None}, {"v": 8}],
        [{"v": 10}, {"v": None}, {"v": 20}, {"v": 30}],
    ]:
        values = [row["v"] for row in records if row["v"] is not None]
        _append(
            rows,
            counters,
            4,
            f"Given rows {records}, drop null v and return mean",
            [
                f"Drop null v values in {records} and return mean",
                f"Filter null v entries from {records}, then compute mean",
                f"Return the mean after dropping null v from {records}",
            ],
            sum(values) / len(values),
            "numeric",
            "data_cleaning_pipeline",
        )

    for csv_text, threshold in [
        ("name,score\nAva,88\nBen,91\nCal,79\nDia,95", 90),
        ("name,score\nIan,72\nJia,86\nKen,90\nLux,94", 86),
    ]:
        names = []
        for name, score in [line.split(",") for line in csv_text.splitlines()[1:]]:
            if int(score) >= threshold:
                names.append(name)
        _append(
            rows,
            counters,
            4,
            f"From CSV text '{csv_text}', keep score>={threshold} and return names joined by comma",
            [
                f"Keep score>={threshold} from CSV text '{csv_text}' and join the names",
                f"Return comma-joined names from '{csv_text}' with score>={threshold}",
                f"Filter '{csv_text}' on score>={threshold} and join matching names",
            ],
            ",".join(names),
            "exact",
            "csv_pipeline",
        )

    for payload, window in [
        ({"prices": [1.0, 2.0, 3.0, 4.0, 5.0]}, 3),
        ({"prices": [12.0, 14.0, 16.0, 18.0, 20.0]}, 2),
    ]:
        prices = payload["prices"]
        output = []
        for index in range(len(prices) - window + 1):
            chunk = prices[index:index + window]
            output.append(round(sum(chunk) / len(chunk), 4))
        _append(
            rows,
            counters,
            4,
            f"Given payload {payload}, compute {window}-point moving average",
            [
                f"Compute {window}-point moving average from payload {payload}",
                f"Return {window}-point moving average for payload {payload}",
                f"Calculate a {window}-point moving average using {payload}",
            ],
            output,
            "exact",
            "timeseries_pipeline",
        )

    for lines, field_name in [
        (['{"x":1}', '{"x":2}', '{"x":4}', '{"skip":9}'], "x"),
        (['{"score":5}', '{"score":7}', '{"score":8}', '{"other":1}'], "score"),
    ]:
        total = 0
        for line in lines:
            row = json.loads(line)
            if field_name in row:
                total += row[field_name]
        _append(
            rows,
            counters,
            4,
            f"Read JSON lines {lines}, keep {field_name} records and return sum {field_name}",
            [
                f"Return total {field_name} from JSON lines {lines}",
                f"Sum {field_name} for JSON lines {lines}",
                f"Keep records with {field_name} in {lines} and return sum {field_name}",
            ],
            total,
            "numeric",
            "jsonl_pipeline",
        )

    for lines in [
        ["alpha,4", "beta,1", "alpha,3", "gamma,2"],
        ["red,5", "blue,2", "red,1", "green,4", "blue,1"],
    ]:
        grouped: dict[str, int] = {}
        for line in lines:
            key, raw_value = line.split(",", 1)
            grouped[key] = grouped.get(key, 0) + int(raw_value)
        ordered = [[key, value] for key, value in sorted(grouped.items(), key=lambda item: (-item[1], item[0]))]
        _append(
            rows,
            counters,
            4,
            f"Take text lines {lines}, aggregate counts and return descending pairs",
            [
                f"Aggregate counts for text lines {lines} and return descending pairs",
                f"Return descending aggregated pairs from {lines}",
                f"Group and sum {lines}, then output descending pairs",
            ],
            ordered,
            "exact",
            "text_etl_pipeline",
        )

    for url in [
        "https://svc.example.com/api?region=hk&team=ml&view=full",
        "https://demo.org/report?day=mon&owner=alex&status=open",
    ]:
        _append(
            rows,
            counters,
            4,
            f"Parse URL '{url}' and return query parameter names sorted",
            [
                f"Return sorted query parameter names for URL '{url}'",
                f"Extract query keys from '{url}' and sort them",
                f"List sorted query parameter names in '{url}'",
            ],
            sorted(part.split("=")[0] for part in url.split("?", 1)[1].split("&")),
            "exact",
            "url_processing",
        )

    for rows_data, threshold in [
        ([{"name": "Uma", "score": 84}, {"name": "Vic", "score": 86}, {"name": "Wen", "score": 91}, {"name": "Xiu", "score": 73}], 86),
        ([{"name": "Ray", "score": 78}, {"name": "Sue", "score": 82}, {"name": "Tao", "score": 82}, {"name": "Uma", "score": 99}], 82),
    ]:
        _append(
            rows,
            counters,
            4,
            f"Filter rows {rows_data} where score >= {threshold} and return names",
            [
                f"Keep names from {rows_data} with score >= {threshold}",
                f"Return rows in {rows_data} where score >= {threshold} as names only",
                f"Filter {rows_data} using score >= {threshold} and output names",
            ],
            [row["name"] for row in rows_data if row["score"] >= threshold],
            "exact",
            "table_filter",
        )

    for records in [
        [{"cat": "infra", "amt": 18}, {"cat": "ml", "amt": 32}, {"cat": "infra", "amt": 22}, {"cat": "ui", "amt": 11}],
        [{"cat": "eval", "amt": 14}, {"cat": "rag", "amt": 21}, {"cat": "eval", "amt": 16}, {"cat": "rag", "amt": 9}],
    ]:
        grouped: dict[str, int] = {}
        for row in records:
            grouped[row["cat"]] = grouped.get(row["cat"], 0) + row["amt"]
        _append(
            rows,
            counters,
            4,
            f"Aggregate total by category for {records}",
            [
                f"Compute category totals for {records}",
                f"Return aggregated category totals for {records}",
                f"Sum the amounts by category in {records}",
            ],
            grouped,
            "exact",
            "aggregation_pipeline",
        )

    assert counters == {1: 20, 2: 20, 3: 20, 4: 20}, counters
    return rows


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    out_path = repo_root / "evaluation" / "benchmark" / "dataset.json"
    dataset = build_dataset()
    out_path.write_text(json.dumps(dataset, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(dataset)} samples to {out_path}")


if __name__ == "__main__":
    main()
