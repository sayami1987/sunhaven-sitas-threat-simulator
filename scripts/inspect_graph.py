"""Print the actual synthetic graph structure and optionally export its edges."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.graph_engine import build_graph
from src.model_loader import load_environment
from src.models import ModelError


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--environment", type=Path, default=ROOT / "config/environment.json")
    args = parser.parse_args()
    try:
        env = load_environment(args.environment)
        graph = build_graph(env)
    except ModelError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"environment": env.id, "summary": graph.summary()}, indent=2))
    for edge in graph.edges.values():
        print(f"{edge.id}: {edge.source} -> {edge.target} [{edge.relationship}; likelihood={edge.likelihood}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
