-- Initial schema for Unblock.
-- Applied automatically on first container start via docker-compose
-- (mounted into /docker-entrypoint-initdb.d). For schema changes after
-- the team is up and running, switch to a real migration tool (e.g. Alembic)
-- rather than editing this file directly.

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE channels (
    id   TEXT PRIMARY KEY,      -- Slack channel ID, e.g. C0123ABCD456
    name TEXT NOT NULL
);

CREATE TABLE threads (
    id         TEXT PRIMARY KEY,   -- Slack thread_ts (the root message's ts)
    channel_id TEXT NOT NULL REFERENCES channels(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE messages (
    id            TEXT PRIMARY KEY,   -- Slack message ts
    channel_id    TEXT NOT NULL REFERENCES channels(id),
    thread_id     TEXT REFERENCES threads(id),
    author        TEXT,
    text          TEXT NOT NULL,
    posted_at     TIMESTAMPTZ NOT NULL,
    permalink     TEXT,
    search_vector TSVECTOR GENERATED ALWAYS AS (to_tsvector('english', text)) STORED
);

-- Powers keyword search (exact stack trace / error code matches)
CREATE INDEX idx_messages_search ON messages USING GIN (search_vector);

CREATE TABLE embeddings (
    thread_id TEXT PRIMARY KEY REFERENCES threads(id),
    embedding VECTOR(1536) NOT NULL,  -- adjust dimension to match your embedding model
    model     TEXT NOT NULL
);

-- Powers vector similarity search
CREATE INDEX idx_embeddings_ivfflat ON embeddings
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE TABLE feedback (
    id         SERIAL PRIMARY KEY,
    query      TEXT NOT NULL,
    thread_ids TEXT[] NOT NULL,
    reaction   TEXT NOT NULL CHECK (reaction IN ('up', 'down')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
