# Local HTTP Server for Namma Space with Autonomous Reconstruction Pipeline
import http.server
import mimetypes
import os
import socket
import json
import threading
import zipfile
import shutil
from pathlib import Path
from urllib.parse import urlparse

import pipeline_worker

# MIME types configuration
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("application/json", ".json")
mimetypes.add_type("application/octet-stream", ".splat")
mimetypes.add_type("application/octet-stream", ".ply")

ROOT_DIR = Path(__file__).parent.resolve()
WEB_DIR = ROOT_DIR / "web"
UPLOADS_DIR = ROOT_DIR / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# Global pipeline state
PIPELINE_STATE = {
    "status": "idle",       # "idle", "processing", "completed", "error"
    "stage": "",
    "progress": 0,
    "message": "Ready for video upload.",
    "details": None,
    "error": None
}
STATE_LOCK = threading.Lock()

def update_status(stage: str, progress: int, message: str, details=None, error=None):
    with STATE_LOCK:
        PIPELINE_STATE["stage"] = stage
        PIPELINE_STATE["progress"] = progress
        PIPELINE_STATE["message"] = message
        if stage == "completed":
            PIPELINE_STATE["status"] = "completed"
        elif stage == "error":
            PIPELINE_STATE["status"] = "error"
            PIPELINE_STATE["error"] = error
        else:
            PIPELINE_STATE["status"] = "processing"
        if details:
            PIPELINE_STATE["details"] = details


def run_pipeline_thread(video_path: Path):
    try:
        def worker_callback(stage, pct, msg):
            update_status(stage, pct, msg)
            
        result = pipeline_worker.process_video_pipeline(video_path, WEB_DIR, callback=worker_callback)
        update_status("completed", 100, "Reconstruction Complete! 3D twin ready.", details=result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        update_status("error", 0, f"Reconstruction failed: {str(e)}", error=str(e))


class NammaSpaceHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def end_headers(self):
        # Mandatory headers for SharedArrayBuffer & WebAssembly multi-threaded sorting
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Embedder-Policy", "credentialless")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        super().end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            with STATE_LOCK:
                data = json.dumps(PIPELINE_STATE).encode("utf-8")
            self.wfile.write(data)
            return

        super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/upload":
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length <= 0:
                self.send_error(400, "Empty payload")
                return

            # Read raw body
            body = self.rfile.read(content_length)
            content_type = self.headers.get("Content-Type", "")

            filename = "uploaded_video.mp4"
            file_bytes = b""

            if "multipart/form-data" in content_type:
                # Parse boundary
                boundary = content_type.split("boundary=")[-1].strip()
                boundary_bytes = ("--" + boundary).encode("latin1")
                parts = body.split(boundary_bytes)
                for part in parts:
                    if b'filename="' in part:
                        headers_part, file_data = part.split(b"\r\n\r\n", 1)
                        # Extract filename
                        header_str = headers_part.decode("latin1", errors="ignore")
                        for line in header_str.split("\r\n"):
                            if "filename=" in line:
                                fn = line.split('filename="')[-1].split('"')[0]
                                if fn: filename = fn
                        # Strip trailing CRLF
                        file_bytes = file_data.rstrip(b"\r\n--")
                        break
            else:
                file_bytes = body
                if "X-Filename" in self.headers:
                    filename = self.headers["X-Filename"]

            target_path = UPLOADS_DIR / filename
            with open(target_path, "wb") as f:
                f.write(file_bytes)

            ext = target_path.suffix.lower()

            # Handle direct ZIP or SPLAT upload (Instant unpack)
            if ext == ".zip":
                update_status("unpacking", 50, "Unpacking 3D Gaussian twin assets...")
                try:
                    with zipfile.ZipFile(target_path, "r") as z:
                        for item in z.infolist():
                            if item.filename.endswith(".splat"):
                                with z.open(item) as src, open(WEB_DIR / "scene.splat", "wb") as dst:
                                    shutil.copyfileobj(src, dst)
                            elif item.filename.endswith(".json"):
                                with z.open(item) as src, open(WEB_DIR / "cameras.json", "wb") as dst:
                                    shutil.copyfileobj(src, dst)
                    update_status("completed", 100, "Pre-packaged 3D twin loaded successfully!")
                    self.send_json_response({"success": True, "type": "zip", "message": "Assets extracted"})
                except Exception as e:
                    update_status("error", 0, f"Failed to unpack zip: {e}", error=str(e))
                    self.send_json_response({"success": False, "error": str(e)}, status=500)
                return

            elif ext == ".splat":
                shutil.copy2(target_path, WEB_DIR / "scene.splat")
                update_status("completed", 100, "Splat scene loaded directly!")
                self.send_json_response({"success": True, "type": "splat", "message": "Splat updated"})
                return

            # Handle Video Upload (.mp4, .mov, etc.)
            elif ext in [".mp4", ".mov", ".m4v", ".avi"]:
                update_status("queued", 5, f"Video '{filename}' uploaded ({len(file_bytes)/(1024*1024):.1f} MB). Starting pipeline...")
                threading.Thread(target=run_pipeline_thread, args=(target_path,), daemon=True).start()
                self.send_json_response({"success": True, "type": "video", "filename": filename})
                return
            else:
                self.send_json_response({"success": False, "error": f"Unsupported format: {ext}"}, status=400)
                return

        self.send_error(404, "Unknown endpoint")

    def send_json_response(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def log_message(self, format, *args):
        # Clean logging
        pass


def find_available_port(start_port=8080):
    for p in range(start_port, start_port + 20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", p)) != 0:
                return p
    return start_port

if __name__ == "__main__":
    port = find_available_port(8080)
    server = http.server.HTTPServer(("127.0.0.1", port), NammaSpaceHandler)
    print("=" * 70, flush=True)
    print(f"  NAMMA SPACE AUTONOMOUS WEB PORTAL & PIPELINE", flush=True)
    print(f"  Live Server: http://127.0.0.1:{port}/index.html", flush=True)
    print(f"  Direct Video Upload API: http://127.0.0.1:{port}/api/upload", flush=True)
    print("=" * 70, flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer terminated.", flush=True)
