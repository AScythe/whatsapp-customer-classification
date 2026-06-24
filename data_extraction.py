# Description: Extracts WhatsApp JSON export into hourly JSONL files, with deduplication via timestamp tracking.

import json
import logging
import os
import sys
from datetime import datetime
from collections import defaultdict
import glob

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("data_extraction")

source_files = sorted(glob.glob("whatsapp_raw_messages/*.json"))
if not source_files:
    print("No source JSON files found in whatsapp_raw_messages/")
    sys.exit(1)

print("\nAvailable source files:")
phones = {}
for i, path in enumerate(source_files, 1):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    phone = None
    for msg in data.get("messages", []):
        phone = msg.get("sender", {}).get("phone")
        if phone:
            phone = phone.strip().lstrip("+")
            break
    phones[i] = phone
    print(f"  [{i}]  {os.path.basename(path)}  ({phone or 'unknown'})")
print("  [0]  Exit")

while True:
    try:
        choice = int(input("\nSelect customer: "))
        if choice == 0:
            sys.exit()
        selected = source_files[choice - 1]
        break
    except (ValueError, IndexError):
        print("Invalid choice.")

input_file = selected
phone = phones[choice]
base_output_dir = f"{phone}_chat_archives" if phone else "chat_archives"


def load_extracted_timestamps(tracker_file):
    if not os.path.exists(tracker_file):
        return None
    with open(tracker_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return set(data.get("extracted_timestamps", []))


def save_extracted_timestamps(tracker_file, timestamps):
    os.makedirs(os.path.dirname(tracker_file), exist_ok=True)
    with open(tracker_file, "w", encoding="utf-8") as f:
        json.dump(
            {"extracted_timestamps": sorted(timestamps)},
            f,
            ensure_ascii=False,
            indent=2,
        )


def seed_from_existing_jsonl(base_dir):
    timestamps = set()
    for root, dirs, files in os.walk(base_dir):
        if "_tracking" in root:
            continue
        for fname in files:
            if not fname.endswith(".jsonl"):
                continue
            jsonl_path = os.path.join(root, fname)
            with open(jsonl_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        ts = obj.get("timestamp")
                        if ts:
                            timestamps.add(ts)
                    except json.JSONDecodeError:
                        continue
    logger.info("Seeded %d existing timestamps from JSONL files.", len(timestamps))
    return timestamps


def main():
    logger.info("Loading raw messages from %s ...", input_file)
    logger.info("Output folder: %s", base_output_dir)

    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    tracking_dir = os.path.join(base_output_dir, "_tracking")
    tracker_file = os.path.join(tracking_dir, "extracted_timestamps.json")

    extracted_ts = load_extracted_timestamps(tracker_file)
    if extracted_ts is None:
        extracted_ts = seed_from_existing_jsonl(base_output_dir)
        save_extracted_timestamps(tracker_file, extracted_ts)

    new_groups = defaultdict(list)
    new_timestamps = set()

    for message in data.get("messages", []):
        ts = message.get("timestamp")
        if not ts:
            continue
        if ts in extracted_ts:
            continue

        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        hour_key = dt.strftime("%Y-%m-%d-%H")

        extracted_data = {
            "timestamp": ts,
            "name": message.get("sender", {}).get("name"),
            "phone_number": message.get("sender", {}).get("phone"),
            "body": message.get("body"),
            "type": message.get("type"),
            "media_link": message.get("media_link"),
        }

        new_groups[hour_key].append(extracted_data)
        new_timestamps.add(ts)

    if not new_timestamps:
        logger.info("Nothing new to extract.")
        return

    for hour_key in sorted(new_groups):
        messages = new_groups[hour_key]
        year_month = hour_key[:7]
        day = hour_key[:10]
        day_folder = os.path.join(base_output_dir, year_month, day)
        os.makedirs(day_folder, exist_ok=True)

        hourly_file = os.path.join(day_folder, f"{hour_key}.jsonl")
        with open(hourly_file, "a", encoding="utf-8") as f:
            for msg in messages:
                f.write(json.dumps(msg, ensure_ascii=False) + "\n")

        logger.info("Appended %d message(s) to %s", len(messages), os.path.basename(hourly_file))

    extracted_ts.update(new_timestamps)
    save_extracted_timestamps(tracker_file, extracted_ts)

    logger.info("Done. Extracted %d new message(s).", len(new_timestamps))


if __name__ == "__main__":
    main()
