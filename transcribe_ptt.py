# Description: Transcribes Darija voice messages (.ogg) using ychafiqui/whisper-medium-darija.

import json
import logging
import os
import sys
import torch
import shutil
import time
import glob
from transformers import pipeline, logging as trf_logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("transcribe")
trf_logging.set_verbosity_error()

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


def get_device():
    if torch.cuda.is_available():
        logger.info("Using GPU: %s", torch.cuda.get_device_name(0))
        return 0
    else:
        logger.warning("No GPU detected. Using CPU (slower).")
        return -1


def count_pending(base_dir):
    """Count PTT entries needing transcription, without loading the model."""
    pending = 0
    for root, dirs, files in os.walk(base_dir):
        if "_tracking" in root:
            continue
        for fname in files:
            if not fname.endswith(".jsonl") or fname.startswith("extracted_info"):
                continue
            jsonl_path = os.path.join(root, fname)
            with open(jsonl_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if obj.get("type") != "ptt":
                        continue
                    media_link = obj.get("media_link", "")
                    if not media_link:
                        continue
                    if media_link.startswith("data:"):
                        continue
                    if "transcript" in obj:
                        continue
                    media_path = os.path.join(root, media_link)
                    if os.path.exists(media_path):
                        pending += 1
    return pending


def load_pipeline(device):
    logger.info("Loading Whisper-darija model (first run downloads ~1.5 GB)...")
    t0 = time.time()
    pipe = pipeline(
        "automatic-speech-recognition",
        model="ychafiqui/whisper-medium-darija",
        device=device,
    )
    logger.info("Model loaded in %.1fs", time.time() - t0)
    return pipe


def process_jsonl(jsonl_path, pipe):
    dir_name = os.path.dirname(jsonl_path)

    with open(jsonl_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    updated_lines = []
    updated = False

    for line in lines:
        line = line.rstrip("\n").rstrip("\r")
        if not line:
            continue

        obj = json.loads(line)

        if obj.get("type") == "ptt":
            media_link = obj.get("media_link", "")
            if (
                media_link
                and not media_link.startswith("data:")
                and "transcript" not in obj
            ):
                media_path = os.path.join(dir_name, media_link)
                if os.path.exists(media_path):
                    logger.info("Transcribing: %s", os.path.basename(media_path))
                    try:
                        t0 = time.time()
                        result = pipe(media_path)
                        obj["transcript"] = result["text"]
                        updated = True
                        elapsed = time.time() - t0
                        snippet = result["text"][:60]
                        logger.info('  -> "%s" (%.1fs)', snippet, elapsed)
                    except Exception as e:
                        logger.error("Error transcribing %s: %s", media_path, e)

        updated_lines.append(json.dumps(obj, ensure_ascii=False))

    if updated:
        temp_path = jsonl_path + ".tmp"
        with open(temp_path, "w", encoding="utf-8") as f:
            for entry in updated_lines:
                f.write(entry + "\n")
        shutil.move(temp_path, jsonl_path)
        logger.info("Updated %s", os.path.basename(jsonl_path))
    else:
        logger.info("No new entries to transcribe in %s", os.path.basename(jsonl_path))


def main():
    logger.info("Scanning for JSONL files with PTT voice messages...")
    t0 = time.time()

    pending = count_pending(BASE_DIR)
    if pending == 0:
        logger.info("Nothing to transcribe. All PTT entries already transcribed.")
        return

    logger.info("Found %d message(s) pending transcription.", pending)
    device = get_device()
    pipe = load_pipeline(device)

    transcribed = 0
    for root, dirs, files in os.walk(BASE_DIR):
        if "_tracking" in root:
            continue
        for fname in files:
            if fname.endswith(".jsonl") and not fname.startswith("extracted_info"):
                jsonl_path = os.path.join(root, fname)
                logger.info("Processing: %s", os.path.relpath(jsonl_path))
                process_jsonl(jsonl_path, pipe)
                transcribed += 1

    if transcribed == 0:
        logger.warning("No JSONL files found.")
    else:
        logger.info("Done. Transcribed %d/%d pending in %.1fs.", min(pending, transcribed), pending, time.time() - t0)


if __name__ == "__main__":
    main()
