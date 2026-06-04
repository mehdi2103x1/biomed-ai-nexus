"""
utils.pdf_report
================
Generate a one-page PDF prediction report (downloadable from the app).

Uses ``fpdf2`` (pure-python, no system dependencies) so it works on any
deployment target. The public :func:`build_prediction_pdf` returns raw bytes
ready for ``st.download_button``.
"""
from __future__ import annotations

from datetime import datetime
from typing import Mapping

import pandas as pd
from fpdf import FPDF

from config import APP_SUBTITLE, APP_TITLE, AUTHOR_PROGRAM, FEATURE_META, PRIMARY_COLOR
from utils.logger import get_logger

log = get_logger("pdf_report")


def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


# The built-in Helvetica font is latin-1 only. Map the few unicode characters we
# use (and anything exotic in a free-text patient id) down to safe equivalents.
_UNICODE_MAP = {
    "—": "-", "–": "-", "…": "...", "‘": "'", "’": "'",
    "“": '"', "”": '"', " ": " ",
}


def _s(text: object) -> str:
    """Return a latin-1-safe string for fpdf2's core fonts."""
    s = str(text)
    for bad, good in _UNICODE_MAP.items():
        s = s.replace(bad, good)
    return s.encode("latin-1", "replace").decode("latin-1")


class _ReportPDF(FPDF):
    """FPDF subclass with a branded header and footer."""

    def header(self) -> None:
        r, g, b = _hex_to_rgb(PRIMARY_COLOR)
        self.set_fill_color(r, g, b)
        self.rect(0, 0, self.w, 22, "F")
        self.set_xy(10, 6)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 16)
        self.cell(0, 8, _s(APP_TITLE), ln=1)
        self.set_x(10)
        self.set_font("Helvetica", "", 10)
        self.cell(0, 5, _s(f"{APP_SUBTITLE} - Prediction Report"))
        self.set_text_color(0, 0, 0)
        self.ln(16)

    def footer(self) -> None:
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, _s(
                  f"{AUTHOR_PROGRAM}  |  Generated {datetime.now():%Y-%m-%d %H:%M}  |  "
                  f"Page {self.page_no()}"), align="C")


def _section(pdf: _ReportPDF, title: str) -> None:
    pdf.set_font("Helvetica", "B", 12)
    r, g, b = _hex_to_rgb(PRIMARY_COLOR)
    pdf.set_text_color(r, g, b)
    pdf.cell(0, 8, _s(title), ln=1)
    pdf.set_text_color(0, 0, 0)
    pdf.set_draw_color(220, 220, 220)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(2)


def build_prediction_pdf(
    decision: Mapping,
    form: Mapping[str, float | str],
    comparison: pd.DataFrame,
    patient_id: str | None = None,
) -> bytes:
    """Render the prediction PDF and return it as ``bytes``.

    Parameters
    ----------
    decision : Mapping
        Output of :meth:`ModelManager.ensemble_decision`.
    form : Mapping
        The raw patient inputs.
    comparison : DataFrame
        Per-model comparison frame from :meth:`ModelManager.predict_all`.
    patient_id : str, optional
        Free-text identifier printed on the report.
    """
    pdf = _ReportPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    # ---- Patient / meta ------------------------------------------------- #
    _section(pdf, "1. Summary")
    pdf.set_font("Helvetica", "", 10)
    pid = patient_id or "—"
    is_disease = decision["label"] == 1
    rr, gg, bb = (220, 38, 38) if is_disease else (16, 150, 100)
    pdf.cell(40, 7, "Patient ID:", 0); pdf.cell(0, 7, _s(pid), ln=1)
    pdf.cell(40, 7, "Date:", 0); pdf.cell(0, 7, f"{datetime.now():%Y-%m-%d %H:%M}", ln=1)

    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(rr, gg, bb)
    pdf.cell(40, 9, "Result:", 0)
    pdf.cell(0, 9, _s(f"{decision['text']}  (risk: {decision['risk']})"), ln=1)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, _s(f"Disease probability: {decision['probability']:.1%}    "
                      f"Confidence: {decision['confidence']:.1%}    "
                      f"{decision['agreement']}"), ln=1)
    pdf.ln(3)

    # ---- Inputs --------------------------------------------------------- #
    _section(pdf, "2. Biological & Clinical Inputs")
    pdf.set_font("Helvetica", "", 9)
    col_w = (pdf.w - pdf.l_margin - pdf.r_margin) / 2
    items = list(FEATURE_META.keys())
    for i in range(0, len(items), 2):
        for j in range(2):
            if i + j < len(items):
                key = items[i + j]
                meta = FEATURE_META[key]
                val = form.get(key, "—")
                unit = meta.get("unit", "")
                pdf.set_font("Helvetica", "B", 9)
                pdf.cell(col_w * 0.55, 6, _s(f"{meta['label']}:"), 0)
                pdf.set_font("Helvetica", "", 9)
                pdf.cell(col_w * 0.45, 6, _s(f"{val} {unit}".strip()), 0)
        pdf.ln(6)
    pdf.ln(2)

    # ---- Model comparison ---------------------------------------------- #
    _section(pdf, "3. Model Comparison")
    pdf.set_font("Helvetica", "B", 9)
    headers = ["Model", "Prediction", "Disease Prob.", "Confidence"]
    widths = [55, 50, 40, 40]
    pdf.set_fill_color(*_hex_to_rgb(PRIMARY_COLOR))
    pdf.set_text_color(255, 255, 255)
    for hcell, w in zip(headers, widths):
        pdf.cell(w, 7, hcell, 1, 0, "C", fill=True)
    pdf.ln(7)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 9)
    for _, row in comparison.iterrows():
        pdf.cell(widths[0], 7, _s(row["Model"]), 1)
        pdf.cell(widths[1], 7, _s(row["Prediction"]), 1, 0, "C")
        pdf.cell(widths[2], 7, f"{row['Disease Probability']:.1%}", 1, 0, "C")
        pdf.cell(widths[3], 7, f"{row['Confidence']:.1%}", 1, 0, "C")
        pdf.ln(7)
    pdf.ln(4)

    # ---- Disclaimer ----------------------------------------------------- #
    _section(pdf, "4. Disclaimer")
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(0, 5,
        "This report is generated by an academic machine-learning prototype "
        f"({APP_TITLE}) trained on a public liver-patient dataset. "
        "It is a decision-support demonstration and must NOT be used for actual "
        "clinical diagnosis. Always consult a qualified healthcare professional.")

    out = pdf.output()
    log.info("PDF report generated (%d bytes)", len(bytes(out)))
    return bytes(out)
