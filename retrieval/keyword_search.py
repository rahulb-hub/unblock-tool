"""In-memory keyword search over thread chunks for local tests and demos."""

import re
from collections import Counter
from typing import Sequence

from retrieval.models import SearchHit, StoredThreadEmbedding


TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9_./:-]+")


def keyword_search(
    query: str,
    documents: Sequence[StoredThreadEmbedding],
    limit: int = 5,
) -> list[SearchHit]:
    """Rank documents by simple token overlap with the query."""
    query_terms = _tokenize(query)
    if not query_terms:
        return []

    hits = []
    for document in documents:
        score = _keyword_score(query_terms, query, document.chunk.text)
        if score > 0:
            hits.append((document, score))

    hits.sort(key=lambda item: item[1], reverse=True)
    return [
        SearchHit(document=document, score=score, rank=rank, source="keyword")
        for rank, (document, score) in enumerate(hits[:limit], start=1)
    ]


def _keyword_score(query_terms: Counter, query: str, text: str) -> float:
    text_terms = _tokenize(text)
    overlap = sum(
        min(count, text_terms.get(term, 0)) for term, count in query_terms.items()
    )
    if overlap == 0:
        return 0.0

    exact_bonus = 2.0 if query.lower() in text.lower() else 0.0
    return float(overlap) + exact_bonus


def _tokenize(text: str) -> Counter:
    return Counter(token.lower() for token in TOKEN_PATTERN.findall(text))