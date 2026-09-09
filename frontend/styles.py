"""
Shared CSS styles for NoticeSense UI.
Import and call inject_global_css() in every page.
"""

GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── Reset & Base ─────────────────────────────────────────── */
html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }

.main .block-container {
    padding-top: 1.5rem;
    padding-bottom: 3rem;
    max-width: 1100px;
}

/* ── Sidebar ──────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0a0a14 0%, #0f0f1e 100%) !important;
    border-right: 1px solid rgba(124,106,247,0.15);
}
[data-testid="stSidebar"] .stRadio label {
    color: #94a3b8 !important;
    font-size: 14px;
    padding: 6px 0;
    transition: color .2s;
}
[data-testid="stSidebar"] .stRadio label:hover { color: #c4b5fd !important; }

/* ── Gradient page header ─────────────────────────────────── */
.ns-header {
    background: linear-gradient(135deg, #1a1040 0%, #0d1b2a 100%);
    border: 1px solid rgba(124,106,247,0.25);
    border-radius: 16px;
    padding: 32px 36px 28px;
    margin-bottom: 28px;
    position: relative;
    overflow: hidden;
}
.ns-header::before {
    content: '';
    position: absolute; top: -60px; right: -60px;
    width: 220px; height: 220px;
    background: radial-gradient(circle, rgba(124,106,247,0.18) 0%, transparent 70%);
    border-radius: 50%;
}
.ns-header h1 {
    font-size: 28px !important; font-weight: 800 !important;
    background: linear-gradient(90deg, #a78bfa, #60a5fa);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin: 0 0 6px !important;
}
.ns-header p { color: #94a3b8; margin: 0; font-size: 15px; }

/* ── Cards ────────────────────────────────────────────────── */
.ns-card {
    background: #111827;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px;
    padding: 22px 26px;
    margin-bottom: 16px;
    transition: border-color .25s, box-shadow .25s;
}
.ns-card:hover {
    border-color: rgba(124,106,247,0.35);
    box-shadow: 0 4px 24px rgba(124,106,247,0.10);
}
.ns-card-purple { border-left: 4px solid #7c6af7; }
.ns-card-orange { border-left: 4px solid #f97316; }
.ns-card-green  { border-left: 4px solid #22c55e; }
.ns-card-blue   { border-left: 4px solid #38bdf8; }

.ns-card-title {
    font-size: 13px; font-weight: 600; letter-spacing: .8px;
    text-transform: uppercase; color: #64748b; margin-bottom: 8px;
}
.ns-card-value {
    font-size: 15px; color: #e2e8f0; line-height: 1.6;
}

/* ── Pill badge ───────────────────────────────────────────── */
.ns-badge {
    display: inline-block;
    padding: 3px 12px; border-radius: 999px;
    font-size: 12px; font-weight: 600; letter-spacing: .4px;
}
.ns-badge-purple { background: rgba(124,106,247,0.18); color: #a78bfa; }
.ns-badge-green  { background: rgba(34,197,94,0.15);  color: #4ade80; }
.ns-badge-orange { background: rgba(249,115,22,0.15); color: #fb923c; }
.ns-badge-red    { background: rgba(239,68,68,0.15);  color: #f87171; }

/* ── Action step ─────────────────────────────────────────── */
.ns-step {
    display: flex; gap: 14px; align-items: flex-start;
    background: rgba(17,24,39,0.8);
    border: 1px solid rgba(34,197,94,0.2);
    border-radius: 10px; padding: 12px 16px; margin-bottom: 10px;
}
.ns-step-num {
    min-width: 28px; height: 28px; border-radius: 50%;
    background: rgba(34,197,94,0.15); color: #4ade80;
    font-size: 12px; font-weight: 700;
    display: flex; align-items: center; justify-content: center;
}
.ns-step-text { color: #cbd5e1; font-size: 14px; line-height: 1.6; padding-top: 3px; }

/* ── Deadline row ────────────────────────────────────────── */
.ns-deadline {
    background: rgba(249,115,22,0.07);
    border: 1px solid rgba(249,115,22,0.2);
    border-radius: 10px; padding: 14px 18px; margin-bottom: 10px;
    display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;
}
.ns-deadline-label { color: #94a3b8; font-size: 13px; font-weight: 500; }
.ns-deadline-date  { color: #fbd38d; font-size: 14px; font-weight: 600; }

/* ── Divider ─────────────────────────────────────────────── */
.ns-divider {
    border: none; border-top: 1px solid rgba(255,255,255,0.07);
    margin: 20px 0;
}

/* ── Upload zone ─────────────────────────────────────────── */
[data-testid="stFileUploader"] {
    background: rgba(124,106,247,0.05) !important;
    border: 2px dashed rgba(124,106,247,0.3) !important;
    border-radius: 12px !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: rgba(124,106,247,0.6) !important;
    background: rgba(124,106,247,0.08) !important;
}

/* ── Buttons ─────────────────────────────────────────────── */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #7c6af7, #6366f1) !important;
    border: none !important; border-radius: 10px !important;
    font-weight: 600 !important; letter-spacing: .3px !important;
    transition: opacity .2s, transform .15s !important;
}
.stButton > button[kind="primary"]:hover {
    opacity: .88 !important; transform: translateY(-1px) !important;
}

/* ── Chat bubbles ────────────────────────────────────────── */
[data-testid="stChatMessage"] {
    background: #111827 !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 12px !important;
}

/* ── Metric cards ────────────────────────────────────────── */
[data-testid="stMetric"] {
    background: #111827;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 12px; padding: 14px 18px !important;
}
[data-testid="stMetricLabel"] { color: #64748b !important; font-size: 12px !important; }
[data-testid="stMetricValue"] { color: #e2e8f0 !important; font-size: 15px !important; }

/* ── Status/spinner ──────────────────────────────────────── */
[data-testid="stStatusWidget"] {
    background: #111827 !important;
    border: 1px solid rgba(124,106,247,0.2) !important;
    border-radius: 12px !important;
}

/* ── Hide default hamburger & footer ─────────────────────── */
#MainMenu, footer { visibility: hidden; }
</style>
"""

def inject_global_css():
    import streamlit as st
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


def page_header(icon: str, title: str, subtitle: str = ""):
    import streamlit as st
    st.markdown(f"""
    <div class="ns-header">
        <h1>{icon} {title}</h1>
        {"<p>" + subtitle + "</p>" if subtitle else ""}
    </div>
    """, unsafe_allow_html=True)
