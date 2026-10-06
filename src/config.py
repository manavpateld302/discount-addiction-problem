from pathlib import Path

# Finds the main project folder automatically.
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Project folders
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw" / "olist"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
REPORTS_DIR = PROJECT_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
DOCS_DIR = PROJECT_ROOT / "docs"

# Makes synthetic-data rules reproducible later in the project.
RANDOM_SEED = 42