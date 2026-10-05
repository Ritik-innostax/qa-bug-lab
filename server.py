#!/usr/bin/env python3
"""Local server for the QA Scanner Functional Bug Lab.

Serves ``site/`` as static files and answers two JSON endpoints used by the forms:

    POST /api/contact    {"name", "email", "message"} -> 200 {"ok": true} | 400 {"ok": false, "error"}
    POST /api/subscribe  {"email"}                    -> 200 {"ok": true} | 400 {"ok": false, "error"}

Standard library only. Missing paths answer a real HTTP 404 with ``site/404.html``; directory
listings are disabled. Only ``site/`` is served, so ``expected_bugs.json`` and the README are
never reachable from the browser.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from functools import partial
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

SITE_DIR = Path(__file__).resolve().parent / "site"
NOT_FOUND_PAGE = SITE_DIR / "404.html"
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MAX_BODY_BYTES = 64 * 1024


def _text(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    return value.strip() if isinstance(value, str) else ""


def validate_contact(payload: dict[str, Any]) -> str | None:
    if not _text(payload, "name"):
        return "Please enter your name."
    if not EMAIL_RE.match(_text(payload, "email")):
        return "Please enter a valid email address."
    if not _text(payload, "message"):
        return "Please enter a message."
    return None


def validate_subscribe(payload: dict[str, Any]) -> str | None:
    if not EMAIL_RE.match(_text(payload, "email")):
        return "Please enter a valid email address."
    return None


API_ROUTES = {
    "/api/contact": validate_contact,
    "/api/subscribe": validate_subscribe,
}


class LabHandler(SimpleHTTPRequestHandler):
    verbose = False

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def list_directory(self, path: str) -> None:  # type: ignore[override]
        self.send_error(HTTPStatus.NOT_FOUND)
        return None

    def send_error(self, code: int, message: str | None = None, explain: str | None = None) -> None:
        if code != HTTPStatus.NOT_FOUND:
            super().send_error(code, message, explain)
            return
        body = NOT_FOUND_PAGE.read_bytes()
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def do_POST(self) -> None:
        validator = API_ROUTES.get(self.path.split("?", 1)[0])
        if validator is None:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        length = int(self.headers.get("Content-Length") or 0)
        if length > MAX_BODY_BYTES:
            self._send_json(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"ok": False, "error": "Request too large."})
            return
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
        except (json.JSONDecodeError, UnicodeDecodeError):
            payload = None
        if not isinstance(payload, dict):
            self._send_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": "Request body must be a JSON object."})
            return
        error = validator(payload)
        if error:
            self._send_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": error})
        else:
            self._send_json(HTTPStatus.OK, {"ok": True})

    def _send_json(self, status: HTTPStatus, body: dict[str, Any]) -> None:
        encoded = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format: str, *args: Any) -> None:
        if self.verbose:
            super().log_message(format, *args)


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve the QA Scanner Functional Bug Lab.")
    parser.add_argument("--host", default=os.environ.get("HOST", "127.0.0.1"),
                        help="Bind address (default $HOST or 127.0.0.1; use 0.0.0.0 when hosted).")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8765")),
                        help="Port to listen on (default $PORT or 8765).")
    parser.add_argument("--verbose", action="store_true", help="Log every request.")
    args = parser.parse_args()

    LabHandler.verbose = args.verbose
    handler = partial(LabHandler, directory=str(SITE_DIR))
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(f"Bug lab serving {SITE_DIR} at http://{args.host}:{args.port}/", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
