# REST API

Base path: `/api`. OpenAPI at `/docs`.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/dashboard` | Dashboard aggregates |
| GET | `/groups/search?q=` | Returns no results; live Telegram search is unavailable |
| GET | `/groups/{id}` | Group detail |
| POST | `/groups/{id}/analyze` | Run AI analysis, store result |
| GET | `/groups/{id}/analysis` | List analyses |
| GET | `/groups/{id}/messages` | Messages from data provider |
| POST | `/groups/{id}/observed-messages` | Import up to 500 user-copied messages for private analysis |
| POST | `/groups/intake` | Record user-confirmed add/skip group decision |
| GET | `/groups/intake-status/{id}` | Return this installation's add/skip decision |
| POST | `/groups/{id}/simulate-reply` | Disabled (410); use manual reply logging |
| POST | `/groups/{id}/log-manual-reply` | Save a user-copied reply as a private notification |
| GET | `/feed` | List feed items ordered |
| POST | `/feed` | Add group to feed (by group id) |
| PUT | `/feed/{id}` | Update order, enabled, manual reorder |
| DELETE | `/feed/{id}` | Remove from feed |
| POST | `/feed/{id}/record-manual-post` | Record a user-confirmed manual send (not delivery-verified) |
| POST | `/feed/reorder` | Bulk reorder |
| GET | `/posts` | List posts |
| POST | `/posts` | Create post |
| GET | `/posts/{id}` | Get post |
| PUT | `/posts/{id}` | Update post |
| DELETE | `/posts/{id}` | Delete post |
| POST | `/posts/{id}/duplicate` | Duplicate post |
| POST | `/posts/recommend` | AI recommend for `feed_item_id` |
| GET | `/scheduler` | Get scheduler settings |
| PUT | `/scheduler` | Update scheduler |
| POST | `/bot/start` | Returns 409; automatic posting is disabled in manual data mode |
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
| POST | `/settings/reset-demo` | Disabled (410); no demo data is seeded |

Every `/api` route other than `/health` requires `X-Telegram-Username`, entered manually by the user in Settings. It scopes user-owned data by normalized username and creates an account row if needed. This header is not verified authentication: callers can claim another username. `X-Installation-ID` is optional installation metadata, not the data ownership key.

Real Telegram message retrieval, message counting, posting, and deletion are not API operations. The manual-send endpoint records the user's confirmation only; it does not verify delivery.

Analysis and recommendation requests require a valid OpenAI or Anthropic key on the server. Missing keys return HTTP 503; mock AI fallback is disabled.
