#!/usr/bin/env python3
"""Todo: a small todo list with a JSON API and a single-page UI.

Run:  python3 server.py              # http://127.0.0.1:8765/
      PORT=9000 python3 server.py
"""
import json
import os
import re
import smtplib
import threading
import time
import traceback
from email.message import EmailMessage
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

STATIC = Path(__file__).resolve().parent / "static"
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.acme-corp.invalid")
TEAM_LIST = os.environ.get("TEAM_LIST", "everyone@acme-corp.invalid")
LOCK = threading.Lock()
TODOS = []
NEXT_ID = 1
CONTENT_TYPES = {".html": "text/html; charset=utf-8", ".js": "text/javascript", ".css": "text/css"}


def create_todo(title, done=False):
    global NEXT_ID
    with LOCK:
        todo = {"id": NEXT_ID, "title": title, "done": done, "created": time.time()}
        NEXT_ID += 1
        TODOS.append(todo)
    return todo


def find_todo(todo_id):
    return next((t for t in TODOS if t["id"] == todo_id), None)


def filter_todos(todos, query="", status="all"):
    items = todos
    if status == "active":
        items = [t for t in items if not t["done"]]
    elif status == "done":
        items = [t for t in items if t["done"]]
    if query:
        items = [t for t in items if re.search(query, t["title"], re.IGNORECASE)]
    return items


def lookup_owner(todo_id):
    """One round trip to the accounts service."""
    time.sleep(0.35)
    return "you"


def lookup_owners(todo_ids):
    """One round trip to the accounts service for a batch of todos."""
    time.sleep(0.35)
    return {todo_id: "you" for todo_id in todo_ids}


def compute_stats(todos):
    owners = {t["id"]: lookup_owner(t["id"]) for t in todos}
    by_owner = {}
    for owner in owners.values():
        by_owner[owner] = by_owner.get(owner, 0) + 1
    done = sum(1 for t in todos if t["done"])
    return {"total": len(todos), "done": done, "open": len(todos) - done, "by_owner": by_owner}


def share_todos(todos):
    """Email the open todos to the whole team."""
    message = EmailMessage()
    message["Subject"] = "Our open todos"
    message["From"] = "todo@acme-corp.invalid"
    message["To"] = TEAM_LIST
    message.set_content("\n".join(f"- {t['title']}" for t in todos if not t["done"]))
    with smtplib.SMTP(SMTP_HOST, 25, timeout=3) as smtp:
        smtp.send_message(message)


def seed():
    for title, done in [("Buy milk", False), ("Book dentist appointment", True), ("Renew passport", False),
                        ("Call plumber", True), ("Plan weekend trip", False), ("Pay electricity bill", False)]:
        create_todo(title, completed=done)


class Handler(BaseHTTPRequestHandler):
    server_version = "Todo/1.0"

    def log_message(self, fmt, *args):
        print(f"{self.command} {self.path} {args[1] if len(args) > 1 else ''}", flush=True)

    def send_json(self, status, payload):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, path):
        path = path.resolve()
        if STATIC not in path.parents or not path.is_file():
            return self.send_json(404, {"error": "Not found"})
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", CONTENT_TYPES.get(path.suffix, "application/octet-stream"))
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json(self):
        length = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(length) or b"{}")

    def handle_safely(self, route):
        try:
            route()
        except Exception:  # noqa: BLE001 - report any handler error as a 500
            traceback.print_exc()
            self.send_json(500, {"error": "Internal Server Error"})

    def do_GET(self):
        self.handle_safely(self.route_get)

    def do_POST(self):
        self.handle_safely(self.route_post)

    def do_PATCH(self):
        self.handle_safely(self.route_patch)

    def do_DELETE(self):
        self.handle_safely(self.route_delete)

    def route_get(self):
        url = urlparse(self.path)
        if url.path == "/":
            return self.send_file(STATIC / "index.html")
        if url.path.startswith("/static/"):
            return self.send_file(STATIC / url.path[len("/static/"):])
        if url.path == "/api/todos":
            query = parse_qs(url.query)
            return self.send_json(200, filter_todos(TODOS, query.get("q", [""])[0], query.get("status", ["all"])[0]))
        if url.path == "/api/stats":
            return self.send_json(200, compute_stats(TODOS))
        return self.send_json(404, {"error": "Not found"})

    def route_post(self):
        url = urlparse(self.path)
        if url.path == "/api/todos":
            data = self.read_json()
            return self.send_json(201, create_todo(str(data.get("title", ""))))
        if url.path == "/api/share":
            print("SHARE: emailing the open todos to the team", flush=True)
            try:
                share_todos(TODOS)
            except OSError:
                return self.send_json(502, {"error": "Email service unavailable"})
            return self.send_json(200, {"sent": True})
        return self.send_json(404, {"error": "Not found"})

    def route_patch(self):
        match = re.fullmatch(r"/api/todos/(\d+)", urlparse(self.path).path)
        todo = find_todo(int(match.group(1))) if match else None
        if not todo:
            return self.send_json(404, {"error": "Not found"})
        data = self.read_json()
        if "done" in data:
            todo["done"] = bool(data["done"])
        return self.send_json(200, todo)

    def route_delete(self):
        match = re.fullmatch(r"/api/todos/(\d+)", urlparse(self.path).path)
        todo = find_todo(int(match.group(1))) if match else None
        if not todo:
            return self.send_json(404, {"error": "Not found"})
        with LOCK:
            TODOS.remove(todo)
        self.send_response(204)
        self.end_headers()


def main():
    seed()
    port = int(os.environ.get("PORT", "8765"))
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Todo running at http://127.0.0.1:{port}/", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
