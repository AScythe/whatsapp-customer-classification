<!-- converted from database architecture.docx -->

Now I have a clear picture. Let me lay out the options.
Current Architecture (file-based)
chat_archives/
YYYY-MM/
YYYY-MM-DD/
YYYY-MM-DD-HH.jsonl        ← messages per hour
media/
ptt_YYYY-MM-DD-HH_NNN.ogg ← audio files
_tracking/
extracted_info_YYYY-MM-DD.json ← tracking
Data shape (from the JSONL):
- timestamp, name, phone_number, body, type, media_link, transcript (optional)
- Audio files: .ogg at ~10-100 KB each

---
Option 1: SQLite (Recommended for local/single-user)
Lightweight, zero-server, embedded. Best fit given this is a local CLI tool.
Schema:
CREATE TABLE messages (
id          INTEGER PRIMARY KEY AUTOINCREMENT,
timestamp   TEXT NOT NULL,        -- ISO 8601
name        TEXT,
phone_number TEXT,
body        TEXT,                 -- chat text
msg_type    TEXT NOT NULL,        -- 'chat' | 'ptt' | 'image' | ...
transcript  TEXT,                 -- Darija transcription (NULL until processed)
media_id    INTEGER REFERENCES media(id),
source_file TEXT,                 -- '2026-06-18-10.jsonl' (audit trail)
UNIQUE(timestamp, name, body, msg_type)  -- avoid duplicate ingestion
);
CREATE TABLE media (
id        INTEGER PRIMARY KEY AUTOINCREMENT,
filename  TEXT NOT NULL,          -- 'ptt_2026-06-18-10_001.ogg'
rel_path  TEXT NOT NULL UNIQUE,   -- '2026-06/2026-06-18/media/ptt_...ogg'
mime_type TEXT DEFAULT 'audio/ogg',
file_size INTEGER,
duration  REAL,                   -- seconds (populated after transcribe)
sha256    TEXT                    -- deduplication
);
-- Full-text search for body + transcript
CREATE VIRTUAL TABLE messages_fts USING fts5(
body, transcript, name,
content='messages', content_rowid='id'
);
Why SQLite:
- Single .db file, no server process
- Ships with Python's sqlite3 module (zero deps)
- FTS5 for fast search across Darija transcripts and chat text
- Media stays on filesystem (referenced by path) — no need to bloat DB with blobs
- JSONL import/export is a one-liner (INSERT ... SELECT json_extract(...))
- Concurrent writes not needed (single-user CLI tool)
Trade-offs:
- Writes are serialized (fine for hourly batch imports)
- Schema migrations require manual ALTER TABLE
- Not great for remote access

---
Option 2: DuckDB (if you want analytical queries)
Columnar, also embedded. Best for: "show me all messages from Barae in June with transcripts" — runs fast on 100k+ messages.
Same schema as SQLite but in DuckDB syntax. DuckDB reads JSON natively so you can SELECT * FROM read_jsonl('*.jsonl') without importing.
Why choose DuckDB over SQLite:
- Native JSONL loading — no ETL needed
- Columnar compression — 5-10x smaller on disk for message data
- Window functions, UNPIVOT, etc. for analysis
- Still embedded (single .duckdb file)
Trade-offs:
- No FTS (full-text search) — you'd use LIKE or regexp_matches
- Heavier library (~30 MB vs sqlite3 built-in)
- Fewer ORM integrations

---
Option 3: PostgreSQL (if you want a server or multi-user)
Only if you plan to: serve this via a web app, have multiple people querying, or want JSONB/array columns.
Trade-offs:
- Requires installation + background service
- Massive overkill for a CLI tool
---
Audio storage strategy (for all options)
Recommendation: Keep audio as files on disk, store only the relative path + metadata in the DB.
chat_archives/
YYYY-MM/YYYY-MM-DD/media/ptt_*.ogg   ← files stay here
In DB: media.rel_path = '2026-06/2026-06-18/media/ptt_2026-06-18-10_001.ogg'
Why not BLOBs:
- .ogg files are binary opaque bloat inside the DB
- Backups/rsync of audio files become harder
- Playing audio from Python is trivial with a file path, annoying with a BLOB
- No benefit — you never need transactional consistency between audio bytes and metadata

---
My recommendation
Use SQLite with the schema above. It's:
- Zero new dependencies (import sqlite3 is stdlib)
- FTS5 for searching transcripts/body
- Media stays as files (thin media table tracks paths + metadata)
- A single Python script can replace data_extraction.py to write to DB instead of JSONL, OR you can keep JSONL as-is and have a second script that loads JSONL → SQLite for querying
Question for you: Do you want the database to replace the JSONL files (new pipeline: raw JSON → DB → export JSONL on demand), or sit alongside them (keep current JSONL pipeline, then DB is a query/analysis layer that ingests from JSONL)?