# Customer Lead Classification — Plan

## Overview

Classify the aggregated customer context (from `customer_context.txt`) as `HOT_LEAD`, `EXISTING_CUSTOMER`, or `COLD_LEAD` using Qwen3.5-4B as the LLM. The result is saved as a timestamped file in the tracking directory. Re-running the script re-classifies with the latest context.

## Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| LLM | Qwen3.5-4B (HuggingFace) | Strong multilingual support (Arabic + English) |
| Inference backend | `transformers` pipeline | Consistent with existing `transcribe_ptt.py` |
| Thinking mode | **Disabled** (`enable_thinking=False`) | Need direct JSON output, not chain-of-thought |
| Sampling | `temperature=0.2`, `top_p=0.9` | Low temperature for deterministic classification |
| GPU/CPU | Auto-detect with CPU fallback | Production has GPU, dev machine doesn't |
| Prompt format | YAML file with `{customer_context}` placeholder | Clean separation of prompt from code |
| Output filename | `{sanitized_latest_ts}_{TIER}.txt` | Self-documenting, no overwrites |
| Output location | `chat_archives/_tracking/` | Consistent with existing tracking files |

## New Files

| File | Action |
|---|---|
| `prompts/classify_customer.yaml` | **Create** — YAML prompt template |
| `classify_customer.py` | **Create** — classification script |
| `PLAN_classify_customer.md` | **Create** — this plan document |

## Files Auto-Created (at runtime)

| File | Purpose |
|---|---|
| `chat_archives/_tracking/{ts}_{TIER}.txt` | Classification result (e.g. `2026-06-21T11-15-52Z_HOT_LEAD.txt`) |

Unchanged: `data_extraction.py`, `extract_media_ptt.py`, `transcribe_ptt.py`, `build_customer_context.py`, `play_ptt.py`

## Algorithm: classify_customer.py

```
1. Load appended_timestamps.json from chat_archives/_tracking/
   → Get latest_time = max(timestamps) → error if no timestamps
   → Fail early if file missing

2. Load prompts/classify_customer.yaml
   → Read system_prompt field containing {customer_context} placeholder

3. Read customer_context.txt from chat_archives/
   → Count lines → context_line_count
   → Substitute entire content into {customer_context} placeholder

4. Assemble chat messages:
     system: {system_prompt with context substituted}
     user:  "Classify the transcript above."

5. Load Qwen3.5-4B model:
     device = 0 if torch.cuda.is_available() else -1
     dtype = torch.float16 if device >= 0 else torch.float32
     model = AutoModelForCausalLM.from_pretrained(
         "Qwen/Qwen3.5-4B",
         torch_dtype=dtype,
         device_map="auto"
     )
     tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen3.5-4B")

6. Run inference:
     inputs = tokenizer.apply_chat_template(messages, ...)
     with torch.no_grad():
         outputs = model.generate(
             **inputs,
             max_new_tokens=256,
             temperature=0.2,
             top_p=0.9,
             do_sample=True,
         )
     response = tokenizer.decode(outputs[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)

7. Parse response JSON from the generated text:
     Expected: {"tier": "HOT_LEAD", "reason": "..."}
     If malformed → retry once with stricter emphasis on JSON
     If still fails → print error, exit non-zero

8. Sanitize latest_time for Windows filename:
     2026-06-21T11:15:52.000Z → 2026-06-21T11-15-52Z
     (replace : with -, strip .000)

9. Write result file:
     Path: chat_archives/_tracking/{sanitized_ts}_{tier}.txt
     Content:
       Latest message: 2026-06-21T11:15:52.000Z
       Context lines: 32

       Classification: HOT_LEAD
       Reason: <1-sentence justification>

10. Print summary to stdout:
      "Classification: HOT_LEAD — User is asking for a payment link."
      "Result saved to: _tracking/2026-06-21T11-15-52Z_HOT_LEAD.txt"
```

## Prompt Template: prompts/classify_customer.yaml

```yaml
system_prompt: |
  You are a lead triage assistant analyzing chat transcripts from a product campaign. Classify the user into exactly one of three tiers: HOT_LEAD, EXISTING_CUSTOMER, or COLD_LEAD based on these rules:

  1. HOT_LEAD: The user shows high intent or is evaluating specific details to buy right now.
  Look for:
  - Requests for payment links, pricing variants, or bank details.
  - Specific product availability questions (e.g., "Do you have size M in blue?").
  - Delivery/shipping logistics for their specific location.
  - Phrases indicating immediate interest (e.g., "Send me the invoice," "Can I order?").

  2. EXISTING_CUSTOMER: The user already bought a product and has a post-purchase inquiry.
  Look for:
  - Phrases indicating user already purchased a product.
  - Tracking numbers or delivery status updates for a past order.
  - Complaints about a defective item or payment issues from a previous purchase.
  - Repeat purchase requests for accessories or refills.

  3. COLD_LEAD: The user shows low intent, is browsing casually, or wants general information.
  Look for:
  - Anything that doesn't fit the criteria of HOT_LEAD or EXISTING_CUSTOMER.
  - Very broad product questions ("What is this?", "How does it work?").
  - Requests for reviews or general proof without asking how to buy.
  - Unsubscribe or rejection phrases ("Stop", "Not interested", "No thanks").

  Analyze the following chat transcript below to classify the user into its appropriate tier:
  {customer_context}

  Return ONLY the JSON object as Final Answer: {"tier": "TIER_NAME", "reason": "1-sentence justification"}.
```

## GPU / CPU Detection

```python
device = 0 if torch.cuda.is_available() else -1
```

- GPU available → `float16`, fast inference
- CPU only → `float32`, slower (warning printed)

## Edge Cases

| Case | Handling |
|---|---|
| `appended_timestamps.json` missing | Error: "Run build_customer_context.py first. No timestamps found." |
| `customer_context.txt` missing | Error: "Run build_customer_context.py first. customer_context.txt not found." |
| Prompt file missing | Error: "Prompt file not found: prompts/classify_customer.yaml" |
| Model not downloaded | Auto-download from HuggingFace on first run (~9GB) |
| LLM output is malformed JSON | Retry once with "ONLY valid JSON" emphasis; if still fails → error |
| LLM outputs thinking before JSON | Strip `<think>...</think>` block before parsing |
| Context is empty | Warn: "customer_context.txt is empty. Cannot classify." |

## Dependencies

New: `pyyaml` (`pip install pyyaml`)

Already in project: `transformers`, `torch`

Optional: `bitsandbytes`, `accelerate` (for 4-bit quantization to reduce memory)

## Usage

```bash
python classify_customer.py
```

## Updated Pipeline

```
Step 1: python data_extraction.py          → hourly JSONL
Step 2: python extract_media_ptt.py        → .ogg files
Step 3: python transcribe_ptt.py           → add Darija transcripts
Step 4: python build_customer_context.py   → customer_context.txt
Step 5: python classify_customer.py        → _tracking/{ts}_{TIER}.txt   ← NEW
Step 6: python play_ptt.py                 → interactive playback
```
