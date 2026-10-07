"""Production retrieval service over the real Unblock database."""

from sqlalchemy.orm import Session

from retrieval.embeddings import EmbeddingService
from retrieval.models import MergedSearchResult
from retrieval.search.database import keyword_search_db, vector_search_db
from retrieval.search.ranking import reciprocal_rank_fusion
from shared.models import Citation, SearchRequest, SearchResponse
from storage.db import SessionLocal


class RetrievalSearchService:
    """Search real ingested Slack data and return the shared bot response shape."""

    def __init__(
        self,
        embedding_service: EmbeddingService | None = None,
        session_factory=SessionLocal,
    ) -> None:
        self.embedding_service = embedding_service or EmbeddingService()
        self.session_factory = session_factory

    def search(self, request: SearchRequest, limit: int = 5) -> SearchResponse:
        with self.session_factory() as session:
            results = self.search_session(session, request.query, limit=limit)

        return SearchResponse(
            answer=self._build_answer(request.query, results),
            citations=_build_citations(results),
        )

    def search_session(
        self,
        session: Session,
        query: str,
        limit: int = 5,
    ) -> list[MergedSearchResult]:
        query_embedding = self.embedding_service.embed_query(query)
        keyword_hits = keyword_search_db(session, query, limit=limit * 2)
        vector_hits = vector_search_db(session, query_embedding.vector, limit=limit * 2)
        return reciprocal_rank_fusion(keyword_hits, vector_hits, limit=limit)

    def _build_answer(self, query: str, results: list[MergedSearchResult]) -> str:
        if not results:
            return "No strong match was found in the indexed Slack threads."
        top_result = results[0]
        chunk = top_result.document.chunk
        snippet = _trim_snippet(chunk.text)
        source = f" Source: {chunk.permalink}" if chunk.permalink else ""
        return (
            f"Top Slack match for '{query}' was found in #{chunk.channel}. "
            f"{snippet}{source}"
        )


def _build_citations(results: list[MergedSearchResult]) -> list[Citation]:
    citations: list[Citation] = []
    for result in results:
        chunk = result.document.chunk
        if not chunk.permalink:
            continue
        citations.append(
            Citation(
                thread_id=result.document.id,
                permalink=chunk.permalink,
                snippet=chunk.text[:300],
            )
        )
    return citations


def _trim_snippet(text: str, max_length: int = 300) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= max_length:
        return normalized
    return normalized[: max_length - 3].rstrip() + "..."