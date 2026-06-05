"""
utils.styles
============
The visual design system for HepatoScope.

Aesthetic direction — *refined clinical instrument*:
  * a calm deep-slate canvas (dark) or warm clinical paper (light), never neon;
  * a single trustworthy **teal** accent with clear clinical semantics
    (teal = healthy, amber/red = risk);
  * a premium serif display face (**Spectral**) for headings paired with a
    technical sans (**IBM Plex Sans**) for body and **IBM Plex Mono** for the
    numeric read-outs — a scientific, considered pairing, not generic AI sans;
  * subtle grain + a single soft glow for depth instead of loud gradients;
  * restrained, staggered load motion.

All markup helpers (hero, KPI cards, pills, result card, section header) live
here so the page modules stay focused on logic.
"""
from __future__ import annotations

import streamlit as st

from config import APP_TITLE, AUTHOR_BYLINE

# Claude-inspired warm theme: ivory/cream canvas, terracotta accent, charcoal
# text. Every component reads from these CSS custom properties.
_THEME_COLORS = {
    "bg": "#faf9f5", "bg2": "#f2efe6", "surface": "#ffffff", "surface2": "#f6f4ec",
    "border": "#e7e3d6", "border_soft": "#efece1",
    "text": "#2b2a26", "muted": "#73716a", "faint": "#a8a59a",
    "primary": "#cc785c", "primary_deep": "#b8623f", "primary_soft": "rgba(204,120,92,.12)",
    "danger": "#bd4636", "danger_soft": "rgba(189,70,54,.10)",
    "ok": "#5b8266", "warn": "#b7791f", "high": "#c97a3c",
    "shadow": "0 16px 38px -26px rgba(70,55,40,.28)",
    "glow": "rgba(204,120,92,.10)",
}

# A faint SVG grain overlay for premium depth (data-URI, no external request).
_GRAIN = (
    "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' "
    "width='160' height='160'%3E%3Cfilter id='n'%3E%3CfeTurbulence "
    "type='fractalNoise' baseFrequency='0.85' numOctaves='2'/%3E%3C/filter%3E"
    "%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.5'/"
    "%3E%3C/svg%3E\")"
)


