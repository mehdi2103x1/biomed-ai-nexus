"""
utils.visualization
====================
Reusable Plotly figure builders.

Every function returns a ``plotly.graph_objects.Figure`` so the pages stay thin
(``st.plotly_chart(fig, use_container_width=True)``). Colours come from
:mod:`config` to keep the whole app on one palette.
"""
from __future__ import annotations

from typing import Mapping, Sequence

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from config import ACCENT_COLOR, CLASS_NAMES, DANGER_COLOR, OK_COLOR, PRIMARY_COLOR

_DISEASE_COLOR = DANGER_COLOR
_HEALTHY_COLOR = OK_COLOR

# Charts are drawn on a transparent background and inherit the active app theme.
# ``set_theme`` (called by app.py each run) picks font/grid colours that read
# well on either the dark or the light canvas.
_THEME = {
    "template": "plotly_dark",
    "font": "#cbd5e1",
    "grid": "rgba(148,163,184,.16)",
}
_FONT_FAMILY = "Hanken Grotesk, -apple-system, sans-serif"


def set_theme(dark: bool = True) -> None:
    """Update the module-level chart theme to match the app (dark/light)."""
    if dark:
        _THEME.update(template="plotly_dark", font="#cbd5e1",
                      grid="rgba(148,163,184,.16)")
    else:  # warm light (Claude cream) theme
        _THEME.update(template="plotly_white", font="#57534e",
                      grid="rgba(120,113,100,.16)")


