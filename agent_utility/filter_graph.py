# Description: Filters graphify-out/graph.json into type-specific sub-graphs with boundary stubs.
# Preserves all top-level metadata keys and adds minimal stub nodes for cross-type edges.

import argparse
import json
import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

GRAPH_PATH = "graphify-out/graph.json"

OUTPUT_TYPES = {
    "code": {"code", "rationale"},
    "document": {"document"},
}

STUB_KEYS = {"id", "file_type", "label"}


def make_stub(node):
    return {k: v for k, v in node.items() if k in STUB_KEYS}


def filter_graph(graph, target_full_types):
    node_map = {n["id"]: n for n in graph["nodes"]}
    links = graph["links"]

    full_ids = {n["id"] for n in graph["nodes"] if n.get("file_type") in target_full_types}

    out_links = []
    stub_ids = set()
    for link in links:
        s_in = link["source"] in full_ids
        t_in = link["target"] in full_ids
        if not s_in and not t_in:
            continue
        if not s_in:
            stub_ids.add(link["source"])
        if not t_in:
            stub_ids.add(link["target"])
        out_links.append(link)

    full_nodes = [node_map[nid] for nid in sorted(full_ids)]
    stub_nodes = [make_stub(node_map[sid]) for sid in sorted(stub_ids)]

    out = {k: v for k, v in graph.items() if k not in ("nodes", "links")}
    out["nodes"] = full_nodes + stub_nodes
    out["links"] = out_links

    return out, len(full_nodes), len(stub_nodes), len(out_links)


def main():
    parser = argparse.ArgumentParser(
        description="Filter graph.json into type-specific sub-graphs with boundary stubs."
    )
    parser.add_argument(
        "names", nargs="*", choices=list(OUTPUT_TYPES),
        help="Output names to generate (e.g., code, document)"
    )
    parser.add_argument(
        "--all", action="store_true",
        help="Generate all sub-graphs"
    )
    parser.add_argument(
        "--out-dir", default="graphify-out",
        help="Output directory (default: graphify-out)"
    )
    args = parser.parse_args()

    if args.all:
        names = list(OUTPUT_TYPES)
    elif args.names:
        names = args.names
    else:
        parser.error("Specify at least one output name or --all")

    graph = json.load(open(GRAPH_PATH, "r", encoding="utf-8"))
    logger.info("Read %d nodes, %d links from %s", len(graph["nodes"]), len(graph["links"]), GRAPH_PATH)

    for name in names:
        target_types = OUTPUT_TYPES[name]
        sub_graph, n_full, n_stubs, n_edges = filter_graph(graph, target_types)
        out_path = os.path.join(args.out_dir, f"graph-{name}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(sub_graph, f, ensure_ascii=False, indent=2)
        type_label = ",".join(sorted(target_types))
        logger.info(
            "Wrote %s: %d nodes (%d full, %d stubs), %d edges (types: %s)",
            out_path, n_full + n_stubs, n_full, n_stubs, n_edges, type_label
        )


if __name__ == "__main__":
    main()
