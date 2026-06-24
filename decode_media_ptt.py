# Description: Decodes base64-encoded media (voice messages, images) from WhatsApp JSONL to local files.

import json
import logging
import os
import sys
import base64
from media_utils import find_next_seq, parse_data_uri, get_type_prefix
import shutil
import tempfile
import glob

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("extract_media")

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

MIME_EXT_MAP = {
    "audio/ogg": ".ogg",
    "image/jpeg": ".jpg",
    "image/png": ".png",
}


def process_jsonl(jsonl_path):
    dir_name = os.path.dirname(jsonl_path)
    base_name = os.path.splitext(os.path.basename(jsonl_path))[0]
    media_dir = os.path.join(dir_name, "media")

    with open(jsonl_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    seq = find_next_seq(media_dir, base_name, "ptt")
    updated_lines = []
    extracted_count = 0

    for line in lines:
        line = line.rstrip("\n").rstrip("\r")
        if not line:
            continue

        obj = json.loads(line)
        media_link = obj.get("media_link")

        if media_link and media_link.startswith("data:"):
            mime_type, payload = parse_data_uri(media_link)
            if mime_type in MIME_EXT_MAP:
                ext = MIME_EXT_MAP[mime_type]
                type_prefix = get_type_prefix(obj.get("type", ""))

                media_filename = f"{type_prefix}_{base_name}_{seq:03d}{ext}"
                media_path = os.path.join(media_dir, media_filename)

                if not os.path.exists(media_path):
                    if not payload:
                        logger.warning("Empty base64 payload for %s", media_filename)
                        updated_lines.append(json.dumps(obj, ensure_ascii=False))
                        continue
                    assert payload is not None
                    os.makedirs(media_dir, exist_ok=True)
                    try:
                        audio_data = base64.b64decode(payload)
                        with open(media_path, "wb") as af:
                            af.write(audio_data)
                        logger.info("Decoded -> %s", media_filename)
                    except Exception as e:
                        logger.error("Error decoding %s: %s", media_filename, e)
                        updated_lines.append(json.dumps(obj, ensure_ascii=False))
                        continue

                obj["media_link"] = f"media/{media_filename}"
                extracted_count += 1
                seq += 1

        updated_lines.append(json.dumps(obj, ensure_ascii=False))

    if extracted_count > 0:
        with open(jsonl_path + ".tmp", "w", encoding="utf-8") as f:
            for entry in updated_lines:
                f.write(entry + "\n")
        shutil.move(jsonl_path + ".tmp", jsonl_path)
        logger.info(
            "Updated %s (%d files extracted)",
            os.path.basename(jsonl_path),
            extracted_count,
        )
    else:
        logger.info("No new media to extract in %s", os.path.basename(jsonl_path))


def main():
    logger.info("Scanning for JSONL files with embedded media...")
    found = 0
    for root, dirs, files in os.walk(BASE_DIR):
        if "_tracking" in root:
            continue
        for fname in files:
            if fname.endswith(".jsonl") and not fname.startswith("extracted_info"):
                jsonl_path = os.path.join(root, fname)
                logger.info("Processing: %s", os.path.relpath(jsonl_path))
                process_jsonl(jsonl_path)
                found += 1

    if found == 0:
        logger.warning("No JSONL files found.")
    else:
        logger.info("Done. Scanned %d JSONL file(s).", found)


if __name__ == "__main__":
    main()
