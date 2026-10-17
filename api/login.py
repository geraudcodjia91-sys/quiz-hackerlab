# -*- coding: utf-8 -*-
from vwrap import reply, cookie_of
from handlers import handle_login


def handler(req, resp):
    b = req.body or b""
    if isinstance(b, str):
        b = b.encode("utf-8")
    reply(resp, handle_login(b, cookie_of(req)))
