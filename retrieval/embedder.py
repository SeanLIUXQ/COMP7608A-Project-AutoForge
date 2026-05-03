from __future__ import annotations

import re


def tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9_]+", text.lower()))


def lexical_similarity(query: str, document: str) -> float:
    query_tokens = tokenize(query)
    document_tokens = tokenize(document)
    if not query_tokens or not document_tokens:
        return 0.0
    overlap = len(query_tokens & document_tokens) / len(query_tokens)
    length_ratio = min(len(query_tokens), len(document_tokens)) / max(len(query_tokens), len(document_tokens))
    return round((overlap * 0.8) + (length_ratio * 0.2), 4)
