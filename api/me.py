# -*- coding: utf-8 -*-
from vwrap import reply, cookie_of
from handlers import handle_me


def handler(req, resp):
    reply(resp, handle_me(cookie_of(req)))
