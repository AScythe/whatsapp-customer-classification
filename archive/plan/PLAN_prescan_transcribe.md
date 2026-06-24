# Plan: Pre-scan to Avoid Loading Whisper Model When Nothing to Transcribe

## Problem

Every run of `transcribe_ptt.py` loads `ychafiqui/whisper-medium-darija` (~1.5 GB, 10-30s) before discovering whether any work exists. When all PTT messages are already transcribed, this is entirely wasted.

## Solution

Add a lightweight pre-scan that counts pending transcriptions by reading JSONL files without loading any ML model. If zero pending, exit immediately.

---

## Design

### New function: `count_pending()`

```python
def count_pending(base_dir):
    """Count PTT entries needing transcription, without loading the model."""
    pending = 0
    for root, dirs, files in os.walk(base_dir):
        if "_tracking" in root:
            continue
        for fname in files:
            if not fname.endswith(".jsonl") or fname.startswith("extracted_info"):
                continue
            jsonl_path = os.path.join(root, fname)
            with open(jsonl_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if obj.get("type") != "ptt":
                        continue
                    media_link = obj.get("media_link", "")
                    if not media_link:
                        continue
                    if media_link.startswith("data:"):
                        continue
                    if "transcript" in obj:
                        continue
                    media_path = os.path.join(root, media_link)
                    if os.path.exists(media_path):
                        pending += 1
    return pending
```

### Rules: pre-scan must match `process_jsonl()` exactly

Every condition that prevents transcription in `process_jsonl()` must be replicated identically in `count_pending()`. Here's the complete correspondence table:

| Condition in `process_jsonl()` | Must match in `count_pending()` |
|---|---|
| `obj.get("type") == "ptt"` | `obj.get("type") != "ptt"` → skip |
| `media_link` is truthy | `not media_link` → skip |
| `not media_link.startswith("data:")` | `media_link.startswith("data:")` → skip |
| `"transcript" not in obj` | `"transcript" in obj` → skip |
| `os.path.exists(media_path)` | `not os.path.exists(media_path)` → skip |
| malformed JSON → skip | `json.JSONDecodeError` → skip (same) |
| `_tracking/` subdirectory → skip | `"_tracking" in root` → skip (same) |
| `extracted_info*.jsonl` → skip | `fname.startswith("extracted_info")` → skip (same) |

### Modified `main()` flow

```
main():
    logger.info("Scanning for JSONL files with PTT voice messages...")
    t0 = time.time()
    pending = count_pending(BASE_DIR)          ← NEW

    if pending == 0:
        logger.info("Nothing to transcribe. All PTT entries already transcribed.")
        return                                  ← EARLY EXIT, no model loading

    logger.info("Found %d message(s) pending transcription.", pending)
    device = get_device()                       ← only now enter the expensive path
    pipe = load_pipeline(device)

    found = 0
    for root, dirs, files in os.walk(BASE_DIR):  ← walks again for actual work
        ...

    logger.info("Done. Transcribed %d/%d pending in %.1fs.", found, pending, time.time() - t0)
```

### `process_jsonl()` stays unchanged

No modifications needed. The per-entry logic, temp-file atomic write, and error handling remain exactly as-is.

---

## Edge cases analyzed

| Scenario | Pre-scan behavior | Main pass behavior | Correct? |
|---|---|---|---|
| All PTT transcribed | `pending = 0` → exit | Never runs | Yes |
| No PTT in data at all | `pending = 0` → exit | Never runs | Yes |
| One new PTT added | `pending = 1` → proceed | Transcribes 1 entry | Yes |
| Partial batch (some new, some done) | Counts only entries without `transcript` key + file exists | Processes same entries | Yes |
| Media file deleted after extraction | `os.path.exists(media_path)` = False → not counted | `os.path.exists(media_path)` = False → skipped with error log | Yes (consistent) |
| JSONL has corrupt JSON lines | `json.JSONDecodeError` caught → skip line | Same catch in process_jsonl's `json.loads()` | Yes |
| Re-run while transcription in progress (crash) | Counts untranscribed entries | Re-processes them (idempotent) | Yes |
| `extracted_info*.jsonl` present | Skipped by name filter | Skipped by same filter in `os.walk` | Yes |

---

## Risk: double-walk cost

Both `count_pending()` and `process_jsonl()` walk all JSONL files and parse every line. This is acceptable because:

- **JSONL files are tiny** — each line is one WhatsApp message (typically 200-800 bytes). Even 10,000 messages = ~5-8 MB total across all files.
- **No model loading** — the pre-scan is pure Python file I/O, which completes in <1s for realistic datasets.
- **Whisper model loading is ~10-30s** — the overhead of double-walking is ~0.1-0.5% of the model load time.

---

## Summary of code changes

| Location | Change | Lines |
|---|---|---|
| After `get_device()` (line 49) | New `count_pending(base_dir)` function | +32 |
| `main()`: before `device = get_device()` | Insert `pending = count_pending(BASE_DIR)` + early exit | +6 |
| `main()`: end | Log actual vs pending count (cosmetic) | +1 |

**Total: ~39 lines added, 0 lines changed, 0 lines deleted.**
**`process_jsonl()` untouched.**
