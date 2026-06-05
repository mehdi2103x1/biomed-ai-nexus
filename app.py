"""
app.py
======
HepatoScope — Streamlit entry-point.

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
    APP_ICON, APP_SUBTITLE, APP_TITLE, AUTHOR_BYLINE, AUTHOR_PROGRAM, MODEL_REGISTRY,
)
from pages import about, dashboard, evaluation, home, prediction
from utils.logger import get_logger
from utils.models import ModelManager
from utils.preprocessing import load_raw_dataset
from utils.styles import inject_css
from utils import visualization

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
            f"<div style='display:flex;align-items:center;gap:.7rem;padding:.2rem 0 .1rem'>"
            f"<div style='font-size:2rem;line-height:1'>{APP_ICON}</div>"
            f"<div><div style=\"font-family:'Spectral',serif;font-weight:700;"
            f"font-size:1.34rem;line-height:1.05;letter-spacing:-.01em\">{APP_TITLE}</div>"
            f"<div style='font-size:.72rem;color:var(--muted);letter-spacing:.02em'>"
            f"{AUTHOR_BYLINE}</div></div></div>",
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
        n_loaded = len(get_manager().estimators)
        st.markdown(
            f"<div style='font-size:.74rem;color:var(--muted);line-height:1.7'>"
            f"<span style='color:var(--primary)'>●</span> {n_loaded}/{len(MODEL_REGISTRY)} "
            f"models loaded<br>{AUTHOR_PROGRAM}</div>",
            unsafe_allow_html=True,
        )
        return choice


def main() -> None:
    choice = _sidebar()
    inject_css(dark=True)
    visualization.set_theme(False)   # light (cream) chart theme

    ctx = {
        "manager": get_manager(),
        "dataset": get_dataset(),
        "dark": True,
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
