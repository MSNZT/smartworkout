import base64
import hashlib
import hmac
import json
import time

from app.errors.auth import TokenExpiredError, TokenInvalidError


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64decode(s: str) -> bytes:
    padding = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + padding)


def _sign(payload_b64: str, secret: str) -> str:
    sig = hmac.new(
        secret.encode(),
        payload_b64.encode(),
        hashlib.sha256,
    ).digest()
    return _b64encode(sig)


def issue(payload: dict, secret: str, ttl_seconds: int = 7 * 24 * 3600) -> str:
    data = {
        **payload,
        "exp": int(time.time()) + ttl_seconds,
    }
    payload_b64 = _b64encode(json.dumps(data, separators=(",", ":")).encode())
    signature = _sign(payload_b64, secret)
    return f"{payload_b64}.{signature}"


def verify(token: str, secret: str) -> dict:
    try:
        payload_b64, signature = token.split(".")
    except ValueError:
        raise TokenInvalidError()

    expected = _sign(payload_b64, secret)
    if not hmac.compare_digest(signature, expected):
        raise TokenInvalidError()

    try:
        data = json.loads(_b64decode(payload_b64))
    except (ValueError, json.JSONDecodeError):
        raise TokenInvalidError()

    if data.get("exp", 0) < int(time.time()):
        raise TokenExpiredError()

    return data