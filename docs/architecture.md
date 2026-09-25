# Telegram Auto Bot Architecture

This project is an independent automation system. It does not use the Telegram Bot API, MTProto, Telegram Client API, Telegram Web, or browser automation. All current activity is simulated by a replaceable `DataProvider`.

## Runtime

```text
Chrome side panel (React + TypeScript)
        | configurable HTTP URL
        v
FastAPI REST API
        |
        +-- services: groups, posts, feed, automation, notifications
        +-- providers/data: DataProvider -> MockDataProvider
        +-- providers/ai: AIProvider -> OpenAIProvider | ClaudeProvider
        +-- APScheduler worker
        v
PostgreSQL (SQLAlchemy + Alembic)
```

The extension owns presentation and user intent. The server owns persistence, bot state, scheduling, posting eligibility, feed rotation, mock posting, and AI credentials. API routes remain thin and call service-layer methods.

## Provider boundaries

`DataProvider` exposes group search, messages, simulated posting/replacement, and replies. The mock implementation is deterministic and never leaves the application. `AIProvider` returns Pydantic-validated structured results. Provider selection is server-side through environment configuration; secrets never enter the extension bundle.

## Automation loop

`AutomationEngine` checks persisted bot state, scheduler rules, daily limits, and the feed cursor before each operation. It processes enabled feed items in order, records success/skip/failure, advances the cursor even after a skip or failure, and never performs real Telegram actions.

## Delivery phases

1. Foundation: configuration, database, migrations, Docker, API health.
2. Mock groups and analysis, feed, and posts.
3. Scheduler, persistent bot state, ordered rotation, eligibility and history.
4. Replies, notifications, opportunities, and AI provider integrations.
5. Production hardening: auth, HTTPS deployment, rate limiting, structured logs, and broader test coverage.
