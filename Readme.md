# Unblock – Slack Engineering Knowledge Retrieval

Unblock is an engineering assistant that helps developers find relevant discussions and solutions from Slack when they are blocked by an issue.

## Overview

The system collects useful engineering conversations from Slack, processes them, and makes them searchable.

High-level flow:

```text
Slack
  ↓
Slack Ingestion
  ↓
Thread Grouping & Filtering
  ↓
Database
  ↓
Keyword + Vector Search
  ↓
Relevant Threads
  ↓
AI-generated Answer
  ↓
Slack
```

## Folder structure

```
ingestion/   Dev 1 — Slack backfill, pagination, thread grouping, noise filtering
storage/     Dev 2 — DB access layer + schema migrations
retrieval/   Dev 3 — embeddings, hybrid search, merge & rank, Claude synthesis
bot/         Dev 4 — Slack app, /unblock command, Block Kit formatting, feedback
shared/      Types used by more than one track (see shared/models.py) —
             changes here affect Dev 3 and Dev 4 directly, flag them to the team
```

## Setup

1. Clone the repo.
2. Copy the env template and fill in real values:
   ```
   cp .env.example .env
   ```
3. Start Postgres (with pgvector) and apply the initial schema automatically:
   ```
   docker-compose up -d
   ```
4. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```
5. You should now have a running database at the `DATABASE_URL` in your `.env`,
   with the schema in `storage/migrations/0001_initial_schema.sql` already applied.

## Making schema changes

The first migration runs automatically because docker-compose mounts
`storage/migrations/` into Postgres's init directory — but that only happens
on the *first* container start. Once the team is actively working, adopt a
real migration tool (e.g. Alembic) for further schema changes rather than
editing `0001_initial_schema.sql` directly, so changes are tracked and
re-runnable instead of applied by hand.

## Contribution workflow

- Branch off `main` per feature (`git checkout -b dev1/backfill-script`).
- Open a PR before merging; at least one other developer reviews it.
- Anyone touching `shared/models.py` pings the team first — Dev 3 and Dev 4
  both build directly against those types, so a silent change there breaks
  someone else's work without warning.
