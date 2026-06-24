# Model Selection for Customer Classification

## Overview

Add a model selection feature to `classify_customer.py` so the user can choose between `Qwen/Qwen3.5-2B` (for CPU/dev machines) and `Qwen/Qwen3.5-4B` (for GPU/production) via a single constant. The 2B model will use `float16` on CPU to fit within ~8 GB available RAM.

## Memory Analysis

| Model | Params (+ vision) | float32 RAM | float16 RAM | Fits this machine? |
|---|---|---|---|---|
| 4B | ~5B total | ~20 GB | ~10 GB | ❌ Offloaded to disk, inference crashes |
| 2B | ~2.5B total | ~10 GB | ~5 GB  | ✅ float16 fits in 8 GB free RAM |

**This machine:** 16 GB total, ~8 GB available. CPU-only (no CUDA).

## Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Selection method | Module-level constant `MODEL` | Simple, visible at top of file, easy to change |
| Model values | `"qwen35_2b"` / `"qwen35_4b"` | Short, descriptive keys map to HF model IDs |
| 2B on CPU | Force `float16` | Reduces RAM from ~10 GB to ~5 GB, fits within available memory |
| 4B on CPU | Keep `float32` | 4B already failed on CPU; user should use GPU |
| GPU path | Unchanged for both models (`float16`) | GPU has enough VRAM for either model |
| Thinking mode | `enable_thinking=False` for both | 2B defaults to non-thinking anyway; 4B we disable explicitly |

## Files to Create / Modify

| File | Action |
|---|---|
| `classify_customer.py` | **Modify** — add `MODEL`, `MODEL_MAP`, update `get_device()`, update `load_model()` messages |
| `PLAN_model_selection.md` | **Create** — this document |

**Unchanged:** `prompts/classify_customer.yaml`, `data_extraction.py`, `extract_media_ptt.py`, `transcribe_ptt.py`, `play_ptt.py`, `build_customer_context.py`, `PLAN_classify_customer.md`

## Changes to classify_customer.py

### 1. Add model selection constants (after imports, before `BASE_DIR`)

```python
# Options: "qwen35_2b", "qwen35_4b"
MODEL = "qwen35_2b"

MODEL_MAP = {
    "qwen35_2b": "Qwen/Qwen3.5-2B",
    "qwen35_4b": "Qwen/Qwen3.5-4B",
}
```

### 2. Replace hardcoded `MODEL_NAME`

```python
# Before:
MODEL_NAME = "Qwen/Qwen3.5-4B"

# After:
MODEL_NAME = MODEL_MAP[MODEL]
```

### 3. Update `get_device()` to use float16 for 2B on CPU

```python
def get_device():
    if torch.cuda.is_available():
        logger.info("Using GPU: %s", torch.cuda.get_device_name(0))
        return torch.float16
    else:
        if MODEL == "qwen35_2b":
            logger.info("CPU mode: using float16 for 2B model (~5 GB RAM expected)")
            return torch.float16
        else:
            logger.warning("No GPU detected / CPU mode.")
            logger.warning("4B model needs ~20 GB RAM on CPU — this will likely fail.")
            logger.warning("Switch MODEL to qwen35_2b for CPU or use a GPU machine.")
            return torch.float32
```

### 4. Update `load_model()` messages

The current warning says "CPU requires ~20GB RAM" which is only true for the 4B model. Make it conditional:

```python
if not torch.cuda.is_available():
    if MODEL == "qwen35_2b":
        logger.info("CPU mode: 2B model in float16 (~5 GB). This may still be slow.")
    else:
        logger.warning("CPU mode: 4B model needs ~20 GB RAM — likely to fail.")
```

### 5. Add model info log at startup

In `main()`, log which model is being used:

```python
logger.info("Model: %s (%s)", MODEL_NAME, MODEL)
```

## Usage

```bash
# Edit classify_customer.py, set MODEL = "qwen35_2b" or "qwen35_4b"
python classify_customer.py
```

### Switching between machines

| Environment | MODEL setting | Expected performance |
|---|---|---|
| Dev machine (CPU, 16 GB) | `qwen35_2b` | Slow but functional (~minutes per inference) |
| Production machine (GPU) | `qwen35_4b` | Fast (~seconds per inference) |
| Production machine (GPU) | `qwen35_2b` | Fast (~seconds), lower quality |

## Verification

After implementation:
1. Run with `MODEL = "qwen35_2b"` on this dev machine — should load and complete inference
2. Switch to `MODEL = "qwen35_4b"` — should give clear error about insufficient RAM
3. Both should display proper timestamped logging throughout

## Rollback

If the 2B model also fails on CPU, revert `MODEL` back to `qwen35_4b` and run only on GPU.
