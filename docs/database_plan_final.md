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

## Step 2: Database Schema

### Step 2.1: Enable Extensions

```sql
-- Trigram matching for typo-tolerant full-text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Automated partition management (creates future months, drops old ones)
CREATE EXTENSION IF NOT EXISTS pg_partman;
```

### Step 2.2: Users Table

Stores contact registry — upserted on every message arrival.

```sql
CREATE TABLE users (
    phone_number VARCHAR(50) PRIMARY KEY,  -- e.g. "212620375029"
    display_name VARCHAR(255),             -- e.g. "Barae"
    avatar_url TEXT,                       -- e.g. "https://abs.twimg.com/..."
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Step 2.3: Messages Table (Partitioned)

Core message store. Partitioned by month so indexes stay small and queries remain <5ms at 50M+ messages. The composite PK `(chat_id, message_time, id)` ensures unique deduplication and enables efficient range scans.

```sql
CREATE TABLE messages (
    id             VARCHAR(100)   NOT NULL,  -- e.g. "2AE83EF073668F322CDB"
    chat_id        VARCHAR(100)   NOT NULL,  -- e.g. "256903619858615@lid"
    sender_phone   VARCHAR(50)    REFERENCES users(phone_number),
    message_time   TIMESTAMPTZ    NOT NULL,  -- ISO 8601 auto-parsed by Postgres
    from_me        BOOLEAN        NOT NULL,
    message_type   VARCHAR(50)    NOT NULL,  -- 'chat', 'ptt', 'image', 'document', 'call_log', 'e2e_notification'
    body           TEXT,                     -- text content; NULL for media-only messages
    media_url      TEXT,                     -- S3 URL (after base64 decode + upload)
    ad_thumbnail_url TEXT,                   -- S3 URL for ad thumbnail
    ad_id          VARCHAR(100),             -- extracted from ad_info for analytics
    ad_title       VARCHAR(255),
    raw_json       JSONB,                    -- full original payload — safety net for future API changes

    PRIMARY KEY (chat_id, message_time, id)
) PARTITION BY RANGE (message_time);

-- Automated monthly partitions via pg_partman
SELECT partman.create_parent(
    p_parent_table => 'public.messages',
    p_control      => 'message_time',
    p_type         => 'native',
    p_interval     => 'monthly',
    p_premake      => 3       -- creates current month + 3 future months
);

-- THE MAGIC INDEX: replicates NoSQL clustering speed — groups by chat, sorts newest-first
CREATE INDEX idx_messages_chat_time
    ON messages(chat_id, message_time DESC, id DESC);

-- Full-text search index (typo-tolerant via pg_trgm)
CREATE INDEX idx_messages_body_search
    ON messages USING gin (body gin_trgm_ops);

-- Partial index for ad analytics — only indexes rows WHERE ad_id is not null
CREATE INDEX idx_messages_ad_id
    ON messages(ad_id) WHERE ad_id IS NOT NULL;
