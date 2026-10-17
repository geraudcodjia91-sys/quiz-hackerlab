# -*- coding: utf-8 -*-
from vwrap import reply, cookie_of
from handlers import handle_pdf_list


def handler(req, resp):
    reply(resp, handle_pdf_list(cookie_of(req)))
