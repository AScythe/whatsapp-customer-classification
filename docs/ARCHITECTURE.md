# Architecture — WhatsApp Customer Lead Pipeline

> **Last verified:** 2026-06-24 12:30 EDT

## Project Structure

```
whatsapp_customer_classification/
├── data_extraction.py            # Step 1 — raw JSON → hourly JSONL
├── decode_media_ptt.py          # Step 2 — decode base64 media to files
├── decode_media_doc.py          # Step 2b — decode base64 documents to files
├── media_utils.py               # Shared helpers (find_next_seq, parse_data_uri, get_type_prefix)
├── transcribe_ptt.py             # Step 3 — Darija Whisper transcription
├── play_ptt.py                   # Step 4 (optional) — CLI voice message player
├── build_customer_context.py     # Step 5 — JSONL → plain-text context file
├── classify_customer.py          # Step 6 — Qwen3.5 lead classification
├── prompts/
│   └── classify_customer.yaml    # LLM system prompt (editable)
├── tests/
│   └── test_agent_guidelines.py  # AGENTS.md compliance validation
├── agent_utility/
│   ├── dedup_graph_nodes.py      # Graph node deduplication
│   ├── filter_graph.py           # Graph sub-type filtering
│   └── enhance_graph_viewer.py   # Interactive graph HTML enhancer
├── docs/
│   ├── SPECIFICATIONS.md         # Product vision and spec
│   └── PLAN_*.md                 # Planning documents
├── refs/
│   ├── AGENT_SETUP.md            # Development environment setup
│   ├── DOCUMENT_GUIDELINES.md    # Document scope governance
│   ├── PROJECT_BEST_PRACTICES.md # Coding patterns and lessons learned
│   └── PROMPTING_LESSONS.md      # Prompt engineering notes
├── .opencode/
│   └── skills/                   # Agentic workflow skill definitions
├── graphify-out/                 # Knowledge graph (auto-generated)
├── .cocoindex_code/              # Code index (auto-generated)
├── .gitignore                    # Ignores PII data and auto-generated files
├── AGENTS.md                     # Agent behavioral rules
├── LICENSE                       # MIT license
├── README.md                     # User-facing setup guide
└── opencode.json                 # OpenCode plugin config
```

## Module Descriptions

### data_extraction.py

Lead line: `# Description: Extracts WhatsApp JSON export into hourly JSONL files, with deduplication via timestamp tracking.`

Reads a raw WhatsApp JSON export from `whatsapp_raw_messages/`, groups messages by hour, and appends them to hourly JSONL files under `{phone}_chat_archives/`. Tracks extracted timestamps in `_tracking/extracted_timestamps.json` for idempotency.

- Prompts user to select which phone number's export to process
- Handles both fresh extraction (no existing JSONL) and incremental (only new messages)
- Outputs structured JSONL with fields: `timestamp`, `name`, `phone_number`, `body`, `type`, `media_link`

#### Functions
- `load_extracted_timestamps(tracker_file)` — reads previously extracted timestamps from JSON tracker file; returns `set` or `None`
- `save_extracted_timestamps(tracker_file, timestamps)` — persists timestamp set to JSON tracker file
- `seed_from_existing_jsonl(base_dir)` — scans existing JSONL files to rebuild timestamp set (for resuming without tracker file)
- `main()` — orchestrates extraction: loads source, compares against tracker, groups new messages by hour, appends to JSONL files

### media_utils.py

Shared helper functions for media and document decoding. Extracted to avoid duplication between `decode_media_ptt.py` and `decode_media_doc.py`.

#### Functions
- `find_next_seq(media_dir, hour_key, type_prefix)` — finds the next available sequence number for a media filename within a directory
- `parse_data_uri(uri)` — splits a data URI into MIME type and base64 payload
- `get_type_prefix(message_type)` — maps message type string to file prefix (`ptt`, `img`, `doc`, `media`)

### decode_media_ptt.py

Lead line: `# Description: Decodes base64-encoded media (voice messages, images) from WhatsApp JSONL to local files.`

Walks all JSONL files in the selected customer folder, finds entries with `data:` URI in `media_link`, decodes the base64 payload, and writes media files to a `media/` subfolder. Updates the JSONL `media_link` from data URI to local path.

- Only decodes MIME types in `MIME_EXT_MAP` (currently `audio/ogg`, `image/jpeg`, `image/png`)
- Uses sequential numbering per hour-key to avoid filename collisions
- Writes updated JSONL atomically via temp file + `shutil.move`

#### Functions
- `process_jsonl(jsonl_path)` — processes a single JSONL file: decodes all embedded media, updates the file in-place
- `main()` — walks customer directory tree, processes every JSONL file with embedded media

### decode_media_doc.py

