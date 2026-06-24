# Description: Shared helper functions for media/document decoding — find_next_seq, parse_data_uri, get_type_prefix.

import os
import re


def find_next_seq(media_dir, hour_key, type_prefix):
    max_seq = 0
    if os.path.exists(media_dir):
        pattern = rf"^{type_prefix}_{hour_key}_(\d+)\."
        for fname in os.listdir(media_dir):
            match = re.match(pattern, fname)
            if match:
                seq_num = int(match.group(1))
                if seq_num > max_seq:
                    max_seq = seq_num
    return max_seq + 1


def parse_data_uri(uri):
    if not uri.startswith("data:"):
        return None, None
    try:
        header, payload = uri.split("base64,", 1)
        mime_type = header.removeprefix("data:").removesuffix(";").split(";")[0]
        return mime_type, payload
    except ValueError:
        return None, None


def get_type_prefix(message_type):
    prefix_map = {
        "ptt": "ptt",
        "image": "img",
        "document": "doc",
    }
    return prefix_map.get(message_type, "media")
