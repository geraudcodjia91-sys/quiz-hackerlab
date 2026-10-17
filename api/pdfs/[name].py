# -*- coding: utf-8 -*-
"""GET    /api/pdfs/<name>  -> sert le PDF (connexion requise)
   DELETE /api/pdfs/<name>  -> supprime le PDF (admin)"""
from urllib.parse import unquote

from vwrap import reply, cookie_of
from handlers import handle_pdf_get, handle_pdf_delete


def handler(req, resp):
    name = unquote((req.query_params or {}).get("name", ""))
    tok = cookie_of(req)
    if (req.method or "").upper() == "DELETE":
        reply(resp, handle_pdf_delete(name, tok))
    else:
        reply(resp, handle_pdf_get(name, tok))
