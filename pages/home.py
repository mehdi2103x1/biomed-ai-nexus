"""
pages.home
==========
Landing page: hero banner, a one-line description, dataset KPI cards and the
application workflow diagram (built in pure HTML/CSS).
"""
from __future__ import annotations

import streamlit as st

from config import APP_SUBTITLE, APP_TITLE, DATASET_NAME
from utils.preprocessing import dataset_overview
from utils.styles import hero, render_kpis, section


def _workflow_diagram() -> None:
    """A lightweight, dependency-free workflow diagram of the ML pipeline."""
    steps = [
        ("📝", "Patient Data", "Blood-panel form"),
        ("⚙️", "Preprocessing", "Impute · Scale · Encode"),
        ("🤖", "5 ML Models", "DT · RF · LR · SVM · XGB"),
        ("🗳️", "Ensemble Vote", "Soft voting"),
        ("📊", "Prediction", "Class · Probability · Risk"),
        ("🗂️", "History & Dashboard", "CSV · KPIs · Charts"),
    ]
    cells = []
    for i, (icon, title, sub) in enumerate(steps):
        arrow = "" if i == len(steps) - 1 else "<div class='wf-arrow'>➜</div>"
        cells.append(
            f"<div class='wf-step'><div class='wf-ico'>{icon}</div>"
            f"<div class='wf-title'>{title}</div>"
            f"<div class='wf-sub'>{sub}</div></div>{arrow}"
        )
    st.markdown(
        """
        <style>
        .wf-wrap{display:flex;flex-wrap:wrap;align-items:stretch;gap:.4rem;justify-content:center;}
        .wf-step{flex:1 1 150px;min-width:140px;background:var(--surface);
                 border:1px solid var(--border);border-radius:14px;padding:1rem .8rem;
                 text-align:center;position:relative;z-index:1;}
        .wf-step::before{content:"";position:absolute;left:0;top:0;bottom:0;width:3px;
                 background:var(--primary);opacity:.7;border-radius:3px 0 0 3px;}
        .wf-ico{font-size:1.6rem;} .wf-title{font-weight:600;margin-top:.3rem;font-family:'Spectral',serif;}
        .wf-sub{font-size:.76rem;color:var(--muted);margin-top:.2rem;}
        .wf-arrow{display:flex;align-items:center;font-size:1.2rem;color:var(--primary);opacity:.65;}
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(f"<div class='wf-wrap'>{''.join(cells)}</div>", unsafe_allow_html=True)


def render(ctx: dict) -> None:
    hero(f"{APP_TITLE}", f"{APP_SUBTITLE} — an interactive biomedical AI platform")

    st.markdown(
        "Predicts liver disease from routine blood-panel biomarkers and patient "
        "data using five Machine-Learning models, with comparative evaluation, "
        "an analytics dashboard and explainable, exportable results."
    )

    # --- Dataset KPI cards ------------------------------------------------ #
    df = ctx["dataset"]
    ov = dataset_overview(df)
    section(f"Dataset overview — {DATASET_NAME}")
    render_kpis([
        {"icon": "🧬", "value": f"{ov['n_rows']}", "label": "Patient records"},
        {"icon": "🩸", "value": f"{ov['n_disease']}", "label": "Liver disease cases",
         "sub": f"{ov['disease_rate']:.0%} of cohort"},
        {"icon": "✅", "value": f"{ov['n_healthy']}", "label": "Healthy controls"},
        {"icon": "🔢", "value": f"{ov['n_features']}", "label": "Clinical features"},
    ])
    st.write("")
    render_kpis([
        {"icon": "👤", "value": f"{ov['mean_age']:.0f} yr", "label": "Mean age"},
        {"icon": "⚧", "value": f"{ov['pct_male']:.0%}", "label": "Male proportion"},
        {"icon": "🧪", "value": f"{ov['missing_values']}", "label": "Missing values handled"},
        {"icon": "🤖", "value": "5", "label": "ML models"},
    ])

    # --- Workflow --------------------------------------------------------- #
    section("Application workflow")
    _workflow_diagram()
