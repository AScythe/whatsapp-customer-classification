# WhatsApp-Style Message Storage Architecture (Final Consolidated Plan)

> Combines PostgreSQL Two-Tier storage, AWS S3 media offloading, Redis async ingestion, cursor pagination, client-side caching, and enterprise safeguards — distilled from 4 prior plans into one definitive architecture.

---

## Architecture Overview

```
[ WhatsApp / BulkSMS API ]
        │ (Webhook / Polling — raw JSON)
        ▼
[ Backend API (Node.js/Python) ] ────────> Returns 200 OK instantly
        │
        │ (Pushes raw JSON to queue)
        ▼
[ Redis Queue (Buffer) ]
        │
        │ (Background worker pulls & processes)
        ▼
[ Background Worker ] ───────────────────────────────┐
        │                                              │
        │ 1. Decode base64 media → upload to S3        │
        │ 2. Extract ad metadata (ad_id, ad_title)     │
        │ 3. Upsert users table                        ▼
        │ 4. Upsert messages table              [ AWS S3 Bucket ]
        │ 5. Upsert chat_inbox table            (Images, Voice, Docs,
        ▼                                          Ad Thumbnails)
[ PostgreSQL Database ]
  ┌──────────────────────┐  ┌──────────────────────────┐  ┌──────────────────────────┐
  │        users         │  │        messages          │  │       chat_inbox         │
  ├──────────────────────┤  ├──────────────────────────┤  ├──────────────────────────┤
  │ phone_number (PK)    │◄─│ sender_phone (FK)        │  │ chat_id (PK)             │
  │ display_name         │  │ id (PK)                  │  │ participant_phone (FK)   │
  │ avatar_url           │  │ chat_id (Partitioned)    │  │ participant_name         │
  │ created_at           │  │ message_time (DESC idx)  │  │ last_message_body        │
  └──────────────────────┘  │ from_me                  │  │ last_message_time        │
                            │ message_type             │  │ last_message_id          │
                            │ body                     │  │ last_from_me             │
                            │ media_url ───────────────┼──> (S3 URL)                │
                            │ ad_thumbnail_url ────────┼──> (S3 URL)                │
                            │ ad_id, ad_title          │  │ unread_count             │
                            │ raw_json (JSONB)         │  │ is_active_session        │
                            └──────────────────────────┘  │ updated_at               │
                                                          └──────────────────────────┘
                                                                  ▲
                                                                  │
                                                           [ Client UI ]
                                                           (SQLite/IndexedDB
                                                            local cache)
```

---

## Step 1: Storage Engine — Why PostgreSQL

| Requirement | Winner | Why |
|-------------|--------|-----|
| Relational integrity | **PostgreSQL** | `users` FK on messages, referential constraints |
| JSONB for raw payloads | **PostgreSQL** | Native `JSONB` — store full API response as backup |
| Full-text search | **PostgreSQL** | `pg_trgm` + GIN index — fast across millions of messages |
| Time-series partitioning | **PostgreSQL** | `PARTITION BY RANGE` + `pg_partman` — zero-maintenance monthly partitions |
| Horizontal scale | NoSQL (would win) | Not needed at this scale — proper indexing handles 50M+ messages |
| Operational simplicity | **PostgreSQL** | One engine to manage vs. ScyllaDB cluster |

**Decision:** PostgreSQL. Add NoSQL (ScyllaDB/Cassandra) only if you exceed 500M+ messages and need horizontal write scaling.

---

## Step 7: Production Safeguards

| Concern | Solution | Plan Source |
|---------|----------|-------------|
| Duplicate messages from API retries | `ON CONFLICT (chat_id, message_time, id) DO NOTHING` | Plan 1 |
| Out-of-order webhooks | `GREATEST()` + `CASE` on inbox upsert | Plan 3 (v3) |
| Partition management at scale | `pg_partman` — auto-creates/drops monthly partitions | Plan 3 (v3) |
| Base64 bloat in DB | Decode → S3 → store URL only | Plan 1 |
| Empty sidebar previews | UI fallback for `e2e_notification`, `call_log`, etc. | Plan 3 (v3) |
| Unread count drift | Atomic `unread_count = unread_count + 1` (not SET) | Plan 3 (v3) |
| Agent distraction (false unread) | Redis `active_view:{chatId}` flag | Plan 3 (v3) |
| Webhook flood | Redis queue → backend returns 200 instantly | Plan 2 |
| Scroll duplication during live updates | Cursor pagination (tuple comparison) | Plan 2 |
| Unknown future API fields | `raw_json JSONB` preserves everything | Plan 1 |

---

## Sample Database Tables (Using Your Real Data)

### Table: `users`

| phone_number | display_name | avatar_url |
|---|---|---|
| `212620375029` | Barae | `https://abs.twimg.com/...default_profile_normal.png` |
| `212659878174` | 🙂🙂 | `https://cdn.whatsapp.net/.../avatar.jpg` |
| `BusinessNumber` | My Business | `https://your-bucket.s3.amazonaws.com/...biz_logo.jpg` |

### Table: `messages`

| id | chat_id | sender_phone | message_time | from_me | type | body | media_url | ad_id |
|---|---|---|---|---|---|---|---|---|
| `2AE83EF0...` | `2569036198...@lid` | `212620375029` | `2026-06-18 10:44:37+00` | false | ptt | *(null)* | `https://s3...media/2AE83EF0.ogg` | null |
| *(next)* | `2569036198...@lid` | `212620375029` | `2026-06-24 07:52:43+00` | false | chat | `Ok` | null | null |
| *(next)* | `2569036198...@lid` | `212620375029` | `2026-06-24 07:52:39+00` | false | chat | `Quelles sont les pièces...` | null | `120247147198940639` |
| *(next)* | `2569036198...@lid` | `BusinessNumber` | `2026-06-24 07:52:43+00` | true | automated_greeting | `Notre conseiller est...` | null | `120247147198940639` |

### Table: `chat_inbox` (what the UI sees on the main screen)

| chat_id | participant_name | last_message_body | last_message_time | last_from_me | unread_count |
|---|---|---|---|---|---|
| `2569036198...@lid` | Barae | `Ok` | `2026-06-24 07:52:43+00` | false | 3 |
| `9988776655...@lid` | Ahmed | `🎤 Voice message` | `2026-06-24 07:30:00+00` | true | 0 |
| `1122334455...@lid` | Fatima | `🔒 End-to-end encrypted` | `2026-06-24 06:15:00+00` | false | 1 |

---

## Summary

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Database** | PostgreSQL + pg_partman | Reliable, searchable, partitioned message store |
| **Media** | AWS S3 | Offload base64 bloat — keep DB lean |
| **Queue** | Redis | Async ingestion — webhook returns in <10ms |
| **Search** | pg_trgm GIN index | Typo-tolerant full-text across millions of messages |
| **Cache** | SQLite/IndexedDB (client) | Instant UI — network is optional for rendering |
| **Analytics** | Partial index on ad_id | ROI reports without touching JSONB blobs |

**Start here.** Add NoSQL horizontal scaling only when you exceed 500M messages. PostgreSQL with proper indexing, partitioning, and the two-tier `messages` + `chat_inbox` pattern will comfortably handle 50M+ messages with <5ms query times.
