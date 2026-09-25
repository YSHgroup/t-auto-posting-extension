# API Contract

FastAPI publishes interactive OpenAPI documentation at `/docs` and `/redoc`.

## Core endpoints

- `GET /api/health`
- `GET /api/dashboard`
- `GET /api/groups/search?q=`
- `GET /api/groups/{id}`
- `POST /api/groups/{id}/analyze`
- `GET /api/groups/{id}/messages?limit=500`
- `GET|POST|PUT|DELETE /api/feed[/id]`
- `GET|POST|PUT|DELETE /api/posts[/id]`
- `POST /api/posts/recommend`
- `GET|PUT /api/scheduler`
- `GET /api/bot/status`, `POST /api/bot/start`, `POST /api/bot/stop`
- `GET /api/history`
- `GET /api/notifications`, `POST /api/notifications/{id}/read`
- `POST /api/groups/{id}/opportunities`, `GET /api/opportunities`

Mock mode is the default and remains available when PostgreSQL is not running. With PostgreSQL available, startup initializes the SQLAlchemy schema and `python -m app.database.seed` loads the 50+ mock groups and demo posts. Run `alembic upgrade head` for controlled production migrations.
