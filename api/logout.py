# -*- coding: utf-8 -*-
from vwrap import reply
from handlers import handle_logout


def handler(req, resp):
    reply(resp, handle_logout())