def inject_css(dark: bool = True) -> None:
    """Inject the full stylesheet (Claude-inspired warm theme)."""
    t = _THEME_COLORS
    grain_opacity = ".018"
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=Hanken+Grotesk:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

        :root {{
          --bg:{t['bg']}; --bg2:{t['bg2']}; --surface:{t['surface']}; --surface2:{t['surface2']};
          --border:{t['border']}; --border-soft:{t['border_soft']};
          --text:{t['text']}; --muted:{t['muted']}; --faint:{t['faint']};
          --primary:{t['primary']}; --primary-deep:{t['primary_deep']}; --primary-soft:{t['primary_soft']};
          --danger:{t['danger']}; --danger-soft:{t['danger_soft']};
          --ok:{t['ok']}; --warn:{t['warn']}; --high:{t['high']};
          --shadow:{t['shadow']}; --glow:{t['glow']};
          --serif:'Fraunces',Georgia,serif;
          --sans:'Hanken Grotesk',-apple-system,sans-serif;
          --mono:'IBM Plex Mono',ui-monospace,monospace;
          --r:14px;
        }}

        /* ---------- Canvas ---------- */
        .stApp {{
          background:
            radial-gradient(820px 480px at 92% -10%, var(--glow), transparent 55%),
            var(--bg);
          color: var(--text);
          font-family: var(--sans);
        }}
        .stApp::before {{
          content:""; position:fixed; inset:0; pointer-events:none; z-index:0;
          background-image:{_GRAIN}; background-size:160px; opacity:{grain_opacity};
        }}
        .block-container {{ padding-top: 1.4rem; padding-bottom: 3rem; max-width: 1180px; }}
        /* hide Streamlit chrome: main menu, footer, status, Deploy button AND the
           sidebar collapse/expand controls — the sidebar is permanently open, so it
           can never get stuck closed. */
        #MainMenu, footer, [data-testid="stStatusWidget"],
        [data-testid="stToolbar"], [data-testid="stDeployButton"],
        .stDeployButton, [data-testid="stToolbarActions"],
        [data-testid="stSidebarCollapseButton"],
        [data-testid="stSidebarCollapsedControl"],
        [data-testid="collapsedControl"] {{ display: none !important; }}
        [data-testid="stHeader"] {{ background: transparent; height: 0; }}
        /* force the sidebar to stay visible even if a previous session collapsed it */
        section[data-testid="stSidebar"] {{
          transform: none !important; visibility: visible !important;
          margin-left: 0 !important;
          width: 17rem !important; min-width: 17rem !important;
        }}
        section[data-testid="stSidebar"][aria-expanded="false"] {{
          transform: none !important; margin-left: 0 !important;
        }}

        /* equal-height cards: stretch columns so KPI/cards align on a row */
        [data-testid="stHorizontalBlock"] {{ align-items: stretch; }}
        [data-testid="stHorizontalBlock"] > [data-testid="column"] {{ display: flex; flex-direction: column; }}
        [data-testid="stHorizontalBlock"] > [data-testid="column"] > div {{ height: 100%; }}

        /* ---------- Typography ---------- */
        h1, h2, h3, h4 {{ font-family: var(--serif); letter-spacing:-.01em; color: var(--text); font-weight:600; }}
        .stApp p, .stApp li, .stApp label {{ font-family: var(--sans); }}
        /* never override Material icon fonts (otherwise icons leak their ligature text) */
        [data-testid="stIconMaterial"], .material-icons,
        [class*="material-symbols"], span[translate="no"] {{
          font-family: 'Material Symbols Rounded','Material Symbols Outlined','Material Icons' !important;
        }}
        .block-container h2 {{ font-size:1.5rem; margin-top:.4rem; }}
        .block-container h3 {{ font-size:1.18rem; }}
        a {{ color: var(--primary); text-decoration: none; }}

        /* ---------- Sidebar (clean, full-width; native collapse arrow works) ---------- */
        section[data-testid="stSidebar"] {{
          background: linear-gradient(180deg, var(--surface), var(--bg2));
          border-right: 1px solid var(--border);
        }}
        section[data-testid="stSidebar"] .block-container {{ padding-top: 1.4rem; }}
        section[data-testid="stSidebar"] hr {{ border-color: var(--border-soft); }}
        /* sidebar radio nav -> menu items */
        section[data-testid="stSidebar"] [role="radiogroup"] label {{
          display:flex; align-items:center; gap:.5rem; padding:.5rem .7rem; margin:.12rem 0;
          border-radius:10px; cursor:pointer; border:1px solid transparent;
          font-weight:500; color: var(--muted); transition: all .15s ease;
        }}
        section[data-testid="stSidebar"] [role="radiogroup"] label:hover {{
          background: var(--primary-soft); color: var(--text);
        }}
        section[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {{
          background: var(--primary-soft); color: var(--text);
          border-color: color-mix(in srgb, var(--primary) 45%, transparent);
        }}
        section[data-testid="stSidebar"] [role="radiogroup"] [data-baseweb="radio"] > div:first-child {{ display:none; }}

        /* ---------- Buttons ---------- */
        .stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {{
          font-family: var(--sans); font-weight:600; border-radius:11px;
          border:1px solid var(--primary); background: var(--primary); color:#fdfbf7;
          padding:.5rem 1.1rem; transition: all .16s ease; box-shadow: 0 8px 20px -12px var(--primary);
        }}
        .stButton > button:hover, .stDownloadButton > button:hover, .stFormSubmitButton > button:hover {{
          background: var(--primary-deep); border-color: var(--primary-deep);
          transform: translateY(-1px);
        }}
        .stButton > button:focus {{ box-shadow: 0 0 0 3px var(--primary-soft) !important; }}

        /* ---------- Inputs ---------- */
        [data-testid="stForm"] {{
          background: var(--surface); border:1px solid var(--border);
          border-radius:18px; padding:1.4rem 1.5rem; box-shadow: var(--shadow);
        }}
        .stNumberInput input, .stTextInput input, .stTextArea textarea,
        [data-baseweb="select"] > div {{
          background: var(--surface2) !important; border:1px solid var(--border) !important;
          border-radius:10px !important; color: var(--text) !important; font-family: var(--mono) !important;
        }}
        .stNumberInput input:focus, .stTextInput input:focus {{
          border-color: var(--primary) !important; box-shadow: 0 0 0 3px var(--primary-soft) !important;
        }}
        .stSlider [data-baseweb="slider"] [role="slider"] {{ background: var(--primary) !important; }}
        .stSlider [data-baseweb="slider"] > div > div {{ background: var(--primary) !important; }}
        label, .stRadio label, .stSelectbox label {{ color: var(--muted) !important; font-weight:500; }}

        /* ---------- Tabs / expander / dataframe ---------- */
        .stTabs [data-baseweb="tab-list"] {{ gap:4px; border-bottom:1px solid var(--border); }}
        .stTabs [data-baseweb="tab"] {{ color: var(--muted); font-weight:600; }}
        .stTabs [aria-selected="true"] {{ color: var(--primary) !important; }}
        [data-testid="stExpander"] {{ border:1px solid var(--border); border-radius:12px; background: var(--surface); }}
        [data-testid="stDataFrame"] {{ border:1px solid var(--border); border-radius:12px; overflow:hidden; }}
        [data-testid="stMetric"] {{ background: var(--surface); border:1px solid var(--border);
          border-radius:var(--r); padding:1rem 1.1rem; }}
        .stAlert {{ border-radius:12px; border:1px solid var(--border); }}

        /* ---------- Hero ---------- */
        .hero {{
          position:relative; z-index:1; background: var(--surface);
          border:1px solid var(--border); border-radius:20px;
          padding:1.9rem 2rem 1.7rem; margin-bottom:1.5rem; overflow:hidden;
          box-shadow: var(--shadow);
        }}
        .hero::after {{
          content:""; position:absolute; right:-60px; top:-80px; width:260px; height:260px;
          background: radial-gradient(circle, var(--glow), transparent 70%); pointer-events:none;
        }}
        .hero .eyebrow {{
          font-family: var(--mono); font-size:.72rem; letter-spacing:.22em; text-transform:uppercase;
          color: var(--primary); font-weight:600; margin-bottom:.55rem;
        }}
        .hero h1 {{ font-size:2.15rem; line-height:1.08; margin:0; font-weight:700; }}
        .hero .accent {{ width:54px; height:3px; background: var(--primary); border-radius:2px; margin:.85rem 0 .8rem; }}
        .hero p {{ margin:0; color: var(--muted); font-size:1.02rem; max-width:60ch; }}

        /* ---------- KPI cards ---------- */
        .kpi {{
          position:relative; z-index:1; background: var(--surface); border:1px solid var(--border);
          border-radius:var(--r); padding:1.05rem 1.15rem .95rem; height:100%; overflow:hidden;
          transition: transform .16s ease, border-color .16s ease;
        }}
        .kpi::before {{ content:""; position:absolute; left:0; top:0; bottom:0; width:3px; background: var(--primary); opacity:.85; }}
        .kpi:hover {{ transform: translateY(-3px); border-color: color-mix(in srgb, var(--primary) 40%, var(--border)); }}
        .kpi .k-ico {{ font-size:1.15rem; opacity:.9; }}
        .kpi .k-val {{ font-family: var(--mono); font-size:1.62rem; font-weight:600; color: var(--text); margin:.12rem 0; line-height:1.1; }}
        .kpi .k-lab {{ font-size:.72rem; color: var(--muted); text-transform:uppercase; letter-spacing:.09em; font-weight:600; }}
        .kpi .k-sub {{ font-size:.76rem; color: var(--primary); margin-top:.22rem; font-weight:500; }}

        /* ---------- Panels, pills, result card ---------- */
        .panel {{ position:relative; z-index:1; background: var(--surface); border:1px solid var(--border);
          border-radius:var(--r); padding:1.15rem 1.3rem; margin-bottom:1rem; }}
        .panel b {{ color: var(--text); }}
        .pill {{ display:inline-block; padding:.3rem .8rem; border-radius:999px; font-size:.76rem; font-weight:600;
          margin:.2rem .18rem; background: var(--primary-soft); color: var(--text);
          border:1px solid color-mix(in srgb, var(--primary) 35%, transparent); font-family: var(--mono); }}
        .dx {{ position:relative; z-index:1; border-radius:18px; padding:1.5rem 1.4rem; text-align:center;
          background: var(--surface); border:1px solid var(--border); box-shadow: var(--shadow); }}
        .dx.pos {{ border-color: color-mix(in srgb, var(--danger) 55%, var(--border)); background:
          linear-gradient(180deg, var(--danger-soft), var(--surface)); }}
        .dx.neg {{ border-color: color-mix(in srgb, var(--ok) 55%, var(--border)); background:
          linear-gradient(180deg, color-mix(in srgb, var(--ok) 12%, transparent), var(--surface)); }}
        .dx .dx-ico {{ font-size:2.1rem; }}
        .dx .dx-title {{ font-family: var(--serif); font-size:1.55rem; font-weight:700; margin:.2rem 0 .15rem; }}
        .dx.pos .dx-title {{ color: var(--danger); }}
        .dx.neg .dx-title {{ color: var(--ok); }}
        .dx .dx-sub {{ color: var(--muted); font-size:.86rem; }}

        /* ---------- Section eyebrow header ---------- */
        .sec {{ display:flex; align-items:center; gap:.6rem; margin:1.6rem 0 .4rem; }}
        .sec .bar {{ width:4px; height:20px; background: var(--primary); border-radius:2px; }}
        .sec .t {{ font-family: var(--serif); font-size:1.28rem; font-weight:600; color: var(--text); }}

        /* ---------- Motion ---------- */
        @keyframes rise {{ from {{ opacity:0; transform: translateY(12px); }} to {{ opacity:1; transform:none; }} }}
        .hero {{ animation: rise .5s ease both; }}
        .kpi {{ animation: rise .5s ease both; }}
        .kpi:nth-child(1){{animation-delay:.04s}} .kpi:nth-child(2){{animation-delay:.10s}}
        .kpi:nth-child(3){{animation-delay:.16s}} .kpi:nth-child(4){{animation-delay:.22s}}
        @media (prefers-reduced-motion: reduce) {{ .hero,.kpi {{ animation:none; }} }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------------- #
# Markup helpers
# --------------------------------------------------------------------------- #
def hero(title: str, subtitle: str, eyebrow: str | None = None) -> None:
    """Refined header band: eyebrow · serif title · accent rule · subtitle.

    The eyebrow defaults to the product name + author byline, so the branding
    and authorship appear (small) on every page.
    """
    if eyebrow is None:
        eyebrow = f"{APP_TITLE} · {AUTHOR_BYLINE}"
    st.markdown(
        f"<div class='hero'><div class='eyebrow'>{eyebrow}</div>"
        f"<h1>{title}</h1><div class='accent'></div><p>{subtitle}</p></div>",
        unsafe_allow_html=True,
    )


def section(title: str) -> None:
    """A small section header (accent bar + serif title)."""
    st.markdown(
        f"<div class='sec'><div class='bar'></div><div class='t'>{title}</div></div>",
        unsafe_allow_html=True,
    )


def kpi_card(icon: str, value: str, label: str, sub: str = "") -> str:
    """Return the HTML for one KPI card (place inside an ``st.columns`` cell)."""
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


def result_card(icon: str, title: str, subtitle: str, positive: bool) -> None:
    """The big diagnosis card used on the prediction page."""
    cls = "pos" if positive else "neg"
    st.markdown(
        f"<div class='dx {cls}'><div class='dx-ico'>{icon}</div>"
        f"<div class='dx-title'>{title}</div><div class='dx-sub'>{subtitle}</div></div>",
        unsafe_allow_html=True,
    )


def pills(items: list[str]) -> None:
    st.markdown("".join(f"<span class='pill'>{i}</span>" for i in items),
                unsafe_allow_html=True)
