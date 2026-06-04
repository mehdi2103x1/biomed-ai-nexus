"""
config.py
=========
Central configuration for the HepatoScope platform.

Keeping every path, column name and tunable constant in a single module avoids
"magic strings" scattered across the code base and makes the project easy to
re-deploy on another machine (only this file needs to be checked).
"""
from __future__ import annotations

from pathlib import Path

# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #
ROOT_DIR: Path = Path(__file__).resolve().parent
DATA_DIR: Path = ROOT_DIR / "data"
MODELS_DIR: Path = ROOT_DIR / "models"
ASSETS_DIR: Path = ROOT_DIR / "assets"
LOG_DIR: Path = ROOT_DIR / "logs"

RAW_DATASET: Path = DATA_DIR / "liver_raw.csv"
DATASET_NAME: str = "Liver Patient Dataset (30K)"
HISTORY_CSV: Path = DATA_DIR / "historical_predictions.csv"
METRICS_JSON: Path = MODELS_DIR / "metrics.json"
PREPROCESSOR_PATH: Path = MODELS_DIR / "preprocessor.pkl"

# Make sure the writable folders exist on import (cheap, idempotent).
for _d in (DATA_DIR, MODELS_DIR, ASSETS_DIR, LOG_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------------- #
# Dataset description (Indian Liver Patient Dataset – ILPD)
# --------------------------------------------------------------------------- #
# The raw UCI file ships *without* a header row. These are the canonical names.
RAW_COLUMNS: list[str] = [
    "Age",
    "Gender",
    "Total_Bilirubin",
    "Direct_Bilirubin",
    "Alkaline_Phosphotase",
    "Alamine_Aminotransferase",
    "Aspartate_Aminotransferase",
    "Total_Proteins",
    "Albumin",
    "Albumin_and_Globulin_Ratio",
    "Target",          # 1 = liver patient, 2 = non-liver patient (UCI encoding)
]

# Features fed to the models (Gender is encoded to 0/1 during preprocessing).
NUMERIC_FEATURES: list[str] = [
    "Age",
    "Total_Bilirubin",
    "Direct_Bilirubin",
    "Alkaline_Phosphotase",
    "Alamine_Aminotransferase",
    "Aspartate_Aminotransferase",
    "Total_Proteins",
    "Albumin",
    "Albumin_and_Globulin_Ratio",
]
CATEGORICAL_FEATURES: list[str] = ["Gender"]
FEATURE_ORDER: list[str] = ["Age", "Gender"] + NUMERIC_FEATURES[1:]

# Human-friendly labels + units for the medical form / report.
FEATURE_META: dict[str, dict] = {
    "Age":                          {"label": "Age",                          "unit": "years",   "min": 1.0,   "max": 100.0, "default": 45.0,  "step": 1.0},
    "Gender":                       {"label": "Gender",                       "unit": "",        "options": ["Male", "Female"]},
    "Total_Bilirubin":              {"label": "Total Bilirubin",              "unit": "mg/dL",   "min": 0.0,   "max": 80.0,  "default": 1.0,   "step": 0.1},
    "Direct_Bilirubin":             {"label": "Direct Bilirubin",             "unit": "mg/dL",   "min": 0.0,   "max": 25.0,  "default": 0.3,   "step": 0.1},
    "Alkaline_Phosphotase":         {"label": "Alkaline Phosphotase",         "unit": "IU/L",    "min": 50.0,  "max": 2200.0,"default": 200.0, "step": 1.0},
    "Alamine_Aminotransferase":     {"label": "Alamine Aminotransferase (ALT/SGPT)", "unit": "IU/L", "min": 1.0, "max": 2000.0, "default": 35.0, "step": 1.0},
    "Aspartate_Aminotransferase":   {"label": "Aspartate Aminotransferase (AST/SGOT)", "unit": "IU/L", "min": 1.0, "max": 5000.0, "default": 40.0, "step": 1.0},
    "Total_Proteins":               {"label": "Total Proteins",               "unit": "g/dL",    "min": 1.0,   "max": 12.0,  "default": 6.8,   "step": 0.1},
    "Albumin":                      {"label": "Albumin",                      "unit": "g/dL",    "min": 0.5,   "max": 7.0,   "default": 3.2,   "step": 0.1},
    "Albumin_and_Globulin_Ratio":   {"label": "Albumin / Globulin Ratio",     "unit": "",        "min": 0.1,   "max": 3.0,   "default": 1.0,   "step": 0.01},
}

# --------------------------------------------------------------------------- #
# Target / class semantics
# --------------------------------------------------------------------------- #
# We model a *binary* problem. After preprocessing: 1 = Liver Disease, 0 = No Disease.
CLASS_NAMES: dict[int, str] = {0: "No Liver Disease", 1: "Liver Disease"}
POSITIVE_LABEL: int = 1

# --------------------------------------------------------------------------- #
# Modelling
# --------------------------------------------------------------------------- #
RANDOM_STATE: int = 42
TEST_SIZE: float = 0.2
CV_FOLDS: int = 5

# Registered tabular models (key -> nice display name). The training script and
# the app both iterate over this dict, so adding a model is a one-line change.
MODEL_REGISTRY: dict[str, str] = {
    "decision_tree":       "Decision Tree",
    "random_forest":       "Random Forest",
    "logistic_regression": "Logistic Regression",
    "svm":                 "Support Vector Machine",
    "xgboost":             "XGBoost",
}

# --------------------------------------------------------------------------- #
# UI / theming
# --------------------------------------------------------------------------- #
APP_TITLE: str = "HepatoScope"
APP_SUBTITLE: str = "Liver Disease Intelligence Platform"
APP_ICON: str = "🩺"
AUTHOR_BYLINE: str = "by El Mehdi Mansouri"
PRIMARY_COLOR: str = "#16b8a6"     # clinical teal
ACCENT_COLOR: str = "#0e9384"      # deep teal
DANGER_COLOR: str = "#f06a82"      # clinical red (disease / positive)
OK_COLOR: str = "#2dbb7f"          # healthy / negative
AUTHOR_NAME: str = "El Mehdi Mansouri"
AUTHOR_PROGRAM: str = "Ingénieur Génie Biomédical — UM6SS"
SCHOOL_NAME: str = "École Supérieure Mohammed VI d'Ingénieurs en Sciences de la Santé"
UNIVERSITY_NAME: str = "Université Mohammed VI des Sciences et de la Santé (UM6SS)"
SCHOOL_CITY: str = "Rabat, Maroc"
