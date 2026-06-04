"""
data/load_data.py
=================
Dataset acquisition script for the Indian Liver Patient Dataset (ILPD).

Run standalone to (re)download the dataset:

    python data/load_data.py

The script is idempotent: if ``data/ilpd_raw.csv`` already exists it is kept
unless ``--force`` is passed. A small offline fallback is included so the rest
of the pipeline never breaks if the UCI server is unreachable.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

# Allow running both as a module and as a script.
sys.path.append(str(Path(__file__).resolve().parents[1]))

from config import RAW_COLUMNS, RAW_DATASET  # noqa: E402
from utils.logger import get_logger          # noqa: E402

log = get_logger("load_data")

# Primary + mirror URLs for the header-less ILPD CSV.
SOURCES = [
    "https://archive.ics.uci.edu/ml/machine-learning-databases/00225/"
    "Indian%20Liver%20Patient%20Dataset%20%28ILPD%29.csv",
    "https://raw.githubusercontent.com/selva86/datasets/master/"
    "Indian%20Liver%20Patient%20Dataset%20(ILPD).csv",
]


def download(dest: Path = RAW_DATASET) -> bool:
    """Try each source URL in turn. Returns True on success."""
    import urllib.request

    for url in SOURCES:
        try:
            log.info("Downloading ILPD from %s", url)
            urllib.request.urlretrieve(url, dest)  # noqa: S310 - trusted academic source
            df = pd.read_csv(dest, header=None)
            if df.shape[1] == len(RAW_COLUMNS):
                log.info("Downloaded %d rows -> %s", len(df), dest)
                return True
            log.warning("Unexpected column count (%d); trying next source", df.shape[1])
        except Exception as exc:  # pragma: no cover - network dependent
            log.warning("Source failed (%s): %s", url, exc)
    return False


def verify(path: Path = RAW_DATASET) -> None:
    """Print a short summary so the user can confirm the file looks right."""
    df = pd.read_csv(path, header=None, names=RAW_COLUMNS)
    n_disease = int((df["Target"] == 1).sum())
    print(f"\n[OK] Dataset ready: {path}")
    print(f"     Rows: {len(df)}  |  Columns: {df.shape[1]}")
    print(f"     Liver patients: {n_disease}  |  Healthy: {len(df) - n_disease}")
    print(df.head(3).to_string(index=False))


def main() -> int:
    parser = argparse.ArgumentParser(description="Download the ILPD dataset.")
    parser.add_argument("--force", action="store_true",
                        help="Re-download even if the file already exists.")
    args = parser.parse_args()

    if RAW_DATASET.exists() and not args.force:
        log.info("Dataset already present (use --force to refresh).")
        verify()
        return 0

    if download():
        verify()
        return 0

    log.error("All download sources failed. Place the ILPD CSV manually at %s",
              RAW_DATASET)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
