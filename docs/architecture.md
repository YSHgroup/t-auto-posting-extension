# Architecture

## Overview

Telegram Auto Bot is an independent group assistant. It does not use Telegram Bot API, MTProto, or Telegram Web automation. The content script only presents a user-confirmed group Add/Skip prompt. Real messages are available to AI only when the user manually copies and imports them.

```text
Chrome Extension (React/Vite, MV3, Side Panel)
        │ HTTPS REST
        ▼
FastAPI Application
        ├── API Layer (thin routes)
        ├── Service Layer (business logic)
        ├── AutomationEngine + APScheduler
        ├── AIProvider (OpenAI | Claude)
        ├── DataProvider (Mock demo only)
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
- `simulate_reply(group_id, username, message, post_id?)` (mock demo)

`get_data_provider()` selects the configured provider from `app_settings`. `mock` is
implemented; unsupported modes return an explicit error instead of silently using
mock data.

Telegram group identifiers and source URLs can be saved by a user. This is not a live Telegram data provider. The extension service worker sends only user-confirmed add/skip decisions to the API.

### AIProvider

- `analyze_group(group, messages_sample)` → structured Pydantic model
- `recommend_post(group_analysis, posts)` → ranked recommendations
- `analyze_opportunities(group, messages)` → investment/partnership candidates

Invalid AI JSON: one correction retry, then error to client.

## Automation

- **Bot state**: `STOPPED | RUNNING | PAUSED | ERROR` (persisted)
- **Scheduler settings**: auto mode, hours, days, interval, min messages, max posts/day
- **Feed rotation**: persistent `current_feed_index`, ordered feed items
- **Mock eligibility**: count mock messages between last mock post and latest mock message ≥ `minimum_messages`
- **Mock success**: history, counters, mock replacement of the prior mock post
- **On skip/fail**: record history, advance index (no infinite retry)

APScheduler runs mock-only ticks server-side. For real Telegram groups, Feed supports opening the group and copying selected post content; users manually send/delete in Telegram and can record their own confirmation. No live messages are counted and no real message is posted or deleted.

## Installation data scope

The extension stores a random installation UUID in `chrome.storage.local` and sends `X-Installation-ID`. SQLAlchemy applies owner criteria to user-owned rows, and the scheduler iterates installation-specific state. This separates ordinary installations but is not strong authentication; a trusted account/token flow is required before public deployment.

## Security

- Secrets in server `.env` only
- Extension stores `apiBaseUrl` and an installation UUID in `chrome.storage`
- Production: HTTPS, restrictive CORS, verified authentication, rate limiting

## Monorepo layout

See repository root `README.md` and `docs/database.md`.
