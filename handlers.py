# -*- coding: utf-8 -*-
"""Logique métier partagée par Vercel (api/*.py) et le serveur local (server.py).
Chaque fonction retourne : (body_bytes, status, headers_dict, set_cookie_or_None)"""
import json
import re

import config
import session
import storage


def _j(data, status=200, set_cookie=None):
    body = json.dumps(data, ensure_ascii=False).encode("utf-8")
    return body, status, {"Content-Type": "application/json; charset=utf-8"}, set_cookie


def _user(cookie_token):
    return session.read_token(cookie_token) if cookie_token else None


def _safe_name(name):
    name = (name or "").strip()
    if not name or "/" in name or "\\" in name or name in (".", ".."):
        return None
    return name


def _sanitize(name):
    name = (name or "").replace("\\", "/").split("/")[-1]
    name = re.sub(r"[^A-Za-z0-9 ._-]", "_", name).strip()
    return name or "cours"


def handle_login(body, cookie_token=None):
    try:
        d = json.loads((body or b"").decode("utf-8"))
    except Exception:
        return _j({"ok": False, "error": "bad request"}, 400)
    name = (d.get("name") or "").strip()
    pwd = d.get("password") or ""
    if len(name) < 2:
        return _j({"ok": False, "error": "Entre ton nom (2 caractères minimum)."})
    if pwd == config.ADMIN_PASSWORD:
        role = "admin"
    elif pwd == config.STUDENT_PASSWORD:
        role = "student"
    else:
        return _j({"ok": False, "error": "Nom ou mot de passe incorrect."})
    token = session.create_token(name, role)
    cookie = "hl_session=%s; Path=/; HttpOnly; SameSite=Lax; Max-Age=%d" % (
        token, config.SESSION_DAYS * 86400)
    return _j({"ok": True, "name": name, "role": role}, 200, set_cookie=cookie)


def handle_logout():
    return _j({"ok": True}, 200, set_cookie="hl_session=; Path=/; Max-Age=0")


def handle_me(cookie_token):
    u = _user(cookie_token)
    if u:
        return _j({"ok": True, "name": u["name"], "role": u["role"]})
    return _j({"ok": False})


def handle_pdf_list(cookie_token):
    u = _user(cookie_token)
    if not u:
        return _j({"ok": False, "error": "auth"}, 401)
    items = storage.list_pdfs(admin=(u["role"] == "admin"))
    return _j({"ok": True, "pdfs": items})


def handle_pdf_get(name, cookie_token):
    u = _user(cookie_token)
    if not u:
        return _j({"ok": False, "error": "auth"}, 401)
    name = _safe_name(name)
    if not name:
        return _j({"ok": False, "error": "bad name"}, 400)
    data = storage.get_pdf(name)
    if data is None:
        return _j({"ok": False, "error": "not found"}, 404)
    return data, 200, {"Content-Type": "application/pdf"}, None


def handle_pdf_delete(name, cookie_token):
    u = _user(cookie_token)
    if not u:
        return _j({"ok": False, "error": "auth"}, 401)
    if u["role"] != "admin":
        return _j({"ok": False, "error": "Réservé à l'admin."}, 403)
    name = _safe_name(name)
    if not name:
        return _j({"ok": False, "error": "bad name"}, 400)
    storage.delete_pdf(name)
    return _j({"ok": True})


def handle_upload(body, params, cookie_token):
    """Upload par morceaux : POST /api/upload?name=X&size=N&chunks=C&index=i
    Le corps de la requête = le morceau binaire (<= 3.5 Mo par requête,
    pour rester sous la limite Vercel de 4.5 Mo)."""
    u = _user(cookie_token)
    if not u:
        return _j({"ok": False, "error": "auth"}, 401)
    if u["role"] != "admin":
        return _j({"ok": False, "error": "Réservé à l'admin."}, 403)
    try:
        size = int(params.get("size") or 0)
        chunks = int(params.get("chunks") or 1)
        index = int(params.get("index") or 0)
    except Exception:
        return _j({"ok": False, "error": "bad request"}, 400)
    if chunks < 1 or index < 0 or index >= chunks:
        return _j({"ok": False, "error": "bad request"}, 400)
    name = _sanitize(params.get("name") or "")
    if not name.lower().endswith(".pdf"):
        return _j({"ok": False, "error": "Seuls les fichiers .pdf sont acceptés."})
    if index == 0:
        final = storage.dedup_name(name)
        storage.begin_upload(final, size, chunks, body or b"")
    else:
        final = name
        r = storage.append_upload(final, body or b"", index, chunks)
        if r == "no_upload":
            return _j({"ok": False, "error": "Upload introuvable, recommence depuis le début."}, 400)
    done = (index == chunks - 1)
    return _j({"ok": True, "done": done, "saved": final})
