# Telegram Auto Bot

Independent Telegram group assistant (not a Telegram Bot). Chrome extension (React + TypeScript) + FastAPI + PostgreSQL, with a mock provider for demos and OpenAI / Anthropic Claude analysis.

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
python -m app.database.seed
uvicorn app.main:app --reload --port 8000
```

## Extension

```bash
cd extension
npm install
npm run build
```

Load `extension/dist` as an unpacked extension in Chrome. Open the side panel from the toolbar icon.

Set **Settings → API Server URL** (e.g. `http://localhost:8000`).

## AI configuration

Set keys in server `.env` (never in the extension):

```env
AI_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

If keys are missing, `AI_MOCK_WHEN_NO_KEY=true` uses structured mock AI for local demos.

## Mock data

```bash
cd server && python -m app.database.seed
```

Includes 50+ groups, messages, sample posts, replies, notifications, and opportunities.

Reset from extension **Settings → Reset demo data** or `POST /api/settings/reset-demo`.

## Real Telegram groups (manual workflow)

The extension content script runs only on `web.telegram.org` and asks whether to add or skip the current group. For real group analysis, manually copy text into Group Detail (up to 500 messages). Feed provides an Open Telegram link and Copy selected post action; send and any deletion are performed manually by the user. Use **Record manual send** after sending, and **Log a copied reply** for replies you want in Notifications. The extension does not access Telegram chats or verify delivery. Auto Mode is mock-only.

## Tests

```bash
cd server
export TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/telegram_auto_bot_test
pytest

cd ../extension
npm test
```

## Demo workflow

1. Open extension → **Groups** → search `blockchain startup`
2. Open a group → **Analyze Group**
3. **Posts** → create templates
4. **Feed** → add groups, select posts (AI recommendations are suggestions only)
5. **Scheduler** → 09:00–20:00, Mon–Fri, min 20 messages
6. **Dashboard** → **START BOT**
7. **History** → view success/skipped/failed
8. **Notifications** / **Opportunities** → replies and 500-message scans

## Documentation

- [Implementation status and setup handoff](IMPLEMENTATION_STATUS.md)
- [Architecture](docs/architecture.md)
- [API](docs/api.md)
- [Database](docs/database.md)

## Production notes

- Use HTTPS and restrict `CORS_ORIGINS`
- Configure authentication (hooks reserved for Phase 7 hardening)
- Run API behind a reverse proxy; keep secrets in environment / vault
- User-owned feed, posts, history, notifications, analyses, and scheduler state are separated by a stable extension-installation UUID. This is data partitioning, not verified account authentication; add trusted sign-in/pairing before public multi-tenant deployment.

## Changing backend URL

Extension **Settings → Backend URL → Test Connection**. Same build works for local, staging, and production servers.
