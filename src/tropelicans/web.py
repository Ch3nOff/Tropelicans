"""Standard-library web view for chatting with and inspecting the runtime."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .config import config_to_dict
from .runtime import TropelicansRuntime


HTML = """<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Tropelicans</title>
  <style>
    :root { color-scheme: light dark; --accent: #14b8a6; --panel: rgba(127,127,127,.12); }
    * { box-sizing: border-box; }
    body { font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 0; background: radial-gradient(circle at top left, rgba(20,184,166,.24), transparent 32rem), Canvas; color: CanvasText; }
    header { padding: 1.5rem 2rem; border-bottom: 1px solid rgba(127,127,127,.25); display: flex; justify-content: space-between; gap: 1rem; align-items: center; }
    h1 { margin: 0; font-size: clamp(1.4rem, 2vw, 2.2rem); }
    main { display: grid; grid-template-columns: minmax(0, 1fr) 22rem; gap: 1rem; padding: 1rem; min-height: calc(100vh - 5.5rem); }
    section { background: var(--panel); border: 1px solid rgba(127,127,127,.22); border-radius: 1rem; padding: 1rem; }
    #chat { display: flex; flex-direction: column; min-height: 70vh; }
    #messages { flex: 1; overflow: auto; display: flex; flex-direction: column; gap: .75rem; padding-bottom: 1rem; }
    .msg { max-width: 78ch; padding: .75rem .9rem; border-radius: .9rem; white-space: pre-wrap; line-height: 1.45; }
    .user { align-self: flex-end; background: var(--accent); color: #001f1a; }
    .assistant { align-self: flex-start; background: rgba(127,127,127,.18); }
    form { display: grid; grid-template-columns: 10rem 1fr auto; gap: .5rem; }
    select, textarea, button { font: inherit; border-radius: .7rem; border: 1px solid rgba(127,127,127,.35); padding: .75rem; background: Canvas; color: CanvasText; }
    textarea { resize: vertical; min-height: 3rem; }
    button { cursor: pointer; background: var(--accent); color: #001f1a; font-weight: 700; }
    pre { overflow: auto; background: rgba(0,0,0,.25); padding: .75rem; border-radius: .75rem; }
    @media (max-width: 840px) { main { grid-template-columns: 1fr; } form { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
  <header>
    <div><h1>Tropelicans</h1><div>Local AI runtime chat, workspace, memory, and skills.</div></div>
    <strong id="active">Starting...</strong>
  </header>
  <main>
    <section id="chat">
      <h2>Chat</h2>
      <div id="messages"></div>
      <form id="chatForm">
        <select id="category" aria-label="Agent category"><option value="">Default</option></select>
        <textarea id="prompt" placeholder="Ask Tropelicans to reason, code, inspect this workspace, or remember something..."></textarea>
        <button type="submit">Send</button>
      </form>
    </section>
    <aside>
      <section><h2>Runtime</h2><pre id="status">Loading...</pre></section>
      <section><h2>First steps</h2><ol><li>Choose an agent category.</li><li>Ask a question in chat.</li><li>Use memory and skills from the CLI or config as the framework grows.</li></ol></section>
    </aside>
  </main>
  <script>
    const messages = document.querySelector('#messages');
    const statusBox = document.querySelector('#status');
    const active = document.querySelector('#active');
    const category = document.querySelector('#category');
    const prompt = document.querySelector('#prompt');
    function addMessage(role, text) {
      const item = document.createElement('div');
      item.className = `msg ${role}`;
      item.textContent = text;
      messages.appendChild(item);
      messages.scrollTop = messages.scrollHeight;
    }
    async function refreshStatus() {
      const response = await fetch('/api/status');
      const data = await response.json();
      statusBox.textContent = JSON.stringify(data, null, 2);
      active.textContent = `Active: ${data.activeAgents.join(', ') || 'none'}`;
      category.innerHTML = '<option value="">Default</option>' + Object.entries(data.config.agents).map(([name, agent]) => `<option value="${name}">${name} (${agent.category})</option>`).join('');
    }
    document.querySelector('#chatForm').addEventListener('submit', async (event) => {
      event.preventDefault();
      const text = prompt.value.trim();
      if (!text) return;
      addMessage('user', text);
      prompt.value = '';
      const response = await fetch('/api/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ prompt: text, category: category.value || null }) });
      const data = await response.json();
      if (!response.ok) { addMessage('assistant', data.error || 'Runtime error'); return; }
      addMessage('assistant', data.text);
      await refreshStatus();
    });
    addMessage('assistant', 'Welcome to Tropelicans. This is the one-command local web runtime.');
    refreshStatus();
  </script>
</body>
</html>"""


def serve(workspace: Path, config_path: Path | None = None, host: str | None = None, port: int | None = None) -> None:
    runtime = TropelicansRuntime(workspace, config_path)
    bind_host = host or runtime.config.web_view.host
    bind_port = port or runtime.config.web_view.port

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path == "/api/status":
                self._json({
                    "workspace": str(runtime.workspace),
                    "activeAgents": runtime.router.active_agents(),
                    "config": config_to_dict(runtime.config),
                    "memoryEntries": len(runtime.memory.list()),
                    "skills": [skill.name for skill in runtime.skills.list()],
                })
                return
            self._html(HTML)

        def do_POST(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path != "/api/chat":
                self._json({"error": "not found"}, status=404)
                return
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length) or b"{}")
            prompt = str(payload.get("prompt", "")).strip()
            category = payload.get("category")
            if not prompt:
                self._json({"error": "prompt is required"}, status=400)
                return
            try:
                result = runtime.run(prompt, category=str(category) if category else None)
            except RuntimeError as error:
                self._json({"error": str(error)}, status=500)
                return
            self._json({
                "text": result.response.text,
                "agent": result.response.agent,
                "activeAgents": result.active_agents,
                "workspaceChanges": [change.__dict__ for change in result.workspace_changes],
                "matchedSkills": result.matched_skills,
            })

        def log_message(self, format: str, *args: object) -> None:
            return

        def _html(self, text: str, status: int = 200) -> None:
            payload = text.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def _json(self, data: object, status: int = 200) -> None:
            payload = json.dumps(data).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

    print(f"Tropelicans web runtime: http://{bind_host}:{bind_port}")
    ThreadingHTTPServer((bind_host, bind_port), Handler).serve_forever()
