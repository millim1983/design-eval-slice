from __future__ import annotations
from pathlib import Path
import os

APP_DIR = Path(__file__).resolve().parents[1]     # .../backend/app
BACKEND_DIR = APP_DIR.parent                      # .../backend
ROOT_DIR = BACKEND_DIR.parent                     # .../design-eval-slice

DATA_DIR = Path(os.getenv("DATA_DIR", APP_DIR / "data"))
SCHEMAS_DIR = Path(os.getenv("SCHEMAS_DIR", APP_DIR / "schemas"))
SEEDS_DIR = Path(os.getenv("SEEDS_DIR", APP_DIR / "seeds"))
DB_PATH = Path(os.getenv("DB_PATH", DATA_DIR / "slice.db"))

GUIDELINE_FILE = Path(os.getenv("GUIDELINE_FILE", SEEDS_DIR / "guidelines" / "kda_2025_guideline.md"))
RUBRIC_FILE = Path(os.getenv("RUBRIC_FILE", SEEDS_DIR / "rubrics" / "kda_2025_v1.json"))

def ensure_dirs():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
