# Project Overview, Implementation Status, and Next Steps

## 1. What this project is

This repository is a Chrome side-panel application built with React, TypeScript, Vite, and Manifest V3, backed by a FastAPI server and PostgreSQL. It provides group/feed management, post templates, AI analysis, scheduling settings, posting history, notifications, and opportunity classification.

It is **not a Telegram Bot**. It does not use Telegram Bot API, MTProto, Telegram Client API, Selenium, Puppeteer, or Playwright. Its Telegram Web integration is limited to a small user-confirmed Add/Skip group prompt. Real Telegram actions remain manual.

```text
Chrome side panel + Telegram Web Add/Skip prompt
                    |
                    | REST (installation-scoped)
                    v
                 FastAPI
                  /   \
        PostgreSQL    OpenAI / Claude
                    \
             Manual user-provided data provider
```

## 2. What is implemented

### Extension

- React + TypeScript side panel with Dashboard, Groups, Feed, Posts, Scheduler, History, Notifications, Opportunities, and Settings pages.
- Configurable backend URL.
- The user manually enters a Telegram username in Settings. The extension sends its normalized value as `X-Telegram-Username`; a separate installation UUID remains only as technical installation metadata.
- A content script injected only on `https://web.telegram.org/*`.
- The Telegram prompt asks the user to confirm a group identity and choose **Add to feed** or **Skip this group**. Both choices are saved, and the prompt is suppressed after a decision for that installation.
- The prompt does not inspect Telegram chat messages or click Telegram controls.
- Feed offers an Open Telegram link and a Copy selected post action. The user reviews, sends, and if needed deletes messages manually.
- While Chrome is open, Scheduler can navigate through enabled Telegram feed links in order using Chrome alarms, and notify the count of manually imported message entries since the last recorded manual send. It does not post or inspect Telegram.
- Group Detail accepts up to 500 message lines that the user manually copies from Telegram.
- Group Detail also lets the user manually log a copied reply to create a private notification.

### Backend and database

- FastAPI API, SQLAlchemy models, and Alembic migrations.
- OpenAI and Anthropic Claude AI provider abstractions; API keys remain on the server.
- Manual-only data provider; it returns only groups explicitly added by a user and message text explicitly imported under that username.
- Demo seed, simulated replies, mock search, and demo reset are disabled. Existing legacy/demo group rows are tagged as legacy by the migration and are not returned by the active provider.
- Per-username scoping for posts, feed, analyses, assignments, history, replies, notifications, opportunities, scheduler/bot state, AI/app settings, skipped-group decisions, and manually imported message observations.
- Migrations `002_installation_ownership`, `003_manual_data_only`, and `004_username_accounts` add ownership tables/columns and create an account row for each entered username. Existing owner IDs cannot be mapped to usernames automatically; those rows remain under their prior/legacy owner.
- User-entered group IDs and Telegram URLs can be placed in the feed.
- Real group analysis and opportunity classification can use message text only after the user manually imports it.
- A user-confirmed manual send can be recorded in the current installation's history. The server does not verify Telegram delivery.
- The background scheduler cannot post using the manual provider. Bot start is rejected, and the UI disables automatic posting.

### Data and feature boundaries

| Capability | Current behavior |
|---|---|
| Group keyword search | Disabled; add a group manually or through the Telegram Web Add/Skip prompt |
| Add/skip a real Telegram group | User-confirmed prompt or manual group ID/URL |
| Analyze real group content | User manually copies/imports up to 500 messages; AI analyzes that supplied text |
| Post recommendation | AI suggestion based on a saved analysis and the user's post templates; user selects a post |
| Send a real Telegram post | Manual: copy, open Telegram, review, and send yourself |
| Record a real send | User-confirmed history record; not delivery-verified |
| Delete/replace a real Telegram post | Manual only; no Telegram message is deleted by the extension |
| Count live messages since the last real post | Not available; Telegram messages are not collected |
| Real Telegram replies/notifications | Manual copied-reply logging only; no reply monitoring |
| Real opportunity discovery | Runs on manually imported text; author attribution requires an `@username: message` prefix |
| Auto Mode | Disabled for the manual provider; it does not operate Telegram Web |
| Scheduled group navigation | While Chrome is open, opens enabled Telegram URLs in feed order during saved work hours and reports manually imported message counts |

