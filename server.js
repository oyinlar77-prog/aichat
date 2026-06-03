const express = require("express");
const multer = require("multer");
const path = require("path");
const fs = require("fs");
const fetch = (...args) =>
  import("node-fetch").then(({ default: f }) => f(...args));
const FormDataNode = require("form-data");

const app = express();
const PORT = process.env.PORT || 3000;

// API Keys from Railway environment variables
const ANTHROPIC_API_KEY = process.env.ANTHROPIC_API_KEY || "";
const OPENAI_API_KEY = process.env.OPENAI_API_KEY || "";

// File upload setup
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    const dir = "/tmp/uploads";
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
    cb(null, dir);
  },
  filename: (req, file, cb) => {
    cb(null, Date.now() + "-" + file.originalname);
  },
});
const upload = multer({ storage, limits: { fileSize: 20 * 1024 * 1024 } });

app.use(express.json({ limit: "50mb" }));
app.use(express.urlencoded({ extended: true, limit: "50mb" }));

// Serve uploaded files
app.use("/uploads", express.static("/tmp/uploads"));

// ─── HTML Frontend ────────────────────────────────────────────────────────────
app.get("/", (req, res) => {
  res.send(`<!DOCTYPE html>
<html lang="uz">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Chat</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;800&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,300&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #0a0a0f;
    --surface: #111118;
    --surface2: #1a1a24;
    --border: #2a2a3a;
    --accent: #7c6af7;
    --accent2: #4facf7;
    --gpt: #10a37f;
    --text: #e8e8f0;
    --text2: #8888a0;
    --radius: 16px;
    --gap: 16px;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'DM Sans', sans-serif;
    height: 100dvh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  /* Animated background */
  body::before {
    content: '';
    position: fixed; inset: 0; z-index: 0;
    background:
      radial-gradient(ellipse 60% 40% at 20% 10%, rgba(124,106,247,0.12) 0%, transparent 60%),
      radial-gradient(ellipse 50% 50% at 80% 90%, rgba(79,172,247,0.08) 0%, transparent 60%);
    pointer-events: none;
  }

  header {
    position: relative; z-index: 10;
    padding: 16px 24px;
    border-bottom: 1px solid var(--border);
    background: rgba(10,10,15,0.8);
    backdrop-filter: blur(20px);
    display: flex; align-items: center; justify-content: space-between;
    gap: 16px;
    flex-wrap: wrap;
  }
  .logo {
    font-family: 'Syne', sans-serif;
    font-weight: 800;
    font-size: 1.4rem;
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -0.5px;
  }

  .model-selector {
    display: flex; gap: 8px; align-items: center;
  }
  .model-btn {
    padding: 7px 16px;
    border-radius: 50px;
    border: 1.5px solid var(--border);
    background: transparent;
    color: var(--text2);
    font-family: 'DM Sans', sans-serif;
    font-size: 0.82rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
    white-space: nowrap;
  }
  .model-btn:hover { border-color: var(--accent); color: var(--text); }
  .model-btn.active-claude {
    background: linear-gradient(135deg, rgba(124,106,247,0.2), rgba(79,172,247,0.1));
    border-color: var(--accent);
    color: var(--accent);
  }
  .model-btn.active-gpt {
    background: linear-gradient(135deg, rgba(16,163,127,0.2), rgba(16,163,127,0.05));
    border-color: var(--gpt);
    color: var(--gpt);
  }

  .clear-btn {
    padding: 7px 14px;
    border-radius: 50px;
    border: 1.5px solid var(--border);
    background: transparent;
    color: var(--text2);
    font-family: 'DM Sans', sans-serif;
    font-size: 0.8rem;
    cursor: pointer;
    transition: all 0.2s;
  }
  .clear-btn:hover { border-color: #f47; color: #f47; }

  #chat {
    position: relative; z-index: 1;
    flex: 1;
    overflow-y: auto;
    padding: 24px;
    display: flex;
    flex-direction: column;
    gap: 20px;
    scroll-behavior: smooth;
  }
  #chat::-webkit-scrollbar { width: 4px; }
  #chat::-webkit-scrollbar-track { background: transparent; }
  #chat::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }

  .msg {
    display: flex;
    gap: 12px;
    animation: slideIn 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
    max-width: 820px;
  }
  .msg.user { align-self: flex-end; flex-direction: row-reverse; }
  .msg.assistant { align-self: flex-start; }

  @keyframes slideIn {
    from { opacity: 0; transform: translateY(12px) scale(0.97); }
    to { opacity: 1; transform: translateY(0) scale(1); }
  }

  .avatar {
    width: 36px; height: 36px;
    border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1rem;
    flex-shrink: 0;
    font-family: 'Syne', sans-serif;
    font-weight: 800;
  }
  .avatar.user-av { background: linear-gradient(135deg, #3a3a4a, #2a2a3a); border: 1px solid var(--border); }
  .avatar.claude-av { background: linear-gradient(135deg, rgba(124,106,247,0.3), rgba(79,172,247,0.2)); border: 1px solid rgba(124,106,247,0.4); }
  .avatar.gpt-av { background: linear-gradient(135deg, rgba(16,163,127,0.3), rgba(16,163,127,0.1)); border: 1px solid rgba(16,163,127,0.4); }

  .bubble {
    padding: 14px 18px;
    border-radius: 18px;
    max-width: calc(100% - 52px);
    line-height: 1.65;
    font-size: 0.92rem;
    font-weight: 400;
  }
  .msg.user .bubble {
    background: linear-gradient(135deg, rgba(124,106,247,0.25), rgba(79,172,247,0.15));
    border: 1px solid rgba(124,106,247,0.3);
    border-top-right-radius: 4px;
  }
  .msg.assistant .bubble {
    background: var(--surface);
    border: 1px solid var(--border);
    border-top-left-radius: 4px;
  }
  .msg.assistant.gpt .bubble {
    border-color: rgba(16,163,127,0.2);
  }

  .bubble pre {
    background: #0d0d16;
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 12px;
    overflow-x: auto;
    margin: 10px 0;
    font-size: 0.82rem;
  }
  .bubble code {
    font-family: 'Fira Code', monospace;
    font-size: 0.85em;
    background: rgba(124,106,247,0.12);
    padding: 2px 6px;
    border-radius: 4px;
  }
  .bubble pre code { background: none; padding: 0; }

  .model-tag {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    margin-bottom: 6px;
    padding: 0 2px;
  }
  .claude .model-tag { color: var(--accent); }
  .gpt .model-tag { color: var(--gpt); }
  .user .model-tag { color: var(--text2); text-align: right; }

  /* File previews inside messages */
  .file-preview {
    display: flex; align-items: center; gap: 10px;
    background: rgba(255,255,255,0.05);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 10px 14px;
    margin-bottom: 8px;
    font-size: 0.85rem;
  }
  .file-preview .icon { font-size: 1.4rem; }
  .file-preview a { color: var(--accent2); text-decoration: none; }
  .file-preview a:hover { text-decoration: underline; }
  .file-preview img { max-width: 200px; max-height: 150px; border-radius: 8px; display: block; }

  /* Typing indicator */
  .typing { display: flex; gap: 5px; align-items: center; padding: 6px 4px; }
  .typing span {
    width: 7px; height: 7px; background: var(--accent); border-radius: 50%;
    animation: bounce 1.2s infinite;
  }
  .typing span:nth-child(2) { animation-delay: 0.2s; background: var(--accent2); }
  .typing span:nth-child(3) { animation-delay: 0.4s; }
  @keyframes bounce {
    0%,60%,100% { transform: translateY(0); }
    30% { transform: translateY(-6px); }
  }

  /* Bottom bar */
  .bottom {
    position: relative; z-index: 10;
    padding: 16px 24px;
    border-top: 1px solid var(--border);
    background: rgba(10,10,15,0.9);
    backdrop-filter: blur(20px);
  }

  /* File attachments preview area */
  #attachments {
    display: flex; gap: 8px; flex-wrap: wrap;
    margin-bottom: 10px;
  }
  .attach-chip {
    display: flex; align-items: center; gap: 6px;
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 50px;
    padding: 5px 12px 5px 8px;
    font-size: 0.78rem;
    color: var(--text2);
    position: relative;
  }
  .attach-chip .chip-icon { font-size: 1rem; }
  .attach-chip .remove-chip {
    cursor: pointer;
    opacity: 0.6;
    transition: opacity 0.2s;
    font-size: 0.9rem;
    margin-left: 2px;
  }
  .attach-chip .remove-chip:hover { opacity: 1; color: #f47; }

  .input-row {
    display: flex;
    gap: 10px;
    align-items: flex-end;
    background: var(--surface);
    border: 1.5px solid var(--border);
    border-radius: var(--radius);
    padding: 10px 12px;
    transition: border-color 0.2s;
  }
  .input-row:focus-within { border-color: var(--accent); }

  .icon-btn {
    width: 36px; height: 36px;
    border-radius: 10px;
    border: none;
    background: transparent;
    color: var(--text2);
    cursor: pointer;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.1rem;
    transition: all 0.2s;
    flex-shrink: 0;
  }
  .icon-btn:hover { background: var(--surface2); color: var(--text); }

  #textInput {
    flex: 1;
    background: none;
    border: none;
    outline: none;
    color: var(--text);
    font-family: 'DM Sans', sans-serif;
    font-size: 0.92rem;
    resize: none;
    min-height: 24px;
    max-height: 180px;
    line-height: 1.5;
    padding: 4px 0;
  }
  #textInput::placeholder { color: var(--text2); }

  .send-btn {
    width: 38px; height: 38px;
    border-radius: 11px;
    border: none;
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    color: white;
    cursor: pointer;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.1rem;
    transition: all 0.2s;
    flex-shrink: 0;
  }
  .send-btn:hover { transform: scale(1.08); filter: brightness(1.1); }
  .send-btn:disabled { opacity: 0.4; cursor: not-allowed; transform: none; }

  .hint {
    text-align: center;
    font-size: 0.72rem;
    color: var(--text2);
    margin-top: 10px;
    opacity: 0.7;
  }

  /* Welcome screen */
  .welcome {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 12px;
    text-align: center;
    padding: 40px;
    animation: fadeIn 0.6s ease;
  }
  .welcome-icon { font-size: 3.5rem; margin-bottom: 4px; }
  .welcome h2 {
    font-family: 'Syne', sans-serif;
    font-weight: 800;
    font-size: 1.8rem;
    background: linear-gradient(135deg, var(--text), var(--text2));
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  .welcome p { color: var(--text2); font-size: 0.9rem; max-width: 360px; line-height: 1.6; }
  @keyframes fadeIn { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: translateY(0); } }

  .error-msg { color: #f47; font-style: italic; }

  #fileInput { display: none; }
</style>
</head>
<body>

<header>
  <span class="logo">✦ AI Chat</span>
  <div class="model-selector">
    <button class="model-btn active-claude" id="btnClaude" onclick="setModel('claude')">
      ◆ Claude Sonnet 4
    </button>
    <button class="model-btn" id="btnGpt" onclick="setModel('gpt')">
      ⬡ GPT-4.1
    </button>
  </div>
  <button class="clear-btn" onclick="clearChat()">🗑 Tozalash</button>
</header>

<div id="chat">
  <div class="welcome" id="welcome">
    <div class="welcome-icon">✦</div>
    <h2>Salom! Men sizning AI yordamchingizman</h2>
    <p>Matn yozing yoki fayl yuklang. Claude Sonnet 4 va GPT-4.1 modellari bilan ishlang.</p>
  </div>
</div>

<div class="bottom">
  <div id="attachments"></div>
  <div class="input-row">
    <button class="icon-btn" onclick="document.getElementById('fileInput').click()" title="Fayl yuklash">📎</button>
    <input type="file" id="fileInput" multiple accept="*/*" onchange="handleFiles(this.files)">
    <textarea id="textInput" placeholder="Xabar yozing..." rows="1" onkeydown="handleKey(event)" oninput="autoResize(this)"></textarea>
    <button class="send-btn" id="sendBtn" onclick="sendMessage()">➤</button>
  </div>
  <p class="hint">Enter — yuborish &nbsp;·&nbsp; Shift+Enter — yangi qator &nbsp;·&nbsp; Fayllar: rasm, PDF, hujjat va boshqalar</p>
</div>

<script>
let currentModel = 'claude';
let history = [];
let pendingFiles = []; // { file, url, name, type }

// ── Model selection ──────────────────────────────────────────────────────────
function setModel(m) {
  currentModel = m;
  document.getElementById('btnClaude').className = 'model-btn' + (m === 'claude' ? ' active-claude' : '');
  document.getElementById('btnGpt').className = 'model-btn' + (m === 'gpt' ? ' active-gpt' : '');
}

// ── Auto-resize textarea ─────────────────────────────────────────────────────
function autoResize(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 180) + 'px';
}

// ── File handling ────────────────────────────────────────────────────────────
function handleFiles(files) {
  Array.from(files).forEach(f => {
    pendingFiles.push({ file: f, name: f.name, type: f.type });
  });
  renderAttachments();
  document.getElementById('fileInput').value = '';
}

function renderAttachments() {
  const el = document.getElementById('attachments');
  el.innerHTML = '';
  pendingFiles.forEach((f, i) => {
    const chip = document.createElement('div');
    chip.className = 'attach-chip';
    const icon = f.type.startsWith('image/') ? '🖼️' : f.type === 'application/pdf' ? '📄' : '📎';
    chip.innerHTML = \`<span class="chip-icon">\${icon}</span><span>\${f.name}</span><span class="remove-chip" onclick="removeFile(\${i})">✕</span>\`;
    el.appendChild(chip);
  });
}

function removeFile(i) {
  pendingFiles.splice(i, 1);
  renderAttachments();
}

// ── Keyboard handler ─────────────────────────────────────────────────────────
function handleKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
}

// ── Clear chat ───────────────────────────────────────────────────────────────
function clearChat() {
  history = [];
  pendingFiles = [];
  renderAttachments();
  const chat = document.getElementById('chat');
  chat.innerHTML = '';
  const welcome = document.createElement('div');
  welcome.className = 'welcome'; welcome.id = 'welcome';
  welcome.innerHTML = \`<div class="welcome-icon">✦</div>
    <h2>Salom! Men sizning AI yordamchingizman</h2>
    <p>Matn yozing yoki fayl yuklang. Claude Sonnet 4 va GPT-4.1 modellari bilan ishlang.</p>\`;
  chat.appendChild(welcome);
}

// ── Send message ─────────────────────────────────────────────────────────────
async function sendMessage() {
  const inp = document.getElementById('textInput');
  const text = inp.value.trim();
  if (!text && pendingFiles.length === 0) return;

  // Hide welcome
  const welcome = document.getElementById('welcome');
  if (welcome) welcome.remove();

  const sendBtn = document.getElementById('sendBtn');
  sendBtn.disabled = true;
  inp.value = '';
  inp.style.height = 'auto';

  // Upload files first
  let uploadedFiles = [];
  if (pendingFiles.length > 0) {
    const fd = new FormData();
    pendingFiles.forEach(f => fd.append('files', f.file));
    try {
      const res = await fetch('/upload', { method: 'POST', body: fd });
      const data = await res.json();
      uploadedFiles = data.files || [];
    } catch(e) {
      appendMsg('assistant', currentModel, '<span class="error-msg">Fayl yuklashda xatolik.</span>');
      sendBtn.disabled = false;
      return;
    }
  }
  pendingFiles = [];
  renderAttachments();

  // Build user message display
  let userHtml = '';
  uploadedFiles.forEach(f => {
    if (f.type && f.type.startsWith('image/')) {
      userHtml += \`<div class="file-preview"><img src="\${f.url}" alt="\${f.name}"></div>\`;
    } else {
      const icon = f.type === 'application/pdf' ? '📄' : '📎';
      userHtml += \`<div class="file-preview"><span class="icon">\${icon}</span><a href="\${f.url}" target="_blank">\${f.name}</a></div>\`;
    }
  });
  if (text) userHtml += \`<span>\${escapeHtml(text)}</span>\`;
  appendMsg('user', 'user', userHtml);

  // Build history message
  const userContent = buildUserContent(text, uploadedFiles);
  history.push({ role: 'user', content: userContent });

  // Typing indicator
  const typingId = 'typing-' + Date.now();
  appendTyping(typingId);

  try {
    const res = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model: currentModel, history, files: uploadedFiles })
    });
    const data = await res.json();
    removeTyping(typingId);

    if (data.error) {
      appendMsg('assistant', currentModel, \`<span class="error-msg">\${escapeHtml(data.error)}</span>\`);
    } else {
      const reply = data.reply || '';
      history.push({ role: 'assistant', content: reply });
      appendMsg('assistant', currentModel, formatMarkdown(reply));
    }
  } catch(e) {
    removeTyping(typingId);
    appendMsg('assistant', currentModel, '<span class="error-msg">Serverga ulanishda xatolik.</span>');
  }

  sendBtn.disabled = false;
  inp.focus();
}

// ── Build user content for API ───────────────────────────────────────────────
function buildUserContent(text, files) {
  if (files.length === 0) return text;
  // For multimodal - images inline, files as text reference
  const parts = [];
  files.forEach(f => {
    if (f.type && f.type.startsWith('image/')) {
      parts.push({ type: 'image_url', url: f.url, name: f.name });
    } else {
      parts.push({ type: 'file', url: f.url, name: f.name, mimeType: f.type });
    }
  });
  if (text) parts.push({ type: 'text', text });
  return parts;
}

// ── DOM helpers ───────────────────────────────────────────────────────────────
function appendMsg(role, model, html) {
  const chat = document.getElementById('chat');
  const div = document.createElement('div');
  div.className = 'msg ' + role + (model === 'gpt' ? ' gpt' : ' claude');

  let avatarClass = role === 'user' ? 'user-av' : (model === 'gpt' ? 'gpt-av' : 'claude-av');
  let avatarIcon = role === 'user' ? '👤' : (model === 'gpt' ? '⬡' : '◆');
  let label = role === 'user' ? 'Siz' : (model === 'gpt' ? 'GPT-4.1' : 'Claude Sonnet 4');

  div.innerHTML = \`
    <div class="avatar \${avatarClass}">\${avatarIcon}</div>
    <div>
      <div class="model-tag">\${label}</div>
      <div class="bubble">\${html}</div>
    </div>\`;
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
}

function appendTyping(id) {
  const chat = document.getElementById('chat');
  const div = document.createElement('div');
  div.className = 'msg assistant claude';
  div.id = id;
  const model = currentModel;
  let avatarClass = model === 'gpt' ? 'gpt-av' : 'claude-av';
  let avatarIcon = model === 'gpt' ? '⬡' : '◆';
  let label = model === 'gpt' ? 'GPT-4.1' : 'Claude Sonnet 4';
  div.innerHTML = \`
    <div class="avatar \${avatarClass}">\${avatarIcon}</div>
    <div>
      <div class="model-tag">\${label}</div>
      <div class="bubble"><div class="typing"><span></span><span></span><span></span></div></div>
    </div>\`;
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
}
function removeTyping(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

function escapeHtml(s) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function formatMarkdown(text) {
  // Basic markdown-like formatting
  return escapeHtml(text)
    .replace(/\`\`\`([\\s\\S]*?)\`\`\`/g, '<pre><code>$1</code></pre>')
    .replace(/\`([^\`]+)\`/g, '<code>$1</code>')
    .replace(/\\*\\*(.+?)\\*\\*/g, '<strong>$1</strong>')
    .replace(/\\*(.+?)\\*/g, '<em>$1</em>')
    .replace(/\\n/g, '<br>');
}
</script>
</body>
</html>`);
});