Lead line: `# Description: Decodes base64-encoded documents (PDF, DOC, DOCX, XLS, XLSX) from WhatsApp JSONL to local files.`

Walks all JSONL files in the selected customer folder, finds entries with `type="document"` and a `data:` URI in `media_link`, decodes the base64 payload, and writes document files to a `media/` subfolder alongside other media. Updates the JSONL `media_link` from data URI to local path.

- Only processes entries where `type` is `"document"` (skips voice messages, images, etc.)
- Supports PDF, DOC, DOCX, XLS, XLSX MIME types
- Uses sequential numbering per hour-key to avoid filename collisions
- Writes updated JSONL atomically via temp file + `shutil.move`
- Idempotent — skips entries where `media_link` no longer starts with `data:`

#### Functions
- `process_jsonl(jsonl_path)` — processes a single JSONL file: decodes document entries, updates the file in-place
- `main()` — walks customer directory tree, processes every JSONL file with document entries

### transcribe_ptt.py

Lead line: `# Description: Transcribes Darija voice messages (.ogg) using ychafiqui/whisper-medium-darija.`

Scans the customer folder for untranscribed voice messages, loads the `ychafiqui/whisper-medium-darija` model, and adds a `transcript` field to each PTT entry in the JSONL files.

- Skips entries where `transcript` already exists (idempotent)
- Skips entries whose `media_link` is still a data URI (not yet decoded — must run Step 2 first)
- Counts pending entries before loading the model (saves time if nothing to do)
- Uses GPU if available, falls back to CPU

#### Functions
- `get_device()` — returns CUDA device index (0) or CPU (-1) based on availability
- `count_pending(base_dir)` — scans JSONL files to count PTT entries needing transcription without loading the model
- `load_pipeline(device)` — loads the Whisper-darija pipeline from Hugging Face; downloads model on first run
- `process_jsonl(jsonl_path, pipe)` — transcribes all pending PTT entries in a single JSONL file
- `main()` — orchestrates: count pending, load model, walk files, transcribe

### play_ptt.py

Lead line: `# Description: Interactive CLI player for decoded WhatsApp voice messages via ffplay.`

Interactive CLI voice message browser. Scans the customer folder for `.ogg` files, presents a day-by-day menu, and plays selected messages via `ffplay`.

- Requires FFmpeg in PATH
- Shows message metadata before playing: sender name, timestamp, text body, transcript
- Handles keyboard interrupts gracefully

#### Functions
- `check_ffplay()` — verifies ffplay is available on PATH, exits with guidance if not
- `find_ogg_files()` — walks customer folder, groups `.ogg` files by day directory
- `parse_timestamp_from_filename(ogg_filename)` — extracts hour-key and sequence number from media filename
- `find_matching_entry(jsonl_path, filename)` — finds the JSONL entry corresponding to a media file by matching `media_link`
- `collect_entries_for_day(ogg_list)` — assembles full entry data (timestamp, sender, body, transcript) for a day's voice messages
- `print_context(entry, current, total)` — displays formatted message metadata before playback
- `play_audio(path)` — plays an audio file via ffplay subprocess
- `input_int(prompt, min_val, max_val)` — robust integer input with bounds checking and interrupt handling
- `show_day_menu(day_ogg_map)` — displays day selection menu and dispatches to message menu
- `show_message_menu(day_name, ogg_list)` — displays message list for a day and plays selected audio
- `main()` — entry point: verifies ffplay, finds ogg files, launches day menu

### build_customer_context.py

Lead line: `# Description: Merges message bodies and transcripts from JSONL into a single LLM-ready context file.`

Merges all messages and transcripts from JSONL files into a single plain-text file (`{timestamp}_customer_context.txt`). One line per message — `body` and `transcript` are joined with ` | ` when both exist.

- Tracks appended timestamps in `_tracking/appended_timestamps.json`
- Creates a new context file named after the latest message timestamp (enables incremental builds)
- Skips messages with no `body` and no `transcript`

#### Functions
- `load_tracker()` — reads appended timestamp set from JSON tracker file
- `save_tracker(timestamps)` — persists appended timestamp set to JSON tracker file
- `sanitize_ts(ts)` — replaces colons with hyphens and removes `.000` for filesystem-safe filenames
- `context_file_for_ts(ts)` — builds the context file path from a timestamp
- `find_jsonl_files()` — globs all JSONL files under the customer folder, excluding `_tracking`
- `compose_line(body, transcript)` — merges body and transcript into a single output line
- `main()` — reads all JSONL, assembles entries, writes context file, updates tracker

### classify_customer.py

Lead line: `# Description: Classifies customer lead tier (HOT/EXISTING/COLD) using a local Qwen3.5 LLM.`

