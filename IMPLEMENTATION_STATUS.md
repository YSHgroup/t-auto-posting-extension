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
             Mock provider for demo data
```

## 2. What is implemented

### Extension

- React + TypeScript side panel with Dashboard, Groups, Feed, Posts, Scheduler, History, Notifications, Opportunities, and Settings pages.
- Configurable backend URL.
- A stable random installation UUID stored in `chrome.storage.local`; the extension sends it as `X-Installation-ID`.
- A content script injected only on `https://web.telegram.org/*`.
- The Telegram prompt asks the user to confirm a group identity and choose **Add to feed** or **Skip this group**. Both choices are saved, and the prompt is suppressed after a decision for that installation.
- The prompt does not inspect Telegram chat messages or click Telegram controls.
- Feed offers an Open Telegram link and a Copy selected post action. The user reviews, sends, and if needed deletes messages manually.
- Group Detail accepts up to 500 message lines that the user manually copies from Telegram.
- Group Detail also lets the user manually log a copied reply to create a private notification.

### Backend and database

- FastAPI API, SQLAlchemy models, and Alembic migrations.
- OpenAI and Anthropic Claude AI provider abstractions; API keys remain on the server.
- Mock data provider for demo groups/messages and the original simulated workflow.
- Per-installation scoping for posts, feed, analyses, assignments, history, replies, notifications, opportunities, scheduler/bot state, AI/app settings, skipped-group decisions, and manually imported message observations.
- Migration `002_installation_ownership` adds ownership columns and the new skipped-group and manually imported message tables. Existing rows are assigned to the `legacy` owner.
- User-entered group IDs and Telegram URLs can be placed in the feed.
- Real group analysis and opportunity classification can use message text only after the user manually imports it.
- A user-confirmed manual send can be recorded in the current installation's history. The server does not verify Telegram delivery.
- The background scheduler iterates installations independently, but it operates only on mock-provider groups. Unknown real groups are skipped; no real message is published.

### Data and feature boundaries

| Capability | Current behavior |
|---|---|
| Group keyword search | Demo/mock catalog only; not a live Telegram search |
| Add/skip a real Telegram group | User-confirmed prompt or manual group ID/URL |
| Analyze real group content | User manually copies/imports up to 500 messages; AI analyzes that supplied text |
| Post recommendation | AI suggestion based on a saved analysis and the user's post templates; user selects a post |
| Send a real Telegram post | Manual: copy, open Telegram, review, and send yourself |
| Record a real send | User-confirmed history record; not delivery-verified |
| Delete/replace a real Telegram post | Manual only; no Telegram message is deleted by the extension |
| Count live messages since the last real post | Not available; Telegram messages are not collected |
| Real Telegram replies/notifications | Manual copied-reply logging only; no reply monitoring |
| Real opportunity discovery | Runs on manually imported text; author attribution requires an `@username: message` prefix |
| Auto Mode | Mock simulation only; it does not operate Telegram Web |

## 3. Important identity and security limitation

The installation UUID keeps ordinary Chrome profiles' application rows separated. It is a client-provided identifier, **not authenticated identity**: a caller can forge a UUID header. Do not expose this API as a public multi-tenant service until a trusted sign-in or pairing flow, server-issued credentials, token hashing/rotation, rate limiting, and account recovery have been implemented.

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
4. From `server`, apply Alembic migrations with `alembic upgrade head`.
5. Start FastAPI with Uvicorn on port 8000 (or your chosen port).
6. Visit `/docs` on the API host to inspect the generated OpenAPI documentation.

### Extension setup

1. From `extension`, install npm dependencies and create the production extension build.
2. In `chrome://extensions`, enable Developer mode and load `extension/dist` as an unpacked extension.
3. Open the extension side panel and use Settings to enter the backend URL.
4. Ensure the API is reachable from the extension. FastAPI allows Chrome extension origins using a Chrome-extension origin regex; continue to use HTTPS and restrict origins appropriately in production.

### Optional mock demo data

- The command-line seed creates demo records under the `legacy` owner, which is not the UUID of a newly installed extension.
- To initialize/reset demo records for the current extension installation, use **Settings → Reset demo data**. This clears that installation's owned demo records and seeds its sample workflow. Do not use it if you need to preserve that installation's data.
- Mock group search is still the original catalog and should not be mistaken for real Telegram search.

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

For a fully automatic real-Telegram workflow, the following capabilities are intentionally **not implemented**: live message/member collection, live message counts, Telegram posting, automatic deletion, and automatic reply monitoring. This project will not simulate these capabilities as successful. Any future integration must use an authorized, supported data/action mechanism and be reviewed for platform terms, user consent, privacy, and account safety.

Before public production deployment, also implement verified user authentication/authorization rather than relying on `X-Installation-ID`, production rate limiting, secret management, backups, and operational monitoring.

## 6. Documentation map

- `README.md` — overview and basic setup.
- `docs/architecture.md` — component/provider boundaries and scheduler behavior.
- `docs/api.md` — REST routes and request identity header.
- `docs/database.md` — tables, ownership, and indexes.
- This document — implementation status, operating limits, and user setup steps.

## 7. Validation status

Dependencies, tests, and builds were not run for this handoff. The user should install the required dependencies and perform the build/database migration before trying the workflow. Editor diagnostics may report missing frontend modules or Chrome typings until npm dependencies are installed.
