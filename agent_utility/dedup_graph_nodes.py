# Description: Merges duplicate nodes in graphify-out/graph.json whose source_file points
# to the same canonical file via different import path representations (e.g., "App.tsx",
# "src/App.tsx", "frontend/src/App.tsx" all mapping to the same physical file).
# Also merges true extraction duplicates (same source_file + same label + same location).
# Re-points all edges from ghost nodes to the canonical node, then removes duplicates.
# Run: uv run python agent_utility/dedup_graph_nodes.py

import json
import os
import sys
from collections import defaultdict

GRAPH_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "graphify-out")
GRAPH_PATH = os.path.join(GRAPH_DIR, "graph.json")
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))


def resolve_real_path(path):
    full = os.path.normpath(os.path.join(PROJECT_ROOT, path))
    if os.path.exists(full):
        return os.path.relpath(full, PROJECT_ROOT).replace("\\", "/")
    return None


def pick_file_level_node(candidates, target_path):
    target_basename = os.path.basename(target_path).lower()
    for c in candidates:
        if c.get("label", "").lower() == target_basename or c.get("label", "") == c.get("source_file", ""):
            return c
    return candidates[0]


def phase2_suffix_match(ghost_nodes, canonical_paths, canonical_by_path):
    merge_map = {}
    stats = {"ambiguous": 0, "no_match": 0}
    for gn in ghost_nodes:
        gsf = gn.get("source_file", "")
        if not gsf:
            continue
        matching = [cpath for cpath in canonical_paths if cpath.endswith(gsf) or cpath == gsf]
        if len(matching) == 1:
            merge_map[gn["id"]] = pick_file_level_node(canonical_by_path[matching[0]], matching[0])["id"]
        elif len(matching) > 1:
            stats["ambiguous"] += 1
        else:
            stats["no_match"] += 1
    return merge_map, stats


def phase2_basename_match(ghost_nodes, canonical_by_path, already_matched_ghost_ids):
    merge_map = {}
    stats = {"ambiguous": 0, "no_match": 0}
    remaining = [gn for gn in ghost_nodes if gn["id"] not in already_matched_ghost_ids]

    canon_by_basename = defaultdict(list)
    for cpath, nlist in canonical_by_path.items():
        canon_by_basename[os.path.basename(cpath).lower()].append(cpath)

    for gn in remaining:
        gsf = gn.get("source_file", "")
        if not gsf:
            continue
        base = os.path.basename(gsf).lower()
        matching = canon_by_basename.get(base, [])
        if len(matching) == 1:
            merge_map[gn["id"]] = pick_file_level_node(canonical_by_path[matching[0]], matching[0])["id"]
        elif len(matching) > 1:
            stats["ambiguous"] += 1
        else:
            stats["no_match"] += 1
    return merge_map, stats


def phase2_prefix_match(ghost_nodes, canonical_paths, canonical_by_path, already_matched_ghost_ids):
    merge_map = {}
    stats = {"ambiguous": 0, "no_match": 0}
    remaining = [gn for gn in ghost_nodes if gn["id"] not in already_matched_ghost_ids]

    for gn in remaining:
        gsf = gn.get("source_file", "")
        if not gsf:
            continue
        matching = []
        for cpath in canonical_paths:
            parent = os.path.dirname(cpath)
            candidate = parent + "/" + gsf if parent else gsf
            candidate = candidate.replace("\\", "/")
            if resolve_real_path(candidate):
                matching.append(cpath)
        if len(matching) == 1:
            merge_map[gn["id"]] = pick_file_level_node(canonical_by_path[matching[0]], matching[0])["id"]
        elif len(matching) > 1:
            stats["ambiguous"] += 1
        else:
            stats["no_match"] += 1
    return merge_map, stats


def phase3_true_duplicates(canonical_by_path, node_map):
    merge_map = {}
    stats = {"groups_found": 0, "nodes_merged": 0}
    for cpath, nlist in canonical_by_path.items():
        # Group by (label, source_location)
        loc_groups = defaultdict(list)
        for n in nlist:
            key = (n.get("label", ""), n.get("source_location", ""))
            loc_groups[key].append(n)
        for key, group in loc_groups.items():
            if len(group) > 1:
                stats["groups_found"] += 1
                # Keep the first one, merge all others into it
                keep = group[0]
                for dup in group[1:]:
                    merge_map[dup["id"]] = keep["id"]
                    stats["nodes_merged"] += 1
    return merge_map, stats


