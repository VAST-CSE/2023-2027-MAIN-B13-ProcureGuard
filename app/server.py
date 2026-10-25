"""
Lightweight HTTP Server for the Intelligent Procurement System.

Uses Python standard library only (http.server, json).
Serves the modern frontend and connects directly to the real VerificationEngine
at `/api/verify` for genuine live 3-way matching.
"""

import http.server
import json
import os
import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.verification.engine import VerificationEngine

FRONTEND_DIR = PROJECT_ROOT / "frontend"


class ProcurementRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Handles static files from frontend/ and exposes /api/verify."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FRONTEND_DIR), **kwargs)

    def do_GET(self):
        """Handle GET requests for static frontend assets and health check."""
        if self.path == "/api/health":
            self._send_json({"status": "ok", "service": "Intelligent Procurement Verification Engine"})
            return
        # Standard static file serving
        return super().do_GET()

    def do_POST(self):
        """Handle live verification requests against the Python VerificationEngine."""
        if self.path == "/api/verify":
            content_length = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(content_length)

            try:
                payload = json.loads(raw_body.decode("utf-8"))
                po = payload.get("po", {})
                grn = payload.get("grn", {})
                invoice = payload.get("invoice", {})

                # Execute genuine verification using the actual Python VerificationEngine
                engine = VerificationEngine()
                result = engine.verify(po, grn, invoice)

                self._send_json(result.to_dict(), status=200)
            except Exception as e:
                self._send_json(
                    {"error": f"Failed to execute verification: {str(e)}"},
                    status=400,
                )
            return

        self._send_json({"error": "Endpoint not found"}, status=404)

    def _send_json(self, data: dict, status: int = 200):
        """Utility to write JSON responses."""
        response_bytes = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(response_bytes)

    def end_headers(self):
        # Prevent caching for live development
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        super().end_headers()


def run_server(port: int = 8000, host: str = "127.0.0.1"):
    """Launch the HTTP server."""
    server_address = (host, port)
    httpd = http.server.ThreadingHTTPServer(server_address, ProcurementRequestHandler)
    print(f"\n========================================================")
    print(f" Intelligent Procurement Verification & Risk System ")
    print(f"========================================================")
    print(f" Web UI:      http://{host}:{port}")
    print(f" Live API:    http://{host}:{port}/api/verify")
    print(f" Engine:      app/verification/engine.py (Python stdlib)")
    print(f" Press Ctrl+C to stop the server.")
    print(f"========================================================\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer shutting down gracefully.")
        httpd.server_close()


if __name__ == "__main__":
    port = 8000
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    run_server(port=port)
