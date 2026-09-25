# Telegram Auto Bot

An independent Chrome extension and FastAPI automation demo. It intentionally does not integrate Telegram APIs or Telegram Web. Mock groups, messages, replies, posting, and opportunity discovery make the complete workflow testable locally.

## Quick start

```bash
docker compose up -d postgres
cd backend
python3.14 -m venv .venv
. .venv/bin/activate
pip install -e .
uvicorn app.main:app --reload --port 8000
```

For a configured PostgreSQL instance, run the migration and seed commands before starting the server:

```bash
alembic upgrade head
python -m app.database.seed
```

In a second terminal:

```bash
cd web
npm install
npm run dev
```

Open the Vite URL, set the backend URL to `http://localhost:8000`, and use the mock dashboard. API docs are at `http://localhost:8000/docs`.

Set `AI_PROVIDER=mock` for the zero-secret demo. Use `AI_PROVIDER=openai` or `AI_PROVIDER=anthropic` with the corresponding server-side API key to enable structured provider calls. The application never connects to Telegram services.

For Chrome side-panel packaging, build the Vite app and load the generated `web/dist` directory as an unpacked extension once a production manifest is added. See `web/README.md` for the extension build notes.
