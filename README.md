# Telegram Auto Bot

Independent Telegram group assistant (not a Telegram Bot). Chrome extension (React + TypeScript) + FastAPI + PostgreSQL, with user-entered group data and OpenAI / Anthropic Claude analysis.

The Telegram Web content script is restricted to `web.telegram.org` and only presents a user-confirmed Add/Skip prompt. It does not inspect chat messages, click Telegram controls, send messages, or delete messages. For real groups, users manually import copied message text for AI analysis, copy a selected post, send it themselves, and optionally record that manual action in history. Delivery is not independently verified.

## Requirements

- Node.js **22+**
- Python **3.14+**
- PostgreSQL 16+
- Docker & Docker Compose (optional)

## Quick start (Docker)

```bash
cp .env.example .env
docker compose up -d
# API: http://localhost:8000/docs
```

## Backend (local)

```bash
cd server
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp ../.env.example ../.env
# Start PostgreSQL (docker compose up -d db)
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### Database authentication troubleshooting

If `alembic upgrade head` reports `password authentication failed for user "postgres"`, PostgreSQL is reachable but the credentials in the root `.env` do not match that server. Set `DATABASE_URL` to the actual PostgreSQL username, password, host, port, and database. The example URL uses `postgres` / `postgres` and is only correct for a fresh Compose database.

For a fresh Compose database, run `docker compose up -d db` and use `postgresql+psycopg://postgres:postgres@localhost:5432/telegram_auto_bot`. If the Compose volume already existed, changing `POSTGRES_PASSWORD` in Compose does not change the password inside that existing database. Either update the database role password using the credentials you already have, or—only if the stored database data is disposable—remove the Compose volume and recreate it. Do not remove the volume if it contains data you need.

On Windows, run Alembic from the `server` directory after confirming the root `.env` has the correct `DATABASE_URL`. If the password contains URL-reserved characters such as `@`, `:`, `/`, or `#`, URL-encode those characters in the connection URL.

If the traceback shows `.venv`/Alembic and `migrations/env.py` under different checkout directories, the command is mixing two copies of the repository. Change into the intended checkout's `server` directory and invoke Alembic through that same checkout's virtual-environment Python (for example, `.venv\Scripts\python.exe -m alembic -c alembic.ini upgrade head`). Confirm the root `.env` beside that checkout is the one containing the `DATABASE_URL` you intend to use. This fixes a mixed-checkout configuration, but the PostgreSQL password must still be correct for the server listening on port 5432.

## Extension

```bash
cd extension
npm install
npm run build
```

Load `extension/dist` as an unpacked extension in Chrome. Open the side panel from the toolbar icon.

Set **Settings → API Server URL** (e.g. `http://localhost:8000`).

## AI configuration

## Recent fixes (2026-10-01)

- Dashboard UI now immediately reflects local start/stop commands and prefers the local runtime state when showing the bot status.
- The dashboard countdown (reversal counter) pauses when the local bot is stopped and resumes when restarted or resumed.
- Start / Stop / Resume / Reset actions refresh local navigation state by reading `chrome.storage` and the `telegram-auto-bot-local-navigation` alarm, keeping the displayed remaining time accurate.
- The Telegram intake content-script now detects group titles more reliably by preferring `og:title`, using additional DOM selectors, and cleaning common Telegram suffixes/trailing counts.

These changes are implemented in:

- `extension/src/pages/DashboardPage.tsx` — local state refresh, countdown behavior, and UI status preference.
- `extension/src/telegram-intake.ts` — improved group name detection.

If you keep developing, commit and build the extension before loading the unpacked `extension/dist` directory.

How to verify the fixes

1. Build and load the extension in Chrome (developer mode):

```bash
cd extension
npm install
npm run build
```

2. Open Chrome Extensions and load `extension/dist` unpacked. Open the extension side panel.

3. Dashboard behavior
- Click `START BOT` — the button should switch to `STOP BOT` and the status dot should show RUNNING immediately.
- The reversal counter should begin counting down from the scheduled interval. Click `STOP BOT` — the counter must pause and the remaining time should be preserved. Click `RESUME` — the counter should continue from the preserved time.

4. Navigation behavior
- Ensure you have at least one enabled Feed group with a `group_telegram_url`. When the local navigation interval elapses, the extension background should open the Telegram URL in a tab (or update an existing Telegram tab). If navigation does not occur, check the extension background console for alarms or errors.

5. Intake detection
- On `web.telegram.org`, open a group and confirm the Add/Skip prompt shows the cleaned group name (not noisy page title). If the title is still incorrect, open the page console and inspect `document.querySelector("meta[property='og:title']")` and the selectors listed in `extension/src/telegram-intake.ts`.

Debugging tips (when things don't navigate)

- Open the extension background page console (Extensions → background page) and watch for alarm firing logs or errors.
- Inspect `chrome.alarms.get('telegram-auto-bot-local-navigation')` and `chrome.storage.local.get('telegram_auto_bot_navigation:<username>')` in the console to verify scheduledTime and `pausedRemainingMs` values.
- If navigation does not occur but the timer reached zero, confirm feed items have `group_telegram_url` and are enabled.


Set keys in server `.env` (never in the extension):

```env
AI_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

Analysis requires the selected provider's API key to be configured on the server. There is no mock AI fallback. Remove the old `AI_MOCK_WHEN_NO_KEY` line from any pre-existing local `.env`; it is no longer used.

## Data source

No groups, messages, users, posts, replies, or opportunities are seeded. Add groups from Telegram Web using the explicit Add/Skip prompt or enter a group ID manually. Real message text must be copied and imported by the user. Live Telegram search and automatic Telegram actions are not implemented.

## Real Telegram groups (manual workflow)

The extension content script runs only on `web.telegram.org` and asks whether to add or skip the current group. For real group analysis, manually copy text into Group Detail (up to 500 messages). Feed provides an Open Telegram link and Copy selected post action; send and any deletion are performed manually by the user. Use **Record manual send** after sending, and **Log a copied reply** for replies you want in Notifications. The extension does not access Telegram chats or verify delivery. Automatic posting is disabled.

The Scheduler page can run **scheduled group navigation**: while Chrome is open, it opens enabled Feed links in order at the configured interval during selected workdays/hours and notifies with the number of message entries manually imported since the last recorded manual send. This is an imported-data count, not a live Telegram count. It does not post, read messages, or delete messages.

## Tests

```bash
cd server
export TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/telegram_auto_bot_test
pytest

cd ../extension
npm test
```

## Demo workflow

1. Open a group in Telegram Web and choose Add or Skip.
2. Create post templates and select one for the feed item.
3. Manually import permitted message text and request AI analysis.
4. Copy the selected post, send it yourself in Telegram, then record your send.
5. Manually log copied replies and scan imported messages for opportunities.

## Documentation

- [Implementation status and setup handoff](IMPLEMENTATION_STATUS.md)
- [Architecture](docs/architecture.md)
- [API](docs/api.md)
- [Database](docs/database.md)

## Production notes

- Use HTTPS and restrict `CORS_ORIGINS`
- Configure authentication (hooks reserved for Phase 7 hardening)
- Run API behind a reverse proxy; keep secrets in environment / vault
- User-owned feed, posts, history, notifications, analyses, and scheduler state are separated by the Telegram username manually entered in Settings. Usernames are not verified; add trusted sign-in/pairing before public multi-tenant deployment.
- The side panel now requires a username at first launch, and group metadata is also scoped per username by migration `005_private_groups`.

## Changing backend URL

Extension **Settings → Backend URL → Test Connection**. Same build works for local, staging, and production servers.
