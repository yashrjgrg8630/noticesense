"""
dashboard.py – NoticeSense Phase 3
Professional dashboard with card-based agent output.
"""

import sys, os
from pathlib import Path
project_root = str(Path(__file__).parent.parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import streamlit as st
from frontend.styles import inject_global_css, page_header


def _badge(days):
    if days is None:
        return ""
    if days < 0:
        return f'<span class="ns-badge ns-badge-red">⚠ {abs(days)}d overdue</span>'
    if days == 0:
        return '<span class="ns-badge ns-badge-red">⚠ Due Today</span>'
    if days <= 7:
        return f'<span class="ns-badge ns-badge-orange">⏰ {days}d left</span>'
    if days <= 30:
        return f'<span class="ns-badge ns-badge-orange">📅 {days}d left</span>'
    return f'<span class="ns-badge ns-badge-green">✓ {days}d left</span>'


def show_dashboard():
    inject_global_css()
    page_header("📊", "Notice Dashboard",
                "AI-extracted insights from your uploaded notice.")

    agent_results  = st.session_state.get("agent_results")
    structured     = st.session_state.get("structured_data", {})

    if not agent_results:
        st.markdown("""
        <div style="text-align:center;padding:56px 0;color:#475569">
            <div style="font-size:44px">📊</div>
            <div style="font-size:15px;font-weight:600;margin-top:12px;color:#64748b">
                No analysis yet
            </div>
            <div style="font-size:13px;margin-top:6px">
                Upload a notice from the Home page first.
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    # ── Metadata strip ────────────────────────────────────────────────────────
    doc_type = structured.get("document_type","—")
    issuer   = structured.get("issuing_authority") or structured.get("issuer","—") or "—"
    ref_no   = structured.get("reference_number","—") or "—"
    doc_date = structured.get("date","—") or "—"

    c1, c2, c3, c4 = st.columns(4)
    for col, label, val in [(c1,"Type",doc_type),(c2,"Issuer",issuer),
                             (c3,"Reference",ref_no),(c4,"Notice Date",doc_date)]:
        col.metric(label, val)

    st.markdown("<hr class='ns-divider'>", unsafe_allow_html=True)

    # ── Section 1: Intent ─────────────────────────────────────────────────────
    intent = agent_results.get("intent", {})
    st.markdown("""
    <div style="font-size:11px;font-weight:700;letter-spacing:.8px;color:#7c6af7;margin-bottom:10px">
        📌 &nbsp;SUMMARY &amp; INTENT
    </div>
    """, unsafe_allow_html=True)

    notice_type = intent.get("notice_type","Unknown")
    summary     = intent.get("summary","No summary available.")

    st.markdown(f"""
    <div class="ns-card ns-card-purple">
        <div style="margin-bottom:10px">
            <span class="ns-badge ns-badge-purple">{notice_type}</span>
        </div>
        <div class="ns-card-value">{summary}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr class='ns-divider'>", unsafe_allow_html=True)

    # ── Section 2: Deadlines ──────────────────────────────────────────────────
    deadline = agent_results.get("deadline", {})
    st.markdown("""
    <div style="font-size:11px;font-weight:700;letter-spacing:.8px;color:#f97316;margin-bottom:10px">
        ⏳ &nbsp;REQUIRED DEADLINES
    </div>
    """, unsafe_allow_html=True)

    if deadline.get("has_deadline") and deadline.get("deadlines"):
        for item in deadline["deadlines"]:
            days = item.get("days_remaining")
            badge = _badge(days)
            st.markdown(f"""
            <div class="ns-deadline">
                <div>
                    <div class="ns-deadline-label">{item.get('label','Deadline')}</div>
                    <div class="ns-deadline-date">📅 &nbsp;{item.get('date','')}</div>
                </div>
                <div>{badge}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        msg = deadline.get("no_deadline_message","No deadline mentioned in the notice.")
        st.markdown(f"""
        <div class="ns-card" style="border-left:4px solid #22c55e;text-align:center;color:#4ade80;padding:18px">
            ✓ &nbsp;{msg}
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr class='ns-divider'>", unsafe_allow_html=True)

    # ── Section 3: Action Items ───────────────────────────────────────────────
    action = agent_results.get("action", {})
    st.markdown("""
    <div style="font-size:11px;font-weight:700;letter-spacing:.8px;color:#22c55e;margin-bottom:10px">
        ✅ &nbsp;ACTION ITEMS
    </div>
    """, unsafe_allow_html=True)

    actions = action.get("actions", [])
    if actions:
        for i, act in enumerate(actions, 1):
            st.markdown(f"""
            <div class="ns-step">
                <div class="ns-step-num">{i}</div>
                <div class="ns-step-text">{act}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="ns-card" style="color:#94a3b8;text-align:center">
            No specific actions identified.
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr class='ns-divider'>", unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align:center;font-size:13px;color:#334155;padding:4px">
        💬 &nbsp;Head to <b>Chat</b> to ask questions about this notice
    </div>
    """, unsafe_allow_html=True)