// ─── File Upload Endpoint ──────────────────────────────────────────────────────
app.post("/upload", upload.array("files", 10), (req, res) => {
  if (!req.files || req.files.length === 0) {
    return res.json({ files: [] });
  }
  const files = req.files.map((f) => ({
    name: f.originalname,
    url: `/uploads/${f.filename}`,
    path: f.path,
    type: f.mimetype,
    size: f.size,
  }));
  res.json({ files });
});

// ─── Chat Endpoint ─────────────────────────────────────────────────────────────
app.post("/chat", async (req, res) => {
  const { model, history, files } = req.body;

  try {
    if (model === "claude") {
      const reply = await callClaude(history, files);
      res.json({ reply });
    } else {
      const reply = await callGPT(history, files);
      res.json({ reply });
    }
  } catch (err) {
    console.error("Chat error:", err.message);
    res.json({ error: err.message });
  }
});

// ─── Claude API ────────────────────────────────────────────────────────────────
async function callClaude(history, files) {
  if (!ANTHROPIC_API_KEY) throw new Error("ANTHROPIC_API_KEY sozlanmagan");

  // Build messages for Claude
  const messages = history.map((m, i) => {
    if (typeof m.content === "string") {
      return { role: m.role, content: m.content };
    }
    // Last user message with files - build multimodal content
    if (m.role === "user" && Array.isArray(m.content)) {
      const parts = [];
      for (const part of m.content) {
        if (part.type === "image_url") {
          // Read file and encode as base64
          try {
            const filePath = part.url.replace("/uploads/", "/tmp/uploads/");
            const data = fs.readFileSync(filePath);
            const base64 = data.toString("base64");
            parts.push({
              type: "image",
              source: {
                type: "base64",
                media_type: part.type || "image/jpeg",
                data: base64,
              },
            });
          } catch (e) {
            parts.push({ type: "text", text: `[Rasm: ${part.name}]` });
          }
        } else if (part.type === "file") {
          // For PDFs
          if (part.mimeType === "application/pdf") {
            try {
              const filePath = part.url.replace("/uploads/", "/tmp/uploads/");
              const data = fs.readFileSync(filePath);
              const base64 = data.toString("base64");
              parts.push({
                type: "document",
                source: {
                  type: "base64",
                  media_type: "application/pdf",
                  data: base64,
                },
              });
            } catch (e) {
              parts.push({ type: "text", text: `[Fayl: ${part.name}]` });
            }
          } else {
            // Try to read as text
            try {
              const filePath = part.url.replace("/uploads/", "/tmp/uploads/");
              const content = fs.readFileSync(filePath, "utf8");
              parts.push({
                type: "text",
                text: `[Fayl: ${part.name}]\n\`\`\`\n${content.slice(0, 8000)}\n\`\`\``,
              });
            } catch (e) {
              parts.push({ type: "text", text: `[Fayl: ${part.name}]` });
            }
          }
        } else if (part.type === "text" && part.text) {
          parts.push({ type: "text", text: part.text });
        }
      }
      return { role: "user", content: parts };
    }
    return { role: m.role, content: String(m.content) };
  });

  const response = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "x-api-key": ANTHROPIC_API_KEY,
      "anthropic-version": "2023-06-01",
      "content-type": "application/json",
    },
    body: JSON.stringify({
      model: "claude-opus-4-7",
      max_tokens: 4096,
      system:
        "Siz foydali AI yordamchisiz. O'zbek, rus va ingliz tillarini bilasiz. Foydalanuvchi qaysi tilda gapirsa, o'sha tilda javob bering.",
      messages,
    }),
  });

  const data = await response.json();
  if (data.error) throw new Error(data.error.message || "Claude API xatosi");
  return data.content?.[0]?.text || "";
}