def _base_layout(fig: go.Figure, title: str = "", height: int = 380) -> go.Figure:
    fig.update_layout(
        title=dict(text=title, font=dict(size=15, family=_FONT_FAMILY)),
        template=_THEME["template"],
        height=height,
        margin=dict(l=10, r=10, t=50 if title else 20, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(size=13, family=_FONT_FAMILY, color=_THEME["font"]),
        colorway=[PRIMARY_COLOR, ACCENT_COLOR, "#6aa9ff", DANGER_COLOR,
                  "#e0a82e", "#9b8cff"],
    )
    fig.update_xaxes(gridcolor=_THEME["grid"], zerolinecolor=_THEME["grid"])
    fig.update_yaxes(gridcolor=_THEME["grid"], zerolinecolor=_THEME["grid"])
    return fig


# --------------------------------------------------------------------------- #
# Prediction page
# --------------------------------------------------------------------------- #
def probability_gauge(proba: float, title: str = "Disease Probability") -> go.Figure:
    """Speedometer-style gauge for the final disease probability."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=proba * 100,
        number={"suffix": " %"},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": _DISEASE_COLOR},
            "steps": [
                {"range": [0, 25],  "color": "#064e3b"},
                {"range": [25, 50], "color": "#854d0e"},
                {"range": [50, 75], "color": "#7c2d12"},
                {"range": [75, 100],"color": "#7f1d1d"},
            ],
            "threshold": {"line": {"color": "white", "width": 3},
                          "thickness": 0.75, "value": 50},
        },
        title={"text": title},
    ))
    return _base_layout(fig, height=300)


def model_comparison_bar(comparison: pd.DataFrame) -> go.Figure:
    """Per-model disease-probability bar chart."""
    fig = px.bar(
        comparison.sort_values("Disease Probability"),
        x="Disease Probability", y="Model", orientation="h",
        color="Disease Probability", color_continuous_scale="RdYlGn_r",
        range_x=[0, 1], text=comparison.sort_values("Disease Probability")
        ["Disease Probability"].map(lambda v: f"{v:.0%}"),
    )
    fig.update_traces(textposition="outside")
    return _base_layout(fig, "Per-model disease probability")


def feature_importance_bar(importance: Mapping[str, float], top: int = 10) -> go.Figure:
    """Horizontal bar chart of the most influential features."""
    s = pd.Series(importance).sort_values(ascending=True).tail(top)
    fig = px.bar(
        x=s.values, y=[k.replace("_", " ") for k in s.index],
        orientation="h", color=s.values, color_continuous_scale="Tealgrn",
    )
    fig.update_layout(coloraxis_showscale=False,
                      xaxis_title="Importance", yaxis_title="")
    return _base_layout(fig, "Feature importance")


# --------------------------------------------------------------------------- #
# Evaluation page
# --------------------------------------------------------------------------- #
def roc_curves(models: Mapping[str, dict]) -> go.Figure:
    """Overlay ROC curves of every model on one axis."""
    fig = go.Figure()
    for m in models.values():
        roc = m["roc"]
        fig.add_trace(go.Scatter(
            x=roc["fpr"], y=roc["tpr"], mode="lines",
            name=f"{m['name']} (AUC={roc['auc']:.3f})",
        ))
    fig.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode="lines",
                             line=dict(dash="dash", color="grey"),
                             name="Chance", showlegend=False))
    fig.update_layout(xaxis_title="False Positive Rate",
                      yaxis_title="True Positive Rate",
                      legend=dict(x=0.5, y=0.05))
    return _base_layout(fig, "ROC curves", height=460)


def confusion_heatmap(matrix: Sequence[Sequence[int]], name: str = "") -> go.Figure:
    """Annotated confusion-matrix heatmap."""
    z = np.array(matrix)
    labels = ["No Disease", "Disease"]
    fig = px.imshow(
        z, x=labels, y=labels, text_auto=True,
        color_continuous_scale="Blues",
        labels=dict(x="Predicted", y="Actual", color="Count"),
    )
    fig.update_coloraxes(showscale=False)
    return _base_layout(fig, f"Confusion matrix — {name}".strip(" —"), height=360)


def metrics_grouped_bar(models: Mapping[str, dict]) -> go.Figure:
    """Grouped bar chart comparing accuracy/precision/recall/F1/AUC."""
    metrics = ["accuracy", "precision", "recall", "f1", "auc"]
    fig = go.Figure()
    for metric in metrics:
        fig.add_trace(go.Bar(
            name=metric.upper(),
            x=[m["name"] for m in models.values()],
            y=[m["metrics"][metric] for m in models.values()],
        ))
    fig.update_layout(barmode="group", yaxis=dict(range=[0, 1]),
                      yaxis_title="Score", legend_title="Metric")
    return _base_layout(fig, "Model performance comparison", height=440)


def training_time_bar(models: Mapping[str, dict]) -> go.Figure:
    """Bar chart of (tuning + fit) wall-clock time per model."""
    names = [m["name"] for m in models.values()]
    times = [m["train_time"] for m in models.values()]
    fig = px.bar(x=names, y=times, color=times, color_continuous_scale="Sunsetdark")
    fig.update_layout(coloraxis_showscale=False,
                      xaxis_title="", yaxis_title="Seconds")
    return _base_layout(fig, "Training time", height=340)


# --------------------------------------------------------------------------- #
# Dashboard page
# --------------------------------------------------------------------------- #
def class_distribution_pie(n_disease: int, n_healthy: int) -> go.Figure:
    fig = px.pie(
        names=[CLASS_NAMES[1], CLASS_NAMES[0]],
        values=[n_disease, n_healthy], hole=0.5,
        color_discrete_sequence=[_DISEASE_COLOR, _HEALTHY_COLOR],
    )
    fig.update_traces(textinfo="percent+label")
    return _base_layout(fig, "Class distribution", height=360)


def history_timeline(history: pd.DataFrame) -> go.Figure:
    """Line chart of predictions over time (count + mean confidence)."""
    if history.empty:
        return _base_layout(go.Figure(), "Predictions over time", height=340)
    h = history.copy()
    h["date"] = pd.to_datetime(h["timestamp"]).dt.date
    daily = h.groupby("date").agg(count=("prediction", "size"),
                                  confidence=("confidence", "mean")).reset_index()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=daily["date"], y=daily["count"], mode="lines+markers",
                             name="Predictions", line=dict(color=ACCENT_COLOR)))
    fig.add_trace(go.Scatter(x=daily["date"], y=daily["confidence"] * daily["count"].max(),
                             mode="lines", name="Avg confidence (scaled)",
                             line=dict(color=PRIMARY_COLOR, dash="dot")))
    fig.update_layout(xaxis_title="Date", yaxis_title="Count")
    return _base_layout(fig, "Predictions over time", height=340)


def history_outcome_bar(history: pd.DataFrame) -> go.Figure:
    if history.empty:
        return _base_layout(go.Figure(), "Predicted outcomes", height=340)
    counts = history["prediction"].value_counts()
    fig = px.bar(x=counts.index, y=counts.values,
                 color=counts.index,
                 color_discrete_map={CLASS_NAMES[1]: _DISEASE_COLOR,
                                     CLASS_NAMES[0]: _HEALTHY_COLOR})
    fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="Count")
    return _base_layout(fig, "Predicted outcomes", height=340)


def confidence_distribution(history: pd.DataFrame) -> go.Figure:
    if history.empty:
        return _base_layout(go.Figure(), "Confidence distribution", height=340)
    fig = px.histogram(history, x="confidence", nbins=20,
                       color_discrete_sequence=[ACCENT_COLOR])
    fig.update_layout(xaxis_title="Confidence", yaxis_title="Count",
                      xaxis=dict(range=[0, 1]))
    return _base_layout(fig, "Confidence distribution", height=340)