## 3. Important identity and security limitation

The manually entered Telegram username is the account data key. Entering it is never automatic. It is **not verified identity**: a caller can claim another person's username, and all clients entering the same username share that account's app data. Do not expose this API as a public multi-tenant service until trusted sign-in/pairing, server-issued credentials, token hashing/rotation, rate limiting, and account recovery have been implemented.

The extension does not store OpenAI keys, Anthropic keys, or database credentials.

## 4. What you need to do to run it

### Prerequisites

- Node.js 22+
- Python 3.14+
- PostgreSQL 16+ (Docker Compose can provide the database)
- Chrome

### Backend setup

1. Create the root `.env` from `.env.example` and set the database URL and whichever AI provider/key you want to use. Keep secrets in the server environment only.
2. Start PostgreSQL. For a local backend, start the Compose `db` service; alternatively use a PostgreSQL server you manage.
3. From `server`, create/activate a Python environment and install the project dependencies (including the development extra if you plan to run tests).
4. From `server`, apply Alembic migrations with `alembic upgrade head` (includes `004_username_accounts`).
5. Start FastAPI with Uvicorn on port 8000 (or your chosen port).
6. Visit `/docs` on the API host to inspect the generated OpenAPI documentation.

### Extension setup

1. From `extension`, install npm dependencies and create the production extension build.
2. In `chrome://extensions`, enable Developer mode and load `extension/dist` as an unpacked extension.
3. Open the extension side panel and use Settings to enter your Telegram username and backend URL.
4. Ensure the API is reachable from the extension. FastAPI allows Chrome extension origins using a Chrome-extension origin regex; continue to use HTTPS and restrict origins appropriately in production.

### Data initialization

- No sample users, groups, messages, posts, replies, or opportunities are seeded.
- `python -m app.database.seed` is intentionally disabled and returns an explanatory error.
- Migration `003` tags existing group catalog rows as legacy and sets stored data modes to manual. The active provider ignores legacy rows; it does not delete them.
- Groups and posts must be entered by the user; AI analysis requires a configured provider API key.

### Real-group manual workflow

1. Open a group in Telegram Web. Confirm **Add to feed** or **Skip this group** in the prompt. If URL parsing does not identify the group, enter its ID manually in the prompt.
2. In the extension, open Feed and select one of your post templates for the group.
3. Open the group from Feed. If you want AI analysis, manually copy message text from Telegram and paste it into Group Detail. Use one message per line; prefix a line with `@username: ` if you want author-specific opportunity analysis.
4. Review the AI result; it is an inference from the text you supplied, not a verified fact.
5. Use **Copy selected post**, switch to Telegram, review it, and send it yourself. Manually remove an earlier message if appropriate.
6. Return to Feed and choose **Record manual send**. This records your confirmation only.
7. To create a notification, manually copy a reply and enter it in Group Detail under **Log a copied reply**.
8. Use **Explore Opportunities** after importing up to 500 messages. No Telegram member/message enumeration occurs.

## 5. Remaining implementation work

The following capabilities are not implemented: automatic Telegram username detection/verification, live message/member collection, live message counts, Telegram posting, automatic deletion, and automatic reply monitoring. Users enter the username themselves. It is used as the database account key but is not authentication. Real group analysis requires user-copied messages and configured OpenAI or Claude credentials.

Before public production deployment, also implement verified user authentication/authorization rather than relying on `X-Installation-ID`, production rate limiting, secret management, backups, and operational monitoring.

## 6. Documentation map

- `README.md` — overview and basic setup.
- `docs/architecture.md` — component/provider boundaries and scheduler behavior.
- `docs/api.md` — REST routes and request identity header.
- `docs/database.md` — tables, ownership, and indexes.
- This document — implementation status, operating limits, and user setup steps.

## 7. Validation status

Dependencies, tests, and builds were not run for this handoff. The user should install the required dependencies and perform the build/database migration before trying the workflow. Editor diagnostics may report missing frontend modules or Chrome typings until npm dependencies are installed.
