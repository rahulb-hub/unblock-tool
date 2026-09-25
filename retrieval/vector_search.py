"""In-memory vector search over embedded thread chunks for local tests and demos."""

import math
from typing import Sequence

from retrieval.models import SearchHit, StoredThreadEmbedding


def vector_search(
    query_vector: Sequence[float],
    documents: Sequence[StoredThreadEmbedding],
    limit: int = 5,
) -> list[SearchHit]:
    """Rank documents by cosine similarity to the query vector."""
    hits = [
        (document, cosine_similarity(query_vector, document.vector))
        for document in documents
    ]
    hits.sort(key=lambda item: item[1], reverse=True)
    return [
        SearchHit(document=document, score=score, rank=rank, source="vector")
        for rank, (document, score) in enumerate(hits[:limit], start=1)
    ]


def cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right):
        raise ValueError("Vectors must have the same dimension for cosine similarity.")

    dot_product = sum(
        left_value * right_value for left_value, right_value in zip(left, right)
    )
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot_product / (left_norm * right_norm)