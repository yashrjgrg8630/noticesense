/* ================================================================
   app.js – NoticeSense SPA
   Handles: routing, file upload, agent results rendering, chat
   ================================================================ */

const API = '';               // same origin as FastAPI
let SESSION_ID = sessionStorage.getItem('ns_session') || null;
let SESSION_DATA = JSON.parse(sessionStorage.getItem('ns_data') || 'null');
let chatHistory  = [];

// ── Router ──────────────────────────────────────────────────────────────────
function navigate(page) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('page-' + page).classList.add('active');
  document.getElementById('nav-' + page).classList.add('active');
  window.scrollTo(0, 0);
  if (page === 'dashboard') renderDashboard();
  if (page === 'chat')      initChat();
}

// ── Session status dots ──────────────────────────────────────────────────────
function updateStatus() {
  document.getElementById('dot-notice').classList.toggle('active', !!SESSION_ID);
  document.getElementById('dot-analysis').classList.toggle('active', !!SESSION_DATA);
}

// ── HOME PAGE ────────────────────────────────────────────────────────────────
function initHome() {
  const zone     = document.getElementById('upload-zone');
  const input    = document.getElementById('file-input');
  const fileInfo = document.getElementById('file-info');
  const fileName = document.getElementById('file-name');
  const analyseBtn = document.getElementById('btn-analyse');
  const progress = document.getElementById('progress-box');

  let selectedFile = null;

  // Drag and drop
  zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('drag'); });
  zone.addEventListener('dragleave', () => zone.classList.remove('drag'));
  zone.addEventListener('drop', e => {
    e.preventDefault(); zone.classList.remove('drag');
    if (e.dataTransfer.files[0]) selectFile(e.dataTransfer.files[0]);
  });
  input.addEventListener('change', () => { if (input.files[0]) selectFile(input.files[0]); });

  function selectFile(f) {
    selectedFile = f;
    fileName.textContent = `📎 ${f.name}  (${(f.size/1024).toFixed(1)} KB)`;
    fileInfo.style.display = 'flex';
    analyseBtn.disabled = false;
  }

  analyseBtn.addEventListener('click', async () => {
    if (!selectedFile) return;
    analyseBtn.disabled = true;
    progress.style.display = 'block';

    const steps = ['step-ocr','step-parse','step-agents'];
    const labels = ['📄 Running OCR extraction…','🧹 Cleaning and parsing text…','🤖 Running AI agents…'];
    setStep(0);

    const form = new FormData();
    form.append('file', selectedFile);

    try {
      // Fake step progression while waiting
      let stepIdx = 0;
      const stepTimer = setInterval(() => {
        if (stepIdx < 2) { stepIdx++; setStep(stepIdx); }
      }, 1500);

      const res  = await fetch(`${API}/api/upload`, { method: 'POST', body: form });
      clearInterval(stepTimer);

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Upload failed');
      }

      const data = await res.json();
      SESSION_ID   = data.session_id;
      SESSION_DATA = data;
      chatHistory  = [];
      sessionStorage.setItem('ns_session', SESSION_ID);
      sessionStorage.setItem('ns_data', JSON.stringify(SESSION_DATA));
      updateStatus();

      // Mark all done
      steps.forEach(s => { const el = document.getElementById(s); el.classList.add('done'); el.classList.remove('active'); el.querySelector('.step-indicator').innerHTML = '✓'; });

      showResult(data);

    } catch (err) {
      progress.innerHTML += `<div class="alert error" style="margin-top:12px">⚠️ ${err.message}</div>`;
    }

    analyseBtn.disabled = false;
  });

  function setStep(i) {
    ['step-ocr','step-parse','step-agents'].forEach((s, idx) => {
      const el = document.getElementById(s);
      el.classList.remove('active','done');
      const ind = el.querySelector('.step-indicator');
      if (idx < i)       { el.classList.add('done');   ind.innerHTML = '✓'; }
      else if (idx === i) { el.classList.add('active'); ind.innerHTML = '<span class="spinner"></span>'; }
      else                { ind.innerHTML = '○'; }
    });
  }

  function showResult(data) {
    const intent = data.agent_results?.intent || {};
    const resultEl = document.getElementById('result-box');
    resultEl.innerHTML = `
      <div class="card green" style="margin-top:20px">
        <div class="card-label">Analysis Complete</div>
        <div style="margin:8px 0"><span class="badge purple">${intent.notice_type || 'Unknown'}</span></div>
        <div class="card-value">${intent.summary || ''}</div>
      </div>
      <div style="display:flex;gap:10px;margin-top:12px">
        <button class="btn btn-secondary" style="flex:1" onclick="navigate('dashboard')">View Dashboard</button>
        <button class="btn btn-secondary" style="flex:1" onclick="navigate('chat')">Open Chat</button>
      </div>`;
    resultEl.style.display = 'block';
  }
}

