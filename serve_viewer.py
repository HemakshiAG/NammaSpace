import http.server
import os
from pathlib import Path

viewer_dir = Path("test_room_splat/viewer").resolve()
os.chdir(viewer_dir)

class CORSHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

server = http.server.HTTPServer(("127.0.0.1", 8080), CORSHandler)
print("Server started on http://127.0.0.1:8080", flush=True)
server.serve_forever()
