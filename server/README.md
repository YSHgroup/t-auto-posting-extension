# Telegram Auto Bot — API Server

FastAPI backend with PostgreSQL, mock data provider, AI providers (OpenAI / Claude), and APScheduler automation.

## Setup

```bash
cd server
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp ../.env.example ../.env
alembic upgrade head
python -m app.database.seed
uvicorn app.main:app --reload --port 8000
```

OpenAPI: http://localhost:8000/docs

## Tests

Requires PostgreSQL (see `TEST_DATABASE_URL`):

```bash
pytest
```
