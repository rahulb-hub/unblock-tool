import unittest

from retrieval.models import EmbeddingResult
from retrieval.providers import EmbeddingProvider
from retrieval.sample_voyage_search import (
	build_sample_voyage_prompt,
	embed_sample_slack_threads,
	run_sample_voyage_hybrid_search,
)


class FakeVoyageProvider(EmbeddingProvider):
	name = "fake-voyage"
	model = "fake-voyage-model"

	def __init__(self):
		self.calls = []

	def generate_embeddings(self, texts, input_type):
		self.calls.append((list(texts), input_type))
		vectors = []
		for text in texts:
			lower_text = text.lower()
			if "learner" in lower_text or "github sso" in lower_text:
				vectors.append([1.0, 0.0, 0.0])
			elif "calendar" in lower_text or "graph" in lower_text:
				vectors.append([0.0, 1.0, 0.0])
			else:
				vectors.append([0.0, 0.0, 1.0])
		return vectors


class FakeEmbeddingService:
	def __init__(self):
		self.provider = FakeVoyageProvider()

	def embed_batch(self, texts, input_type="document"):
		vectors = self.provider.generate_embeddings(texts, input_type)
		return [
			EmbeddingResult(
				vector=vector,
				provider=self.provider.name,
				model=self.provider.model,
				dimension=3,
				input_type=input_type,
			)
			for vector in vectors
		]

	def embed_query(self, query):
		return self.embed_batch([query], input_type="query")[0]


class SampleVoyageSearchTest(unittest.TestCase):
	def test_embeds_sample_threads_as_documents(self):
		service = FakeEmbeddingService()

		documents = embed_sample_slack_threads(service)

		self.assertEqual(len(documents), 3)
		self.assertEqual(service.provider.calls[0][1], "document")
		self.assertEqual(documents[0].id, "thread-learner-api-403")

	def test_embeds_query_and_returns_expected_top_result(self):
		service = FakeEmbeddingService()

		results = run_sample_voyage_hybrid_search(
			"Learner API forbidden 403 GitHub SSO",
			service=service,
		)

		self.assertEqual(results[0].document.id, "thread-learner-api-403")
		self.assertEqual(service.provider.calls[-1][1], "query")

	def test_builds_prompt_with_voyage_ranked_sample_results(self):
		service = FakeEmbeddingService()

		messages = build_sample_voyage_prompt(
			"Calendar sync Microsoft Graph timeout",
			service=service,
		)

		self.assertIn("thread-calendar-graph-timeout", messages[1]["content"])
		self.assertIn("Permalink:", messages[1]["content"])


if __name__ == "__main__":
	unittest.main()