"""
pages.evaluation
================
Model-evaluation dashboard.

Reads ``models/metrics.json`` (produced by ``train.py``) and renders, for every
model: accuracy / precision / recall / F1 / AUC, the ROC curve, the confusion
matrix, the full classification report, training time and best hyper-parameters.
A ranking table summarises which model wins.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from utils.styles import df_table, hero, render_kpis, section
from utils.visualization import (
    confusion_heatmap, metrics_grouped_bar, roc_curves, training_time_bar,
)


def render(ctx: dict) -> None:
    hero("Model Evaluation",
         "Performance of the five Machine-Learning models on the held-out test set")

    mgr = ctx["manager"]
    metrics = mgr.metrics
    if not metrics or "models" not in metrics:
        st.error("No metrics found. Run `python train.py` to train and evaluate "
                 "the models first.")
        return

    models = metrics["models"]
    ranking = metrics.get("ranking", [])

    # --- Headline: best model -------------------------------------------- #
    if ranking:
        best = ranking[0]
        section("Best model")
        render_kpis([
            {"icon": "🥇", "value": best["name"], "label": "Top performer"},
            {"icon": "🎯", "value": f"{best['accuracy']:.1%}", "label": "Accuracy"},
            {"icon": "⚖️", "value": f"{best['f1']:.3f}", "label": "F1 score"},
            {"icon": "📐", "value": f"{best['auc']:.3f}", "label": "ROC AUC"},
        ])

    # --- Comparison charts ----------------------------------------------- #
    section("Comparative metrics")
    st.plotly_chart(metrics_grouped_bar(models), use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(roc_curves(models), use_container_width=True)
    with c2:
        st.plotly_chart(training_time_bar(models), use_container_width=True)

    # --- Ranking table --------------------------------------------------- #
    section("Model ranking")
    rdf = pd.DataFrame(ranking)[
        ["rank", "name", "accuracy", "precision", "recall", "f1", "auc"]
    ].copy()
    for c in ["accuracy", "precision", "recall", "f1", "auc"]:
        rdf[c] = rdf[c].map(lambda v: f"{v:.3f}")
    rdf.columns = ["Rank", "Model", "Accuracy", "Precision", "Recall", "F1", "AUC"]
    df_table(rdf, highlight_first=True)

    # --- Per-model deep dive --------------------------------------------- #
    section("Per-model detail")
    names = {m["name"]: k for k, m in models.items()}
    choice = st.selectbox("Select a model", list(names.keys()))
    m = models[names[choice]]

    render_kpis([
        {"icon": "🎯", "value": f"{m['metrics']['accuracy']:.3f}", "label": "Accuracy"},
        {"icon": "🎚️", "value": f"{m['metrics']['precision']:.3f}", "label": "Precision"},
        {"icon": "📡", "value": f"{m['metrics']['recall']:.3f}", "label": "Recall"},
        {"icon": "⏱️", "value": f"{m['train_time']:.1f} s", "label": "Training time"},
    ])

    d1, d2 = st.columns(2)
    with d1:
        st.plotly_chart(confusion_heatmap(m["confusion"], m["name"]),
                        use_container_width=True)
    with d2:
        st.markdown("**Classification report**")
        report = pd.DataFrame(m["report"]).transpose().round(3)
        df_table(report, index=True, index_label="")

    if m.get("best_params"):
        st.markdown("**Best hyper-parameters** (GridSearchCV)")
        st.json(m["best_params"])

    if m.get("feature_importance"):
        from utils.visualization import feature_importance_bar
        st.markdown("**Feature importance**")
        st.plotly_chart(feature_importance_bar(m["feature_importance"]),
                        use_container_width=True)
