"""
pages.about
===========
Project description, technology stack, ML pipeline explanation and author info.
"""
from __future__ import annotations

import streamlit as st

from config import AUTHOR_NAME, AUTHOR_PROGRAM
from utils.styles import hero, pills


def render(ctx: dict) -> None:
    hero("About this project",
         "BioMed AI Nexus — Liver Disease Prediction Platform")

    st.markdown("""
**BioMed AI Nexus** is an academic biomedical-AI platform that predicts liver
disease from routine blood-panel biomarkers, demonstrates deep-learning image
analysis, and explains every prediction. It was built for the *Machine Learning —
Supervised Learning* module of the Biomedical Engineering programme.

**Problem statement.** *How can liver diseases be predicted from biological
analyses and patient medical data?*
""")

    st.markdown("#### 🛠️ Technologies used")
    pills(["Python 3", "Streamlit", "Scikit-Learn", "XGBoost",
           "TensorFlow / Keras", "Pandas", "NumPy", "OpenCV", "Plotly",
           "Matplotlib", "fpdf2", "joblib"])

    st.markdown("#### 🔬 Machine-learning pipeline")
    st.markdown("""
1. **Data acquisition** — Indian Liver Patient Dataset (ILPD, 583 records, 10 features).
2. **Cleaning** — column naming, gender encoding, binary target mapping
   (1 = liver patient → *Disease*, 2 = non-patient → *No disease*).
3. **Preprocessing** — median imputation of missing values (A/G ratio),
   `StandardScaler` standardisation, fitted on the **train split only** to avoid
   data leakage.
4. **Modelling** — five supervised classifiers trained and tuned with
   `GridSearchCV` (5-fold stratified CV): Decision Tree, Random Forest, Logistic
   Regression, SVM, XGBoost.
5. **Evaluation** — accuracy, precision, recall, F1, ROC-AUC, confusion matrix
   and classification report on a held-out 20 % test set.
6. **Inference** — soft-voting ensemble across the five models, with a risk band
   and confidence score.
7. **Explainability** — feature importance (tabular) and Grad-CAM (image CNN).
8. **Persistence** — predictions logged to `historical_predictions.csv`; a PDF
   report is generated on demand.
""")

    st.markdown("#### 🧱 Architecture")
    st.code("""project/
├── app.py                 # Streamlit entry-point + sidebar router
├── config.py              # central configuration (paths, features, palette)
├── train.py               # offline training & evaluation pipeline
├── pages/                 # home, prediction, image_analysis, evaluation,
│                          #   dashboard, about  (one render() each)
├── utils/                 # preprocessing, models, visualization, image_model,
│                          #   pdf_report, history, styles, logger
├── data/                  # ilpd_raw.csv, load_data.py, historical_predictions.csv
├── models/                # *.pkl estimators, preprocessor.pkl, metrics.json
├── notebooks/             # exploratory analysis
├── assets/  · logs/
├── requirements.txt · README.md
""", language="text")

    st.markdown("#### 👤 Author")
    c1, c2 = st.columns([1, 3])
    with c1:
        st.markdown("<div style='font-size:4rem;text-align:center'>🧑‍⚕️</div>",
                    unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
**{AUTHOR_NAME}**
{AUTHOR_PROGRAM}

Project: *BioMed AI Nexus — Liver Disease Prediction Platform*
Module: Machine Learning — Supervised Learning
""")

    st.warning("⚕️ **Medical disclaimer.** This is an academic prototype trained on "
               "a public dataset. It is **not** a certified medical device and must "
               "not be used for real clinical diagnosis.")
