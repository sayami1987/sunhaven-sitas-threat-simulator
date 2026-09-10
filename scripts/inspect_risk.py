"""Score actual paths to a fictional asset and display their arithmetic."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.graph_engine import build_graph
from src.model_loader import load_environment, load_risk_model
from src.pathfinder import find_paths
from src.risk_engine import rank_paths


def main():
    graph = build_graph(load_environment(ROOT / "config/environment.json"))
    risk = load_risk_model(ROOT / "config/risk-model.json")
    paths = find_paths(graph, "attacker_external", "asset_care_records").paths
    for path, score in rank_paths(graph, paths, risk):
        values = [graph.edges[edge_id].likelihood for edge_id in path.edge_ids]
        print(f"{path.id}: min{values} = {score.likelihood}; impact={score.impact}; {score.likelihood} x {score.impact} = {score.risk_score} ({score.severity})")
    print("Scores are synthetic educational indicators, not exact probabilities.")


if __name__ == "__main__":
    main()