// ── DASHBOARD PAGE ───────────────────────────────────────────────────────────
function renderDashboard() {
  const el = document.getElementById('dashboard-content');
  if (!SESSION_DATA) {
    el.innerHTML = `<div class="empty"><div class="empty-icon">📊</div><div class="empty-title">No analysis yet</div><div class="empty-sub">Upload a notice from the Home page first.</div></div>`;
    return;
  }

  const { structured_data: s, agent_results: a, filename } = SESSION_DATA;
  const intent   = a?.intent   || {};
  const deadline = a?.deadline || {};
  const action   = a?.action   || {};

  // Metrics
  const metrics = [
    { label: 'Type',      val: s?.document_type || '—' },
    { label: 'Issuer',    val: s?.issuing_authority || s?.issuer || '—' },
    { label: 'Reference', val: s?.reference_number || '—' },
    { label: 'Date',      val: s?.date || '—' },
  ];

  let deadlineHtml = '';
  if (deadline.has_deadline && deadline.deadlines?.length) {
    deadlineHtml = deadline.deadlines.map(d => `
      <div class="deadline-row">
        <div><div class="deadline-label">${d.label}</div><div class="deadline-date">📅 ${d.date}</div></div>
        <div>${daysBadge(d.days_remaining)}</div>
      </div>`).join('');
  } else {
    deadlineHtml = `<div class="card green" style="text-align:center;color:#4ade80">✓ ${deadline.no_deadline_message || 'No deadline mentioned in the notice.'}</div>`;
  }

  const stepsHtml = (action.actions || []).map((a, i) => `
    <div class="step"><div class="step-num">${i+1}</div><div class="step-text">${a}</div></div>`).join('');

  el.innerHTML = `
    <div class="metrics">${metrics.map(m => `<div class="metric"><div class="metric-label">${m.label}</div><div class="metric-value" title="${m.val}">${m.val}</div></div>`).join('')}</div>
    <hr class="divider">
    <div class="section-title purple">Summary &amp; Intent</div>
    <div class="card purple">
      <div style="margin-bottom:10px"><span class="badge purple">${intent.notice_type || 'Unknown'}</span></div>
      <div class="card-value">${intent.summary || 'No summary available.'}</div>
    </div>
    <hr class="divider">
    <div class="section-title orange">Required Deadlines</div>
    ${deadlineHtml}
    <hr class="divider">
    <div class="section-title green">Action Items</div>
    ${stepsHtml || '<div class="card" style="color:#94a3b8;text-align:center">No specific actions identified.</div>'}`;
}

function daysBadge(days) {
  if (days == null) return '';
  if (days < 0)   return `<span class="badge red">⚠ ${Math.abs(days)}d overdue</span>`;
  if (days === 0) return `<span class="badge red">⚠ Due Today</span>`;
  if (days <= 7)  return `<span class="badge orange">⏰ ${days}d left</span>`;
  if (days <= 30) return `<span class="badge orange">📅 ${days}d left</span>`;
  return `<span class="badge green">✓ ${days}d left</span>`;
}

// ── CHAT PAGE ────────────────────────────────────────────────────────────────
function initChat() {
  const msgs    = document.getElementById('chat-messages');
  const input   = document.getElementById('chat-input');
  const sendBtn = document.getElementById('chat-send');
  const emptyEl = document.getElementById('chat-empty');
  const wrapEl  = document.getElementById('chat-main');

  if (!SESSION_ID) {
    emptyEl.style.display = 'block';
    wrapEl.style.display  = 'none';
    return;
  }
  emptyEl.style.display = 'none';
  wrapEl.style.display  = 'flex';

  // Re-render history
  msgs.innerHTML = '';
  chatHistory.forEach(m => appendBubble(m.role, m.content));

  async function send(text) {
    if (!text.trim() || !SESSION_ID) return;
    input.value = '';
    input.style.height = 'auto';
    sendBtn.disabled = true;
    appendBubble('user', text);
    chatHistory.push({ role: 'user', content: text });

    const thinking = appendBubble('assistant', '● ● ●', true);

    try {
      const res = await fetch(`${API}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: SESSION_ID, message: text, history: chatHistory.slice(0,-1) }),
      });
      const data = await res.json();
      const reply = data.reply || data.detail || 'No response.';
      thinking.remove();
      appendBubble('assistant', reply);
      chatHistory.push({ role: 'assistant', content: reply });
    } catch (e) {
      thinking.remove();
      appendBubble('assistant', `⚠️ Error: ${e.message}`);
    }
    sendBtn.disabled = false;
    msgs.scrollTop = msgs.scrollHeight;
  }

  sendBtn.onclick = () => send(input.value);
  input.addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(input.value); } });
  input.addEventListener('input', () => { input.style.height = 'auto'; input.style.height = input.scrollHeight + 'px'; });

  // Chip clicks
  document.querySelectorAll('#chat-page .chip').forEach(c => {
    c.addEventListener('click', () => send(c.textContent));
  });
}

function appendBubble(role, text, thinking = false) {
  const msgs = document.getElementById('chat-messages');
  const div = document.createElement('div');
  div.className = `chat-bubble ${role === 'user' ? 'bubble-user' : 'bubble-assistant'}${thinking ? ' bubble-thinking' : ''}`;
  div.textContent = text;
  msgs.appendChild(div);
  msgs.scrollTop = msgs.scrollHeight;
  return div;
}

// ── Init ────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initHome();
  updateStatus();
  navigate('home');
});
