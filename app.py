"""
app.py
======
BioMed AI Nexus — Streamlit entry-point.

Responsibilities:
    * configure the page + inject the theme (light / dark toggle),
    * load & cache the dataset and the trained ModelManager,
    * render a styled sidebar and route to the selected page module.

Run with:
    streamlit run app.py
"""
from __future__ import annotations

import streamlit as st

from config import (
    APP_ICON, APP_SUBTITLE, APP_TITLE, AUTHOR_PROGRAM, MODEL_REGISTRY,
)
from pages import about, dashboard, evaluation, home, image_analysis, prediction
from utils.logger import get_logger
from utils.models import ModelManager
from utils.preprocessing import load_raw_dataset
from utils.styles import inject_css

log = get_logger("app")

st.set_page_config(
    page_title=f"{APP_TITLE} — {APP_SUBTITLE}",
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

# Sidebar navigation registry: label -> (icon, render fn).
PAGES = {
    "Home": ("🏠", home.render),
    "Liver Disease Prediction": ("🔬", prediction.render),
    "Image Analysis": ("🖼️", image_analysis.render),
    "Model Evaluation": ("📊", evaluation.render),
    "Dashboard": ("📈", dashboard.render),
    "About": ("ℹ️", about.render),
}


@st.cache_resource(show_spinner="Loading trained models…")
def get_manager() -> ModelManager:
    """Load the persisted models + preprocessor once per server process."""
    return ModelManager().load()


@st.cache_data(show_spinner=False)
def get_dataset():
    """Load + cache the ILPD dataset (used by Home / Dashboard)."""
    try:
        return load_raw_dataset()
    except FileNotFoundError as exc:
        log.error("Dataset missing: %s", exc)
        return None


def _sidebar() -> str:
    with st.sidebar:
        st.markdown(
            f"<div style='text-align:center;padding:.4rem 0 0'>"
            f"<div style='font-size:2.6rem'>{APP_ICON}</div>"
            f"<div style='font-weight:800;font-size:1.25rem'>{APP_TITLE}</div>"
            f"<div style='font-size:.8rem;opacity:.7'>{APP_SUBTITLE}</div></div>",
            unsafe_allow_html=True,
        )
        st.divider()
        choice = st.radio(
            "Navigation",
            list(PAGES.keys()),
            format_func=lambda k: f"{PAGES[k][0]}  {k}",
            label_visibility="collapsed",
        )
        st.divider()
        dark = st.toggle("🌙 Dark mode", value=True)
        st.caption(f"Models loaded: {len(get_manager().estimators)}/{len(MODEL_REGISTRY)}")
        st.caption(f"👤 {AUTHOR_PROGRAM}")
        return choice, dark  # type: ignore[return-value]


def main() -> None:
    choice, dark = _sidebar()
    inject_css(dark=dark)

    ctx = {
        "manager": get_manager(),
        "dataset": get_dataset(),
        "dark": dark,
    }

    # The Home/Dashboard pages need the dataset; guard gracefully.
    if ctx["dataset"] is None and choice in ("Home",):
        st.error("Dataset not found. Run `python data/load_data.py` first.")
        return

    try:
        PAGES[choice][1](ctx)
    except Exception as exc:  # pragma: no cover - top-level safety net
        log.exception("Page '%s' crashed", choice)
        st.error(f"An unexpected error occurred on this page: {exc}")
        st.caption("Check `logs/app.log` for the full traceback.")


if __name__ == "__main__":
    main()
