"""
pages.prediction
================
Liver-disease prediction from tabular patient data.

Flow: interactive medical form (number inputs, sliders, dropdown, radio) ->
soft validation -> automatic preprocessing -> predict with all 5 models ->
ensemble decision -> rich result display (class, probability gauge, confidence,
risk, feature importance, model comparison) -> save to history + PDF download.
"""
from __future__ import annotations

import time

import streamlit as st

from config import FEATURE_META
from utils.history import append_record
from utils.pdf_report import build_prediction_pdf
from utils.preprocessing import validate_form
from utils.styles import df_table, hero, render_kpis, result_card, section
from utils.visualization import (
    feature_importance_bar, model_comparison_bar, probability_gauge,
)

_RISK_COLORS = {
    "Low": "#2dbb7f", "Moderate": "#e0a82e",
    "High": "#f5853f", "Very High": "#f06a82",
}


def _num(label: str, key: str) -> float:
    """A number input driven by the FEATURE_META ranges."""
    m = FEATURE_META[key]
    return st.number_input(label, min_value=float(m["min"]), max_value=float(m["max"]),
                           value=float(m["default"]), step=float(m["step"]))


def _build_form() -> dict:
    """Render the medical form (number fields only) and return raw inputs."""
    section("Patient biological & clinical data")
    form: dict = {}

    with st.form("patient_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            form["Age"] = _num("Age (years)", "Age")
            form["Gender"] = st.radio("Gender", ["Male", "Female"], horizontal=True)
            form["Total_Bilirubin"] = _num("Total Bilirubin (mg/dL)", "Total_Bilirubin")
            form["Direct_Bilirubin"] = _num("Direct Bilirubin (mg/dL)", "Direct_Bilirubin")
        with c2:
            form["Alkaline_Phosphotase"] = _num("Alkaline Phosphotase (IU/L)", "Alkaline_Phosphotase")
            form["Alamine_Aminotransferase"] = _num("Alamine Aminotransferase / ALT (IU/L)", "Alamine_Aminotransferase")
            form["Aspartate_Aminotransferase"] = _num("Aspartate Aminotransferase / AST (IU/L)", "Aspartate_Aminotransferase")
        with c3:
            form["Total_Proteins"] = _num("Total Proteins (g/dL)", "Total_Proteins")
            form["Albumin"] = _num("Albumin (g/dL)", "Albumin")
            form["Albumin_and_Globulin_Ratio"] = _num("Albumin / Globulin Ratio", "Albumin_and_Globulin_Ratio")

        patient_id = st.text_input("Patient ID / name (optional)", "")
        submitted = st.form_submit_button("Predict liver disease",
                                          use_container_width=True)

    form["_submitted"] = submitted
    form["_patient_id"] = patient_id
    return form


def _result_banner(decision: dict) -> None:
    """Big diagnosis result card (refined, clinical)."""
    is_disease = decision["label"] == 1
    icon = "⚠" if is_disease else "✓"
    result_card(icon, decision["text"], decision["agreement"], positive=is_disease)


def render(ctx: dict) -> None:
    hero("Liver Disease Prediction",
         "Enter the patient's blood-panel results — five models vote on the outcome")

    mgr = ctx["manager"]
    if not mgr.is_ready:
        st.error("⚠️ Models are not trained yet. Run `python train.py` in the "
                 "project root, then reload the app.")
        return

    form = _build_form()

    if not form["_submitted"]:
        return

    # --- Validation ------------------------------------------------------- #
    warnings = validate_form(form)
    if warnings:
        with st.expander(f"⚠️ {len(warnings)} input warning(s) — click to review"):
            for w in warnings:
                st.write("•", w)

    # --- Inference with progress + spinner ------------------------------- #
    progress = st.progress(0, text="Preprocessing inputs…")
    with st.spinner("Running 5 machine-learning models…"):
        time.sleep(0.2)
        progress.progress(35, text="Scaling & encoding features…")
        comparison = mgr.predict_all(form)
        progress.progress(75, text="Aggregating model votes…")
        decision = mgr.ensemble_decision(comparison)
        time.sleep(0.15)
        progress.progress(100, text="Done")
    progress.empty()

    # --- Result ----------------------------------------------------------- #
    section("Result")
    left, right = st.columns([1, 1])
    with left:
        _result_banner(decision)
        st.write("")
        render_kpis([
            {"icon": "🎯", "value": f"{decision['probability']:.0%}",
             "label": "Disease probability"},
            {"icon": "📈", "value": f"{decision['confidence']:.0%}",
             "label": "Confidence"},
        ])
        risk = decision["risk"]
        st.markdown(
            f"<div class='panel' style='border-left:6px solid {_RISK_COLORS[risk]}'>"
            f"<b>Risk level:</b> <span style='color:{_RISK_COLORS[risk]};font-weight:800'>"
            f"{risk}</span></div>", unsafe_allow_html=True)
    with right:
        st.plotly_chart(probability_gauge(decision["probability"]),
                        use_container_width=True)

    # --- Model comparison + feature importance --------------------------- #
    section("How each model voted")
    cc1, cc2 = st.columns([1.1, 1])
    with cc1:
        show = comparison[["Model", "Prediction", "Disease Probability", "Confidence"]].copy()
        show["Disease Probability"] = show["Disease Probability"].map(lambda v: f"{v:.1%}")
        show["Confidence"] = show["Confidence"].map(lambda v: f"{v:.1%}")
        df_table(show)
    with cc2:
        st.plotly_chart(model_comparison_bar(comparison), use_container_width=True)

    # Feature importance from the best model (if available).
    best_key = mgr.best_model_key()
    fi = mgr.metrics.get("models", {}).get(best_key, {}).get("feature_importance", {})
    if fi:
        section(f"Feature importance — {mgr.metrics['models'][best_key]['name']}")
        st.plotly_chart(feature_importance_bar(fi), use_container_width=True)

    # --- Persist to history ---------------------------------------------- #
    append_record({
        "source": "tabular",
        "prediction": decision["text"],
        "probability": round(decision["probability"], 4),
        "confidence": round(decision["confidence"], 4),
        "risk": decision["risk"],
        "best_model": mgr.metrics.get("models", {}).get(best_key, {}).get("name", ""),
        "age": form["Age"],
        "gender": form["Gender"],
        "details": form["_patient_id"] or "",
    })
    st.toast("Prediction saved to history ✅")

    # --- PDF download ----------------------------------------------------- #
    section("Export")
    try:
        pdf_bytes = build_prediction_pdf(
            decision, form, comparison, patient_id=form["_patient_id"] or None)
        st.download_button(
            "⬇️ Download prediction report (PDF)",
            data=pdf_bytes,
            file_name=f"liver_report_{int(time.time())}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
    except Exception as exc:  # pragma: no cover
        st.warning(f"Could not generate PDF report: {exc}")
