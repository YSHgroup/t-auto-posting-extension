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
| POST | `/groups/{id}/observed-messages` | Import up to 500 user-copied messages for private analysis |
| POST | `/groups/intake` | Record user-confirmed add/skip group decision |
| GET | `/groups/intake-status/{id}` | Return this installation's add/skip decision |
| POST | `/groups/{id}/simulate-reply` | Add a mock reply and unread notification |
| POST | `/groups/{id}/log-manual-reply` | Save a user-copied reply as a private notification |
| POST | `/groups/{id}/log-manual-reply` | Save a user-copied real reply as a private notification |
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

Every `/api` route other than `/health` requires `X-Installation-ID`, a UUID created and stored by the extension. It scopes user-owned data by installation, but it is not a substitute for authenticated accounts or an authorization credential.

Real Telegram message retrieval, message counting, posting, and deletion are not API operations. The manual-send endpoint records the user's confirmation only; it does not verify delivery.
