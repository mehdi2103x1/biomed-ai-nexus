"""
utils.styles
============
Centralised CSS injection, theme handling (light / dark) and small HTML
component helpers (KPI cards, hero banner, pills). Keeping the markup here keeps
the page modules focused on logic.
"""
from __future__ import annotations

import streamlit as st

from config import ACCENT_COLOR, PRIMARY_COLOR

# Two palettes toggled by the sidebar dark-mode switch.
THEMES = {
    "dark": {
        "bg": "#0e1117", "panel": "#161b26", "panel2": "#1f2633",
        "text": "#e6edf3", "muted": "#9aa7b4", "border": "#2a3344",
    },
    "light": {
        "bg": "#f6f8fb", "panel": "#ffffff", "panel2": "#eef2f7",
        "text": "#1a2233", "muted": "#5b6776", "border": "#dde4ee",
    },
}


def inject_css(dark: bool = True) -> None:
    """Inject the global stylesheet, parameterised by the active theme."""
    t = THEMES["dark"] if dark else THEMES["light"]
    st.markdown(
        f"""
        <style>
        .stApp {{
            background:
              radial-gradient(1200px 600px at 100% -10%, {ACCENT_COLOR}22, transparent 60%),
              radial-gradient(1000px 500px at -10% 110%, {PRIMARY_COLOR}22, transparent 55%),
              {t['bg']};
            color: {t['text']};
        }}
        #MainMenu, footer {{visibility: hidden;}}
        section[data-testid="stSidebar"] {{
            background: {t['panel']};
            border-right: 1px solid {t['border']};
        }}
        .hero {{
            background: linear-gradient(120deg, {PRIMARY_COLOR}, {ACCENT_COLOR});
            padding: 2.1rem 2rem; border-radius: 18px; color: white;
            box-shadow: 0 14px 40px rgba(0,0,0,.28); margin-bottom: 1.3rem;
        }}
        .hero h1 {{margin: 0; font-size: 2.0rem; font-weight: 800; letter-spacing:-.5px;}}
        .hero p  {{margin:.4rem 0 0; opacity:.95; font-size:1.02rem;}}
        .kpi {{
            background: {t['panel']}; border: 1px solid {t['border']};
            border-radius: 14px; padding: 1.05rem 1.15rem; height: 100%;
            transition: transform .15s ease, box-shadow .15s ease;
        }}
        .kpi:hover {{transform: translateY(-3px); box-shadow: 0 10px 26px rgba(0,0,0,.25);}}
        .kpi .k-ico {{font-size: 1.6rem;}}
        .kpi .k-val {{font-size: 1.7rem; font-weight: 800; margin:.15rem 0; color:{t['text']};}}
        .kpi .k-lab {{font-size:.82rem; color:{t['muted']}; text-transform:uppercase; letter-spacing:.4px;}}
        .kpi .k-sub {{font-size:.78rem; color:{PRIMARY_COLOR}; margin-top:.2rem;}}
        .panel {{
            background:{t['panel']}; border:1px solid {t['border']};
            border-radius:14px; padding:1.2rem 1.3rem; margin-bottom:1rem;
        }}
        .pill {{
            display:inline-block; padding:.28rem .7rem; border-radius:999px;
            font-size:.78rem; font-weight:600; margin:.18rem;
            background:{ACCENT_COLOR}22; color:{t['text']}; border:1px solid {ACCENT_COLOR}55;
        }}
        .result-card {{
            border-radius:16px; padding:1.5rem; text-align:center; color:white;
            box-shadow:0 12px 34px rgba(0,0,0,.3);
        }}
        .stButton>button {{
            border-radius:10px; font-weight:600; border:0;
            background:linear-gradient(120deg,{PRIMARY_COLOR},{ACCENT_COLOR}); color:white;
        }}
        .stButton>button:hover {{filter:brightness(1.08);}}
        .stTabs [data-baseweb="tab-list"] {{gap:6px;}}
        @keyframes fadeUp {{from{{opacity:0;transform:translateY(10px);}}to{{opacity:1;transform:none;}}}}
        .hero, .kpi, .panel {{animation: fadeUp .45s ease both;}}
        </style>
        """,
        unsafe_allow_html=True,
    )


def hero(title: str, subtitle: str) -> None:
    """Render the gradient hero banner."""
    st.markdown(
        f"<div class='hero'><h1>{title}</h1><p>{subtitle}</p></div>",
        unsafe_allow_html=True,
    )


def kpi_card(icon: str, value: str, label: str, sub: str = "") -> str:
    """Return the HTML for one KPI card (use inside an ``st.columns`` cell)."""
    sub_html = f"<div class='k-sub'>{sub}</div>" if sub else ""
    return (
        f"<div class='kpi'><div class='k-ico'>{icon}</div>"
        f"<div class='k-val'>{value}</div>"
        f"<div class='k-lab'>{label}</div>{sub_html}</div>"
    )


def render_kpis(cards: list[dict]) -> None:
    """Lay out a list of KPI dicts ({icon,value,label,sub}) in equal columns."""
    cols = st.columns(len(cards))
    for col, c in zip(cols, cards):
        with col:
            st.markdown(
                kpi_card(c["icon"], c["value"], c["label"], c.get("sub", "")),
                unsafe_allow_html=True,
            )


def pills(items: list[str]) -> None:
    st.markdown("".join(f"<span class='pill'>{i}</span>" for i in items),
                unsafe_allow_html=True)
