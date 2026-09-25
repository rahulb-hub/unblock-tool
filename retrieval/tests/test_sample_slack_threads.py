import unittest

from retrieval.claude_prompt import build_claude_messages
from retrieval.sample_slack_threads import SAMPLE_QUERY_CASES, run_sample_hybrid_search


class SampleSlackThreadsTest(unittest.TestCase):
	def test_sample_queries_return_expected_thread_in_top_results(self):
		for case in SAMPLE_QUERY_CASES:
			with self.subTest(query=case.query):
				results = run_sample_hybrid_search(case.query, case.query_vector)
				result_ids = [result.document.id for result in results]

				self.assertIn(case.expected_thread_id, result_ids[:2], case.note)

	def test_claude_prompt_includes_sample_thread_citations(self):
		case = SAMPLE_QUERY_CASES[0]
		results = run_sample_hybrid_search(case.query, case.query_vector)

		messages = build_claude_messages(case.query, results)
		user_prompt = messages[1]["content"]

		self.assertIn("Thread ID: thread-learner-api-403", user_prompt)
		self.assertIn("https://slack.example/archives/CENGHELP/p1790000001", user_prompt)
		self.assertIn("Permalink:", user_prompt)


if __name__ == "__main__":
	unittest.main()