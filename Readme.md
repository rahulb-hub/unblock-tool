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
3. Start Postgres (with pgvector). It's mapped to **host port 5433**, not the
   default 5432, to avoid clashing with a locally installed Postgres:
   ```
   docker-compose up -d db
   ```
   On first container start this only enables the pgvector extension
   (`storage/migrations/0001_initial_schema.sql`) — no tables exist yet.
4. Create a virtualenv and install Python dependencies:
   ```
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
5. Create the tables by running the Alembic migrations:
   ```
   alembic upgrade head
   ```
6. You should now have a running database at the `DATABASE_URL` in your `.env`
   (default `postgresql://unblock:unblock@localhost:5433/unblock`) with all
   tables created: `channels`, `threads`, `messages`, `embeddings`,
   `ingestion_runs`, `feedback`.

### Inspecting the database in DBeaver

Create a new PostgreSQL connection with:

| Field    | Value      |
|----------|------------|
| Host     | `localhost`|
| Port     | `5433`     |
| Database | `unblock`  |
| Username | `unblock`  |
| Password | `unblock`  |

Leave SSL disabled — it's a local dev container. Once connected, expand
`unblock` → `Schemas` → `public` → `Tables` to browse the schema.

## Schema & migrations (Dev 2)

Schema is owned by SQLAlchemy models in `storage/models/` (declarative base in
`storage/models/base.py`) and applied via Alembic (`alembic.ini`, `alembic/`).
`storage/migrations/0001_initial_schema.sql` is legacy — it now only enables
the `vector` extension on first container start; it no longer creates tables.

To change the schema:
1. Edit or add a model in `storage/models/` (and import it in
   `storage/models/__init__.py` so Alembic sees it).
2. Generate a migration:
   ```
   alembic revision --autogenerate -m "describe the change"
   ```
3. Review the generated file in `alembic/versions/` — autogenerate doesn't
   always get pgvector imports or naming quite right, adjust if needed.
4. Apply it:
   ```
   alembic upgrade head
   ```

Because Dev 1 (ingestion) and Dev 3 (retrieval) both write to and read from
this schema, flag changes here to the team the same day they happen.

## Contribution workflow

- Branch off `main` per feature (`git checkout -b dev1/backfill-script`).
- Open a PR before merging; at least one other developer reviews it.
- Anyone touching `shared/models.py` pings the team first — Dev 3 and Dev 4
  both build directly against those types, so a silent change there breaks
  someone else's work without warning.
