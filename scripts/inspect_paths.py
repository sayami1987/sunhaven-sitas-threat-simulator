"""Discover real bounded paths in the packaged environment for a chosen asset."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.graph_engine import build_graph
from src.model_loader import load_environment
from src.models import ModelError
from src.pathfinder import find_paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default="attacker_external")
    parser.add_argument("--target", default="asset_care_records")
    parser.add_argument("--max-depth", type=int, default=12)
    args = parser.parse_args()
    try:
        graph = build_graph(load_environment(ROOT / "config/environment.json"))
        result = find_paths(graph, args.source, args.target, max_depth=args.max_depth)
    except ModelError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(f"Source: {args.source}; target: {args.target}; depth limit: {args.max_depth}")
    print(f"Paths found: {len(result.paths)}; edges examined: {result.expansions}; depth-pruned branches: {result.depth_pruned}")
    for path in result.paths:
        print(f"{path.id} ({len(path.edge_ids)} edges)")
        print("  " + " -> ".join(path.node_ids))
        print("  Edges: " + ", ".join(path.edge_ids))
    print("Reachability is conditional on the synthetic edges and selected depth bound.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
