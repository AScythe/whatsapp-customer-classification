# Description: Merges message bodies and transcripts from JSONL into a single LLM-ready context file.

import json
import logging
import os
import sys
import glob

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("build_context")

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


def load_tracker():
    if not os.path.exists(TRACKER_FILE):
        return set()
    with open(TRACKER_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return set(data.get("appended_timestamps", []))


def save_tracker(timestamps):
    os.makedirs(TRACKING_DIR, exist_ok=True)
    with open(TRACKER_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {"appended_timestamps": sorted(timestamps)},
            f,
            ensure_ascii=False,
            indent=2,
        )


def sanitize_ts(ts):
    return ts.replace(":", "-").replace(".000", "")


def context_file_for_ts(ts):
    return os.path.join(BASE_DIR, f"{sanitize_ts(ts)}_customer_context.txt")


def find_jsonl_files():
    pattern = os.path.join(BASE_DIR, "**", "*.jsonl")
    all_files = glob.glob(pattern, recursive=True)
    tracking_path = os.path.normpath(TRACKING_DIR)
    return [
        f
        for f in all_files
        if not os.path.normpath(os.path.dirname(f)).startswith(tracking_path)
    ]


def compose_line(body, transcript):
    if body and transcript:
        return f"{body} | {transcript}"
    elif body:
        return body
    elif transcript:
        return transcript
    return None


def main():
    jsonl_files = find_jsonl_files()

    if not jsonl_files:
        logger.warning("No JSONL files found.")
        return

    all_entries = []
    all_timestamps = set()

    for filepath in sorted(jsonl_files):
        with open(filepath, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    logger.warning(
                        "%s:%d - malformed JSON, skipping.",
                        os.path.relpath(filepath),
                        line_num,
                    )
                    continue

                ts = entry.get("timestamp")
                if not ts:
                    logger.warning(
                        "%s:%d - missing timestamp, skipping.",
                        os.path.relpath(filepath),
                        line_num,
                    )
                    continue

                all_timestamps.add(ts)
                body = entry.get("body") or ""
                transcript = entry.get("transcript") or ""
                output = compose_line(body, transcript)
                if output is None:
                    continue

                all_entries.append((ts, output))

    if not all_entries:
        logger.warning("No messages found in any JSONL files.")
        return

    latest_ts = max(all_timestamps)
    context_path = context_file_for_ts(latest_ts)

    if os.path.exists(context_path):
        logger.info("Context up-to-date at %s. Skipping build.", latest_ts)
        return

    all_entries.sort(key=lambda x: x[0])

    os.makedirs(BASE_DIR, exist_ok=True)
    with open(context_path, "w", encoding="utf-8") as f:
        for _, line_text in all_entries:
            f.write(line_text + "\n")

    save_tracker(all_timestamps)

    logger.info("Built %s (%d entries).", context_path, len(all_entries))
    logger.info("Tracker: %s", TRACKER_FILE)


if __name__ == "__main__":
    main()
