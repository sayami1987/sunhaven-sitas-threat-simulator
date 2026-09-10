"""Run the full pytest suite using the current Python interpreter."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    raise SystemExit(subprocess.call([sys.executable, "-m", "pytest", *sys.argv[1:]], cwd=ROOT))
