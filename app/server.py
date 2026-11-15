
import json
import logging
import socket
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from app.core.cookies import parse_cookies
from app.core.cors import cors_headers, preflight_response
from app.handlers import register_routes
from app.httpresponse import Response, error_response
from app.routing import router


MAX_BODY_SIZE = 1024 * 1024

log = logging.getLogger(__name__)


class SmartWorkoutServer(ThreadingHTTPServer):
    request_queue_size = 128


class HTTPRequestHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    timeout = 30
    server_version = "SmartWorkout"
    sys_version = ""

    def version_string(self):
        return "SmartWorkout"

    def _handle(self) -> None:
        self._response_started = False

        try:
            self._dispatch()
        except (BrokenPipeError, ConnectionResetError, TimeoutError):
            self.close_connection = True
        except Exception:
            self.close_connection = True
            log.exception("Unhandled HTTP server error")

            if not self._response_started:
                self._send(error_response(
                    {
                        "code": "INTERNAL_ERROR",
                        "message": "Internal server error",
                    },
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                ))

    def _read_body(self):
        lengths = self.headers.get_all("Content-Length", [])

        if self.headers.get("Transfer-Encoding") or len(lengths) > 1:
            return None, error_response(
                {
                    "code": "BAD_REQUEST",
                    "message": "invalid request headers",
                },
                HTTPStatus.BAD_REQUEST,
            )

        raw = lengths[0] if lengths else "0"

        if not raw or not raw.isascii() or not raw.isdigit():
            return None, error_response(
                {
                    "code": "BAD_REQUEST",
                    "message": "invalid Content-Length",
                },
                HTTPStatus.BAD_REQUEST,
            )

        raw = raw.lstrip("0") or "0"

        if len(raw) > len(str(MAX_BODY_SIZE)) or int(raw) > MAX_BODY_SIZE:
            return None, error_response(
                {
                    "code": "PAYLOAD_TOO_LARGE",
                    "message": "request body too large",
                },
                HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
            )

        length = int(raw)

        if length == 0:
            return None, None

        try:
            data = self.rfile.read(length)

            if len(data) != length:
                raise ValueError("incomplete request body")

            return json.loads(data), None

        except (ValueError, UnicodeError, RecursionError):
            return None, error_response(
                {
                    "code": "BAD_REQUEST",
                    "message": "invalid json body",
                },
                HTTPStatus.BAD_REQUEST,
            )

        except socket.timeout:
            return None, error_response(
                {
                    "code": "REQUEST_TIMEOUT",
                    "message": "request body timeout",
                },
                HTTPStatus.REQUEST_TIMEOUT,
            )

    def _dispatch(self) -> int:
        parsed = urlparse(self.path)
        path = parsed.path

        if self.command == "OPTIONS":
            self.close_connection = True
            response = preflight_response(self.headers)
            self._send(response)
            return int(response.status)

        method = "GET" if self.command == "HEAD" else self.command

        route, params, allowed = router.resolve(method, path)

        if route is None:
            # Unread body must not become the next HTTP request.
            self.close_connection = True

            if allowed:
                methods = {
                    item.method
                    for item in router.routes
                    if item.regex.fullmatch(path)
                }

                response = error_response(
                    {
                        "code": "METHOD_NOT_ALLOWED",
                        "message": "method not allowed",
                    },
                    HTTPStatus.METHOD_NOT_ALLOWED,
                    headers=[("Allow", ", ".join(sorted(methods)))],
                )
            else:
                response = error_response(
                    {
                        "code": "NOT_FOUND",
                        "message": "not found",
                    },
                    HTTPStatus.NOT_FOUND,
                )

            log.warning({
                "event": "http_route_error",
                "path": path,
                "status": int(response.status),
            })

            self._send(response)
            return int(response.status)

        body, err = self._read_body()

        if err is not None:
            self.close_connection = True
            log.warning({
                "event": "http_body_error",
                "path": path,
                "status": int(err.status),
            })
            self._send(err)
            return int(err.status)

        request = {
            "method": method,
            "path": path,
            "params": params,
            "query": {
                key: values[0]
                for key, values in parse_qs(parsed.query).items()
            },
            "headers": dict(self.headers),
            "cookies": parse_cookies(self.headers.get("Cookie")),
            "body": body,
        }

        result = route.handler(request)
        self._send(result)
        return int(result.status)

    def _send(self, response: Response) -> None:
        no_content = response.status == HTTPStatus.NO_CONTENT

        payload = b"" if no_content else json.dumps(
            response.body if response.body is not None else {},
            ensure_ascii=True,
        ).encode("utf-8")

        self._response_started = True
        self.send_response(response.status)

        if not no_content:
            self.send_header(
                "Content-Type",
                "application/json; charset=utf-8",
            )
            self.send_header("Content-Length", str(len(payload)))

        for name, value in response.headers:
            self.send_header(name, value)

        headers = getattr(self, "headers", None)
        origin = headers.get("Origin") if headers else None

        existing = {name.lower() for name, _ in response.headers}

        for name, value in cors_headers(origin):
            if name.lower() not in existing:
                self.send_header(name, value)

        if getattr(self, "close_connection", False):
            self.send_header("Connection", "close")

        self.end_headers()

        if (
            not no_content
            and getattr(self, "command", "") != "HEAD"
        ):
            self.wfile.write(payload)

    def log_message(self, format, *args):
        pass

    do_GET = _handle
    do_POST = _handle
    do_PUT = _handle
    do_PATCH = _handle
    do_DELETE = _handle
    do_HEAD = _handle
    do_OPTIONS = _handle


def run(port: int = 8000) -> None:
    register_routes()

    with SmartWorkoutServer(("", port), HTTPRequestHandler) as httpd:
        log.info("Starting HTTP server on port %d", port)

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            log.info("Stopping HTTP server")