def main():
    if not os.path.exists(GRAPH_PATH):
        print(f"ERROR: {GRAPH_PATH} not found. Run graphify first.")
        sys.exit(1)

    graph = json.load(open(GRAPH_PATH, "r", encoding="utf-8"))
    nodes = graph["nodes"]
    links = graph["links"]
    total_start = len(nodes)

    # Phase 1: classify nodes as canonical (source_file resolves to real file)
    # or ghost (source_file is a non-resolving import path).
    canonical_by_path = {}
    ghost_nodes = []
    node_map = {}

    for n in nodes:
        nid = n["id"]
        node_map[nid] = n
        sf = n.get("source_file", "")
        if sf:
            real = resolve_real_path(sf)
            if real:
                canonical_by_path.setdefault(real, []).append(n)
            else:
                ghost_nodes.append(n)

    print(f"Total nodes: {len(nodes)}")
    print(f"Canonical paths: {len(canonical_by_path)}")
    print(f"Ghost nodes (non-resolving): {len(ghost_nodes)}")

    canonical_paths = list(canonical_by_path.keys())

    # Phase 2a: match ghost nodes via suffix matching (existing).
    merge_map = {}
    m1, s1 = phase2_suffix_match(ghost_nodes, canonical_paths, canonical_by_path)
    merge_map.update(m1)
    print(f"\nPhase 2a (suffix match): {len(m1)} merged, {s1['ambiguous']} ambiguous, {s1['no_match']} no match")

    # Phase 2b: match remaining ghosts via basename uniqueness.
    m2, s2 = phase2_basename_match(ghost_nodes, canonical_by_path, set(merge_map.keys()))
    merge_map.update(m2)
    print(f"Phase 2b (basename match): {len(m2)} merged, {s2['ambiguous']} ambiguous, {s2['no_match']} no match")

    # Phase 2c: match remaining ghosts via parent-prefix.
    m3, s3 = phase2_prefix_match(ghost_nodes, canonical_paths, canonical_by_path, set(merge_map.keys()))
    merge_map.update(m3)
    print(f"Phase 2c (prefix match): {len(m3)} merged, {s3['ambiguous']} ambiguous, {s3['no_match']} no match")

    # Phase 3: true duplicate merge within same canonical file.
    m4, s4 = phase3_true_duplicates(canonical_by_path, node_map)
    merge_map.update(m4)
    print(f"Phase 3 (true duplicates): {s4['groups_found']} groups, {s4['nodes_merged']} merged")

    # Phase 4: identify orphan ghost nodes (could not be matched to any canonical).
    all_ghost_ids = {gn["id"] for gn in ghost_nodes}
    matched_ghost_ids = set(merge_map.keys())
    orphan_ids = all_ghost_ids - matched_ghost_ids
    orphan_count = len(orphan_ids)
    if orphan_count:
        print(f"\nPhase 4 (orphan deletion): {orphan_count} orphan ghosts to delete")
    del all_ghost_ids, matched_ghost_ids

    remove_ids = set(merge_map.keys()) | orphan_ids

    if not remove_ids:
        print("\nNo duplicates or orphans to remove. Graph is clean.")
        return

    # Phase 5: re-point links from matched ghost IDs to canonical IDs.
    relink_count = 0
    for link in links:
        for key in ("source", "target"):
            old_id = link.get(key, "")
            if old_id in merge_map:
                link[key] = merge_map[old_id]
                relink_count += 1
    if relink_count:
        print(f"Links re-pointed: {relink_count}")

    # Phase 6: remove links referencing removed IDs, then remove nodes.
    total_links_before = len(links)
    graph["links"] = [link for link in links if link.get("source", "") not in remove_ids and link.get("target", "") not in remove_ids]
    actual_link_removed = total_links_before - len(graph["links"])
    original_count = len(nodes)
    graph["nodes"] = [n for n in nodes if n["id"] not in remove_ids]

    # Phase 7: remove any remaining exact duplicate node entries.
    seen_ids = set()
    unique_nodes = []
    dedup_removed = 0
    for n in graph["nodes"]:
        if n["id"] in seen_ids:
            dedup_removed += 1
            continue
        seen_ids.add(n["id"])
        unique_nodes.append(n)
    graph["nodes"] = unique_nodes

    print(f"Ghost/duplicate nodes removed: {len(remove_ids)}")
    print(f"Edges removed (orphan references): {actual_link_removed}")
    print(f"Exact duplicate entries removed: {dedup_removed}")
    print(f"Final node count: {len(graph['nodes'])} (was {original_count}, start {total_start})")

    # Phase 8: write back.
    with open(GRAPH_PATH, "w", encoding="utf-8") as f:
        json.dump(graph, f, ensure_ascii=False, indent=2)
    print(f"\nWritten: {GRAPH_PATH}")


if __name__ == "__main__":
    main()
