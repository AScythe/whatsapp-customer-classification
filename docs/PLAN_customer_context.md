# Customer Context — Plan

## Overview

Aggregate all `body` and `transcript` content from every JSONL entry across `chat_archives/` into a single lean `.txt` file suitable for passing as context to an LLM. Idempotent — re-runs only append new entries.

## Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Output format | `.txt` | Leanest for LLM context — no JSON structure overhead |
| Entry format | One line per entry | Simple, sequential, easy to truncate/slice |
| body + transcript coexist | Merge on one line: `{body} | {transcript}` | Single line per entry keeps ordering clean |
| Only one non-empty | Just that value | No unnecessary decoration |
| Both empty | Skip entirely | Wastes tokens |
| Ordering | Chronological (oldest → newest) | LLM sees natural conversation flow |
| Dedup key | `timestamp` field | Unique per message, already present in every JSONL entry |

## Output Example

`chat_archives/customer_context.txt`:
```
داكورا تيريوهم ليا باش وديك الساعات غادي نولي نرجعوهم
Marhba
Merci
How was the meeting | كان اللقاء مفيدا
```

Note: the last line shows the merge format when both `body` (`"How was the meeting"`) and `transcript` (`"كان اللقاء مفيدا"`) are present.

## New Script: build_customer_context.py

### Algorithm

```
1. Load tracker from chat_archives/_tracking/appended_timestamps.json
   → get set of known timestamps (empty set if file missing)

2. Walk all chat_archives/**/*.jsonl (skip _tracking/ dir)

3. For each JSONL line:
     parse JSON
     if "timestamp" missing → warn, skip line
     if timestamp already in known set → skip
     extract body (default ""), transcript (default "")
     if both body and transcript are empty → skip
     compose output line:
       if body and transcript both non-empty → f"{body} | {transcript}"
       elif body non-empty → body
       elif transcript non-empty → transcript
     collect (timestamp, output_line) into a list

4. If no new entries → print "Nothing new." and exit

5. Sort collected entries by timestamp (chronological)

6. Open customer_context.txt in append mode
   Write each output_line on its own line

7. Add all new timestamps to the known set

8. Write updated tracker file (JSON: array of timestamps)

9. Print summary: "Appended N new entries from M JSONL files."
```

### Tracker File

**Path:** `chat_archives/_tracking/appended_timestamps.json`

```json
{
  "appended_timestamps": [
    "2026-06-18T10:44:37.000Z",
    "2026-06-18T10:45:12.000Z",
    "2026-06-18T10:45:14.000Z"
  ]
}
```

### Edge Cases

| Case | Handling |
|---|---|
| Tracker file missing (first run) | Start with empty set, create file at end |
| Output file missing (first run) | Created on first append |
| JSONL parse error | Log warning, skip malformed line |
| Missing `timestamp` field | Log warning, skip entry |
| Both body and transcript empty | Skip entry entirely |
| Entry has body but no transcript key | transcript defaults to `""` |
| Entry has transcript but no body key | body defaults to `""` |
| Script interrupted mid-write | Timestamps not yet committed → re-run re-processes those entries (minor duplicates possible, no data loss) |

### Crash Safety

- In-memory collection: all new entries are held in a list before writing
- Tracker is saved **after** successful append
- Worst case on crash: the next run may produce a few duplicate lines (acceptable for a utility script)

## Script Interface

```bash
python build_customer_context.py
```

No arguments. No configuration files. Everything is derived from the existing `chat_archives/` structure.

## Files to Create / Modify

| File | Action |
|---|---|
| `build_customer_context.py` | **Create** — aggregation script |
| `chat_archives/customer_context.txt` | **Create** (auto) — output file |
| `chat_archives/_tracking/appended_timestamps.json` | **Create** (auto) — tracker file |

**Unchanged:** `data_extraction.py`, `extract_media_ptt.py`, `transcribe_ptt.py`, `play_ptt.py`

## Updated Pipeline

```
Step 1: python data_extraction.py          → hourly JSONL
Step 2: python extract_media_ptt.py        → .ogg files
Step 3: python transcribe_ptt.py           → add Darija transcripts
Step 4: python build_customer_context.py   → customer_context.txt
Step 5: python classify_customer.py        → _tracking/{ts}_{TIER}.txt   ← NEW
Step 6: python play_ptt.py                 → interactive playback
```

## Dependencies

None. Uses only Python stdlib (`json`, `os`, `glob`).
