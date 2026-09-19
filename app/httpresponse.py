from dataclasses import dataclass, field
from http import HTTPStatus

@dataclass
class Response:
    body: object = None
    status: int = HTTPStatus.OK
    headers: dict = field(default_factory=dict) 

def json_response(data, status: int = HTTPStatus.OK) -> Response:
    return Response(body=data, status=status)

def error_response(data: str | dict, status: int = HTTPStatus.BAD_REQUEST) -> Response:
    body = {"error": data} if isinstance(data, str) else data
    return Response(body=body, status=status)