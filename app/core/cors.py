import os
from http import HTTPStatus

from app.httpresponse import Response, error_response


ALLOWED_ORIGINS = {
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "").split(",")
    if origin.strip()
}

ALLOWED_METHODS = "GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS"
ALLOWED_HEADERS = "Authorization, Content-Type"


def cors_headers(origin: str | None) -> list[tuple[str, str]]:
    if origin not in ALLOWED_ORIGINS:
        return []

    return [
        ("Access-Control-Allow-Origin", origin),
        ("Access-Control-Allow-Credentials", "true"),
        ("Vary", "Origin"),
    ]


def preflight_response(headers) -> Response:
    origin = headers.get("Origin")

    if origin not in ALLOWED_ORIGINS:
        return error_response(
            {
                "code": "FORBIDDEN",
                "message": "CORS origin not allowed",
            },
            HTTPStatus.FORBIDDEN,
        )

    return Response(
        status=HTTPStatus.NO_CONTENT,
        headers=[
            *cors_headers(origin),
            ("Access-Control-Allow-Methods", ALLOWED_METHODS),
            ("Access-Control-Allow-Headers", ALLOWED_HEADERS),
            ("Access-Control-Max-Age", "600"),
        ],
    )