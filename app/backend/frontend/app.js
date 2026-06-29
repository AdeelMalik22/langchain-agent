/* ──────────────────────────────────────────────────
   AgentAI Chat — app.js
   Handles: sidebar, auto-resize textarea, API calls,
            markdown rendering, auto-scroll.
────────────────────────────────────────────────── */

const CHAT_BASE = window.location.origin + '/chat';

// ── DOM refs ────────────────────────────────────────
const messagesEl    = document.getElementById('messages');
const messagesWrap  = document.getElementById('messagesWrap');
const chatForm      = document.getElementById('chatForm');
const messageInput  = document.getElementById('messageInput');
const sendBtn       = document.getElementById('sendBtn');
const welcomeScreen = document.getElementById('welcomeScreen');
const sidebarEl     = document.getElementById('sidebar');
const sidebarToggle = document.getElementById('sidebarToggle');
const menuBtn       = document.getElementById('menuBtn');
const newChatBtn    = document.getElementById('newChatBtn');
const clearBtn      = document.getElementById('clearBtn');
const statusPill    = document.getElementById('statusPill');
const statusText    = document.getElementById('statusText');

// ── State ────────────────────────────────────────────
let isLoading  = false;
let msgCount   = 0;

// ── Sidebar ──────────────────────────────────────────
let sidebarOpen = window.innerWidth > 768;

function setSidebar(open) {
  sidebarOpen = open;
  sidebarEl.classList.toggle('collapsed', !open);
  // Mobile overlay
  let overlay = document.querySelector('.overlay');
  if (!overlay) {
    overlay = document.createElement('div');
    overlay.className = 'overlay';
    document.body.appendChild(overlay);
    overlay.addEventListener('click', () => setSidebar(false));
  }
  overlay.classList.toggle('active', open && window.innerWidth <= 768);
}

setSidebar(sidebarOpen);

sidebarToggle.addEventListener('click', () => setSidebar(false));
menuBtn.addEventListener('click', () => setSidebar(!sidebarOpen));

window.addEventListener('resize', () => {
  if (window.innerWidth > 768 && !sidebarOpen) setSidebar(true);
});

// ── Health check / status ────────────────────────────
async function checkHealth() {
  try {
    const res = await fetch(`${CHAT_BASE}/health`);
    const data = await res.json();
    if (data.agent_ready) {
      statusPill.classList.add('online');
      statusText.textContent = 'Agent online';
    } else {
      statusText.textContent = 'Agent starting…';
      setTimeout(checkHealth, 3000);
    }
  } catch {
    statusText.textContent = 'Offline';
    setTimeout(checkHealth, 5000);
  }
}
checkHealth();

// ── Auto-resize textarea ─────────────────────────────
messageInput.addEventListener('input', () => {
  messageInput.style.height = 'auto';
  messageInput.style.height = Math.min(messageInput.scrollHeight, 200) + 'px';
});

messageInput.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    if (!isLoading) submitMessage();
  }
});

// ── Quick prompt buttons ─────────────────────────────
document.querySelectorAll('.quick-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const prompt = btn.dataset.prompt;
    if (prompt) {
      messageInput.value = prompt;
      messageInput.dispatchEvent(new Event('input'));
      submitMessage();
    }
  });
});

// ── New chat / clear ─────────────────────────────────
function clearChat() {
  msgCount = 0;
  messagesEl.innerHTML = '';
  messagesEl.appendChild(welcomeScreen);
  welcomeScreen.style.display = '';
}

newChatBtn.addEventListener('click', clearChat);
clearBtn.addEventListener('click',   clearChat);

// ── Form submit ──────────────────────────────────────
chatForm.addEventListener('submit', e => {
  e.preventDefault();
  if (!isLoading) submitMessage();
});

