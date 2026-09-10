"""Run the SITAS CLI from any working directory."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.sitas import main

if __name__ == "__main__":
    raise SystemExit(main())
