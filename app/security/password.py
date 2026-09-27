import base64
import hashlib
import hmac
import secrets

ALGORITHM = "pbkdf2_sha256"
ITERATIONS = 600_000
SALT_BYTES = 16
KEY_BYTES = 32


def _b64e(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _b64d(data: str) -> bytes:
    return base64.b64decode(data.encode("ascii"), validate=True)


def hash_password(password: str) -> str:
    if not isinstance(password, str):
        raise TypeError("password must be a string")

    salt = secrets.token_bytes(SALT_BYTES)

    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        ITERATIONS,
        dklen=KEY_BYTES,
    )

    return f"{ALGORITHM}${ITERATIONS}${_b64e(salt)}${_b64e(dk)}"


def verify_password(password: str, stored: str) -> bool:
    if not isinstance(password, str) or not isinstance(stored, str):
        return False

    try:
        algorithm, iterations_s, salt_s, hash_s = stored.split("$")
        if algorithm != ALGORITHM:
            return False

        iterations = int(iterations_s)
        salt = _b64d(salt_s)
        expected = _b64d(hash_s)
    except (ValueError, TypeError):
        return False

    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
        dklen=len(expected),
    )

    return hmac.compare_digest(dk, expected)