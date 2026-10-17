# -*- coding: utf-8 -*-
"""Teste les handlers Vercel (api/*.py) avec de faux objets req/resp.
Lancer : python3 tests/local_test.py"""
import importlib.util
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def load(path, alias):
    spec = importlib.util.spec_from_file_location(alias, os.path.join(ROOT, path))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


api_login = load("api/login.py", "api_login")
api_logout = load("api/logout.py", "api_logout")
api_me = load("api/me.py", "api_me")
api_pdfs = load("api/pdfs.py", "api_pdfs")
api_pdf_name = load("api/pdfs/[name].py", "api_pdf_name")
api_upload = load("api/upload.py", "api_upload")

import storage


class Req:
    def __init__(self, method="GET", body=b"", headers=None, query=None):
        self.method = method
        self.body = body
        self.headers = headers or {}
        self.query_params = query or {}


class Resp:
    def __init__(self):
        self.status_code = 0
        self.headers = {}
        self.body = b""


def call(mod, req):
    r = Resp()
    mod.handler(req, r)
    return r


PASS = 0
FAIL = 0


def check(label, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
        print("  PASS  " + label)
    else:
        FAIL += 1
        print("  FAIL  " + label)


def tok_of(resp):
    c = resp.headers.get("Set-Cookie", "")
    for part in c.split(";"):
        if part.strip().startswith("hl_session="):
            return part.strip()[len("hl_session="):]
    return None


print("== Connexion ==")
r = call(api_me, Req())
check("me sans session -> ok:false", json.loads(r.body)["ok"] is False)

r = call(api_login, Req("POST", json.dumps({"name": "Test", "password": "nope"}).encode()))
check("mauvais mot de passe refuse", json.loads(r.body)["ok"] is False)

r = call(api_login, Req("POST", json.dumps({"name": "Koffi", "password": "hackerlab2026"}).encode()))
stu = tok_of(r)
check("login etudiant ok", json.loads(r.body)["ok"] is True and bool(stu))

r = call(api_me, Req(headers={"cookie": "hl_session=" + stu}))
check("me etudiant -> nom + role", json.loads(r.body) == {"ok": True, "name": "Koffi", "role": "student"})

r = call(api_login, Req("POST", json.dumps({"name": "Prof", "password": "admin2026"}).encode()))
adm = tok_of(r)
check("login admin ok", json.loads(r.body)["ok"] is True and bool(adm))

print("== Upload / lecture PDF ==")
r = call(api_pdfs, Req())
check("liste sans session -> 401", r.status_code == 401)

data = os.urandom(10000)
CHUNK = 4000
parts = [data[i:i + CHUNK] for i in range(0, len(data), CHUNK)]
nparts = len(parts)

r = call(api_upload, Req("POST", b"", {"cookie": "hl_session=" + stu},
                         {"name": "cours.pdf", "size": str(len(data)),
                          "chunks": str(nparts), "index": "0"}))
check("upload par etudiant refuse (403)", r.status_code == 403)

saved = None
ok_all = True
for i, p in enumerate(parts):
    r = call(api_upload, Req("POST", p, {"cookie": "hl_session=" + adm},
                             {"name": (saved or "cours.pdf"), "size": str(len(data)),
                              "chunks": str(nparts), "index": str(i)}))
    d = json.loads(r.body)
    if not d.get("ok"):
        ok_all = False
        break
    saved = d["saved"]
check("upload admin en %d morceaux ok" % nparts, ok_all and saved == "cours.pdf")

r = call(api_pdfs, Req(headers={"cookie": "hl_session=" + stu}))
lst = json.loads(r.body)["pdfs"]
check("etudiant voit 1 pdf complet", len(lst) == 1 and lst[0]["complete"] is True
      and lst[0]["size"] == len(data))

r = call(api_pdf_name, Req(query={"name": "cours.pdf"}, headers={"cookie": "hl_session=" + stu}))
check("lecture pdf ok (contenu identique)", r.status_code == 200 and r.body == data
      and r.headers.get("Content-Type") == "application/pdf")

r = call(api_pdf_name, Req(query={"name": "cours.pdf"}))
check("lecture sans session -> 401", r.status_code == 401)

r = call(api_pdf_name, Req(query={"name": "../config.py"}, headers={"cookie": "hl_session=" + adm}))
check("traversal de chemin bloque (400)", r.status_code == 400)

r = call(api_upload, Req("POST", b"%PDF", {"cookie": "hl_session=" + adm},
                         {"name": "cours.pdf", "size": "4", "chunks": "1", "index": "0"}))
check("memes nom -> dedup cours_2.pdf", json.loads(r.body)["saved"] == "cours_2.pdf")

r = call(api_pdfs, Req(headers={"cookie": "hl_session=" + adm}))
check("liste admin -> 2 pdfs", len(json.loads(r.body)["pdfs"]) == 2)

print("== Upload incomplet (interrompu) ==")
r = call(api_upload, Req("POST", b"x" * 100, {"cookie": "hl_session=" + adm},
                         {"name": "incomplet.pdf", "size": "200", "chunks": "2", "index": "0"}))
check("1er morceau accepte", json.loads(r.body)["ok"] is True)

r = call(api_pdfs, Req(headers={"cookie": "hl_session=" + stu}))
check("etudiant ne voit PAS l'incomplet",
      all(p["name"] != "incomplet.pdf" for p in json.loads(r.body)["pdfs"]))

r = call(api_pdfs, Req(headers={"cookie": "hl_session=" + adm}))
check("admin voit l'incomplet (complete:false)",
      any(p["name"] == "incomplet.pdf" and p["complete"] is False
          for p in json.loads(r.body)["pdfs"]))

print("== Suppression ==")
r = call(api_pdf_name, Req("DELETE", query={"name": "cours.pdf"},
                           headers={"cookie": "hl_session=" + stu}))
check("suppression par etudiant refuse (403)", r.status_code == 403)

r = call(api_pdf_name, Req("DELETE", query={"name": "cours.pdf"},
                           headers={"cookie": "hl_session=" + adm}))
check("suppression admin ok", json.loads(r.body)["ok"] is True)

r = call(api_pdfs, Req(headers={"cookie": "hl_session=" + adm}))
names = [p["name"] for p in json.loads(r.body)["pdfs"]]
check("cours.pdf bien supprime", "cours.pdf" not in names)

for n in ("cours_2.pdf", "incomplet.pdf"):
    storage.delete_pdf(n)

print()
print("RESULTAT: %d ok, %d ko" % (PASS, FAIL))
sys.exit(1 if FAIL else 0)
