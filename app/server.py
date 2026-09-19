import json
import logging
from http import HTTPStatus
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from app.httpresponse import Response, error_response
from app.routing import router
from app.handlers import register_routes

MAX_BODY_SIZE = 1 * 1024 * 1024

register_routes()
log = logging.getLogger(__name__)

class HTTPRequestHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _handle(self) -> None:
        self._dispatch()

    def _read_body(self):
        length = int(self.headers.get("Content-Length") or 0)
        if length > MAX_BODY_SIZE:
            return None, error_response(
                "request body too large", HTTPStatus.REQUEST_ENTITY_TOO_LARGE
            )
        
        if length == 0:
            return None, None
        
        try:
            return json.loads(self.rfile.read(length)), None
        except json.JSONDecodeError:
            return None, error_response("invalid json body", HTTPStatus.BAD_REQUEST)

    def _dispatch(self) -> int:
        parsed = urlparse(self.path)
        path = parsed.path
        query = {k: v[0] for k, v in parse_qs(parsed.query).items()}

        route, params, allowed = router.resolve(self.command, path)
        if route is None:
            status = (HTTPStatus.METHOD_NOT_ALLOWED if allowed else HTTPStatus.NOT_FOUND)
            response = error_response(
                "method not allowed" if allowed else "not found", status,
            )

            self._send(response)
            return int(response.status)

        body, err = self._read_body()
        if err is not None:
            if err.status == HTTPStatus.REQUEST_ENTITY_TOO_LARGE:
                self.close_connection = True
            self._send(err)
            return int(err.status)

        request = {
            "method": self.command,
            "path": path,
            "query": query,
            "headers": dict(self.headers),
            "body": body,
        }

        result = route.handler(request, params)
        
        self._send(result)
        return int(result.status)

    def _send(self, response: Response) -> None:
        payload = json.dumps(
            response.body if response.body is not None else {},
            ensure_ascii=False,
        ).encode("utf-8")

        self.send_response(response.status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))

        for name, value in response.headers.items():
            self.send_header(name, value)

        self.end_headers()
        self.wfile.write(payload)

    do_GET = do_POST = do_PUT = do_PATCH = do_DELETE = _handle

def run(port: int = 8000) -> None:
    httpd = ThreadingHTTPServer(("", port), HTTPRequestHandler)
    log.info("Starting HTTP server on port %d", port)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        log.info("stopping server")
        httpd.server_close()