# Plan: Fix data_extraction.py — Timestamp-level Tracking

## Problem

`data_extraction.py` tracks extraction at **hour granularity** via `_tracking/extracted_info_{day}.json`:

```json
{"date": "2026-06-21", "extracted_hours": ["09", "10", "11"]}
```

If the source JSON is updated with a new message at `2026-06-21T11:30:00.000Z` (hour `11` is already extracted), the script skips the entire hour — the new message is **silently dropped**.

---

## Solution

Replace hour-level tracking with **per-timestamp tracking** using a single file `_tracking/extracted_timestamps.json`. New messages are **appended** to existing hourly JSONL files instead of skipping the whole hour.

---

## Design

### New tracking file: `_tracking/extracted_timestamps.json`

```json
{
  "extracted_timestamps": [
    "2026-06-21T09:35:22.000Z",
    "2026-06-21T10:12:05.000Z",
    "2026-06-21T11:15:52.000Z"
  ]
}
```

- Single file for all days (replaces the per-day `extracted_info_{day}.json` files)
- Simple sorted list of timestamps
- Written once after all processing, not per-day

### New `main()` logic

```
main():
  1. Load source JSON
  2. Load set of extracted timestamps from tracking file (or scan existing JSONL files if first run)
  3. For each message in source:
       If timestamp already in set → skip
       Else → group by hour_key for writing, add to new_timestamps set
  4. If no new timestamps → log "Nothing new." → return
  5. For each hour_key with new messages:
       Open existing JSONL in append mode ("a")
       Write only new messages (one per line)
  6. Update tracking file with old + new timestamps
```

### Key change: append mode

**Before (line 110):** `open(hourly_file, "w")` — creates a fresh file, writes all messages for that hour
**After:** `open(hourly_file, "a")` — appends only new messages to existing file

Existing JSONL files are never rewritten. New messages are simply appended at the end.

---

## Step-by-step comparison

### Old behavior

```
Source JSON has hours {09, 10, 11} for day 2026-06-21
Tracking shows {09, 10, 11} already extracted
→ new_hours = {} → skip entire day
→ New message at T11:30 is LOST
```

### New behavior

```
Source JSON has hours {09, 10, 11} for day 2026-06-21
Tracking shows all existing timestamps
→ Compare each message's timestamp against the set
→ Message at T11:30 has a NEW timestamp not in the set
→ Append it to 2026-06-21-11.jsonl
→ Update tracking file with the new timestamp
```

---

## Complete `main()` rewrite

```python
def main():
    logger.info("Loading raw messages from %s ...", input_file)
    logger.info("Output folder: %s", base_output_dir)

    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    tracking_dir = os.path.join(base_output_dir, "_tracking")
    tracker_file = os.path.join(tracking_dir, "extracted_timestamps.json")

    # Phase 1: load existing timestamps from tracker (or seed from existing files)
    extracted_ts = load_extracted_timestamps(tracker_file)
    if extracted_ts is None:
        extracted_ts = seed_from_existing_jsonl(base_output_dir, tracking_dir)
        save_extracted_timestamps(tracker_file, extracted_ts)

    # Phase 2: find new messages by timestamp
    new_groups = defaultdict(list)
    new_timestamps = set()

    for message in data.get("messages", []):
        ts = message.get("timestamp")
        if not ts:
            continue
        if ts in extracted_ts:
            continue

        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        hour_key = dt.strftime("%Y-%m-%d-%H")

        extracted_data = {
            "timestamp": ts,
            "name": message.get("sender", {}).get("name"),
            "phone_number": message.get("sender", {}).get("phone"),
            "body": message.get("body"),
            "type": message.get("type"),
            "media_link": message.get("media_link"),
        }

        new_groups[hour_key].append(extracted_data)
        new_timestamps.add(ts)

    if not new_timestamps:
        logger.info("Nothing new to extract.")
        return

    # Phase 3: append new messages to hourly JSONL files
    for hour_key in sorted(new_groups):
        messages = new_groups[hour_key]
        year_month = hour_key[:7]
        day = hour_key[:10]
        day_folder = os.path.join(base_output_dir, year_month, day)
        os.makedirs(day_folder, exist_ok=True)

        hourly_file = os.path.join(day_folder, f"{hour_key}.jsonl")
        with open(hourly_file, "a", encoding="utf-8") as f:
            for msg in messages:
                f.write(json.dumps(msg, ensure_ascii=False) + "\n")

        logger.info("Appended %d message(s) to %s", len(messages), os.path.basename(hourly_file))

    # Phase 4: update tracking
    extracted_ts.update(new_timestamps)
    save_extracted_timestamps(tracker_file, extracted_ts)

    logger.info("Done. Extracted %d new message(s).", len(new_timestamps))
```

