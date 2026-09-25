"""Build grounded answer prompts from retrieved candidate threads."""

from retrieval.models import MergedSearchResult


SYSTEM_PROMPT = """You answer developer unblock questions using only the candidate Slack threads provided.
If the candidates do not contain a strong answer, say that no strong match was found.
Do not invent causes, steps, owners, or links. Cite the thread permalink for any claim that comes from a thread."""


def build_claude_messages(
    query: str,
    results: list[MergedSearchResult],
) -> list[dict[str, str]]:
    """Build a Claude-ready message list without calling the Claude API."""
    candidate_text = "\n\n".join(
        _format_candidate(index, result) for index, result in enumerate(results, start=1)
    )
    if not candidate_text:
        candidate_text = "No candidate threads were retrieved."

    user_prompt = f"""Developer query:
{query}

Candidate threads:
{candidate_text}

Return:
1. A short answer.
2. The likely fix or next step, if present in the candidates.
3. Citations with Slack permalinks.
4. A clear no-strong-match statement if the evidence is weak."""

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]


def _format_candidate(index: int, result: MergedSearchResult) -> str:
    chunk = result.document.chunk
    permalink = chunk.permalink or "missing permalink"
    return f"""Candidate {index}
Thread ID: {result.document.id}
Channel: {chunk.channel}
Author: {chunk.author or "unknown"}
Timestamp: {chunk.timestamp or "unknown"}
Permalink: {permalink}
Merged score: {result.score:.4f}
Keyword rank: {result.keyword_rank or "not returned"}
Vector rank: {result.vector_rank or "not returned"}
Thread text:
{chunk.text}"""