```

### Step 2.4: Chat Inbox Table (Denormalized for UI Speed)

Querying the main `messages` table to find the "last message" for 10,000 chats is slow. This table solves it — updated atomically during ingestion.

```sql
CREATE TABLE chat_inbox (
    chat_id             VARCHAR(100) PRIMARY KEY,
    participant_phone   VARCHAR(50)  REFERENCES users(phone_number),
    participant_name    VARCHAR(255),
    last_message_body   TEXT,
    last_message_time   TIMESTAMPTZ,
    last_message_id     VARCHAR(100),
    last_from_me        BOOLEAN,
    unread_count        INT DEFAULT 0,
    is_active_session   BOOLEAN DEFAULT FALSE,  -- agent is currently viewing this chat
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_inbox_time ON chat_inbox(last_message_time DESC);
```

---

## Step 3: Media Storage Strategy (AWS S3)

Messages contain base64-encoded media in `media_link` (voice notes as `data:audio/ogg;base64,...`, images, documents) and `ad_info.thumbnail` (ad images). **Never store base64 in the database** — decode and offload to S3.

| Field in JSON | Store in DB | Store in S3 |
|---------------|-------------|-------------|
| `body` | `messages.body` | — |
| `media_link` (URL) | `messages.media_url` | — |
| `media_link` (base64 data URI) | `messages.media_url` (S3 URL) | `media/{id}.{ext}` |
| `ad_info.thumbnail` (base64) | `messages.ad_thumbnail_url` (S3 URL) | `ad_thumbs/{id}.jpg` |
| `raw_json` | `messages.raw_json` | — |

**Python reference for the S3 upload logic:**

```python
import boto3, base64, uuid

s3 = boto3.client('s3')
BUCKET = 'your-whatsapp-media-bucket'

def upload_base64_to_s3(base64_str, folder="media"):
    raw = base64.b64decode(base64_str)
    key = f"{folder}/{uuid.uuid4()}.bin"
    s3.put_object(Bucket=BUCKET, Key=key, Body=raw)
    return f"https://{BUCKET}.s3.amazonaws.com/{key}"
```

---

## Step 4: The Ingestion Pipeline

### Step 4.1: Webhook Receiver (Non-Blocking)

```javascript
app.post('/webhook/whatsapp/:chatId', async (req, res) => {
    // Push to Redis queue and return immediately — never write to DB in a webhook
    await redisQueue.add('process-messages', {
        chatId: req.params.chatId,
        payload: req.body
    });
    res.status(200).json({ success: true });  // < 10ms response
});
```

### Step 4.2: Background Worker (The Core Logic)

The worker handles: system message fallbacks, base64→S3 upload, ad extraction, atomic DB upserts, and out-of-order webhook resilience.

```javascript
async function processMessages(chatId, payload) {
    for (const msg of payload.messages || []) {
        const sender = msg.sender || {};
        const senderPhone = sender.phone;

        // --- SYSTEM MESSAGE UI FALLBACK ---
        // Prevents blank sidebar when body is empty (e.g. e2e_notification)
        let uiBodyPreview = msg.body || "";
        if (!uiBodyPreview.trim()) {
            if (msg.type === 'e2e_notification') uiBodyPreview = "🔒 End-to-end encrypted";
            else if (msg.type === 'call_log')      uiBodyPreview = "📞 Call";
            else if (msg.type === 'ptt')            uiBodyPreview = "🎤 Voice message";
            else                                     uiBodyPreview = `📦 [${msg.type}]`;
        }

        // --- MEDIA & AD HANDLING ---
        let mediaUrl = msg.media_link || null;
        if (mediaUrl && mediaUrl.startsWith('data:')) {
            mediaUrl = await uploadBase64ToS3(mediaUrl);
        }

        let adThumbUrl = null, adId = null, adTitle = null;
        if (msg.ad_info?.is_from_ad) {
            adId = msg.ad_info.ad_id;
            adTitle = msg.ad_info.ad_title;
            if (msg.ad_info.thumbnail) {
                adThumbUrl = await uploadBase64ToS3(msg.ad_info.thumbnail, 'ad_thumbs');
            }
        }

        // --- UPSERT USER ---
        await db.query(`
            INSERT INTO users (phone_number, display_name, avatar_url)
            VALUES ($1, $2, $3)
            ON CONFLICT (phone_number) DO UPDATE SET
                display_name = EXCLUDED.display_name,
                avatar_url   = EXCLUDED.avatar_url
        `, [senderPhone, sender.name, sender.avatar]);

        // --- UPSERT MESSAGE (idempotent) ---
        await db.query(`
            INSERT INTO messages
                (id, chat_id, sender_phone, message_time, from_me, message_type,
                 body, media_url, ad_thumbnail_url, ad_id, ad_title, raw_json)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)
            ON CONFLICT (chat_id, message_time, id) DO NOTHING
        `, [msg.id, chatId, senderPhone, msg.timestamp, msg.from_me, msg.type,
            msg.body, mediaUrl, adThumbUrl, adId, adTitle, JSON.stringify(msg)]);

        // --- ATOMIC INBOX UPDATE (Out-of-order resilient) ---
        const isAgentViewing = await redis.get(`active_view:${chatId}`) === 'true';
        const unreadIncrement = (msg.from_me || isAgentViewing) ? 0 : 1;

        await db.query(`
            INSERT INTO chat_inbox
                (chat_id, participant_phone, participant_name,
                 last_message_body, last_message_time, last_message_id,
                 last_from_me, unread_count)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ON CONFLICT (chat_id) DO UPDATE SET
                last_message_body = CASE WHEN EXCLUDED.last_message_time >= chat_inbox.last_message_time
                                        THEN EXCLUDED.last_message_body ELSE chat_inbox.last_message_body END,
                last_message_time = GREATEST(EXCLUDED.last_message_time, chat_inbox.last_message_time),
                last_message_id   = CASE WHEN EXCLUDED.last_message_time >= chat_inbox.last_message_time
                                        THEN EXCLUDED.last_message_id ELSE chat_inbox.last_message_id END,
                last_from_me      = CASE WHEN EXCLUDED.last_message_time >= chat_inbox.last_message_time
                                        THEN EXCLUDED.last_from_me ELSE chat_inbox.last_from_me END,
                unread_count      = chat_inbox.unread_count + EXCLUDED.unread_count,
                updated_at        = NOW()
        `, [chatId, senderPhone, sender.name, uiBodyPreview,
            msg.timestamp, msg.id, msg.from_me, unreadIncrement]);
    }
}
```

**Why `GREATEST()` and `CASE` matter:** WhatsApp/Meta webhooks can arrive out of chronological order. Without these guards, an old webhook arriving late would overwrite the "last message preview" with stale content and reset the unread counter.

---

## Step 5: API Endpoints for the UI

### Endpoint A: Load Main Inbox (the Chat List)

```sql
SELECT chat_id, participant_name, last_message_body,
       last_message_time, last_from_me, unread_count
FROM chat_inbox
ORDER BY last_message_time DESC
LIMIT 50;
```

Because `chat_inbox` is a single-row-per-chat table, this returns in <5ms. The `idx_inbox_time` index guarantees sorted order without a sort step.

### Endpoint B: Load a Specific Chat (Cursor Pagination)

Offset pagination (`LIMIT 30 OFFSET 30`) breaks when new messages arrive mid-scroll — messages get duplicated or skipped. Cursor pagination avoids this by using a tuple comparison.

```sql
-- First load: newest 30 messages
SELECT id, body, message_time, from_me, media_url,
       ad_thumbnail_url, message_type, ad_id, ad_title
FROM messages
WHERE chat_id = $1
ORDER BY message_time DESC, id DESC
LIMIT 30;

-- Subsequent loads: older messages (pass last message_time and id from previous page)
SELECT id, body, message_time, from_me, media_url,
       ad_thumbnail_url, message_type, ad_id, ad_title
FROM messages
WHERE chat_id = $1
  AND (message_time, id) < ($2::timestamptz, $3)
ORDER BY message_time DESC, id DESC
LIMIT 30;
```

**Why tuple comparison `(message_time, id) < (t, i)`:** Ties on identical timestamps are broken by `id`, guaranteeing no duplicates or gaps.

### Endpoint C: Full-Text Search

```sql
SELECT chat_id, body, message_time, from_me
FROM messages
WHERE body ILIKE '%search_term%'
ORDER BY message_time DESC
LIMIT 20;
```

The `gin_trgm_ops` index makes `ILIKE` performant even with leading wildcards. For production, upgrade to `tsvector` full-text search with Arabic/French dictionaries.

### Endpoint D: Ad Campaign ROI Analytics

```sql
SELECT ad_title, COUNT(*) AS total_inbound_messages
FROM messages
WHERE ad_id = $1
  AND from_me = false
GROUP BY ad_title;
```

The partial index `idx_messages_ad_id WHERE ad_id IS NOT NULL` makes this query instant — it only scans rows that have ads.

---

## Step 6: Client-Side Caching (The "Instant UI" Secret)

To truly mimic WhatsApp, the UI must **not wait for the network on every scroll**.

1. **Local Database:** Use **SQLite** (via WatermelonDB/Realm on mobile) or **IndexedDB** (via Dexie.js on web).
2. **Delta Syncing:** On app open, ask the backend: *"Give me only messages newer than [max_timestamp_in_local_db]"*.
3. **Offline-First Render:** Render the chat immediately from the local database. When the network fetch finishes, silently append new messages to local DB and update the UI.
4. **Media Caching:** When an S3 media URL is loaded, cache the actual file on the device's local filesystem. Never re-download.

```
[ App Opens ]
      │
      ▼
[ Read from Local SQLite/IndexedDB ] ──────> Render UI instantly
      │
      ▼
[ Ask Backend: "Anything newer than X?" ] ──> Append deltas silently
      │
      ▼
[ Cache new media files locally ]
```

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
