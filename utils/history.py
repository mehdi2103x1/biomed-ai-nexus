"""
utils.history
=============
Persistent prediction history stored in ``data/historical_predictions.csv``.

Each tabular prediction appends one row; the Dashboard page reads the file back
to compute KPIs and charts. Concurrency is not a concern for a single-user
Streamlit app, so a simple append-on-write strategy is used.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Mapping

import pandas as pd

from config import HISTORY_CSV
from utils.logger import get_logger

log = get_logger("history")

HISTORY_COLUMNS: list[str] = [
    "timestamp", "source", "prediction", "probability", "confidence",
    "risk", "best_model", "age", "gender", "details",
]


def _ensure_file(path: Path) -> None:
    if not path.exists():
        pd.DataFrame(columns=HISTORY_COLUMNS).to_csv(path, index=False)
        log.info("Created history file -> %s", path)


def append_record(record: Mapping, path: Path = HISTORY_CSV) -> None:
    """Append a single prediction record to the history CSV."""
    path = Path(path)
    _ensure_file(path)
    row = {col: record.get(col, "") for col in HISTORY_COLUMNS}
    row["timestamp"] = record.get("timestamp", datetime.now().isoformat(timespec="seconds"))
    pd.DataFrame([row]).to_csv(path, mode="a", header=False, index=False)
    log.info("History appended: %s (%.2f)", row["prediction"], row.get("confidence", 0) or 0)


def load_history(path: Path = HISTORY_CSV) -> pd.DataFrame:
    """Return the full history as a ``DataFrame`` (empty frame if none yet)."""
    path = Path(path)
    if not path.exists():
        return pd.DataFrame(columns=HISTORY_COLUMNS)
    try:
        return pd.read_csv(path)
    except Exception as exc:  # pragma: no cover - corrupted file safety net
        log.error("Could not read history: %s", exc)
        return pd.DataFrame(columns=HISTORY_COLUMNS)


def clear_history(path: Path = HISTORY_CSV) -> None:
    """Reset the history file to an empty (header-only) CSV."""
    pd.DataFrame(columns=HISTORY_COLUMNS).to_csv(Path(path), index=False)
    log.info("History cleared")


def history_kpis(history: pd.DataFrame) -> dict:
    """Compute the headline numbers shown on the Dashboard."""
    if history.empty:
        return {"total": 0, "positive": 0, "negative": 0, "avg_confidence": 0.0}
    positive = int((history["prediction"] == "Liver Disease").sum())
    return {
        "total": int(len(history)),
        "positive": positive,
        "negative": int(len(history) - positive),
        "avg_confidence": float(pd.to_numeric(history["confidence"], errors="coerce").mean()),
    }
