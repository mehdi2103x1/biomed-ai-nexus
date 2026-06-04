"""
pages.dashboard
===============
Analytics dashboard over the prediction history.

KPIs (total predictions, positive/negative cases, average confidence) plus four
interactive charts (pie, bar, line, distribution) and the full sortable history
table. History is persisted in ``data/historical_predictions.csv``.
"""
from __future__ import annotations

import streamlit as st

from utils.history import clear_history, history_kpis, load_history
from utils.styles import hero, render_kpis
from utils.visualization import (
    confidence_distribution, history_outcome_bar, history_timeline,
)


def render(ctx: dict) -> None:
    hero("Analytics Dashboard",
         "Live overview of every prediction made on this platform")

    history = load_history()
    kpis = history_kpis(history)

    render_kpis([
        {"icon": "🧮", "value": f"{kpis['total']}", "label": "Total predictions"},
        {"icon": "🩸", "value": f"{kpis['positive']}", "label": "Positive (disease)"},
        {"icon": "✅", "value": f"{kpis['negative']}", "label": "Negative (healthy)"},
        {"icon": "📈", "value": f"{kpis['avg_confidence']:.0%}",
         "label": "Avg confidence"},
    ])

    if history.empty:
        st.info("No predictions recorded yet. Make a prediction on the "
                "**Liver Disease Prediction** or **Image Analysis** page — it will "
                "appear here automatically.")
        return

    # --- Charts ----------------------------------------------------------- #
    st.write("")
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(history_outcome_bar(history), use_container_width=True)
    with c2:
        st.plotly_chart(confidence_distribution(history), use_container_width=True)

    c3, c4 = st.columns([1.4, 1])
    with c3:
        st.plotly_chart(history_timeline(history), use_container_width=True)
    with c4:
        # Pie of prediction sources (tabular vs image).
        import plotly.express as px
        src = history["source"].value_counts()
        fig = px.pie(names=src.index, values=src.values, hole=0.5,
                     title="Prediction sources")
        fig.update_layout(template="plotly_dark", height=340,
                          paper_bgcolor="rgba(0,0,0,0)",
                          margin=dict(l=10, r=10, t=50, b=10))
        st.plotly_chart(fig, use_container_width=True)

    # --- History table ---------------------------------------------------- #
    st.markdown("#### 🗂️ Prediction history")
    view = history.copy()
    if "timestamp" in view.columns:
        view = view.sort_values("timestamp", ascending=False)
    st.dataframe(view, use_container_width=True, hide_index=True)

    cdl, cclr = st.columns([1, 1])
    with cdl:
        st.download_button(
            "⬇️ Export history (CSV)",
            data=history.to_csv(index=False).encode("utf-8"),
            file_name="historical_predictions.csv",
            mime="text/csv", use_container_width=True,
        )
    with cclr:
        if st.button("🗑️ Clear history", use_container_width=True):
            clear_history()
            st.rerun()
