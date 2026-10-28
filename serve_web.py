# Local HTTP Server for Namma Space Web Portal with Cross-Origin Isolation Headers
import http.server
import mimetypes
import os
import socket
from pathlib import Path

# Add MIME types
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("application/json", ".json")
mimetypes.add_type("application/octet-stream", ".splat")
mimetypes.add_type("application/octet-stream", ".ply")

web_dir = Path(__file__).parent / "web"
os.chdir(web_dir)

class IsolationHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Mandatory headers for SharedArrayBuffer & WebAssembly worker depth sorting
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Embedder-Policy", "credentialless")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        super().end_headers()

    def log_message(self, format, *args):
        # Suppress noisy logging
        pass

def find_available_port(start_port=8080):
    for p in range(start_port, start_port + 20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", p)) != 0:
                return p
    return start_port

port = find_available_port(8080)
server = http.server.HTTPServer(("127.0.0.1", port), IsolationHandler)
print(f"Namma Space Web Portal running at: http://127.0.0.1:{port}/index.html", flush=True)
try:
    server.serve_forever()
except KeyboardInterrupt:
    print("\nServer terminated.", flush=True)
