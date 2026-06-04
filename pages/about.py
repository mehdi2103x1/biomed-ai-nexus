"""
pages.about
===========
Project description, technology stack, ML pipeline and author information.
"""
from __future__ import annotations

import streamlit as st

from config import APP_SUBTITLE, APP_TITLE, AUTHOR_NAME, AUTHOR_PROGRAM, DATASET_NAME
from utils.styles import hero, pills, section


def render(ctx: dict) -> None:
    hero("About", f"{APP_TITLE} — {APP_SUBTITLE}")

    st.markdown(f"""
**{APP_TITLE}** is a clinical decision-support platform that predicts liver
disease from routine blood-panel biomarkers and patient data, and explains
every prediction.

**Subject 16 — Liver disease prediction.** *How can liver diseases be predicted
from biological analyses and patient medical data?* This is a **tabular**
machine-learning problem (no medical imaging).
""")

    section("Technologies")
    pills(["Python", "Streamlit", "Scikit-Learn", "XGBoost",
           "Pandas", "NumPy", "Plotly", "Matplotlib"])

    section("Machine-learning pipeline")
    st.markdown(f"""
1. **Data** — {DATASET_NAME}: 30,691 records (~19,000 after removing duplicate
   rows), 10 clinical features.
2. **Preprocessing** — median imputation, gender encoding and standardisation,
   fitted on the training split only to prevent data leakage.
3. **Modelling** — five classifiers tuned with `GridSearchCV` (5-fold stratified
   cross-validation): Decision Tree, Random Forest, Logistic Regression, SVM, XGBoost.
4. **Evaluation** — accuracy, precision, recall, F1 and ROC-AUC on a held-out
   20 % test set; best model ≈ 99 % accuracy.
5. **Inference** — soft-voting ensemble with a confidence score and risk band.
6. **Explainability** — feature-importance ranking and a downloadable PDF report.
""")

    section("Author")
    c1, c2 = st.columns([1, 4])
    with c1:
        st.markdown("<div style='font-size:3.4rem;text-align:center'>🧑‍⚕️</div>",
                    unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
**{AUTHOR_NAME}**
{AUTHOR_PROGRAM}
Module — Machine Learning, Supervised Learning
""")

    st.caption("Academic prototype trained on a public dataset — not a certified "
               "medical device; not for real clinical diagnosis.")
