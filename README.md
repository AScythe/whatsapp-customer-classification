# WhatsApp Customer Lead Pipeline

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

WhatsApp customer lead classification engine — automatically triages inbound leads into sales-ready tiers by extracting chats, transcribing Darija voice notes, and classifying without manual review, all on your own machine.

> **Last verified:** 2026-06-24 12:00 EDT

## What is WhatsApp Customer Lead Pipeline?

A 6-step Python pipeline that turns raw WhatsApp chat exports into actionable sales intelligence. It ingests a WhatsApp message JSON file, extracts conversations, decodes voice messages and media, transcribes Darija audio using a fine-tuned Whisper model, builds a compact LLM-ready context file, and classifies each customer into a lead tier. Every step is idempotent — safe to re-run without duplicating work.

## Features

- **Automatic lead triage** — classify customers as HOT, EXISTING, or COLD without manual review
- **Darija voice transcription** — fine-tuned Whisper model for Moroccan Arabic voice notes
- **Idempotent pipeline** — each step tracks what it's already processed and skips it on re-run
- **Local-first privacy** — all processing runs on your machine; no data sent to external APIs
- **Model flexibility** — choose between 2B (CPU, ~5GB RAM) and 4B (GPU) Qwen3.5 models

## Quick Start

```bash
# Install dependencies
pip install torch transformers yaml

# Place your WhatsApp export in whatsapp_raw_messages/ as {phone}.json
# Then run the full pipeline:
python data_extraction.py    # Step 1: Extract
python decode_media_ptt.py  # Step 2: Decode media
python decode_media_doc.py  # Step 2b: Decode documents
python transcribe_ptt.py     # Step 3: Transcribe voice notes
python build_customer_context.py  # Step 4: Build LLM context
python classify_customer.py  # Step 5: Classify lead
```

## How to Use

Run each step in order. Every script prompts you to select which customer/phone number to process.

### Step 1: Extract data

```bash
python data_extraction.py
```

Scans `whatsapp_raw_messages/*.json`, lists available source files by phone number. Select one → creates `{phone}_chat_archives/` with hourly JSONL files and tracking data in `_tracking/`.

### Step 2: Decode media

```bash
python decode_media_ptt.py
```

Select a customer folder. Decodes base64-encoded media (voice messages, images) from JSONL to files in `media/`. Updates `media_link` in JSONL from data URI to local path.

### Step 2b: Decode documents

```bash
python decode_media_doc.py
```

Select a customer folder. Decodes base64-encoded documents (PDF, DOC, DOCX, XLS, XLSX) from JSONL to files in `media/` alongside other media. Only processes entries with `type="document"`. Updates `media_link` in JSONL from data URI to local path.

### Step 3: Transcribe voice messages

```bash
python transcribe_ptt.py
```

Select a customer folder. Transcribes `.ogg` Darija voice messages using `ychafiqui/whisper-medium-darija`. Adds a `transcript` field to JSONL entries. Skips already-transcribed.

### Step 4 (optional): Play voice messages

```bash
python play_ptt.py
```

Select a customer folder. Interactive browser — pick a day, then a message to play via ffplay. Requires FFmpeg in PATH.

### Step 5: Build customer context

```bash
python build_customer_context.py
```

Select a customer folder. Merges all message `body` and `transcript` fields into `customer_context.txt` — one line per message, no JSON, no timestamps. Tracks appended timestamps for idempotency.

### Step 6: Classify lead tier

```bash
python classify_customer.py
```

Select a customer folder. Loads the Qwen3.5 model, feeds `customer_context.txt` into the classification prompt, and saves the result (`HOT_LEAD`, `EXISTING_CUSTOMER`, or `COLD_LEAD`) to `_tracking/{timestamp}_{TIER}.txt`.

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

## Technical Details

| Technology | Role |
|------------|------|
| Python 3.12+ | Runtime |
| PyTorch | Model inference backend |
| ychafiqui/whisper-medium-darija | Darija speech-to-text |
| Qwen3.5 (2B / 4B) | Lead classification LLM |

To switch between model sizes, edit `classify_customer.py` line 39:

```python
MODEL = "qwen35_2b"   # 2B params, ~5GB RAM, runs on CPU
MODEL = "qwen35_4b"   # 4B params, requires GPU
```

## Testing

```bash
python tests/test_agent_guidelines.py
```

Validates AGENTS.md routing logic, file ownership paths, and project structure.

## Documentation

| Document | Purpose |
|----------|---------|
| [AGENTS.md](AGENTS.md) | AI agent behavioral rules and project structure |
| [README.md](README.md) | User-facing setup and pipeline guide (you are here) |
| [refs/AGENT_SETUP.md](refs/AGENT_SETUP.md) | Development environment setup |
| [refs/PROJECT_BEST_PRACTICES.md](refs/PROJECT_BEST_PRACTICES.md) | Coding patterns and lessons learned |

## Privacy & Security

- **All processing is local** — no data is sent to external APIs or cloud services
- **PII is gitignored** — `whatsapp_raw_messages/` and `*_chat_archives/` are excluded from version control
- **No telemetry** — the pipeline does not phone home or collect usage data
- **Model weights stay on your machine** — the LLM and Whisper models run entirely offline

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes (all scripts should remain idempotent)
4. Run `python tests/test_agent_guidelines.py` to verify
5. Submit a pull request

See [AGENT_SETUP.md](refs/AGENT_SETUP.md) for development environment setup and agent workflow rules.

## License

[MIT](LICENSE)

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError: torch` | Run `pip install torch transformers yaml` |
| `ffplay not found` when running play_ptt.py | Install FFmpeg and add it to your PATH |
| Model download fails during classification | The Qwen3.5 model downloads on first run — ensure a stable internet connection and ~5GB free disk space |
| Voice messages not transcribed | Ensure Step 2 (decode media) ran first — transcription reads decoded `.ogg` files |
| `customer_context.txt` is empty | Run Step 5 after Step 4 — context depends on transcripts |

## Why / Value Proposition

Sales teams spend hours manually reading WhatsApp chats to identify hot leads. This pipeline automates triage end-to-end: extract, transcribe (including Darija voice notes), build context, and classify — turning hours of manual work into a single command.
