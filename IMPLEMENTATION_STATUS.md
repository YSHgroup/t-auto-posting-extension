# Implementation Status

## Current State

This repository implements an independent Telegram-style automation assistant. It does not use the Telegram Bot API, MTProto, Telegram Client API, Telegram Web automation, Selenium, Puppeteer, or Playwright.

The supported demonstration mode is `mock`:

```text
Chrome MV3 side panel
        |
        | REST
        v
FastAPI services
        |
        +-- PostgreSQL via SQLAlchemy/Alembic
        +-- MockDataProvider
        +-- OpenAIProvider or ClaudeProvider
        +-- APScheduler -> AutomationEngine
```

## Completed Workflow

- React + TypeScript + Vite Chrome Manifest V3 side panel.
- Configurable backend URL stored by the extension.
- FastAPI routes for dashboard, groups, analysis, feed, posts, scheduler, bot state, history, notifications, settings, and opportunities.
- PostgreSQL models and Alembic initial migration.
- Fifty-plus catalog groups and seeded mock users/messages.
- Search by group name, username, description, category, and keyword, excluding joined groups and limiting results to 50.
- Group analysis through the AI provider abstraction with structured Pydantic output.
- Post CRUD, duplication, enable/disable, active-post validation, and feed assignments.
- AI post recommendation using `feed_item_id` with manual selection retained in the feed assignment.
- Persistent bot state, feed cursor, ordered rotation, working days, timezone, interval, daily limit, and minimum-message eligibility.
- Mock publishing with previous application posts marked as replaced.
- Success, skipped, and failed posting history with counters.
- Mock reply simulation that creates a group message, reply, and unread notification.
- Opportunity analysis over up to 500 messages, with repeat scans replacing prior group results.
- Seeded runnable demo feed with a selected sample post.
- OpenAI and Anthropic provider implementations with mock fallback when credentials are absent.
- Docker Compose PostgreSQL and FastAPI setup.

## Database Shape

The schema includes:

```text
groups
users
group_messages
group_analysis
posts
feed_items
post_assignments
post_history
replies
notifications
scheduler_settings
bot_state
opportunities
ai_settings
app_settings
```

Relationships and indexes are defined in `server/app/models/entities.py` and the initial Alembic migration.

## Setup To Do

1. Install Python 3.14 and Node.js 22.
2. Copy `.env.example` to `.env` and set database/AI values as needed.
3. Start PostgreSQL with `docker compose up -d db` or use an existing PostgreSQL server.
4. Install backend dependencies from `server` with `pip install -e ".[dev]"`.
5. Run `alembic upgrade head` from `server`.
6. Seed demo data with `python -m app.database.seed`.
7. Start the API with `uvicorn app.main:app --reload --port 8000`.
8. Install extension dependencies from `extension` with `npm install`.
9. Build with `npm run build` and load `extension/dist` as an unpacked Chrome extension.
10. Set the extension backend URL to `http://localhost:8000`.

## Demo Flow

1. Search `blockchain startup` from Groups.
2. Open a group and run analysis.
3. Create or edit posts.
4. Add groups to Feed and select posts.
5. Configure scheduler values and start the bot.
6. Review Dashboard and History as the server scheduler processes feed items.
7. Use the simulated-reply endpoint or seeded reply to view Notifications.
8. Run Explore Opportunities and review evidence levels and confidence.

The mock reply endpoint is:

```http
POST /api/groups/{group_id}/simulate-reply
Content-Type: application/json

{"username":"demo_user","message":"I am interested in the partnership."}
```

## Deliberate Boundaries

- `mock` is the only implemented data mode. Selecting another mode returns an explicit error; no fake external integration is silently used.
- Authentication, production token handling, rate limiting, HTTPS termination, and secret-vault integration remain deployment hardening tasks.
- The extension does not receive or store OpenAI, Anthropic, or database credentials.

## Validation Note

Per the requested workflow, dependency installation, tests, and production builds were not run in this pass. Run the setup commands above after installing Python 3.14, Node.js 22, PostgreSQL, and project dependencies.
