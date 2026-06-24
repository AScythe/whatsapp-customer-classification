# Plan: Timestamped Customer Context Naming + Idempotent Build

## Goal

1. Rename `customer_context.txt` → `{latest_ts}_customer_context.txt` (snapshot-based naming)
2. `build_customer_context.py` skips if `{ts}_customer_context.txt` already matches the latest timestamp in `appended_timestamps.json`
3. `classify_customer.py` reads `{ts}_customer_context.txt` instead of the old static filename
4. All references to the old `customer_context.txt` are removed — clean break

---

## Why this design

The new naming makes every output file self-documenting — its filename embeds the most recent message timestamp it contains. This enables a simple idempotency check at every pipeline step:

| Step | Output | Skip-if-exists check |
|---|---|---|
| `build_customer_context.py` | `{ts}_customer_context.txt` | Does `{ts}_customer_context.txt` exist? |
| `classify_customer.py` | `{ts}_{TIER}.txt` | Does `{ts}_*.txt` exist? |

If both outputs exist for timestamp `ts`, both scripts return in <1 second. If new data arrives (new `ts`), both rebuild from scratch.

The `appended_timestamps.json` tracker is still maintained (by `build_customer_context.py`) so `classify_customer.py` can read the latest timestamp without re-scanning JSONL files.

---

## File-by-file changes

### `build_customer_context.py`

**Remove these constants:**
```python
OUTPUT_FILE = os.path.join(BASE_DIR, "customer_context.txt")    # DELETE (line 37)
```

**Add new helper (after `save_tracker()`):**
```python
def sanitize_ts(ts):
    return ts.replace(":", "-").replace(".000", "")

def context_file_for_ts(ts):
    return os.path.join(BASE_DIR, f"{sanitize_ts(ts)}_customer_context.txt")
```

**Rewrite `main()` body:**

```python
def main():
    known_timestamps = load_tracker()
    jsonl_files = find_jsonl_files()

    if not jsonl_files:
        logger.warning("No JSONL files found.")
        return

    # Phase 1: scan all JSONL files, collect all entries + timestamps
    all_entries = []
    all_timestamps = set()

    for filepath in sorted(jsonl_files):
        with open(filepath, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    logger.warning("%s:%d - malformed JSON, skipping.", os.path.relpath(filepath), line_num)
                    continue

                ts = entry.get("timestamp")
                if not ts:
                    logger.warning("%s:%d - missing timestamp, skipping.", os.path.relpath(filepath), line_num)
                    continue

                all_timestamps.add(ts)
                body = entry.get("body") or ""
                transcript = entry.get("transcript") or ""
                output = compose_line(body, transcript)
                if output is None:
                    continue

                all_entries.append((ts, output))

    if not all_entries:
        logger.warning("No messages found in any JSONL files.")
        return

    latest_ts = max(all_timestamps)
    context_path = context_file_for_ts(latest_ts)

    # Phase 2: skip if context file already exists for this timestamp
    if os.path.exists(context_path):
        logger.info("Context up-to-date at %s. Skipping build.", latest_ts)
        return

    # Phase 3: rebuild from scratch
    all_entries.sort(key=lambda x: x[0])
    os.makedirs(BASE_DIR, exist_ok=True)
    with open(context_path, "w", encoding="utf-8") as f:
        for _, line_text in all_entries:
            f.write(line_text + "\n")

    # Phase 4: update tracker
    save_tracker(all_timestamps)

    logger.info("Built %s (%d entries).", context_path, len(all_entries))
```

**Key behavior changes:**
- Always scans ALL JSONL files (not just for new entries)
- Skips building entirely if `{latest_ts}_customer_context.txt` already exists
- Full rebuild (not incremental append) when it does build
- No reference to old `customer_context.txt` anywhere

---

### `classify_customer.py`

**Remove this constant:**
```python
CONTEXT_FILE = os.path.join(BASE_DIR, "customer_context.txt")    # DELETE (line 36)
```

**Update `load_context()` — accept path as parameter:**

```python
def load_context(context_file):
    if not os.path.exists(context_file):
        logger.error("%s not found. Run build_customer_context.py first.", context_file)
        sys.exit(1)

    with open(context_file, "r", encoding="utf-8") as f:
        content = f.read().strip()

    if not content:
        logger.error("%s is empty. Cannot classify.", context_file)
        sys.exit(1)

    line_count = content.count("\n") + 1
    logger.info("Context loaded (%d lines, %d chars)", line_count, len(content))
    return content, line_count
```

**Update `main()` — construct context file path from latest ts:**

```python
    latest_ts, total_msgs = load_tracker_ts()

    if already_classified(latest_ts):
        logger.info("Already classified up to %s. Skipping classification.", latest_ts)
        return

    prompt_template = load_prompt()

    # NEW: construct context file path from latest timestamp
    sanitized = sanitize_ts(latest_ts)
    context_path = os.path.join(BASE_DIR, f"{sanitized}_customer_context.txt")
    context, line_count = load_context(context_path)
```

No other changes needed — `save_result()` already writes to `BASE_DIR` with `{ts}_{TIER}.txt`.

---

## Files NOT changed

| File | Reason |
|---|---|
| `data_extraction.py` | No reference to context filename |
| `extract_media_ptt.py` | No reference to context filename |
| `transcribe_ptt.py` | No reference to context filename |
| `play_ptt.py` | No reference to context filename |
| `prompts/classify_customer.yaml` | Only contains system prompt, no filenames |
| `README.md` | Will update after code is stable |

---

## Cleanup (manual, one-time)

After both changes are deployed, delete the old files:

```
rm 212620375029_chat_archives/customer_context.txt
```

No stale references remain in the code.

---

## Edge cases

| Scenario | Behavior |
|---|---|
| **First run** — no context file, no tracker file | `load_tracker()` returns empty set → scan → build `{ts}_customer_context.txt` → create tracker |
| **Second run** — same data | `{ts}_customer_context.txt` exists → skip |
| **New extraction** — JSONL files added with newer timestamps | Max ts changes → `{new_ts}_customer_context.txt` doesn't exist → rebuild from scratch |
| **Run `classify` before `build`** | Context file doesn't exist → clear error: "{path} not found. Run build_customer_context.py first." |
| **Multiple customer folders** | Each folder independently discovered and managed |
| **No JSONL files in folder (empty archive)** | `all_entries` empty → "No messages found" warning → return |
| **Manual deletion of `{ts}_customer_context.txt`** | Next build run: file missing → rebuild from scratch → creates new file |

---

## Test plan

After implementation, verify:

1. Run `build_customer_context.py` twice on the same data → first run builds, second run skips
2. Run `classify_customer.py` → it reads `{ts}_customer_context.txt`, not the old name
3. Delete the context file, re-run `build` → rebuilds from scratch
4. Run `classify` before `build` on a fresh folder → clear error message
