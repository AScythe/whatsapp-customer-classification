# Description: Classifies customer lead tier (HOT/EXISTING/COLD) using a local Qwen3.5 LLM.

import json
import logging
import os
import re
import sys
import time
import glob

import torch
import yaml
from transformers import AutoProcessor, AutoModelForMultimodalLM, logging as trf_logging

folders = sorted(glob.glob("*_chat_archives"))
if not folders:
    print("No customer folders found.")
    sys.exit(1)
if len(folders) == 1:
    BASE_DIR = folders[0]
    print(f"Using: {BASE_DIR}")
else:
    print("\nAvailable customer folders:")
    for i, f in enumerate(folders, 1):
        print(f"  [{i}]  {f}")
    print("  [0]  Exit")
    while True:
        try:
            choice = int(input("\nSelect customer: "))
            if choice == 0:
                sys.exit()
            BASE_DIR = folders[choice - 1]
            break
        except (ValueError, IndexError):
            print("Invalid choice.")
TRACKING_DIR = os.path.join(BASE_DIR, "_tracking")
TRACKER_FILE = os.path.join(TRACKING_DIR, "appended_timestamps.json")
PROMPT_FILE = "prompts/classify_customer.yaml"

# Options: "qwen35_2b", "qwen35_4b"
MODEL = "qwen35_2b"

MODEL_MAP = {
    "qwen35_2b": "Qwen/Qwen3.5-2B",
    "qwen35_4b": "Qwen/Qwen3.5-4B",
}

MODEL_NAME = MODEL_MAP[MODEL]

