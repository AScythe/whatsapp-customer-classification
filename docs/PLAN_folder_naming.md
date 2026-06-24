# Folder Naming: `<phone>_chat_archives`

## Goal

Replace the hardcoded folder name `chat_archives` with a phone-number-based name `212620375029_chat_archives` so that the folder reflects the unique customer identity from the WhatsApp data.

## Decision

**Direct naming (Option B):** `data_extraction.py` reads the phone number from the source JSON and creates the folder as `<phone>_chat_archives/` directly — no temp name, no rename.

## Scope: Phase 1 — `data_extraction.py` only

This plan covers only `data_extraction.py`. Phase 2 (updating the other 5 scripts to discover the new folder name) will be planned and executed separately.

## Changes to `data_extraction.py`

### Current flow (lines 14–96)

```
input_file = "whatsapp_raw_messages/whatsapp_messages.json"
base_output_dir = "chat_archives"
                ↓
load JSON → group by hour → for each day:
  tracking_file = chat_archives/_tracking/extracted_info_{day}.json
  if new hours → create chat_archives/2026-06/2026-06-23/ + write JSONL
               → update chat_archives/_tracking/extracted_info_{day}.json
```

### New flow

```
input_file = "whatsapp_raw_messages/whatsapp_messages.json"
                ↓
load JSON → extract phone number from first message's sender.phone
            sanitize: strip whitespace, ensure no problematic chars
base_output_dir = f"{phone}_chat_archives"
                ↓
group by hour → for each day:
  tracking_file = {phone}_chat_archives/_tracking/extracted_info_{day}.json
  if new hours → create {phone}_chat_archives/2026-06/2026-06-23/ + write JSONL
               → update {phone}_chat_archives/_tracking/extracted_info_{day}.json
```

### Specific edits

#### 1. Add `extract_phone()` function (after imports, before `main()`)

```python
def extract_phone(data):
    for msg in data.get("messages", []):
        phone = msg.get("sender", {}).get("phone")
        if phone:
            return phone.strip()
    return None
```

**Design rationale:**
- Iterates messages in order, returns the first non-empty phone found
- In practice all messages share the same sender, so first hit is sufficient
- Returns `None` if no phone found (edge case safety)

#### 2. Add phone sanitization helper (optional, next to `extract_phone()`)

```python
def sanitize_phone(phone):
    return phone.lstrip("+")
```

This strips a leading `+` if present (e.g. `+212620375029` → `212620375029`), since `+` in folder names works on Windows but may cause confusion. The current data has `212620375029` (no `+`), so this is future-proofing.

#### 3. Replace line 15: `base_output_dir`

**Before:**
```python
base_output_dir = "chat_archives"
```

**After:**
```python
phone = None          # will be set in main()
base_output_dir = "chat_archives"  # fallback if phone not found
```

#### 4. Insert phone extraction at the start of `main()`, after loading JSON

```python
def main():
    logger.info("Loading raw messages from %s ...", input_file)
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # ── new block ──
    global base_output_dir
    phone = extract_phone(data)
    if phone:
        phone = sanitize_phone(phone)
        base_output_dir = f"{phone}_chat_archives"
        logger.info("Phone: %s → folder: %s", phone, base_output_dir)
    else:
        logger.warning(
            "No phone found. Using default folder: %s", base_output_dir
        )
    # ── end new block ──

    hourly_groups = defaultdict(list)
    ...
```

**Why a global:** `base_output_dir` is a module-level constant currently (line 15). All references inside `main()` and other functions use it. Making it global avoids refactoring every internal reference.

#### 5. Update `tracking_dir` to derive from `base_output_dir`

Currently line 16:
```python
tracking_dir = os.path.join(base_output_dir, "_tracking")
```

This is already derived from `base_output_dir` — **no change needed**. When `base_output_dir` becomes `212620375029_chat_archives`, `tracking_dir` automatically becomes `212620375029_chat_archives/_tracking`.

Similarly, all `os.makedirs(day_folder, ...)` calls use `base_output_dir` — **no change needed**.

### Summary of code changes

| Location | Change |
|---|---|
| Line 15 | `base_output_dir` split: `phone = None` + `base_output_dir = "chat_archives"` (fallback) |
| After line 17 | Add `extract_phone()` and `sanitize_phone()` functions |
| `main()` after line 23 (JSON load) | Insert phone extraction block → override `base_output_dir` |
| Everything else | Already derives from `base_output_dir`/`tracking_dir` → unaffected |

## Edge Cases

| Scenario | Behavior |
|---|---|
| JSON has phone (normal) | `extract_phone()` returns `212620375029` → folder `212620375029_chat_archives/` |
| JSON missing `sender.phone` | `extract_phone()` returns `None` → keep `chat_archives` as fallback, log warning |
| Phone has leading `+` | `sanitize_phone()` strips it → e.g. `212620375029` |
| Phone has spaces, dashes | `.strip()` removes leading/trailing whitespace; dashes kept as-is (safe in folder names) |
| Re-running with same data | Tracking files live inside `212620375029_chat_archives/_tracking/` → idempotent ✅ |
| Running with a different customer's data | Different phone → different folder → no conflict ✅ |

## What does NOT change

- `tracking_dir` path derivation (already relative to `base_output_dir`)
- `day_folder` creation (already relative to `base_output_dir`)
- JSONL file writing logic
- Tracking file format and update logic
- All logging

## What changes in Phase 2 (separate plan)

The other 5 scripts (`extract_media_ptt.py`, `transcribe_ptt.py`, `build_customer_context.py`, `classify_customer.py`, `play_ptt.py`) all hardcode `BASE_DIR = "chat_archives"`. Phase 2 will add discovery logic (e.g. `_project.json` config file or glob) so they find the renamed folder. This is intentionally out of scope for now.

## Verification Steps

1. Run `python data_extraction.py`
2. Confirm folder `212620375029_chat_archives/` is created
3. Confirm `_tracking/` and JSONL files are inside it
4. Confirm old `chat_archives/` does NOT exist
5. Confirm tracking files reference the correct paths
6. Re-run — confirm no double-extraction (idempotency preserved)