Loads a Qwen3.5 model, reads the customer context file and the YAML prompt template, runs inference, and saves the classification result as `{timestamp}_{TIER}.txt`. Supports two model sizes: 2B (CPU, ~5GB) and 4B (GPU).

- Retries with a stricter prompt if the first JSON parse fails
- Strips `</think>` blocks from model output before parsing
- Saves classification result with timestamp, context line count, tier, and reason

#### Functions
- `load_tracker_ts()` — reads the tracker file to find the latest processed timestamp
- `load_prompt()` — loads and validates the YAML prompt template from `prompts/classify_customer.yaml`
- `load_context(context_file)` — reads the customer context file, validates non-empty
- `sanitize_ts(ts)` — replaces colons with hyphens for filesystem-safe filenames
- `already_classified(latest_ts)` — checks if a classification result already exists for the given timestamp
- `strip_thinking(text)` — removes `<think>...</think>` blocks from model output
- `extract_json(text)` — parses JSON `{"tier": "...", "reason": "..."}` from model output
- `get_device()` — determines torch dtype (float16 for CUDA or CPU/2B, float32 for CPU/4B)
- `load_model(dtype)` — loads the Qwen3.5 processor and model from Hugging Face
- `run_inference(processor, model, system_prompt, context, retry)` — tokenizes input, runs model.generate(), decodes output
- `save_result(latest_ts, tier, reason, context_line_count)` — writes classification result to a timestamped file
- `main()` — full orchestration: load tracker → load prompt → load context → load model → run inference → save result

## Data Flow

The pipeline follows a linear 6-step flow. Data is passed through the filesystem — each script reads from and writes to the `{phone}_chat_archives/` directory tree.

```
WhatsApp JSON Export (whatsapp_raw_messages/{phone}.json)
    │
    ▼
[Step 1] data_extraction.py
    │  Groups messages by hour → appends to YYYY-MM-DD-HH.jsonl
    │  Tracks extracted timestamps in _tracking/extracted_timestamps.json
    ▼
[Step 2] decode_media_ptt.py
    │  Decodes data: URIs → writes media/ptt_*.ogg, media/img_*, etc.
    │  Updates media_link in JSONL from data: URI → local path
    ▼
[Step 2b] decode_media_doc.py
    │  Decodes document data: URIs → writes media/doc_*.pdf, doc_*.docx, etc.
    │  Updates media_link in JSONL from data: URI → local path
    ▼
[Step 3] transcribe_ptt.py
    │  Loads Whisper-darija → transcribes .ogg → adds transcript field to JSONL
    ▼
[Step 4] play_ptt.py (optional)
    │  Reads .ogg files → plays via ffplay
    ▼
[Step 5] build_customer_context.py
    │  Reads all JSONL → merges body + transcript → writes customer_context.txt
    │  Tracks appended timestamps in _tracking/appended_timestamps.json
    ▼
[Step 6] classify_customer.py
    │  Loads Qwen3.5 + YAML prompt → reads customer_context.txt → classifies
    │  Saves result to _tracking/{timestamp}_{TIER}.txt
    ▼
Classification Result (HOT_LEAD / EXISTING_CUSTOMER / COLD_LEAD)
```

### Key Data Files

| File | Format | Purpose |
|------|--------|---------|
| `whatsapp_raw_messages/{phone}.json` | JSON (WhatsApp export) | Source input — messages array with sender, body, type, media_link, timestamp |
| `{phone}_chat_archives/YYYY-MM/YYYY-MM-DD/YYYY-MM-DD-HH.jsonl` | JSONL | Hourly message batches — enriched as pipeline progresses |
| `{phone}_chat_archives/_tracking/extracted_timestamps.json` | JSON | Tracks which timestamps have been extracted (Step 1 idempotency) |
| `{phone}_chat_archives/_tracking/appended_timestamps.json` | JSON | Tracks which timestamps have been included in context (Step 5 idempotency) |
| `{phone}_chat_archives/{timestamp}_customer_context.txt` | Plain text | LLM-ready context — one line per message |
| `{phone}_chat_archives/{timestamp}_{TIER}.txt` | Plain text | Classification result with tier, reason, metadata |

## Import Structure

All pipeline scripts are standalone — they do not import from each other. Each script is independently runnable via `python <script>.py`.

```
data_extraction.py      → json, logging, os, sys, datetime, collections, glob
media_utils.py         → os, re
decode_media_ptt.py   → json, logging, os, sys, base64, shutil, tempfile, glob, media_utils
decode_media_doc.py   → json, logging, os, sys, base64, shutil, glob, media_utils
transcribe_ptt.py       → json, logging, os, sys, torch, shutil, time, glob, transformers
play_ptt.py             → os, json, re, subprocess, shutil, sys, logging, collections, glob
build_customer_context.py → json, logging, os, sys, glob
classify_customer.py    → json, logging, os, re, sys, time, glob, torch, yaml, transformers
```