SAMPLING_PARAMS = {
    "max_new_tokens": 256,
    "temperature": 0.2,
    "top_p": 0.9,
    "do_sample": True,
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("classify")

trf_logging.set_verbosity_error()


def load_tracker_ts():
    if not os.path.exists(TRACKER_FILE):
        logger.error("%s not found. Run build_customer_context.py first.", TRACKER_FILE)
        sys.exit(1)

    with open(TRACKER_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    timestamps = data.get("appended_timestamps", [])
    if not timestamps:
        logger.error("No timestamps in tracker. Run build_customer_context.py first.")
        sys.exit(1)

    latest = max(timestamps)
    logger.info("Found %d timestamps, latest: %s", len(timestamps), latest)
    return latest, len(timestamps)


def load_prompt():
    if not os.path.exists(PROMPT_FILE):
        logger.error("Prompt file not found: %s", PROMPT_FILE)
        sys.exit(1)

    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    template = data.get("system_prompt")
    if not template:
        logger.error("'system_prompt' key missing in %s", PROMPT_FILE)
        sys.exit(1)

    logger.info("Prompt loaded (%d chars)", len(template))
    return template


def load_context(context_file):
    if not os.path.exists(context_file):
        logger.error("%s not found. Run build_customer_context.py first.", context_file)
        sys.exit(1)

    with open(context_file, "r", encoding="utf-8") as f:
        content = f.read().strip()

    if not content:
        logger.error("%s is empty. Cannot classify.", context_file)
        sys.exit(1)

    line_count = content.count("\n") + 1
    logger.info("Context loaded (%d lines, %d chars)", line_count, len(content))
    return content, line_count


def sanitize_ts(ts):
    return ts.replace(":", "-").replace(".000", "")


def already_classified(latest_ts):
    sanitized = sanitize_ts(latest_ts)
    pattern = os.path.join(BASE_DIR, f"{sanitized}_*.txt")
    matches = [f for f in glob.glob(pattern) if not f.endswith("_customer_context.txt")]
    return bool(matches)


def strip_thinking(text):
    return re.sub(r"<think>.*?</think>\n*\s*", "", text, flags=re.DOTALL).strip()


def extract_json(text):
    text = strip_thinking(text)
    brace_start = text.find("{")
    brace_end = text.rfind("}")
    if brace_start == -1 or brace_end == -1:
        return None, text

    candidate = text[brace_start : brace_end + 1]
    try:
        obj = json.loads(candidate)
        if "tier" in obj and "reason" in obj:
            return obj, text
    except json.JSONDecodeError:
        pass
    return None, text


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


def load_model(dtype):
    t0 = time.time()
    logger.info("Loading %s ...", MODEL_NAME)
    processor = AutoProcessor.from_pretrained(MODEL_NAME)

    model_kwargs = {
        "dtype": dtype,
        "device_map": "auto",
    }
    if not torch.cuda.is_available():
        if MODEL == "qwen35_2b":
            logger.info("CPU mode: 2B model in float16 (~5 GB). Slow but should fit.")
        else:
            logger.warning("CPU mode: 4B model needs ~20 GB RAM — likely to fail.")
            logger.warning("Run on production GPU or switch MODEL to qwen35_2b.")

    try:
        model = AutoModelForMultimodalLM.from_pretrained(MODEL_NAME, **model_kwargs)
    except RuntimeError as e:
        logger.error("Failed to load model: %s", e)
        logger.error("This machine likely doesn't have enough RAM.")
        logger.error("Run this script on the production machine with GPU.")
        sys.exit(1)

    elapsed = time.time() - t0
    logger.info("Model loaded in %.1fs", elapsed)
    return processor, model


def run_inference(processor, model, system_prompt, context, retry=False):
    prompt_text = system_prompt.replace("{customer_context}", context)

    if retry:
        prompt_text += (
            "\n\nYou MUST return ONLY valid JSON. No explanations. "
            'Nothing else. Just: {"tier": "...", "reason": "..."}'
        )

    messages = [
        {"role": "system", "content": prompt_text},
        {"role": "user", "content": "Classify the transcript above."},
    ]

    t0 = time.time()
    token_count_before = 0

    logger.info("Tokenizing input ...")
    inputs = processor.apply_chat_template(
        messages,
        add_generation_prompt=True,
        tokenize=True,
        return_dict=True,
        return_tensors="pt",
        enable_thinking=False,
    ).to(model.device)

    input_len = inputs["input_ids"].shape[1]
    logger.info("Input tokenized: %d tokens", input_len)
    logger.info("Starting generation at %s ...", time.strftime("%H:%M:%S"))

    with torch.no_grad():
        outputs = model.generate(**inputs, **SAMPLING_PARAMS)

    elapsed = time.time() - t0
    total_tokens = outputs.shape[1] - input_len
    tokens_per_sec = total_tokens / elapsed if elapsed > 0 else 0

    logger.info("Generation done at %s", time.strftime("%H:%M:%S"))
    logger.info("Generated %d tokens in %.1fs (%.2f tok/s)", total_tokens, elapsed, tokens_per_sec)

    response = processor.decode(
        outputs[0][input_len:], skip_special_tokens=True
    ).strip()

    logger.info("Raw response (%d chars): %s", len(response), response[:120])
    return response


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


def main():
    overall_t0 = time.time()
    logger.info("=" * 55)
    logger.info("Customer Lead Classification — Start")
    logger.info("Model: %s (%s)", MODEL_NAME, MODEL)
    logger.info("=" * 55)

    logger.info("")
    logger.info("--- Step 1/4: Loading tracker and context ---")
    latest_ts, total_msgs = load_tracker_ts()

    if already_classified(latest_ts):
        logger.info("Already classified up to %s. Skipping classification.", latest_ts)
        return

    prompt_template = load_prompt()

    sanitized = sanitize_ts(latest_ts)
    context_path = os.path.join(BASE_DIR, f"{sanitized}_customer_context.txt")
    context, line_count = load_context(context_path)

    logger.info("")
    logger.info("--- Step 2/4: Loading model ---")
    dtype = get_device()
    processor, model = load_model(dtype)

    logger.info("")
    logger.info("--- Step 3/4: Running inference ---")
    response = run_inference(processor, model, prompt_template, context)

    result, raw_output = extract_json(response)
    if result is None:
        logger.warning("First attempt: malformed JSON. Retrying with stricter prompt ...")
        response = run_inference(processor, model, prompt_template, context, retry=True)
        result, raw_output = extract_json(response)

    if result is None:
        logger.error("Could not parse JSON from model output.")
        logger.error("Raw output:\n%s", raw_output)
        sys.exit(1)

    tier = result["tier"]
    reason = result["reason"]

    logger.info("")
    logger.info("--- Step 4/4: Saving result ---")
    filepath = save_result(latest_ts, tier, reason, line_count)

    overall_elapsed = time.time() - overall_t0
    logger.info("")
    logger.info("=" * 55)
    logger.info("  Classification: %s", tier)
    logger.info("  Reason: %s", reason)
    logger.info("  Saved to: %s", filepath)
    logger.info("  Total time: %.1fs", overall_elapsed)
    logger.info("=" * 55)


if __name__ == "__main__":
    main()
