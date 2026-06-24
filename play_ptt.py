# Description: Interactive CLI player for decoded WhatsApp voice messages via ffplay.

import os
import json
import re
import subprocess
import shutil
import sys
import logging
from collections import defaultdict
import glob

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("play")

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


def check_ffplay():
    if not shutil.which("ffplay"):
        logger.error("ffplay not found. Make sure FFmpeg is installed and in your PATH.")
        logger.error("Download: https://ffmpeg.org/download.html")
        sys.exit(1)


def find_ogg_files():
    day_ogg_map = defaultdict(list)
    for root, dirs, files in os.walk(BASE_DIR):
        if os.path.basename(root) == "media":
            day_dir = os.path.dirname(root)
            day_name = os.path.basename(day_dir)
            for f in files:
                if f.endswith(".ogg"):
                    day_ogg_map[day_name].append(os.path.join(root, f))
    return dict(sorted(day_ogg_map.items()))


def parse_timestamp_from_filename(ogg_filename):
    match = re.match(r"\w+_(\d{4}-\d{2}-\d{2}-\d{2})_(\d+)\.\w+$", ogg_filename)
    if match:
        return match.group(1), int(match.group(2))
    return None, None


def find_matching_entry(jsonl_path, filename):
    media_ref = f"media/{filename}"
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if obj.get("media_link") == media_ref:
                return obj
    return None


def collect_entries_for_day(ogg_list):
    entries = []
    for ogg_path in sorted(ogg_list):
        filename = os.path.basename(ogg_path)
        hour_key, seq = parse_timestamp_from_filename(filename)
        if not hour_key:
            continue
        media_dir = os.path.dirname(ogg_path)
        day_dir = os.path.dirname(media_dir)
        jsonl_path = os.path.join(day_dir, f"{hour_key}.jsonl")
        if not os.path.exists(jsonl_path):
            continue
        entry = find_matching_entry(jsonl_path, filename)
        if entry:
            entries.append(
                {
                    "ogg_path": ogg_path,
                    "timestamp": entry.get("timestamp", ""),
                    "name": entry.get("name", "Unknown"),
                    "phone": entry.get("phone_number", ""),
                    "body": entry.get("body", ""),
                    "media_link": entry.get("media_link", ""),
                    "transcript": entry.get("transcript", ""),
                }
            )
    entries.sort(key=lambda e: e["timestamp"])
    return entries


def print_context(entry, current=None, total=None):
    sep = "=" * 46
    print()
    print(sep)
    label = (
        f"  Voice Message  ({current}/{total})" if current and total else "  Voice Message"
    )
    print(label)
    print(f"  From:    {entry['name']}  ({entry['phone']})")
    print(f"  Time:    {entry['timestamp']}")
    print(f"  " + "-" * 42)
    body = entry.get("body", "")
    if body:
        print(f'  "{body}"')
    else:
        print(f"  (no text)")
    transcript = entry.get("transcript", "")
    if transcript:
        print(f"  Transcript: {transcript}")
    print(f"  " + "-" * 42)
    print(f"  Playing {entry.get('media_link', '')}")
    print(sep)


def play_audio(path):
    full_path = os.path.abspath(path)
    try:
        subprocess.run(
            ["ffplay", "-nodisp", "-autoexit", "-loglevel", "warning", "-volume", "100", full_path],
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as e:
        err = (e.stderr or b"").decode("utf-8", errors="replace")[:200]
        logger.warning("Playback failed (exit code %d).", e.returncode)
        if err.strip():
            logger.warning("ffplay: %s", err.strip())


def input_int(prompt, min_val, max_val):
    while True:
        try:
            val = input(prompt).strip()
            if not val:
                continue
            num = int(val)
            if min_val <= num <= max_val:
                return num
            print(f"  Please enter a number between {min_val} and {max_val}.")
        except ValueError:
            print("  Invalid input.")
        except EOFError:
            print()
            return 0
        except KeyboardInterrupt:
            print()
            return -1


def show_day_menu(day_ogg_map):
    days = list(day_ogg_map.keys())
    while True:
        print()
        print("=" * 46)
        print("         WhatsApp Voice Messages")
        print("=" * 46)
        print()
        print("Available days:")
        print()
        for i, day in enumerate(days, 1):
            count = len(day_ogg_map[day])
            msg = "message" if count == 1 else "messages"
            print(f"  [{i}]  {day}  ({count} {msg})")
        print()
        print(f"  [0]  Exit")
        print()
        choice = input_int(f"Select a day (0-{len(days)}): ", 0, len(days))
        if choice == -1 or choice == 0:
            print("Goodbye.")
            return
        show_message_menu(days[choice - 1], day_ogg_map[days[choice - 1]])


def show_message_menu(day_name, ogg_list):
    entries = collect_entries_for_day(ogg_list)
    if not entries:
        logger.warning("No playable voice messages found for %s.", day_name)
        return
    while True:
        print()
        print("=" * 46)
        print(f"  {day_name} - Select a message")
        print("=" * 46)
        print()
        for i, entry in enumerate(entries, 1):
            ts = entry["timestamp"]
            time_part = ts[11:19] if len(ts) >= 19 else ts
            body = entry.get("body", "")
            snippet = f'"{body}"' if body else "(no text)"
            print(f"  [{i}]  {time_part}  - {snippet}")
        print()
        print(f"  [0]  Back")
        print()
        choice = input_int(
            f"Select a message to play (0-{len(entries)}): ", 0, len(entries)
        )
        if choice == -1 or choice == 0:
            return
        entry = entries[choice - 1]
        print_context(entry, current=choice, total=len(entries))
        play_audio(entry["ogg_path"])


def main():
    check_ffplay()
    day_ogg_map = find_ogg_files()
    if not day_ogg_map:
        logger.error("No voice messages found. Run 'python decode_media_ptt.py' first.")
        sys.exit(1)
    show_day_menu(day_ogg_map)


if __name__ == "__main__":
    main()
