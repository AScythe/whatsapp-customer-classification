# Transcribe PTT — Plan

## Overview

Add Darija (Moroccan Arabic) speech-to-text transcription to the WhatsApp message pipeline using a fine-tuned Whisper model from HuggingFace.

## Model

- **Model:** `ychafiqui/whisper-medium-darija`
- **Architecture:** OpenAI Whisper medium (0.8B params), fine-tuned on Darija speech dataset
- **Source:** https://huggingface.co/ychafiqui/whisper-medium-darija
- **Framework:** HuggingFace `transformers` pipeline
- **Cache:** ~1.5 GB downloaded on first use to `~/.cache/huggingface/`

## Why Not NeMo

NeMo's models (FastConformer, Parakeet, etc.) and Whisper are architecturally incompatible. They use different model classes, checkpoint formats, and inference APIs. You cannot load a Whisper model into NeMo's `from_pretrained()`.

Additionally, NeMo's Arabic models are trained on Modern Standard Arabic (MSA), not Darija dialect, so accuracy would be poor.

The correct approach is to use Whisper-darija directly via `transformers`, not through NeMo.

## New Script: transcribe_ptt.py

### Core Logic

```python
from transformers import pipeline
import torch

device = 0 if torch.cuda.is_available() else -1
pipe = pipeline("automatic-speech-recognition",
                model="ychafiqui/whisper-medium-darija",
                device=device)

result = pipe("path/to/audio.ogg")
transcript = result["text"]
```

### Algorithm

```
Walk chat_archives/**/*.jsonl (skip _tracking/ and extracted_info files)
  For each line in JSONL file:
    if type == "ptt"
      AND media_link is a relative file path (not base64, not null)
      AND "transcript" key does NOT exist in the entry:

      → resolve full path: os.path.join(jsonl_dir, media_link)
      → pipe(audio_path) → get transcript text
      → add "transcript" field to the JSON object
      → mark file as updated

  If any lines in the file were updated:
    → write all lines back atomically (.tmp + os.replace)
```

### Self-Tracking

No separate tracking file. The JSONL entry itself tracks state:
- `"transcript"` key missing → need to transcribe
- `"transcript"` key present → already done, skip

This is crash-safe: if the script crashes mid-write, the temp file is discarded and the original file is untouched.

### GPU / CPU Detection

```python
import torch
device = 0 if torch.cuda.is_available() else -1
```

- CUDA GPU available → fast inference
- CPU fallback → slower (estimated 3-5x real-time)

## Updated JSONL Format

**Before:**
```json
{
  "timestamp": "2026-06-18T10:44:37.000Z",
  "name": "Barae",
  "phone_number": "212620375029",
  "body": "",
  "type": "ptt",
  "media_link": "media/ptt_2026-06-18-10_001.ogg"
}
```

**After:**
```json
{
  "timestamp": "2026-06-18T10:44:37.000Z",
  "name": "Barae",
  "phone_number": "212620375029",
  "body": "",
  "type": "ptt",
  "media_link": "media/ptt_2026-06-18-10_001.ogg",
  "transcript": "مرحبا شحال من واحد"
}
```

## Update play_ptt.py

The player's context display will be updated to show the transcript after the "body" field:

```
══════════════════════════════════════════
  Voice Message  (1/8)
  From:    Barae  (212620375029)
  Time:    2026-06-18T10:44:37.000Z
  ────────────────────────────────────────
  (no text)
  Transcript: مرحبا شحال من واحد
  ────────────────────────────────────────
  Playing media/ptt_2026-06-18-10_001.ogg
══════════════════════════════════════════
```

## Full Pipeline

```
Step 1: python data_extraction.py      → hourly JSONL
Step 2: python extract_media_ptt.py    → .ogg files
Step 3: python transcribe_ptt.py       → add Darija transcripts
Step 4: python play_ptt.py             → interactive playback
```

## Files to Create / Modify

| File | Action |
|---|---|
| `transcribe_ptt.py` | **Create** — new transcription script |
| `play_ptt.py` | **Modify** — show transcript in context display |
| `data_extraction.py` | Unchanged |
| `extract_media_ptt.py` | Unchanged |

## Dependencies

```bash
pip install transformers torch torchaudio
```

- `transformers` — HuggingFace pipeline API
- `torch` + `torchaudio` — audio loading + tensor ops (CPU or CUDA)
