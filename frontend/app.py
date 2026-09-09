import sys
import os
from pathlib import Path

project_root = str(Path(__file__).parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import streamlit as st
from backend.utils.file_utils import save_upload_file, clean_upload_dir
from backend.services.ocr_service import process_document
from backend.services.parsing_service import process_and_structure_document
from backend.router.agent_router import run_agents
from frontend.pages.dashboard import show_dashboard
from frontend.pages.chat import show_chat
from frontend.pages.about import show_about
from frontend.styles import inject_global_css

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NoticeSense",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_global_css()

# ── Hide sidebar + default header, inject navbar CSS ─────────────────────────
st.markdown("""
<style>
/* Hide sidebar entirely */
[data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }

/* Pull content to the very top */
.main .block-container {
    padding-top: 0 !important;
    padding-left: 2.5rem !important;
    padding-right: 2.5rem !important;
    max-width: 1200px !important;
}

/* ── Top Navbar ── */
.ns-navbar {
    position: sticky;
    top: 0;
    z-index: 999;
    background: rgba(10,10,20,0.92);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border-bottom: 1px solid rgba(124,106,247,0.18);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 28px;
    height: 60px;
    margin-bottom: 28px;
    margin-left: -2.5rem;
    margin-right: -2.5rem;
}
.ns-logo {
    font-size: 17px;
    font-weight: 800;
    letter-spacing: .4px;
    background: linear-gradient(90deg,#a78bfa,#60a5fa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    display: flex; align-items: center; gap: 8px;
}
.ns-navlinks {
    display: flex; gap: 4px; align-items: center;
}
.ns-navbtn {
    background: transparent !important;
    border: none !important;
    color: #64748b !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 6px 16px !important;
    border-radius: 8px !important;
    cursor: pointer;
    transition: background .2s, color .2s;
    white-space: nowrap;
    letter-spacing: .2px;
}
.ns-navbtn:hover { background: rgba(124,106,247,0.12) !important; color: #c4b5fd !important; }
.ns-navbtn.active {
    background: rgba(124,106,247,0.18) !important;
    color: #a78bfa !important;
    font-weight: 600 !important;
}
.ns-nav-status {
    font-size: 11px; color: #334155;
    display: flex; gap: 12px; align-items: center;
}
.ns-dot { width:7px; height:7px; border-radius:50%; display:inline-block; margin-right:5px; }
</style>
""", unsafe_allow_html=True)

# ── Session defaults ───────────────────────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state.page = "Home"

# ── Navigation bar ─────────────────────────────────────────────────────────────
has_notice  = bool(st.session_state.get("cleaned_text"))
has_results = bool(st.session_state.get("agent_results"))

# Render the static HTML shell of the navbar
st.markdown(f"""
<div class="ns-navbar">
    <div class="ns-logo">📄 NoticeSense</div>
    <div class="ns-navlinks" id="navlinks"></div>
    <div class="ns-nav-status">
        <span>
            <span class="ns-dot" style="background:{'#4ade80' if has_notice else '#1e293b'}"></span>
            Notice
        </span>
        <span>
            <span class="ns-dot" style="background:{'#4ade80' if has_results else '#1e293b'}"></span>
            Analysis
        </span>
    </div>
</div>
""", unsafe_allow_html=True)

# Streamlit buttons for navigation (placed in a hidden-looking row just below navbar)
st.markdown("""
<style>
div[data-testid="stHorizontalBlock"]:has(> div > div > button.nav-pill) {
    position: sticky; top: 60px; z-index: 998;
    background: rgba(10,10,20,0.92);
    backdrop-filter: blur(14px);
    padding: 0 28px 0;
    margin: -28px -2.5rem 20px;
}
/* Style nav buttons */
div.stButton > button {
    background: transparent !important;
    border: 1px solid transparent !important;
    color: #64748b !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    border-radius: 8px !important;
    padding: 5px 14px !important;
    width: 100%;
    transition: all .2s;
}
div.stButton > button:hover {
    background: rgba(124,106,247,0.12) !important;
    color: #c4b5fd !important;
    border-color: rgba(124,106,247,0.25) !important;
}
</style>
""", unsafe_allow_html=True)

pages = ["🏠  Home", "📊  Dashboard", "💬  Chat", "ℹ️  About"]
page_keys = ["Home", "Dashboard", "Chat", "About"]

# Render navigation horizontally using columns that fill the top
nav_cols = st.columns([1, 1, 1, 1, 4])      # 4 nav + spacer
for i, (label, key) in enumerate(zip(pages, page_keys)):
    is_active = st.session_state.page == key
    # Highlight active button with a CSS override
    active_style = f"""
    <style>
    div[data-testid="column"]:nth-of-type({i+1}) div.stButton > button {{
        background: {'rgba(124,106,247,0.18)' if is_active else 'transparent'} !important;
        color: {'#a78bfa' if is_active else '#64748b'} !important;
        font-weight: {'700' if is_active else '500'} !important;
        border-color: {'rgba(124,106,247,0.3)' if is_active else 'transparent'} !important;
    }}
    </style>
    """ if is_active else ""
    st.markdown(active_style, unsafe_allow_html=True)

    with nav_cols[i]:
        if st.button(label, key=f"nav_{key}", use_container_width=True):
            st.session_state.page = key
            st.rerun()

st.markdown("<hr style='border-color:rgba(255,255,255,0.06);margin:4px 0 24px'>",
            unsafe_allow_html=True)

# ── Clear session button (top-right-ish via last column) ─────────────────────
with nav_cols[4]:
    ccol, _ = st.columns([1, 2])
    with ccol:
        if st.button("⟳ Clear", key="nav_clear"):
            for k in ["cleaned_text","structured_data","agent_results","chat_history"]:
                st.session_state.pop(k, None)
            st.session_state.page = "Home"
            st.rerun()

# ── Page content ─────────────────────────────────────────────────────────────
current = st.session_state.page

if current == "Home":
    from frontend.styles import page_header
    page_header("📄", "NoticeSense",
                "Upload any official notice — get instant AI analysis, deadlines & action steps.")

    st.markdown("""
    <div class="ns-card ns-card-purple" style="padding:20px 24px;margin-bottom:4px">
        <div class="ns-card-title">Upload Document</div>
        <div style="color:#64748b;font-size:13px">Supports PDF, PNG, JPG, JPEG</div>
    </div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Drop file here or click to browse",
        type=["pdf","png","jpg","jpeg"],
        label_visibility="collapsed",
    )

    if uploaded_file:
        st.markdown(f"""
        <div style="background:rgba(124,106,247,0.08);border:1px solid rgba(124,106,247,0.25);
                    border-radius:10px;padding:11px 16px;margin:10px 0;font-size:13px;color:#a78bfa">
            📎 &nbsp;<b>{uploaded_file.name}</b>
            <span style="color:#475569;margin-left:8px">({round(uploaded_file.size/1024,1)} KB)</span>
        </div>
        """, unsafe_allow_html=True)

        try:
            saved_path = save_upload_file(uploaded_file)
            if st.button("🚀 Extract & Analyse", type="primary", use_container_width=True):
                with st.status("Analysing your notice...", expanded=True) as status:
                    st.write("📄 Running OCR extraction…")
                    raw_text = process_document(saved_path)

                    if raw_text.startswith("Error"):
                        status.update(label="OCR failed", state="error"); st.error(raw_text); st.stop()

                    st.write("🧹 Cleaning and parsing text…")
                    structured_data, cleaned_text = process_and_structure_document(raw_text)
                    st.session_state["cleaned_text"]    = cleaned_text
                    st.session_state["structured_data"] = structured_data

                    st.write("🤖 Running AI agents…")
                    agent_results = run_agents(cleaned_text)

                    if agent_results.get("error"):
                        status.update(label="Agent error", state="error")
                        st.error(agent_results["error"]); st.stop()

                    st.session_state["agent_results"] = agent_results
                    st.session_state.pop("chat_history", None)
                    status.update(label="✅ Analysis complete!", state="complete")

                intent = agent_results.get("intent", {})
                st.markdown(f"""
                <div class="ns-card ns-card-green" style="margin-top:20px">
                    <div class="ns-card-title">Analysis Complete</div>
                    <span class="ns-badge ns-badge-purple" style="margin:8px 0;display:inline-block">
                        {intent.get('notice_type','Unknown')}
                    </span>
                    <div class="ns-card-value" style="margin-top:8px">{intent.get('summary','')}</div>
                </div>
                """, unsafe_allow_html=True)

                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("📊 View Dashboard", use_container_width=True):
                        st.session_state.page = "Dashboard"; st.rerun()
                with col_b:
                    if st.button("💬 Open Chat", use_container_width=True):
                        st.session_state.page = "Chat"; st.rerun()

        except Exception as e:
            st.error(f"Failed to process: {str(e)}")
    else:
        st.markdown("""
        <div style="text-align:center;padding:60px 20px;color:#334155">
            <div style="font-size:52px;margin-bottom:12px">📂</div>
            <div style="font-size:15px;font-weight:600;color:#475569">No document uploaded yet</div>
            <div style="font-size:13px;color:#334155;margin-top:6px">Upload a PDF or image to get started</div>
        </div>
        """, unsafe_allow_html=True)

elif current == "Dashboard":
    show_dashboard()
elif current == "Chat":
    show_chat()
elif current == "About":
    show_about()
