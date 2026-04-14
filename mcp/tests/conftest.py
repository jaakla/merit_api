import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
SDK_SRC = ROOT.parent / "merit_api" / "src"

for path in (SRC, SDK_SRC):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
