# -*- coding: utf-8 -*-
"""POST /api/upload?name=X&size=N&chunks=C&index=i
Corps = morceau binaire du PDF (upload par morceaux)."""
from vwrap import reply, cookie_of
from handlers import handle_upload


def handler(req, resp):
    b = req.body or b""
    if isinstance(b, str):
        b = b.encode("utf-8")
    reply(resp, handle_upload(b, dict(req.query_params or {}), cookie_of(req)))
