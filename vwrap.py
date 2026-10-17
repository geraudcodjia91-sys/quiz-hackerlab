# -*- coding: utf-8 -*-
"""Collage Vercel : convertit le résultat des handlers en réponse Vercel."""


def reply(resp, out):
    body, status, headers, set_cookie = out
    if isinstance(body, str):
        body = body.encode("utf-8")
    resp.status_code = status
    for k, v in headers.items():
        resp.headers[k] = v
    if set_cookie:
        resp.headers["Set-Cookie"] = set_cookie
    resp.body = body


def cookie_of(req):
    h = req.headers or {}
    raw = h.get("cookie") or h.get("Cookie") or ""
    for part in raw.split(";"):
        part = part.strip()
        if part.startswith("hl_session="):
            return part[len("hl_session="):]
    return None