**Shared dependencies:** `torch`, `transformers`, and `yaml` are shared between `transcribe_ptt.py` and `classify_customer.py`. `media_utils` is shared between `decode_media_ptt.py` and `decode_media_doc.py`. All other dependencies are standard library.

## Key Design Decisions

- **Filesystem as message bus** — scripts pass data through the filesystem (JSONL files on disk) rather than through in-memory queues or a database. This makes each script independently testable and debuggable, and means a failure in one step doesn't lose in-memory progress.

- **Timestamp-based idempotency** — each script tracks what it has processed by storing timestamps in JSON tracker files. This is simpler and more transparent than hash-based deduplication, and matches the natural ordering of chat messages.

- **Standalone scripts over modular package** — each pipeline step is a single `.py` file with its own `main()`. There is no shared module. This keeps the learning curve flat (open any script and see the full flow) and avoids import coupling between steps.

- **JSONL over JSON** — hourly files use newline-delimited JSON (JSONL) instead of a single JSON array. This enables streaming reads/writes and atomic per-line updates without reading the entire file into memory.

- **Separate prompt file** — the classification prompt lives in `prompts/classify_customer.yaml` rather than being embedded in Python code. This enables prompt engineering iterations without touching source code.

## Running Instructions

### Prerequisites
- Python 3.12+
- `pip install torch transformers yaml`
- FFmpeg (optional, for `play_ptt.py`)

### Full Pipeline
```bash
python data_extraction.py
python decode_media_ptt.py
python transcribe_ptt.py
python build_customer_context.py
python classify_customer.py
```

### Individual Steps
Each script prompts for customer folder selection (or auto-selects if only one exists). Run in order — later steps depend on output from earlier steps.

### Tests
```bash
python tests/test_agent_guidelines.py
```

### Maintenance Scripts
```bash
python agent_utility/dedup_graph_nodes.py     # Merge duplicate graph nodes
python agent_utility/filter_graph.py          # Filter graph by sub-type
python agent_utility/enhance_graph_viewer.py  # Enhance graph HTML viewer
ccc index                                     # Rebuild CocoIndex code index
```

## Modifying Instructions

### Adding a Pipeline Step
1. Create a new standalone `.py` script following the existing pattern (logging setup, customer folder selection, idempotency via tracker file)
2. Add it as a new numbered step in the pipeline (README.md and SPECIFICATIONS.md)
3. Call it from the correct position in the flow — later steps may depend on its output

### Changing the Classification Model
1. Edit `classify_customer.py` line 39: change `MODEL` to the new model key
2. Update `MODEL_MAP` dict with the new Hugging Face model ID if it's a different model family
3. Adjust `SAMPLING_PARAMS` if the new model needs different generation parameters

### Editing the Classification Prompt
Edit `prompts/classify_customer.yaml` — the `system_prompt` field contains the full prompt template. Use `{customer_context}` as a placeholder for the chat transcript. No code changes needed.

### Adding New Media Types for Decoding
Add the MIME type to `MIME_EXT_MAP` in `decode_media_ptt.py` and, if needed, add a prefix mapping in `get_type_prefix()`.

## Tests

### test_agent_guidelines.py

Lead line: `Description: Validates AGENTS.md specification-routing logic and structural integrity.`

Covers 12 test groups: skill routing, tool selection, no-match fallthrough, mixed-task layering, priority chain, file ownership paths, commands reference, documentation structure, test suite naming, utility skills, documentation discipline (description headers), and tooling availability.

#### Functions
- `check(condition, msg)` — prints OK/? result and updates PASS/FAIL counters
- `read_file(path)` — reads a text file and returns its content
- `extract_frontmatter(path)` — parses YAML frontmatter from a skill SKILL.md
- `test_skill_routing()` — verifies each loadable skill has a description that matches its trigger phrases
- `test_tool_selection()` — verifies hypothetical queries route to the correct tool (ast-grep, cocoindex, graphify, grep)
- `test_no_match_fallthrough()` — verifies non-trigger messages don't match any skill
- `test_mixed_tasks_combine_layers()` — verifies mixed queries combine tool layers appropriately
- `test_priority_chain()` — verifies the skill loading priority chain is defined in AGENTS.md
- `test_file_ownership_paths()` — verifies every path in File Ownership exists on disk (with exceptions for auto-generated)
- `test_commands_reference()` — verifies every command target in Commands Reference exists
- `test_documentation_structure()` — verifies every doc in Documentation Structure exists
- `test_test_suite_structure()` — verifies naming conventions match actual test files
- `test_utility_skills()` — verifies referenced skill files exist
- `test_documentation_discipline()` — verifies source files have description headers
- `test_tooling_rules()` — verifies required tools (uv, npm) are available on PATH