async function submitMessage() {
  const text = messageInput.value.trim();
  if (!text) return;

  hideWelcome();
  appendUserMessage(text);

  messageInput.value = '';
  messageInput.style.height = 'auto';

  setLoading(true);
  const thinkingRow = appendThinking();

  try {
    const res = await fetch(`${CHAT_BASE}/message`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Server error' }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }

    const data = await res.json();
    thinkingRow.remove();

    if (data.blocked) {
      appendAgentMessage(`⚠️ **Blocked:** ${data.reason}`, true);
    } else {
      appendAgentMessage(data.reply);
    }
  } catch (err) {
    thinkingRow.remove();
    appendAgentMessage(`⚠️ **Error:** ${err.message}`, true);
  } finally {
    setLoading(false);
  }
}

// ── Message helpers ──────────────────────────────────
function hideWelcome() {
  if (welcomeScreen.style.display !== 'none') {
    welcomeScreen.style.display = 'none';
  }
}

function appendUserMessage(text) {
  const row = buildRow('user', escapeHtml(text));
  messagesEl.appendChild(row);
  scrollToBottom();
  msgCount++;
}

function appendAgentMessage(markdown, blocked = false) {
  const html = renderMarkdown(markdown);
  const row  = buildRow('agent', html, blocked);
  messagesEl.appendChild(row);
  scrollToBottom();
  msgCount++;
}

function appendThinking() {
  const row = document.createElement('div');
  row.className = 'thinking-row';
  row.innerHTML = `
    <div class="avatar agent-avatar">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
        <circle cx="12" cy="12" r="9"/>
        <path d="M9 9h.01M15 9h.01M9 15c.6 1 1.4 1.5 3 1.5s2.4-.5 3-1.5" stroke-linecap="round"/>
      </svg>
    </div>
    <div class="thinking-bubble">
      <div class="dot-pulse"><span></span><span></span><span></span></div>
    </div>`;
  messagesEl.appendChild(row);
  scrollToBottom();
  return row;
}

function buildRow(role, contentHtml, blocked = false) {
  const row = document.createElement('div');
  row.className = `message-row ${role}`;

  const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  if (role === 'user') {
    row.innerHTML = `
      <div class="avatar user-avatar">
        ${getUserInitial()}
      </div>
      <div class="bubble-wrap">
        <div class="bubble">${contentHtml}</div>
        <span class="timestamp">${time}</span>
      </div>`;
  } else {
    row.innerHTML = `
      <div class="avatar agent-avatar">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
          <circle cx="12" cy="12" r="9"/>
          <path d="M9 9h.01M15 9h.01M9 15c.6 1 1.4 1.5 3 1.5s2.4-.5 3-1.5" stroke-linecap="round"/>
        </svg>
      </div>
      <div class="bubble-wrap">
        <div class="bubble${blocked ? ' blocked' : ''}">${contentHtml}</div>
        <span class="timestamp">${time}</span>
      </div>`;
  }
  return row;
}

function getUserInitial() {
  return 'U';
}

// ── Loading state ────────────────────────────────────
function setLoading(state) {
  isLoading = state;
  sendBtn.disabled = state;
  messageInput.disabled = state;
}

// ── Scroll ───────────────────────────────────────────
function scrollToBottom() {
  requestAnimationFrame(() => {
    messagesWrap.scrollTop = messagesWrap.scrollHeight;
  });
}

// ── Markdown renderer (lightweight) ─────────────────
function renderMarkdown(md) {
  if (!md) return '';

  let html = escapeHtml(md);

  // Code blocks (``` ... ```)
  html = html.replace(/```(\w*)\n?([\s\S]*?)```/g, (_, lang, code) => {
    return `<pre><code class="lang-${lang || 'text'}">${code.trim()}</code></pre>`;
  });

  // Inline code
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

  // Bold
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

  // Italic
  html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');

  // Headings
  html = html.replace(/^### (.+)$/gm, '<strong style="display:block;margin-top:10px;color:var(--accent-2)">$1</strong>');
  html = html.replace(/^## (.+)$/gm,  '<strong style="display:block;margin-top:12px;font-size:1em;color:var(--accent-2)">$1</strong>');
  html = html.replace(/^# (.+)$/gm,   '<strong style="display:block;margin-top:14px;font-size:1.1em;color:var(--txt)">$1</strong>');

  // Horizontal rule
  html = html.replace(/^---$/gm, '<hr style="border:none;border-top:1px solid var(--border);margin:10px 0">');

  // Unordered list items
  html = html.replace(/^\s*[-*•] (.+)$/gm, '<li style="margin-left:16px;list-style:disc">$1</li>');

  // Numbered list
  html = html.replace(/^\s*\d+\. (.+)$/gm, '<li style="margin-left:16px;list-style:decimal">$1</li>');

  // Newlines → <br> (skip inside pre)
  html = html.replace(/\n(?!<\/?(pre|code|li))/g, '<br>');

  return html;
}

function escapeHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
