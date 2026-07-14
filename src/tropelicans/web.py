"""Small standard-library web view for inspecting the runtime."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .config import config_to_dict
from .runtime import TropelicansRuntime


HTML = """<!doctype html>
<html><head><title>Tropelicans</title><style>body{font-family:system-ui;margin:2rem;max-width:960px}pre{background:#111;color:#eee;padding:1rem;overflow:auto}section{border:1px solid #ddd;border-radius:12px;padding:1rem;margin:1rem 0}</style></head>
<body><h1>Tropelicans Runtime</h1><p>CLI-first AI runtime control plane.</p><section><h2>Status</h2><pre id="status">Loading...</pre></section><script>fetch('/api/status').then(r=>r.json()).then(j=>status.textContent=JSON.stringify(j,null,2))</script></body></html>"""


def serve(workspace: Path, config_path: Path | None = None, host: str | None = None, port: int | None = None) -> None:
    runtime = TropelicansRuntime(workspace, config_path)
    bind_host = host or runtime.config.web_view.host
    bind_port = port or runtime.config.web_view.port

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path == "/api/status":
                payload = json.dumps({
                    "workspace": str(runtime.workspace),
                    "activeAgents": runtime.router.active_agents(),
                    "config": config_to_dict(runtime.config),
                    "memoryEntries": len(runtime.memory.list()),
                    "skills": [skill.name for skill in runtime.skills.list()],
                }).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
                return
            payload = HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

    ThreadingHTTPServer((bind_host, bind_port), Handler).serve_forever()
