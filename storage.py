# -*- coding: utf-8 -*-
"""Stockage des cours PDF.
- Sur Vercel  : Vercel Blob (persistant, quota gratuit)
- En local    : fichiers dans le dossier pdfs/ (dev)
"""
import json
import os
import time
from datetime import datetime, timezone

PREFIX = "pdfs/"
IS_VERCEL = bool(os.environ.get("VERCEL"))
_LOCAL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pdfs")
os.makedirs(_LOCAL_DIR, exist_ok=True)

if IS_VERCEL:
    # SDK officiel Vercel — version SYNCHRONE (vercel.blob.sync)
    from vercel.blob.sync import put_blob, get_blob, delete_blob, query_blobs

    # Mode du store Blob : "private" (recommande) ou "public"
    ACCESS = os.environ.get("BLOB_ACCESS", "private")

    def _meta_name(name):
        return PREFIX + ".meta/" + name + ".json"

    def _all_pdfs():
        out = []
        for b in query_blobs(prefix=PREFIX):
            if b.pathname.startswith(PREFIX + ".meta"):
                continue
            out.append(b)
        return out

    def _read_meta(name):
        try:
            return json.loads(get_blob(_meta_name(name), access=ACCESS).body.decode("utf-8"))
        except Exception:
            return None

    def _write_meta(name, meta):
        put_blob(_meta_name(name), json.dumps(meta).encode("utf-8"),
                 access=ACCESS, content_type="application/json", allow_overwrite=True)

    def begin_upload(name, size, chunks, data):
        put_blob(PREFIX + name, data, access=ACCESS,
                 content_type="application/pdf", allow_overwrite=True)
        _write_meta(name, {"name": name, "size": size, "chunks": chunks,
                           "received": len(data), "done": False})

    def append_upload(name, data, index, chunks):
        """Le SDK 2026 n'a plus d'append : on relit le blob et on re-pousse
        le tout (fichiers de cours = quelques Mo, c'est négligeable)."""
        meta = _read_meta(name)
        if meta is None:
            return "no_upload"
        cur = get_blob(PREFIX + name, access=ACCESS).body
        put_blob(PREFIX + name, cur + data, access=ACCESS,
                 content_type="application/pdf", allow_overwrite=True)
        meta["received"] = meta.get("received", 0) + len(data)
        if index == chunks - 1:
            meta["done"] = True
        _write_meta(name, meta)
        return "ok"

    def get_pdf(name):
        meta = _read_meta(name)
        if not meta or not meta.get("done"):
            return None
        return get_blob(PREFIX + name, access=ACCESS).body

    def list_pdfs(admin=False):
        items = []
        for b in _all_pdfs():
            short = b.pathname[len(PREFIX):]
            meta = _read_meta(short)
            complete = bool(meta and meta.get("done"))
            if complete or admin:
                try:
                    dt = b.uploaded_at
                    if isinstance(dt, (int, float)):
                        dt = datetime.fromtimestamp(dt, tz=timezone.utc)
                    date = dt.strftime("%d/%m/%Y %H:%M")
                except Exception:
                    date = ""
                items.append({"name": short, "size": b.size, "date": date, "complete": complete})
        items.sort(key=lambda x: x["name"])
        return items

    def delete_pdf(name):
        for p in (PREFIX + name, _meta_name(name)):
            try:
                delete_blob(p)
            except Exception:
                pass
        return True

    def exists_pdf(name):
        try:
            get_blob(PREFIX + name, access=ACCESS)
            return True
        except Exception:
            return False

else:
    def _f(name):
        return os.path.join(_LOCAL_DIR, name)

    def _mf(name):
        return os.path.join(_LOCAL_DIR, name + ".meta.json")

    def _all_pdfs():
        class F:
            def __init__(self, name, size, mtime):
                self.name = PREFIX + name
                self.size = size
                self.mtime = mtime
        out = []
        for fn in os.listdir(_LOCAL_DIR):
            if fn.endswith(".pdf") and os.path.isfile(_f(fn)):
                st = os.stat(_f(fn))
                out.append(F(fn, st.st_size, st.st_mtime))
        return out

    def _read_meta(name):
        try:
            with open(_mf(name), "r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            return None

    def _write_meta(name, meta):
        with open(_mf(name), "w", encoding="utf-8") as fh:
            json.dump(meta, fh)

    def begin_upload(name, size, chunks, data):
        with open(_f(name), "wb") as fh:
            fh.write(data)
        _write_meta(name, {"name": name, "size": size, "chunks": chunks,
                           "received": len(data), "done": False})

    def append_upload(name, data, index, chunks):
        meta = _read_meta(name)
        if meta is None:
            return "no_upload"
        with open(_f(name), "ab") as fh:
            fh.write(data)
        meta["received"] = meta.get("received", 0) + len(data)
        if index == chunks - 1:
            meta["done"] = True
        _write_meta(name, meta)
        return "ok"

    def get_pdf(name):
        meta = _read_meta(name)
        if not meta or not meta.get("done"):
            return None
        with open(_f(name), "rb") as fh:
            return fh.read()

    def list_pdfs(admin=False):
        items = []
        for b in _all_pdfs():
            short = b.name[len(PREFIX):]
            meta = _read_meta(short)
            complete = bool(meta and meta.get("done"))
            if complete or admin:
                items.append({"name": short, "size": b.size,
                              "date": time.strftime("%d/%m/%Y %H:%M", time.localtime(b.mtime)),
                              "complete": complete})
        items.sort(key=lambda x: x["name"])
        return items

    def delete_pdf(name):
        for p in (_f(name), _mf(name)):
            if os.path.exists(p):
                os.remove(p)
        return True

    def exists_pdf(name):
        return os.path.isfile(_f(name))


def dedup_name(name):
    """Évite les collisions : cours.pdf -> cours_2.pdf, cours_3.pdf..."""
    if not exists_pdf(name):
        return name
    base, ext = os.path.splitext(name)
    i = 2
    while exists_pdf("%s_%d%s" % (base, i, ext)):
        i += 1
    return "%s_%d%s" % (base, i, ext)
