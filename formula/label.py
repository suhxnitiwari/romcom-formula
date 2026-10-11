"""The tagging sheet: a local page where Suhani marks the tropes in books she's read.

Her answers are the ground truth the trope detector is graded against. Every tick
is saved straight to data/labels.json. The page only runs on this computer,
because it shows publisher blurbs that aren't ours to publish.
"""
import json
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .hardcover import ROOT
from .tropes import TROPES

BOOKS = ROOT / "data" / "books.json"
LABELS = ROOT / "data" / "labels.json"
PAGE = ROOT / "web" / "label.html"


def sheet_books():
    keep = ("id", "title", "author", "year", "description", "favorite", "readers", "shelf")
    return [{k: b[k] for k in keep} for b in json.loads(BOOKS.read_text())]


class Sheet(BaseHTTPRequestHandler):
    def send(self, body, kind="application/json"):
        data = body.encode() if isinstance(body, str) else body
        self.send_response(200)
        self.send_header("content-type", kind + "; charset=utf-8")
        self.send_header("cache-control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/":
            self.send(PAGE.read_bytes(), "text/html")
        elif self.path == "/data":
            labels = json.loads(LABELS.read_text()) if LABELS.exists() else {}
            tropes = [{"key": k, "name": n, "means": m} for k, (n, m) in TROPES.items()]
            self.send(json.dumps({"books": sheet_books(), "tropes": tropes, "labels": labels}))
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path != "/labels":
            return self.send_error(404)
        labels = json.loads(self.rfile.read(int(self.headers["content-length"])))
        LABELS.write_text(json.dumps(labels, indent=1, ensure_ascii=False, sort_keys=True))
        self.send('{"saved": true}')

    def log_message(self, *args):
        pass


def serve(port=8870, open_browser=True):
    server = ThreadingHTTPServer(("127.0.0.1", port), Sheet)
    url = f"http://127.0.0.1:{port}/"
    print(f"Tagging sheet: {url}  (Ctrl+C to stop; every tick is already saved)")
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
