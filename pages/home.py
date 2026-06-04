"""
pages.home
==========
Landing page: hero banner, project objectives, dataset KPI cards, a workflow
diagram (built in pure HTML/CSS) and liver-disease statistics.
"""
from __future__ import annotations

import streamlit as st

from config import APP_SUBTITLE, APP_TITLE
from utils.preprocessing import dataset_overview
from utils.styles import hero, pills, render_kpis


def _workflow_diagram() -> None:
    """A lightweight, dependency-free workflow diagram (matches the brief)."""
    steps = [
        ("📥", "Data Input", "Form / Image upload"),
        ("⚙️", "Preprocessing", "Impute · Scale · Encode"),
        ("🤖", "ML / DL Models", "5 ML models + CNN"),
        ("📊", "Prediction", "Class · Probability · Risk"),
        ("🔍", "Explainability", "Importance · Grad-CAM"),
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
        "**BioMed AI Nexus** predicts liver disease from routine blood-panel "
        "biomarkers and patient data using five Machine-Learning models, adds a "
        "Deep-Learning image-analysis demonstration, and explains every decision "
        "with interactive visualisations."
    )

    # --- Dataset KPI cards ------------------------------------------------ #
    df = ctx["dataset"]
    ov = dataset_overview(df)
    st.markdown("#### 📈 Dataset at a glance — Indian Liver Patient Dataset (ILPD)")
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
        {"icon": "♂️", "value": f"{ov['pct_male']:.0%}", "label": "Male proportion"},
        {"icon": "🧪", "value": f"{ov['missing_values']}", "label": "Missing values handled"},
        {"icon": "🤖", "value": "5 + CNN", "label": "Models available"},
    ])

    # --- Objectives ------------------------------------------------------- #
    st.markdown("#### 🎯 Project objectives")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            "- Predict liver disease from **tabular** biomarkers\n"
            "- Provide a **CNN image-analysis** demonstration with Grad-CAM\n"
            "- **Train & compare** Decision Tree, Random Forest, Logistic "
            "Regression, SVM and XGBoost"
        )
    with c2:
        st.markdown(
            "- Display **interactive dashboards** and KPIs\n"
            "- Maintain a **prediction history** (CSV)\n"
            "- **Explain** predictions (feature importance, Grad-CAM, PDF report)"
        )

    # --- Workflow --------------------------------------------------------- #
    st.markdown("#### 🔄 Application workflow")
    _workflow_diagram()

    # --- Liver disease context ------------------------------------------- #
    st.write("")
    st.markdown("#### 🩺 Why liver disease screening matters")
    g1, g2, g3 = st.columns(3)
    with g1:
        st.markdown("<div class='panel'><b>~2 million</b><br>deaths per year worldwide "
                    "are attributable to liver disease.</div>", unsafe_allow_html=True)
    with g2:
        st.markdown("<div class='panel'><b>Often silent</b><br>early-stage liver damage "
                    "is frequently asymptomatic — biomarkers reveal it first.</div>",
                    unsafe_allow_html=True)
    with g3:
        st.markdown("<div class='panel'><b>Routine bloods</b><br>bilirubin, enzymes and "
                    "proteins enable low-cost, early screening.</div>",
                    unsafe_allow_html=True)

    st.write("")
    st.markdown("**Tech stack**")
    pills(["Python", "Streamlit", "Scikit-Learn", "TensorFlow / Keras", "XGBoost",
           "Pandas", "NumPy", "OpenCV", "Plotly", "Matplotlib"])

    st.info("👈 Use the sidebar to navigate. Start with **Liver Disease Prediction** "
            "to test a patient, or **Model Evaluation** to inspect performance.")
