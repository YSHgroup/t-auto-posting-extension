# Telegram Auto Bot — API Server

FastAPI backend with PostgreSQL, a manual user-supplied data provider, and OpenAI / Claude analysis. Automatic Telegram actions are disabled.

## Setup

```bash
cd server
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp ../.env.example ../.env
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

OpenAPI: http://localhost:8000/docs

No demo data is seeded. Add groups and manually copied message text through the extension. Analysis requires an OpenAI or Anthropic API key configured on the server.

## Tests

Requires PostgreSQL (see `TEST_DATABASE_URL`):

```bash
pytest
```
