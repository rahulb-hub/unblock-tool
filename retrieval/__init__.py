# Dev 3 — AI/Retrieval: embeddings, keyword + vector hybrid search,
# merge & rank, Claude synthesis. Exposes the search endpoint bot/ calls.

from retrieval.claude_prompt import build_claude_messages
from retrieval.embedding_service import EmbeddingService
from retrieval.keyword_search import keyword_search
from retrieval.models import (
	EmbeddedThreadChunk,
	EmbeddingResult,
	MergedSearchResult,
	SearchHit,
	StoredThreadEmbedding,
	ThreadChunk,
)
from retrieval.ranking import reciprocal_rank_fusion
from retrieval.sample_slack_threads import (
	SAMPLE_QUERY_CASES,
	SAMPLE_SLACK_THREADS,
	run_sample_hybrid_search,
)
from retrieval.vector_search import cosine_similarity, vector_search

__all__ = [
	"EmbeddedThreadChunk",
	"EmbeddingResult",
	"EmbeddingService",
	"MergedSearchResult",
	"SAMPLE_QUERY_CASES",
	"SAMPLE_SLACK_THREADS",
	"SearchHit",
	"StoredThreadEmbedding",
	"ThreadChunk",
	"build_claude_messages",
	"cosine_similarity",
	"keyword_search",
	"reciprocal_rank_fusion",
	"run_sample_hybrid_search",
	"vector_search",
]
