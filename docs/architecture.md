# Architecture

## Overview

Telegram Auto Bot is an **independent automation system**. It does not use Telegram Bot API, MTProto, or browser automation. All Telegram-like data flows through a replaceable `DataProvider` (default: `MockDataProvider`).

```text
Chrome Extension (React/Vite, MV3, Side Panel)
        │ HTTPS REST
        ▼
FastAPI Application
        ├── API Layer (thin routes)
        ├── Service Layer (business logic)
        ├── AutomationEngine + APScheduler
        ├── AIProvider (OpenAI | Claude)
        ├── DataProvider (Mock | future External)
        └── PostgreSQL (SQLAlchemy + Alembic)
```

## Provider abstractions

### DataProvider

- `search_groups(query, exclude_joined, limit=50)`
- `get_group(group_id)`
- `validate_group_id(group_id)`
- `get_messages(group_id, limit, after_message_id?)`
- `publish_post(group_id, content)` → simulates post + replace previous app post
- `get_latest_message(group_id)`
- `simulate_replies` (seed/demo)

### AIProvider

- `analyze_group(group, messages_sample)` → structured Pydantic model
- `recommend_post(group_analysis, posts)` → ranked recommendations
- `analyze_opportunities(group, messages)` → investment/partnership candidates

Invalid AI JSON: one correction retry, then error to client.

## Automation

- **Bot state**: `STOPPED | RUNNING | PAUSED | ERROR` (persisted)
- **Scheduler settings**: auto mode, hours, days, interval, min messages, max posts/day
- **Feed rotation**: persistent `current_feed_index`, ordered feed items
- **Eligibility**: count messages between last app post and latest group message ≥ `minimum_messages`
- **On success**: history, counters, mock replace previous post
- **On skip/fail**: record history, advance index (no infinite retry)

Extension only controls the server; APScheduler runs posting ticks server-side.

## Security

- Secrets in server `.env` only
- Extension stores only `apiBaseUrl` (chrome.storage)
- Production: HTTPS, CORS, auth (placeholder hooks in Phase 7)

## Monorepo layout

See repository root `README.md` and `docs/database.md`.
