# Database Schema

PostgreSQL with UUID primary keys where noted.

## Core entities

| Table | Purpose |
|-------|---------|
| `groups` | Shared group metadata and user-confirmed Telegram URL |
| `group_messages` | Legacy demo-message table; ignored by manual provider |
| `observed_group_messages` | Private, manually copied message text, scoped to extension installation |
| `users` | Reserved for authenticated accounts; installation UUID is currently not account authentication |
| `group_analysis` | Latest and historical AI analysis per group |
| `posts` | User-authored post templates |
| `feed_items` | Ordered feed membership + enable flag |
| `post_assignments` | Selected post per feed item (`selected_by`) |
| `post_history` | Every post attempt (success/skipped/failed) |
| `replies` | User-copied replies logged manually |
| `notifications` | Derived from replies / system events |
| `scheduler_settings` | Per-installation automation config |
| `bot_state` | Per-installation state + `current_feed_index` |
| `opportunities` | Stored opportunity scan results |
| `ai_settings` | Per-installation provider preference (keys from env) |
| `app_settings` | Per-installation data mode |
| `skipped_groups` | Per-installation record of groups explicitly skipped in Telegram Web |

Application-owned tables (`group_analysis`, `posts`, `feed_items`, assignments, history,
replies, notifications, scheduler/bot state, opportunities, AI/app settings, copied
observations, and skipped groups) carry `owner_id`, containing the normalized username
entered by the user. API requests bind `X-Telegram-Username` to SQLAlchemy tenant criteria.
Usernames are not verified authentication credentials.

## Relationships

- `Group` 1—N `GroupMessage`, `GroupAnalysis`, `FeedItem`, `PostHistory`, `Reply`, `Opportunity`
- `Post` 1—N `PostAssignment`, `PostHistory`, `Reply`
- `FeedItem` N—1 `Group`, optional `PostAssignment`

## Indexes

- `groups(external_id)` unique
- `feed_items(order_index)` and unique `(owner_id, group_id)`
- `owner_id` indexes on installation-owned tables
- `observed_group_messages(owner_id, group_id, sequence_num)` unique
- `post_history(group_id, posted_at)`
- `post_history(post_id)`
- `notifications(read, created_at)`
- `replies(group_id, created_at)`

## Counters

Tracked on `posts` (usage_count), `feed_items` (post_count, last_posted_at), and daily aggregates via per-installation `post_history` queries. Manual post records are user-confirmed and are not delivery-verified by Telegram.
