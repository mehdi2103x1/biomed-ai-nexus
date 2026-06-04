"""
utils.preprocessing
====================
Data loading and preprocessing for the Indian Liver Patient Dataset (ILPD).

The public surface is small and deliberate:

* :func:`load_raw_dataset`   -> tidy ``pandas.DataFrame`` (named columns, mapped target)
* :class:`LiverPreprocessor` -> fit/transform a single patient *or* a full frame
* :func:`build_feature_frame` -> turn a form ``dict`` into a model-ready row

The :class:`LiverPreprocessor` wraps a scikit-learn ``Pipeline``
(median imputation + standard scaling) so the *exact* same transformation is
applied at training time and at inference time. It is persisted with joblib.
"""
from __future__ import annotations

from pathlib import Path
from typing import Mapping

import numpy as np
import pandas as pd

from config import (
    CLASS_NAMES,
    FEATURE_ORDER,
    NUMERIC_FEATURES,
    RAW_COLUMNS,
    RAW_DATASET,
)
from utils.logger import get_logger

log = get_logger("preprocessing")

# Gender is encoded deterministically (not learnt) so a single patient row can
# be transformed without re-fitting an encoder.
GENDER_MAP: dict[str, int] = {"Male": 1, "Female": 0}


# --------------------------------------------------------------------------- #
# Loading
# --------------------------------------------------------------------------- #
def load_raw_dataset(path: Path | str = RAW_DATASET) -> pd.DataFrame:
    """Load the raw ILPD CSV and return a cleaned, named ``DataFrame``.

    Steps:
      * attach the canonical column names (the UCI file is header-less);
      * strip/normalise the ``Gender`` strings;
      * map the UCI target (1 = patient, 2 = non-patient) to a binary
        ``Target`` (1 = Liver Disease, 0 = No Liver Disease).

    Raises
    ------
    FileNotFoundError
        If the dataset cannot be found at ``path``.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"ILPD dataset not found at {path}. Run `python data/load_data.py` first."
        )

    df = pd.read_csv(path, header=None, names=RAW_COLUMNS)
    df["Gender"] = df["Gender"].astype(str).str.strip().str.capitalize()

    # UCI: 1 = liver patient (disease), 2 = non-liver patient (healthy).
    df["Target"] = df["Target"].map({1: 1, 2: 0}).astype("Int64")

    log.info("Loaded ILPD: %d rows, %d disease / %d healthy",
             len(df), int((df["Target"] == 1).sum()), int((df["Target"] == 0).sum()))
    return df


def encode_gender(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of ``df`` with ``Gender`` encoded to 0/1 (Female/Male)."""
    out = df.copy()
    out["Gender"] = (
        out["Gender"].astype(str).str.capitalize().map(GENDER_MAP).fillna(0).astype(int)
    )
    return out


def dataset_overview(df: pd.DataFrame) -> dict:
    """Compute light summary statistics used by the Home / Dashboard pages."""
    return {
        "n_rows": int(len(df)),
        "n_features": len(FEATURE_ORDER),
        "n_disease": int((df["Target"] == 1).sum()),
        "n_healthy": int((df["Target"] == 0).sum()),
        "disease_rate": float((df["Target"] == 1).mean()),
        "missing_values": int(df[RAW_COLUMNS[:-1]].isna().sum().sum()),
        "mean_age": float(df["Age"].mean()),
        "pct_male": float((df["Gender"].str.capitalize() == "Male").mean()),
    }


