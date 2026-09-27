from dataclasses import dataclass, field
from http import HTTPStatus


@dataclass
class Response:
    status: int
    body: dict | list | None = None
    headers: list[tuple[str, str]] = field(default_factory=list)


def json_response(body, status: int = HTTPStatus.OK, headers=None) -> Response:
    return Response(status=int(status), body=body, headers=list(headers or []))


def error_response(payload: dict, status: int, headers=None) -> Response:
    return Response(status=int(status), body=payload, headers=list(headers or []))