### New helper functions

```python
def load_extracted_timestamps(tracker_file):
    """Return set of timestamps, or None if file doesn't exist."""
    if not os.path.exists(tracker_file):
        return None
    with open(tracker_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return set(data.get("extracted_timestamps", []))


def save_extracted_timestamps(tracker_file, timestamps):
    """Overwrite tracker with sorted list of timestamps."""
    os.makedirs(os.path.dirname(tracker_file), exist_ok=True)
    with open(tracker_file, "w", encoding="utf-8") as f:
        json.dump(
            {"extracted_timestamps": sorted(timestamps)},
            f,
            ensure_ascii=False,
            indent=2,
        )


def seed_from_existing_jsonl(base_output_dir, tracking_dir):
    """First run: scan all existing JSONL files to build the timestamp set."""
    timestamps = set()
    for root, dirs, files in os.walk(base_output_dir):
        if "_tracking" in root:
            continue
        for fname in files:
            if not fname.endswith(".jsonl"):
                continue
            jsonl_path = os.path.join(root, fname)
            with open(jsonl_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        ts = obj.get("timestamp")
                        if ts:
                            timestamps.add(ts)
                    except json.JSONDecodeError:
                        continue
    logger.info("Seeded %d existing timestamps from JSONL files.", len(timestamps))
    return timestamps
```

---

## Migration (existing data)

On the first run with the new code:

1. `load_extracted_timestamps()` returns `None` (file doesn't exist yet)
2. `seed_from_existing_jsonl()` scans all existing JSONL files under `base_output_dir`
3. Collects all timestamps → saves to `extracted_timestamps.json`
4. Then processes the source JSON normally — all existing timestamps are already in the set → skipped
5. Only genuinely new messages (not in existing JSONL files) get extracted

Old `_tracking/extracted_info_*.json` files become unused. Can be manually deleted or left in place (harmless).

---

## Edge cases

| Scenario | Behavior |
|---|---|
| **First run (no existing data)** | `seed_from_existing_jsonl()` finds no files → empty set → all source messages are new → extracted |
| **First run (migration from old system)** | `seed_from_existing_jsonl()` scans existing JSONL → seeds timestamp set → only truly new messages extracted |
| **Source JSON updated with 1 new message in existing hour** | New timestamp not in set → appended to existing JSONL → tracker updated |
| **Source JSON unchanged, re-run** | All source timestamps are in set → "Nothing new to extract." → return |
| **Source JSON updated with messages in a new day** | All timestamps are new → create new JSONL files → append (same as "w" for new files) |
| **Same timestamp appears twice in source JSON** | First occurrence: new → extracted. Second occurrence: already in set → skipped. De-duplication by timestamp. |
| **`_tracking/` directory missing** | `os.makedirs` inside `save_extracted_timestamps()` creates it |
| **JSONL file deleted manually** | Tracker still has the timestamps → messages won't be re-extracted. Would need to delete tracker to force re-extraction. |

---

## No pre-scan needed (already handled)

Unlike `transcribe_ptt.py`, the early exit happens inside `main()` naturally: after iterating all messages, if `new_timestamps` is empty → "Nothing new to extract." → return. No model loading cost to avoid.

---

## Summary of changes

| File | Change |
|---|---|
| `data_extraction.py` | Remove `from collections import defaultdict` → keep |
| | Remove `day_hours` / `new_hours` / per-day tracking loop |
| | Remove all `extracted_info_{day}.json` tracking logic |
| | Add `load_extracted_timestamps()`, `save_extracted_timestamps()`, `seed_from_existing_jsonl()` |
| | Rewrite `main()` to iterate all messages, filter by timestamp, group new ones, append to JSONL, save single tracker |

**Lines changed:** ~10 new helper lines + ~40 rewritten `main()` lines. Roughly same total line count as current.
