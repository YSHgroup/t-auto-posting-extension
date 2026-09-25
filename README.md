# Telegram Auto Bot

Independent Telegram-style **automation assistant** (not a Telegram Bot). Chrome extension (React + TypeScript) + FastAPI + PostgreSQL, with a **replaceable mock data provider** and **AI provider abstraction** (OpenAI / Anthropic Claude).

No Telegram Bot API, MTProto, or Telegram Web automation.

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

- [Architecture](docs/architecture.md)
- [API](docs/api.md)
- [Database](docs/database.md)

## Production notes

- Use HTTPS and restrict `CORS_ORIGINS`
- Configure authentication (hooks reserved for Phase 7 hardening)
- Run API behind a reverse proxy; keep secrets in environment / vault

## Changing backend URL

Extension **Settings → Backend URL → Test Connection**. Same build works for local, staging, and production servers.