# --------------------------------------------------------------------------- #
# Preprocessor
# --------------------------------------------------------------------------- #
class LiverPreprocessor:
    """Fit/transform pipeline: gender encoding -> median impute -> standardise.

    The class keeps the feature order fixed (:data:`config.FEATURE_ORDER`) so
    the numpy matrix columns always line up with model expectations.
    """

    def __init__(self) -> None:
        from sklearn.impute import SimpleImputer
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import StandardScaler

        self.feature_order: list[str] = FEATURE_ORDER
        self._pipe = Pipeline(
            steps=[
                ("impute", SimpleImputer(strategy="median")),
                ("scale", StandardScaler()),
            ]
        )
        self.fitted: bool = False

    # -- internal helpers --------------------------------------------------- #
    def _to_matrix(self, df: pd.DataFrame) -> np.ndarray:
        """Encode gender and return columns in the canonical order as floats."""
        enc = encode_gender(df)
        return enc[self.feature_order].astype(float).to_numpy()

    # -- public API --------------------------------------------------------- #
    def fit(self, df: pd.DataFrame) -> "LiverPreprocessor":
        """Fit the imputer + scaler on a training ``DataFrame``."""
        self._pipe.fit(self._to_matrix(df))
        self.fitted = True
        log.info("LiverPreprocessor fitted on %d samples", len(df))
        return self

    def transform(self, data: pd.DataFrame | Mapping[str, float]) -> np.ndarray:
        """Transform a frame or a single patient dict into a scaled matrix."""
        if not self.fitted:
            raise RuntimeError("LiverPreprocessor must be fitted before transform().")
        if isinstance(data, Mapping):
            data = build_feature_frame(data)
        return self._pipe.transform(self._to_matrix(data))

    def fit_transform(self, df: pd.DataFrame) -> np.ndarray:
        return self.fit(df).transform(df)

    # -- persistence -------------------------------------------------------- #
    def save(self, path: Path | str) -> None:
        import joblib
        joblib.dump(self, Path(path))
        log.info("Preprocessor saved -> %s", path)

    @staticmethod
    def load(path: Path | str) -> "LiverPreprocessor":
        import joblib
        return joblib.load(Path(path))


# --------------------------------------------------------------------------- #
# Form helpers
# --------------------------------------------------------------------------- #
def build_feature_frame(form: Mapping[str, float | str]) -> pd.DataFrame:
    """Convert a Streamlit form ``dict`` into a one-row ``DataFrame``.

    Missing keys are filled with NaN so the imputer can handle them gracefully.
    """
    row = {col: form.get(col, np.nan) for col in ["Age", "Gender", *NUMERIC_FEATURES[1:]]}
    return pd.DataFrame([row])


def validate_form(form: Mapping[str, float | str]) -> list[str]:
    """Return a list of human-readable validation warnings (empty = all good).

    These are *soft* clinical sanity checks — values outside the plausible
    physiological range still run, but the user is warned.
    """
    warnings: list[str] = []
    checks = {
        "Age": (1, 100),
        "Total_Bilirubin": (0, 80),
        "Direct_Bilirubin": (0, 25),
        "Alkaline_Phosphotase": (50, 2200),
        "Alamine_Aminotransferase": (1, 2000),
        "Aspartate_Aminotransferase": (1, 5000),
        "Total_Proteins": (1, 12),
        "Albumin": (0.5, 7),
        "Albumin_and_Globulin_Ratio": (0.1, 3),
    }
    for key, (lo, hi) in checks.items():
        val = form.get(key)
        if val is None or (isinstance(val, float) and np.isnan(val)):
            warnings.append(f"{key.replace('_', ' ')} is missing.")
        elif not (lo <= float(val) <= hi):
            warnings.append(
                f"{key.replace('_', ' ')} = {val} is outside the typical range "
                f"[{lo}, {hi}]."
            )
    # Direct bilirubin can never exceed total bilirubin.
    tb, db = form.get("Total_Bilirubin"), form.get("Direct_Bilirubin")
    if tb is not None and db is not None and float(db) > float(tb):
        warnings.append("Direct Bilirubin should not exceed Total Bilirubin.")
    return warnings


def label_to_text(label: int) -> str:
    """Map the integer class to its display string."""
    return CLASS_NAMES.get(int(label), str(label))
