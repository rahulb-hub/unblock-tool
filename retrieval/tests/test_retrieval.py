import unittest

from retrieval import (
	StoredThreadEmbedding,
	ThreadChunk,
	build_claude_messages,
	cosine_similarity,
	keyword_search,
	reciprocal_rank_fusion,
	vector_search,
)


def document(document_id, text, vector):
	return StoredThreadEmbedding(
		id=document_id,
		chunk=ThreadChunk(
			text=text,
			channel="eng-help",
			author="alex",
			timestamp="2026-09-20T10:15:00Z",
			permalink=f"https://slack.example/{document_id}",
		),
		vector=vector,
	)


class RetrievalTest(unittest.TestCase):
	def test_keyword_search_prioritizes_exact_error_terms(self):
		documents = [
			document(
				"learner",
				"Learner API returned 403 until GitHub SSO was renewed.",
				[1, 0],
			),
			document(
				"calendar",
				"Calendar sync failed with Microsoft Graph timeout.",
				[0, 1],
			),
		]

		hits = keyword_search("Learner API 403", documents)

		self.assertEqual(hits[0].document.id, "learner")
		self.assertEqual(hits[0].source, "keyword")

	def test_vector_search_uses_cosine_similarity(self):
		documents = [
			document("close", "Similar issue", [1, 0]),
			document("far", "Different issue", [0, 1]),
		]

		hits = vector_search([0.9, 0.1], documents)

		self.assertEqual(hits[0].document.id, "close")
		self.assertGreater(cosine_similarity([1, 0], [0.9, 0.1]), 0.9)

	def test_reciprocal_rank_fusion_merges_keyword_and_vector_hits(self):
		documents = [
			document("same", "Learner API issue", [1, 0]),
			document("other", "Calendar issue", [0, 1]),
		]
		keyword_hits = keyword_search("Learner API", documents)
		vector_hits = vector_search([1, 0], documents)

		merged = reciprocal_rank_fusion(keyword_hits, vector_hits)

		self.assertEqual(merged[0].document.id, "same")
		self.assertEqual(merged[0].keyword_rank, 1)
		self.assertEqual(merged[0].vector_rank, 1)

	def test_claude_prompt_requires_grounded_answer_and_citations(self):
		documents = [
			document("learner", "Re-authenticate GitHub SSO to fix 403.", [1, 0])
		]
		merged = reciprocal_rank_fusion(keyword_search("403 GitHub", documents), [])

		messages = build_claude_messages("Getting forbidden from Learner API", merged)

		self.assertIn("using only the candidate Slack threads", messages[0]["content"])
		self.assertIn("https://slack.example/learner", messages[1]["content"])
		self.assertIn("no-strong-match", messages[1]["content"])


if __name__ == "__main__":
	unittest.main()