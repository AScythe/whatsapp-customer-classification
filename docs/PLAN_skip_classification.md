# Skip Classification + Save Result to Root Folder

## Goal

1. Avoid redundant Qwen3.5 inference when `customer_context.txt` hasn't changed since the last classification.
2. Save `{ts}_{TIER}.txt` in `{phone}_chat_archives/` root instead of `_tracking/`.

## Change 1: Skip when already up-to-date

### Logic

1. Read latest timestamp from `_tracking/appended_timestamps.json`
2. Sanitize it (existing `sanitize_ts()` function)
3. Check if `{phone}_chat_archives/{sanitized_ts}_*.txt` exists
4. If found → log "Already classified up to {ts}. Skipping." → exit
5. If not found → proceed with classification → save result

### New function `already_classified()`

```python
def already_classified(latest_ts):
    sanitized = sanitize_ts(latest_ts)
    pattern = os.path.join(BASE_DIR, f"{sanitized}_*.txt")
    return bool(glob.glob(pattern))
```

### Guard in `main()`

Insert after `load_tracker_ts()`:

```python
    if already_classified(latest_ts):
        logger.info("Already classified up to %s. Skipping.", latest_ts)
        return
```

## Change 2: Save result to root folder

### Modify `save_result()`

**Before:** saves to `TRACKING_DIR` (`_tracking/`)
**After:** saves to `BASE_DIR` directly

```python
def save_result(latest_ts, tier, reason, context_line_count):
    sanitized_ts = sanitize_ts(latest_ts)
    filename = f"{sanitized_ts}_{tier}.txt"
    filepath = os.path.join(BASE_DIR, filename)

    content = (
        f"Latest message: {latest_ts}\n"
        f"Context lines: {context_line_count}\n"
        f"\n"
        f"Classification: {tier}\n"
        f"Reason: {reason}\n"
    )

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    return filepath
```

Remove `os.makedirs(TRACKING_DIR, exist_ok=True)` — no longer needed since `BASE_DIR` already exists.

### Remove now-unused `TRACKING_DIR` reference for the result

`TRACKING_DIR` is still used by other functions (`load_tracker_ts`, etc.) — only remove the `makedirs` inside `save_result()`.

## Files changed

Only `classify_customer.py` — ~12 lines added, ~3 lines modified.

## Full diff

```
 existing lines | new | notes
────────────────┼─────┼──────────────────────────────
 import glob    │     │ already present
                │ +5  │ already_classified() function
 sanitize_ts()  │     │ unchanged
 save_result(): │     │
   TRACKING_DIR→│BASE_DIR│ change path
   del makedirs │     │ remove os.makedirs call
 main():        │ +5  │ guard after load_tracker_ts()
```

## Edge cases

| Scenario | Behavior |
|---|---|
| First run, no result file | Glob empty → proceed with classification |
| Re-run with same data | Result file `{ts}_{TIER}.txt` exists → skip |
| New message → new latest ts | No matching result file → reclassify |
| Result file manually deleted | No match → reclassify (creates new file) |
| Multiple customers | Results live inside each customer's own folder, no cross-contamination |