// ─── GPT API ───────────────────────────────────────────────────────────────────
async function callGPT(history, files) {
  if (!OPENAI_API_KEY) throw new Error("OPENAI_API_KEY sozlanmagan");

  const messages = [
    {
      role: "system",
      content:
        "Siz foydali AI yordamchisiz. O'zbek, rus va ingliz tillarini bilasiz. Foydalanuvchi qaysi tilda gapirsa, o'sha tilda javob bering.",
    },
  ];

  for (const m of history) {
    if (typeof m.content === "string") {
      messages.push({ role: m.role, content: m.content });
    } else if (Array.isArray(m.content) && m.role === "user") {
      const parts = [];
      for (const part of m.content) {
        if (part.type === "image_url") {
          try {
            const filePath = part.url.replace("/uploads/", "/tmp/uploads/");
            const data = fs.readFileSync(filePath);
            const base64 = data.toString("base64");
            const mime = part.type || "image/jpeg";
            parts.push({
              type: "image_url",
              image_url: { url: `data:${mime};base64,${base64}` },
            });
          } catch (e) {
            parts.push({ type: "text", text: `[Rasm: ${part.name}]` });
          }
        } else if (part.type === "file") {
          try {
            const filePath = part.url.replace("/uploads/", "/tmp/uploads/");
            const content = fs.readFileSync(filePath, "utf8");
            parts.push({
              type: "text",
              text: `[Fayl: ${part.name}]\n\`\`\`\n${content.slice(0, 8000)}\n\`\`\``,
            });
          } catch (e) {
            parts.push({ type: "text", text: `[Fayl: ${part.name}]` });
          }
        } else if (part.type === "text" && part.text) {
          parts.push({ type: "text", text: part.text });
        }
      }
      messages.push({ role: "user", content: parts });
    } else {
      messages.push({ role: m.role, content: String(m.content) });
    }
  }

  const response = await fetch("https://api.openai.com/v1/chat/completions", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${OPENAI_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: "gpt-5.5-pro",
      max_tokens: 4096,
      messages,
    }),
  });

  const data = await response.json();
  if (data.error) throw new Error(data.error.message || "OpenAI API xatosi");
  return data.choices?.[0]?.message?.content || "";
}

// ─── Start Server ──────────────────────────────────────────────────────────────
app.listen(PORT, () => {
  console.log(`✦ AI Chat server ishga tushdi: http://localhost:${PORT}`);
  console.log(`   Claude API: ${ANTHROPIC_API_KEY ? "✓ sozlangan" : "✗ ANTHROPIC_API_KEY yo'q"}`);
  console.log(`   OpenAI API: ${OPENAI_API_KEY ? "✓ sozlangan" : "✗ OPENAI_API_KEY yo'q"}`);
});
