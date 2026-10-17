# -*- coding: utf-8 -*-
"""Sessions stateless : token signé (HMAC) envoyé en cookie.
Fonctionne sur Vercel car aucune mémoire serveur n'est nécessaire."""
import base64
import hashlib
import hmac
import json
import time

import config


def _b64e(b):
    return base64.urlsafe_b64encode(b).decode().rstrip("=")


def _b64d(s):
    s = s + "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s.encode())


def _sign(payload_b):
    return hmac.new(config.SECRET.encode(), payload_b, hashlib.sha256).digest()


def create_token(name, role):
    payload = json.dumps(
        {"name": name, "role": role, "exp": int(time.time()) + config.SESSION_DAYS * 86400},
        separators=(",", ":"),
    ).encode("utf-8")
    return _b64e(payload) + "." + _b64e(_sign(payload))


def read_token(token):
    """Retourne {name, role, exp} si le token est valide, sinon None."""
    try:
        p, s = token.split(".")
        payload = _b64d(p)
        if not hmac.compare_digest(_sign(payload), _b64d(s)):
            return None
        d = json.loads(payload)
        if d.get("exp", 0) < time.time():
            return None
        return d
    except Exception:
        return None
