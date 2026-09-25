"""Run local sample Slack retrieval with real Voyage embeddings."""

from retrieval.claude_prompt import build_claude_messages
from retrieval.embedding_service import EmbeddingService
from retrieval.exceptions import ConfigError
from retrieval.keyword_search import keyword_search
from retrieval.models import MergedSearchResult, StoredThreadEmbedding
from retrieval.ranking import reciprocal_rank_fusion
from retrieval.sample_slack_threads import SAMPLE_SLACK_THREADS
from retrieval.vector_search import vector_search


def embed_sample_slack_threads(
	service: EmbeddingService | None = None,
) -> list[StoredThreadEmbedding]:
	"""Embed the sample Slack thread text with Voyage document embeddings."""
	service = service or EmbeddingService()
	texts = [document.chunk.text for document in SAMPLE_SLACK_THREADS]
	embeddings = service.embed_batch(texts, input_type="document")

	return [
		StoredThreadEmbedding(
			id=document.id,
			chunk=document.chunk,
			vector=embedding.vector,
		)
		for document, embedding in zip(SAMPLE_SLACK_THREADS, embeddings)
	]


def run_sample_voyage_hybrid_search(
	query: str,
	service: EmbeddingService | None = None,
	limit: int = 3,
) -> list[MergedSearchResult]:
	"""Embed sample Slack data and the query with Voyage, then rank results locally."""
	service = service or EmbeddingService()
	documents = embed_sample_slack_threads(service)
	query_embedding = service.embed_query(query)
	keyword_hits = keyword_search(query, documents, limit=limit)
	vector_hits = vector_search(query_embedding.vector, documents, limit=limit)
	return reciprocal_rank_fusion(keyword_hits, vector_hits, limit=limit)


def build_sample_voyage_prompt(
	query: str,
	service: EmbeddingService | None = None,
	limit: int = 3,
) -> list[dict[str, str]]:
	"""Build a Claude-ready prompt from Voyage-ranked sample Slack results."""
	results = run_sample_voyage_hybrid_search(query, service=service, limit=limit)
	return build_claude_messages(query, results)


def main() -> None:
	query = "Learner API forbidden 403 after laptop refresh GitHub SSO"
	try:
		results = run_sample_voyage_hybrid_search(query)
	except ConfigError as exc:
		print(f"Cannot run Voyage sample search: {exc}")
		print("Add EMBEDDINGS_API_KEY to your local .env or set it in this terminal.")
		return

	for result in results:
		print(result.document.id, result.score, result.document.chunk.permalink)

	print("\nClaude prompt preview:\n")
	print(build_claude_messages(query, results)[1]["content"])


if __name__ == "__main__":
	main()