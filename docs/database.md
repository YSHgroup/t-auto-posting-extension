# Database Schema

PostgreSQL with UUID primary keys where noted.

## Core entities

| Table | Purpose |
|-------|---------|
| `groups` | Cached group metadata from data provider |
| `group_messages` | Optional cache of messages (mock sync) |
| `users` | Mock/app users |
| `group_analysis` | Latest and historical AI analysis per group |
| `posts` | User-authored post templates |
| `feed_items` | Ordered feed membership + enable flag |
| `post_assignments` | Selected post per feed item (`selected_by`) |
| `post_history` | Every post attempt (success/skipped/failed) |
| `replies` | Simulated replies to posts |
| `notifications` | Derived from replies / system events |
| `scheduler_settings` | Singleton row for automation config |
| `bot_state` | Singleton row: state + `current_feed_index` |
| `opportunities` | Stored opportunity scan results |
| `ai_settings` | Singleton: provider preference (keys from env) |
| `app_settings` | Singleton: data mode, timezone |

## Relationships

- `Group` 1—N `GroupMessage`, `GroupAnalysis`, `FeedItem`, `PostHistory`, `Reply`, `Opportunity`
- `Post` 1—N `PostAssignment`, `PostHistory`, `Reply`
- `FeedItem` N—1 `Group`, optional `PostAssignment`

## Indexes

- `groups(external_id)` unique
- `feed_items(order_index)`
- `post_history(group_id, posted_at)`
- `post_history(post_id)`
- `notifications(read, created_at)`
- `replies(group_id, created_at)`

## Counters

Tracked on `posts` (usage_count), `feed_items` (post_count, last_posted_at), `groups` (joined), and daily aggregates via `post_history` queries / materialized counts in dashboard service.
