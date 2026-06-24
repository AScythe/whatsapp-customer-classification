# Replace `_project.json` with CLI `--phone` Arguments

## Goal

Remove `_project.json` and its config-file indirection. Each script takes the phone number directly as a CLI argument and constructs the folder name itself: `{phone}_chat_archives`.

## Why

- `_project.json` is mutable shared state — only one customer at a time, easy to overwrite
- CLI arguments are explicit, stateless, and work with multiple customers in parallel
- The folder name IS the phone number — no need for a config file to look it up

## Changes per script

### Phase 1: Add `argparse` + `--phone` to all 6 scripts

All scripts follow the same pattern at the top:

```python
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--phone", required=True, help="Customer phone number, e.g. 212620375029")
args = parser.parse_args()

PHONE = args.phone
BASE_DIR = f"{PHONE}_chat_archives"
```

| File | What changes |
|---|---|
| `data_extraction.py` | Add argparse block. `base_output_dir` = `f"{PHONE}_chat_archives"`. Input path = `whatsapp_raw_messages/{PHONE}.json`. Remove `extract_phone()` / `sanitize_phone()` (no longer needed). Remove `_project.json` write. |
| `extract_media_ptt.py` | Add argparse block. Replace current `BASE_DIR` line with `PHONE` + `BASE_DIR`. |
| `transcribe_ptt.py` | Same pattern. |
| `build_customer_context.py` | Same pattern. |
| `play_ptt.py` | Same pattern. |
| `classify_customer.py` | Same pattern. |

### Phase 2: Remove `_project.json` entirely

After all scripts are updated, `_project.json` is no longer created or read by any script. It can be deleted.

## Detailed changes per file

### `data_extraction.py`

**Current (lines 14–27):**
```python
input_file = "whatsapp_raw_messages/whatsapp_messages.json"
base_output_dir = "chat_archives"  # fallback

def extract_phone(data): ...
def sanitize_phone(phone): ...

def main():
    ...
    global base_output_dir
    phone = extract_phone(data)
    ...
```

**New:**
```python
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--phone", required=True)
args = parser.parse_args()

PHONE = args.phone
input_file = f"whatsapp_raw_messages/{PHONE}.json"
base_output_dir = f"{PHONE}_chat_archives"

def main():
    ...
    # remove: global base_output_dir, extract_phone(), sanitize_phone()
    # remove: _project.json write at end
```

### `extract_media_ptt.py`, `transcribe_ptt.py`, `play_ptt.py`

**Current:**
```python
import json, logging, os, ...
BASE_DIR = ...  # hardcoded or config read
```

**New — add argparse before `BASE_DIR`:**
```python
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--phone", required=True)
args = parser.parse_args()

BASE_DIR = f"{args.phone}_chat_archives"
```

### `build_customer_context.py`

Same argparse pattern. `TRACKING_DIR`, `TRACKER_FILE`, `OUTPUT_FILE` all auto-resolve from `BASE_DIR`.

### `classify_customer.py`

Same argparse pattern. All derived paths auto-resolve.

## Usage after changes

```bash
# Step-by-step for one customer:
python data_extraction.py --phone 212620375029
python extract_media_ptt.py --phone 212620375029
python transcribe_ptt.py --phone 212620375029
python build_customer_context.py --phone 212620375029
python classify_customer.py --phone 212620375029

# Switch to another customer:
python data_extraction.py --phone 212612345678
python extract_media_ptt.py --phone 212612345678
...

# Both folders coexist:
212620375029_chat_archives/
212612345678_chat_archives/
```

## Edge cases

| Scenario | Behavior |
|---|---|
| `--phone` omitted | `argparse` prints usage and exits with error |
| Phone has spaces or special chars | Used as-is in folder name; caller's responsibility |
| `whatsapp_raw_messages/{phone}.json` doesn't exist | `FileNotFoundError` — clear traceback |
| Source JSON naming convention | Assumes `whatsapp_raw_messages/{phone}.json`. Can be changed in one place later. |

## Files to delete

- `_project.json` (manually, after rollout)

## Files NOT affected

- `prompts/classify_customer.yaml`
- `PLAN_*.md` documents
- Any data inside existing `*_chat_archives/` folders
