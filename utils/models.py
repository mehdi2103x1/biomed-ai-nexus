"""
utils.models
============
Tabular Machine-Learning model management for the liver-disease task.

Two responsibilities, cleanly separated:

* :class:`TabularTrainer` — used **offline** by ``train.py``. It builds the five
  estimators, runs a small hyper-parameter search, evaluates every model on a
  held-out test set and persists the fitted estimators + a ``metrics.json``.
* :class:`ModelManager`  — used **online** by the Streamlit app. It lazily loads
  the persisted estimators and the preprocessor and exposes a single
  :meth:`predict_all` call that returns a tidy comparison across models.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd

from config import (
    CV_FOLDS,
    METRICS_JSON,
    MODEL_REGISTRY,
    MODELS_DIR,
    PREPROCESSOR_PATH,
    RANDOM_STATE,
)
from utils.logger import get_logger
from utils.preprocessing import LiverPreprocessor, label_to_text

log = get_logger("models")


# --------------------------------------------------------------------------- #
# Estimator factory + search spaces
# --------------------------------------------------------------------------- #
def build_estimators() -> dict[str, Any]:
    """Instantiate the five registered estimators with sensible defaults."""
    from sklearn.tree import DecisionTreeClassifier
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.svm import SVC
    from xgboost import XGBClassifier

    return {
        "decision_tree": DecisionTreeClassifier(random_state=RANDOM_STATE),
        "random_forest": RandomForestClassifier(
            random_state=RANDOM_STATE, n_jobs=-1
        ),
        "logistic_regression": LogisticRegression(
            max_iter=2000, random_state=RANDOM_STATE
        ),
        "svm": SVC(probability=True, random_state=RANDOM_STATE),
        "xgboost": XGBClassifier(
            random_state=RANDOM_STATE,
            eval_metric="logloss",
            n_jobs=-1,
            tree_method="hist",
        ),
    }


def search_spaces() -> dict[str, dict]:
    """Compact grids — large enough to be meaningful, small enough to be fast."""
    # ``class_weight``/``scale_pos_weight`` counter the class imbalance
    # (~71 % disease). Grids are kept compact so a full GridSearchCV stays fast
    # even on the ~19k-row dataset (the kernel SVM is the scaling bottleneck).
    return {
        "decision_tree": {
            "max_depth": [6, 12, None],
            "min_samples_leaf": [1, 5],
            "class_weight": [None, "balanced"],
        },
        "random_forest": {
            "n_estimators": [200, 400],
            "max_depth": [None, 16],
            "class_weight": [None, "balanced"],
        },
        "logistic_regression": {
            "C": [0.1, 1.0, 10.0],
            "class_weight": [None, "balanced"],
        },
        "svm": {
            "C": [1.0, 5.0],
            "kernel": ["rbf"],
            "gamma": ["scale"],
            "class_weight": ["balanced"],
        },
        "xgboost": {
            "n_estimators": [300, 500],
            "max_depth": [4, 6],
            "learning_rate": [0.1],
            "subsample": [0.9],
        },
    }


# --------------------------------------------------------------------------- #
# Evaluation container
# --------------------------------------------------------------------------- #
@dataclass
class ModelResult:
    """Everything we want to remember about a trained model."""

    key: str
    name: str
    best_params: dict
    train_time: float
    metrics: dict[str, float]
    roc: dict[str, list]            # {"fpr": [...], "tpr": [...], "auc": float}
    confusion: list[list[int]]
    report: dict                    # sklearn classification_report (dict form)
    feature_importance: dict[str, float] = field(default_factory=dict)

    def to_json(self) -> dict:
        return {
            "key": self.key,
            "name": self.name,
            "best_params": self.best_params,
            "train_time": self.train_time,
            "metrics": self.metrics,
            "roc": self.roc,
            "confusion": self.confusion,
            "report": self.report,
            "feature_importance": self.feature_importance,
        }


# --------------------------------------------------------------------------- #
# Trainer (offline)
# --------------------------------------------------------------------------- #
class TabularTrainer:
    """Train, tune and evaluate every registered model, then persist them."""

    def __init__(self, models_dir: Path = MODELS_DIR) -> None:
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.results: dict[str, ModelResult] = {}
        self.estimators: dict[str, Any] = {}

    def _evaluate(
        self, key: str, est: Any, best_params: dict, train_time: float,
        X_test: np.ndarray, y_test: np.ndarray, feature_names: list[str],
    ) -> ModelResult:
        from sklearn.metrics import (
            accuracy_score, precision_score, recall_score, f1_score,
            roc_auc_score, roc_curve, confusion_matrix, classification_report,
        )

        y_pred = est.predict(X_test)
        y_proba = est.predict_proba(X_test)[:, 1]

        fpr, tpr, _ = roc_curve(y_test, y_proba)
        auc = float(roc_auc_score(y_test, y_proba))

        metrics = {
            "accuracy":  float(accuracy_score(y_test, y_pred)),
            "precision": float(precision_score(y_test, y_pred, zero_division=0)),
            "recall":    float(recall_score(y_test, y_pred, zero_division=0)),
            "f1":        float(f1_score(y_test, y_pred, zero_division=0)),
            "auc":       auc,
        }

        # Feature importance (tree models) or |coefficients| (linear models).
        importance: dict[str, float] = {}
        if hasattr(est, "feature_importances_"):
            importance = dict(zip(feature_names, map(float, est.feature_importances_)))
        elif hasattr(est, "coef_"):
            importance = dict(zip(feature_names, map(float, np.abs(est.coef_[0]))))

        return ModelResult(
            key=key,
            name=MODEL_REGISTRY[key],
            best_params=best_params,
            train_time=train_time,
            metrics=metrics,
            roc={"fpr": fpr.tolist(), "tpr": tpr.tolist(), "auc": auc},
            confusion=confusion_matrix(y_test, y_pred).tolist(),
            report=classification_report(
                y_test, y_pred, output_dict=True, zero_division=0,
                target_names=["No Disease", "Disease"],
            ),
            feature_importance=importance,
        )

    def train(
        self,
        X_train: np.ndarray, y_train: np.ndarray,
        X_test: np.ndarray, y_test: np.ndarray,
        feature_names: list[str],
        tune: bool = True,
    ) -> dict[str, ModelResult]:
        """Fit every model (optionally with GridSearchCV) and evaluate it."""
        from sklearn.model_selection import GridSearchCV, StratifiedKFold

        estimators = build_estimators()
        grids = search_spaces()
        cv = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE)

        for key, base in estimators.items():
            log.info("Training %s ...", MODEL_REGISTRY[key])
            t0 = time.perf_counter()
            if tune and key in grids:
                search = GridSearchCV(
                    base, grids[key], scoring="roc_auc", cv=cv, n_jobs=-1, refit=True,
                )
                search.fit(X_train, y_train)
                est = search.best_estimator_
                best_params = search.best_params_
            else:
                est = base.fit(X_train, y_train)
                best_params = {}
            train_time = time.perf_counter() - t0

            result = self._evaluate(
                key, est, best_params, train_time, X_test, y_test, feature_names
            )
            self.results[key] = result
            self.estimators[key] = est
            log.info(
                "  %s -> acc=%.3f f1=%.3f auc=%.3f (%.1fs)",
                MODEL_REGISTRY[key], result.metrics["accuracy"],
                result.metrics["f1"], result.metrics["auc"], train_time,
            )
        return self.results

    def persist(self, metrics_path: Path = METRICS_JSON) -> None:
        """Save each fitted estimator (``<key>.pkl``) and aggregated metrics."""
        import joblib

        for key, est in self.estimators.items():
            joblib.dump(est, self.models_dir / f"{key}.pkl")
        payload = {
            "feature_names": list(next(iter(self.results.values())).feature_importance.keys())
            if self.results else [],
            "models": {k: r.to_json() for k, r in self.results.items()},
            "ranking": self.ranking(),
        }
        Path(metrics_path).write_text(json.dumps(payload, indent=2), encoding="utf-8")
        log.info("Persisted %d models + metrics -> %s", len(self.estimators), metrics_path)

    def ranking(self) -> list[dict]:
        """Models ordered by AUC then F1 (best first).

        AUC is threshold-independent, so — unlike raw F1 on an imbalanced set —
        it is not inflated by a model that simply predicts the majority class.
        """
        ordered = sorted(
            self.results.values(),
            key=lambda r: (r.metrics["auc"], r.metrics["f1"]),
            reverse=True,
        )
        return [
            {"rank": i + 1, "key": r.key, "name": r.name, **r.metrics}
            for i, r in enumerate(ordered)
        ]


# --------------------------------------------------------------------------- #
# Manager (online)
# --------------------------------------------------------------------------- #
class ModelManager:
    """Load persisted models + preprocessor and serve predictions to the UI."""

    def __init__(self, models_dir: Path = MODELS_DIR) -> None:
        self.models_dir = Path(models_dir)
        self.estimators: dict[str, Any] = {}
        self.metrics: dict = {}
        self.preprocessor: LiverPreprocessor | None = None
        self.feature_names: list[str] = []

    @property
    def is_ready(self) -> bool:
        return bool(self.estimators) and self.preprocessor is not None

    def load(self) -> "ModelManager":
        """Load everything from disk. Safe to call repeatedly (cached by app)."""
        import joblib

        if PREPROCESSOR_PATH.exists():
            self.preprocessor = LiverPreprocessor.load(PREPROCESSOR_PATH)
        if METRICS_JSON.exists():
            self.metrics = json.loads(METRICS_JSON.read_text(encoding="utf-8"))
            self.feature_names = self.metrics.get("feature_names", [])
        for key in MODEL_REGISTRY:
            p = self.models_dir / f"{key}.pkl"
            if p.exists():
                self.estimators[key] = joblib.load(p)
        log.info("ModelManager loaded %d models (ready=%s)",
                 len(self.estimators), self.is_ready)
        return self

    def predict_all(self, form: Mapping[str, float | str]) -> pd.DataFrame:
        """Run every model on one patient. Returns a per-model comparison frame."""
        if not self.is_ready:
            raise RuntimeError("Models are not trained. Run `python train.py` first.")

        X = self.preprocessor.transform(form)  # type: ignore[union-attr]
        rows = []
        for key, est in self.estimators.items():
            proba = float(est.predict_proba(X)[0, 1])
            pred = int(proba >= 0.5)
            rows.append({
                "key": key,
                "Model": MODEL_REGISTRY[key],
                "Prediction": label_to_text(pred),
                "pred_label": pred,
                "Disease Probability": proba,
                "Confidence": max(proba, 1 - proba),
            })
        return pd.DataFrame(rows)

    def ensemble_decision(self, comparison: pd.DataFrame) -> dict:
        """Soft-vote across models -> final class, probability, risk level."""
        mean_proba = float(comparison["Disease Probability"].mean())
        pred = int(mean_proba >= 0.5)
        confidence = max(mean_proba, 1 - mean_proba)
        risk = risk_level(mean_proba)
        agree = int((comparison["pred_label"] == pred).sum())
        return {
            "label": pred,
            "text": label_to_text(pred),
            "probability": mean_proba,
            "confidence": confidence,
            "risk": risk,
            "agreement": f"{agree}/{len(comparison)} models agree",
        }

    def best_model_key(self) -> str | None:
        ranking = self.metrics.get("ranking", [])
        return ranking[0]["key"] if ranking else None


def risk_level(proba: float) -> str:
    """Map a disease probability to a clinical-style risk band."""
    if proba < 0.25:
        return "Low"
    if proba < 0.50:
        return "Moderate"
    if proba < 0.75:
        return "High"
    return "Very High"
