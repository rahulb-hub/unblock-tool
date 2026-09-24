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