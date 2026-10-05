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

## Dev 1: Slack ingestion

Create and install a Slack app in the target workspace with the bot scopes
`channels:history` and `channels:read`, then invite the bot to each monitored
public channel. For private channels, add the corresponding `groups:history`
and `groups:read` scopes and invite the bot there as well. Put the bot token
and channel IDs in `.env`; never commit the real token. `SLACK_CHANNEL_IDS`
uses JSON list syntax, for example `["C0123ABCD456"]`.

Run one backfill manually:

```sh
python -m ingestion.scripts.backfill --channel C0123ABCD456
```

Or omit `--channel` to use `SLACK_CHANNEL_IDS`. The pipeline reads each
channel after its saved timestamp, follows Slack pagination cursors, fetches
full replies for affected threads (including roots older than the checkpoint),
groups and deduplicates messages, and filters bot/system/reaction noise. It
writes the current batch as JSON to `output/threads.json` by default. Each
thread includes its channel ID, root timestamp, root message, and ordered
messages; these map to Dev 2's channel, thread, and message records.

The JSON output is atomically replaced before any channel checkpoint advances.
If output writing fails, the next run fetches the same messages again. The
checkpoint file is `storage/checkpoints.json`; the script takes a non-blocking
process lock so two scheduled runs cannot race over that checkpoint/output.
Schedule `python -m ingestion.scripts.backfill` with cron or your job scheduler
and keep runs single-instance. For example, a daily cron entry from the repo
directory can run `python -m ingestion.scripts.backfill` and append logs to a
managed log destination.

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
