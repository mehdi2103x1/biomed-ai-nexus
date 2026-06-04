"""
train.py
========
Offline training entry-point for BioMed AI Nexus.

It performs the full supervised-learning pipeline on the ILPD dataset:

    1. load + clean the data            (utils.preprocessing)
    2. stratified train/test split
    3. fit the preprocessor (impute + scale) on the TRAIN split only
    4. train + tune the 5 models        (utils.models.TabularTrainer)
    5. evaluate on the held-out test set
    6. persist  models/*.pkl, models/preprocessor.pkl, models/metrics.json

Usage
-----
    python train.py            # full grid-search (a few minutes)
    python train.py --fast     # defaults only, no hyper-parameter tuning
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))

from config import (  # noqa: E402
    FEATURE_ORDER, PREPROCESSOR_PATH, RANDOM_STATE, TEST_SIZE,
)
from utils.logger import get_logger              # noqa: E402
from utils.models import TabularTrainer          # noqa: E402
from utils.preprocessing import (                # noqa: E402
    LiverPreprocessor, load_raw_dataset,
)

log = get_logger("train")


def main() -> int:
    parser = argparse.ArgumentParser(description="Train liver-disease models.")
    parser.add_argument("--fast", action="store_true",
                        help="Skip GridSearchCV (defaults only) for a quick run.")
    args = parser.parse_args()

    from sklearn.model_selection import train_test_split

    # 1. Load -------------------------------------------------------------- #
    df = load_raw_dataset()
    y = df["Target"].astype(int).to_numpy()
    X_df = df.drop(columns=["Target"])

    # 2. Split (stratified, deterministic) -------------------------------- #
    X_train_df, X_test_df, y_train, y_test = train_test_split(
        X_df, y, test_size=TEST_SIZE, stratify=y, random_state=RANDOM_STATE,
    )
    log.info("Split: %d train / %d test", len(X_train_df), len(X_test_df))

    # 3. Preprocessor fitted on TRAIN only (no leakage) ------------------- #
    pre = LiverPreprocessor().fit(X_train_df)
    X_train = pre.transform(X_train_df)
    X_test = pre.transform(X_test_df)
    pre.save(PREPROCESSOR_PATH)

    # 4-5. Train + evaluate ----------------------------------------------- #
    trainer = TabularTrainer()
    trainer.train(
        X_train, y_train, X_test, y_test,
        feature_names=FEATURE_ORDER, tune=not args.fast,
    )

    # 6. Persist ----------------------------------------------------------- #
    trainer.persist()

    print("\n================ MODEL RANKING ================")
    for r in trainer.ranking():
        print(f"  {r['rank']}. {r['name']:<22} "
              f"acc={r['accuracy']:.3f}  f1={r['f1']:.3f}  auc={r['auc']:.3f}")
    print("===============================================")
    print("Models + metrics saved to ./models/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
