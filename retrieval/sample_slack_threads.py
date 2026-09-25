"""Small realistic Slack-like dataset for local retrieval testing."""

from dataclasses import dataclass

from retrieval.keyword_search import keyword_search
from retrieval.models import MergedSearchResult, StoredThreadEmbedding, ThreadChunk
from retrieval.ranking import reciprocal_rank_fusion
from retrieval.vector_search import vector_search


@dataclass(frozen=True)
class SampleQueryCase:
	query: str
	query_vector: list[float]
	expected_thread_id: str
	note: str


SAMPLE_SLACK_THREADS = [
	StoredThreadEmbedding(
		id="thread-learner-api-403",
		chunk=ThreadChunk(
			text=(
				"Learner API is returning 403 for several developers after laptop refresh. "
				"Root cause was expired GitHub SSO on the org. Re-authenticating GitHub "
				"SSO and retrying the request fixed the forbidden response."
			),
			channel="eng-help",
			author="alex",
			timestamp="2026-09-18T09:24:00Z",
			permalink="https://slack.example/archives/CENGHELP/p1790000001",
			metadata={"team": "platform", "service": "learner-api"},
		),
		vector=[1.0, 0.0, 0.0],
	),
	StoredThreadEmbedding(
		id="thread-calendar-graph-timeout",
		chunk=ThreadChunk(
			text=(
				"Calendar sync job failed with Microsoft Graph timeout and 504 errors. "
				"The fix was to rotate the Graph client secret in Key Vault, restart the "
				"calendar-worker deployment, and replay the failed sync batch."
			),
			channel="eng-help",
			author="priya",
			timestamp="2026-09-19T14:08:00Z",
			permalink="https://slack.example/archives/CENGHELP/p1790000002",
			metadata={"team": "integrations", "service": "calendar-worker"},
		),
		vector=[0.0, 1.0, 0.0],
	),
	StoredThreadEmbedding(
		id="thread-checkout-imagepullbackoff",
		chunk=ThreadChunk(
			text=(
				"Checkout service pods were stuck in ImagePullBackOff after the release. "
				"The image tag was published to staging but not promoted to prod ECR. "
				"Promoting the image and restarting the rollout resolved the deploy block."
			),
			channel="deploy-help",
			author="maya",
			timestamp="2026-09-20T11:42:00Z",
			permalink="https://slack.example/archives/CDEPLOY/p1790000003",
			metadata={"team": "payments", "service": "checkout"},
		),
		vector=[0.0, 0.0, 1.0],
	),
]


SAMPLE_QUERY_CASES = [
	SampleQueryCase(
		query="Learner API forbidden 403 after laptop refresh GitHub SSO",
		query_vector=[0.95, 0.03, 0.02],
		expected_thread_id="thread-learner-api-403",
		note="Expected to find the GitHub SSO fix for Learner API 403 errors.",
	),
	SampleQueryCase(
		query="Calendar sync Microsoft Graph timeout 504 client secret",
		query_vector=[0.02, 0.96, 0.02],
		expected_thread_id="thread-calendar-graph-timeout",
		note="Expected to find the Graph secret rotation and worker restart thread.",
	),
	SampleQueryCase(
		query="Checkout deploy ImagePullBackOff image tag prod ECR",
		query_vector=[0.02, 0.03, 0.95],
		expected_thread_id="thread-checkout-imagepullbackoff",
		note="Expected to find the ECR image promotion deploy fix.",
	),
]


def run_sample_hybrid_search(
	query: str,
	query_vector: list[float],
	limit: int = 3,
) -> list[MergedSearchResult]:
	"""Run local keyword + vector retrieval over the sample Slack threads."""
	keyword_hits = keyword_search(query, SAMPLE_SLACK_THREADS, limit=limit)
	vector_hits = vector_search(query_vector, SAMPLE_SLACK_THREADS, limit=limit)
	return reciprocal_rank_fusion(keyword_hits, vector_hits, limit=limit)