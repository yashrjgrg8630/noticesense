"""
about.py – NoticeSense
Professional About page — product-focused, no academic references.
"""

import sys
from pathlib import Path
project_root = str(Path(__file__).parent.parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import streamlit as st
from frontend.styles import inject_global_css, page_header


def show_about():
    inject_global_css()
    page_header("ℹ️", "About NoticeSense",
                "AI-powered platform for understanding official notices instantly.")

    # ── What is NoticeSense ───────────────────────────────────────────────────
    st.markdown("""
    <div class="ns-card ns-card-purple" style="padding:24px 28px">
        <div class="ns-card-title">What is NoticeSense?</div>
        <div class="ns-card-value" style="margin-top:10px">
            NoticeSense is an intelligent document analysis platform that uses
            <b>Agentic AI</b> and <b>OCR technology</b> to instantly break down
            official notices — legal, regulatory, tax, compliance, and more —
            into clear summaries, deadlines, and actionable steps.
            <br><br>
            Instead of spending hours reading dense regulatory language,
            NoticeSense gives you the key information in seconds.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr class='ns-divider'>", unsafe_allow_html=True)

    # ── How it works ──────────────────────────────────────────────────────────
    st.markdown("""
    <div style="font-size:11px;font-weight:700;letter-spacing:.8px;color:#7c6af7;margin-bottom:14px">
        ⚙️ &nbsp;HOW IT WORKS
    </div>
    """, unsafe_allow_html=True)

    steps = [
        ("📤", "Upload",    "Drop in any PDF or image of an official notice"),
        ("🔍", "OCR",       "Tesseract OCR extracts and cleans the full text"),
        ("🧩", "Parse",     "Structured fields (issuer, date, reference) are identified"),
        ("🤖", "AI Agents", "Three specialised agents analyse the notice in parallel"),
        ("📊", "Dashboard", "Results rendered as clear cards — summary, deadlines, actions"),
        ("💬", "Chat",      "Ask follow-up questions grounded in the actual notice"),
    ]

    for i, (icon, title, desc) in enumerate(steps):
        col_icon, col_content = st.columns([1, 10])
        with col_icon:
            st.markdown(f"""
            <div style="width:42px;height:42px;background:rgba(124,106,247,0.15);
                        border-radius:10px;display:flex;align-items:center;
                        justify-content:center;font-size:20px;margin-top:4px">
                {icon}
            </div>
            """, unsafe_allow_html=True)
        with col_content:
            st.markdown(f"""
            <div style="padding-bottom:4px">
                <b style="color:#c4b5fd">{title}</b>
                <span style="color:#64748b;font-size:12px;margin-left:8px">Step {i+1}</span>
                <div style="color:#94a3b8;font-size:13px;margin-top:2px">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<hr class='ns-divider'>", unsafe_allow_html=True)

    # ── The Three Agents ──────────────────────────────────────────────────────
    st.markdown("""
    <div style="font-size:11px;font-weight:700;letter-spacing:.8px;color:#7c6af7;margin-bottom:14px">
        🧠 &nbsp;THE THREE AI AGENTS
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    agents = [
        (c1, "📌", "Intent Agent", "#7c6af7",
         ["Identifies notice type", "Generates plain-language summary", "Classifies issuer and recipient"]),
        (c2, "⏳", "Deadline Agent", "#f97316",
         ["Extracts all key dates", "Detects compliance deadlines", "Calculates days remaining"]),
        (c3, "✅", "Action Agent", "#22c55e",
         ["Converts notice to action steps", "Prioritises by urgency", "Written in plain language"]),
    ]
    for col, icon, name, color, points in agents:
        with col:
            bullets = "".join(f"<li style='color:#94a3b8;font-size:13px;margin-bottom:4px'>{p}</li>"
                              for p in points)
            st.markdown(f"""
            <div class="ns-card" style="border-top:4px solid {color};height:100%">
                <div style="font-size:22px;margin-bottom:8px">{icon}</div>
                <div style="font-weight:700;color:#e2e8f0;margin-bottom:10px">{name}</div>
                <ul style="margin:0;padding-left:18px">{bullets}</ul>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<hr class='ns-divider'>", unsafe_allow_html=True)

    # ── Guardrails ────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="font-size:11px;font-weight:700;letter-spacing:.8px;color:#7c6af7;margin-bottom:14px">
        🛡️ &nbsp;AI GUARDRAILS
    </div>
    <div class="ns-card ns-card-blue">
        <div class="ns-card-value">
            <ul style="margin:0;padding-left:20px;line-height:2">
                <li>Agents only use information explicitly present in the notice</li>
                <li>Deadlines are never invented — only extracted from the text</li>
                <li>No legal advice is provided — users are guided to seek professional help</li>
                <li>If information is missing, agents clearly state so</li>
            </ul>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr class='ns-divider'>", unsafe_allow_html=True)

    # ── Roadmap ───────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="font-size:11px;font-weight:700;letter-spacing:.8px;color:#7c6af7;margin-bottom:14px">
        🔭 &nbsp;ROADMAP
    </div>
    """, unsafe_allow_html=True)

    roadmap = [
        ("🔍", "RAG Support",         "Query across multiple notices using vector databases"),
        ("🗄️", "Persistent Storage",  "PostgreSQL backend for notice history and audit trail"),
        ("🔔", "Deadline Reminders",   "Automated email/SMS alerts before critical dates"),
        ("👥", "Multi-user Access",    "Team workspaces, role-based permissions"),
    ]
    for icon, title, desc in roadmap:
        st.markdown(f"""
        <div class="ns-card" style="display:flex;gap:16px;align-items:center;
                                    padding:14px 18px;margin-bottom:8px">
            <div style="font-size:22px">{icon}</div>
            <div>
                <div style="color:#c4b5fd;font-weight:600;font-size:14px">{title}</div>
                <div style="color:#64748b;font-size:13px;margin-top:2px">{desc}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
