#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Serveur local de développement — mêmes handlers que Vercel.
Utile pour tester sur ton ordi :  python3 server.py"""
import os
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote

import handlers

BASE = os.path.dirname(os.path.abspath(__file__))
INDEX = os.path.join(BASE, "index.html")
PORT = 8000


def cookie_from(raw):
    for part in (raw or "").split(";"):
        part = part.strip()
        if part.startswith("hl_session="):
            return part[len("hl_session="):]
    return None


class H(BaseHTTPRequestHandler):
    def _read(self):
        n = int(self.headers.get("Content-Length", 0) or 0)
        return self.rfile.read(n) if n else b""

    def _write(self, out):
        body, status, headers, set_cookie = out
        self.send_response(status)
        for k, v in headers.items():
            self.send_header(k, v)
        if set_cookie:
            self.send_header("Set-Cookie", set_cookie)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _static(self, path, ctype):
        try:
            with open(path, "rb") as fh:
                data = fh.read()
        except OSError:
            return self._write((b'{"ok":false,"error":"not found"}', 404,
                                {"Content-Type": "application/json"}, None))
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _dispatch(self, method):
        u = urlparse(self.path)
        path = u.path
        qs = {k: v[0] for k, v in parse_qs(u.query).items()}
        body = self._read()
        tok = cookie_from(self.headers.get("Cookie"))

        if path in ("/", "/index.html"):
            return self._static(INDEX, "text/html; charset=utf-8")
        if path == "/api/login" and method == "POST":
            return self._write(handlers.handle_login(body, tok))
        if path == "/api/logout":
            return self._write(handlers.handle_logout())
        if path == "/api/me":
            return self._write(handlers.handle_me(tok))
        if path == "/api/pdfs" and method == "GET":
            return self._write(handlers.handle_pdf_list(tok))
        if path == "/api/upload" and method == "POST":
            return self._write(handlers.handle_upload(body, qs, tok))
        if path.startswith("/api/pdfs/"):
            name = unquote(path[len("/api/pdfs/"):])
            if method == "DELETE":
                return self._write(handlers.handle_pdf_delete(name, tok))
            return self._write(handlers.handle_pdf_get(name, tok))
        return self._write((b'{"ok":false,"error":"not found"}', 404,
                            {"Content-Type": "application/json"}, None))

    def do_GET(self):
        self._dispatch("GET")

    def do_POST(self):
        self._dispatch("POST")

    def do_DELETE(self):
        self._dispatch("DELETE")

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    print("Hacker Lab (local): http://0.0.0.0:%d" % PORT)
    ThreadingHTTPServer(("0.0.0.0", PORT), H).serve_forever()
