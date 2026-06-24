# WhatsApp Customer Lead Pipeline

Pipeline that extracts WhatsApp messages, decodes media, transcribes Darija voice messages, builds a lean LLM context file, and classifies the customer lead tier.

## Prerequisites

- Python 3.12+
- Dependencies: `pip install torch transformers yaml`
- FFmpeg (for `play_ptt.py`, optional)
- Source JSON file(s) in `whatsapp_raw_messages/` — format: `{phone_number}.json`

## Pipeline Steps

Run in order. Each step prompts you to select the customer/phone number.

### Step 1: Extract data

```bash
python data_extraction.py
```

Scans `whatsapp_raw_messages/*.json`, shows available source files with phone numbers. Select one → creates `{phone}_chat_archives/` with hourly JSONL files and tracking data in `_tracking/`.

### Step 2: Decode media

```bash
python extract_media_ptt.py
```

Select customer folder. Decodes base64-encoded media (voice messages, images) from JSONL to files in `media/` subfolder. Updates `media_link` in JSONL from data URI to local path.

### Step 3 (optional): Play voice messages

```bash
python play_ptt.py
```

Select customer folder. Interactive browser — pick a day, then a message to play via ffplay. Requires FFmpeg in PATH.

### Step 4: Transcribe voice messages

```bash
python transcribe_ptt.py
```

Select customer folder. Transcribes `.ogg` Darija voice messages using `ychafiqui/whisper-medium-darija`. Adds `transcript` field to JSONL entries. Skips already-transcribed.

### Step 5: Build customer context

```bash
python build_customer_context.py
```

Select customer folder. Scans all JSONL, merges `body` + `transcript` into `customer_context.txt` — one line per message, no JSON, no timestamps. Tracks appended timestamps for idempotency.

### Step 6: Classify lead tier

```bash
python classify_customer.py
```

Select customer folder. Loads Qwen3.5 model, injects `customer_context.txt` into system prompt, classifies as `HOT_LEAD`, `EXISTING_CUSTOMER`, or `COLD_LEAD`. Saves result to `_tracking/{timestamp}_{TIER}.txt`.

## Folder Structure

```
{phone}_chat_archives/
├── YYYY-MM/
│   └── YYYY-MM-DD/
│       ├── YYYY-MM-DD-HH.jsonl      # hourly message data
│       └── media/
│           ├── ptt_*.ogg             # decoded voice messages
│           └── img_* / doc_*         # other media
├── _tracking/
│   ├── extracted_info_YYYY-MM-DD.json   # extraction tracking
│   ├── appended_timestamps.json         # context build tracking
│   └── {timestamp}_{TIER}.txt           # classification results
└── customer_context.txt                  # aggregated LLM context
```

## Model Selection

Edit `classify_customer.py` line 19:

```python
MODEL = "qwen35_2b"   # 2B params, ~5GB RAM, runs on CPU
MODEL = "qwen35_4b"   # 4B params, requires GPU
```

## Notes

- All scripts are idempotent — safe to re-run, they skip already-processed data
- Classification prompt is in `prompts/classify_customer.yaml`
- Logging uses consistent timestamp format across all scripts
