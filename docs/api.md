# REST API

Base path: `/api`. OpenAPI at `/docs`.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/dashboard` | Dashboard aggregates |
| GET | `/groups/search?q=` | Search groups (max 50, exclude joined) |
| GET | `/groups/{id}` | Group detail |
| POST | `/groups/{id}/analyze` | Run AI analysis, store result |
| GET | `/groups/{id}/analysis` | List analyses |
| GET | `/groups/{id}/messages` | Messages from data provider |
| GET | `/feed` | List feed items ordered |
| POST | `/feed` | Add group to feed (by group id) |
| PUT | `/feed/{id}` | Update order, enabled, manual reorder |
| DELETE | `/feed/{id}` | Remove from feed |
| POST | `/feed/reorder` | Bulk reorder |
| GET | `/posts` | List posts |
| POST | `/posts` | Create post |
| GET | `/posts/{id}` | Get post |
| PUT | `/posts/{id}` | Update post |
| DELETE | `/posts/{id}` | Delete post |
| POST | `/posts/{id}/duplicate` | Duplicate post |
| POST | `/posts/recommend` | AI recommend for feed_group_id |
| GET | `/scheduler` | Get scheduler settings |
| PUT | `/scheduler` | Update scheduler |
| POST | `/bot/start` | Start bot |
| POST | `/bot/stop` | Stop bot |
| GET | `/bot/status` | Bot state + cursor |
| GET | `/history` | Posting history |
| GET | `/notifications` | Notifications filter |
| POST | `/notifications/{id}/read` | Mark read |
| POST | `/notifications/read-all` | Mark all read |
| POST | `/groups/{id}/opportunities` | Scan up to 500 messages |
| GET | `/opportunities` | List stored opportunities |
| GET | `/settings` | App + AI display settings |
| PUT | `/settings` | Update non-secret settings |
| POST | `/settings/test-connection` | Health from extension |
| POST | `/settings/reset-demo` | Reset mock demo data |
