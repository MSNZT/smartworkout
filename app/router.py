import re
from dataclasses import dataclass, field
from typing import Callable, Any

_PARAM_RE = re.compile(r"\{(\w+)\}")

Request = dict[str, Any]
Params = dict[str, str]
Handler = Callable[[Request, Params], Any]
Middleware = Callable[[Request, Params, Handler], Any]

def _compile_pattern(pattern: str) -> re.Pattern:
    parts = _PARAM_RE.split(pattern)
    out = []
    for part in parts:
        if not part:
            continue
        m = _PARAM_RE.fullmatch(part)
        if m:
            out.append(f"(?P<{m.group(1)}>[^/]+)")
        else:
            out.append(re.escape(part))
    return re.compile("^" + "".join(out) + "$")

@dataclass
class Route:
    method: str
    pattern: str
    handler: Callable
    regex: re.Pattern = field(init=False)

    def __post_init__(self):
        self.method.upper()
        self.regex = _compile_pattern(self.pattern)

@dataclass
class Router:
    routes: list[Route] = field(default_factory=list)
    global_middlewares: list[Callable] = field(default_factory=list)

    def use(self, middleware: Callable):
        self.global_middlewares.append(middleware)
        return middleware

    @staticmethod
    def _wrap(middleware: Middleware, next_handler: Handler) -> Handler:
        def wrapped(request: Request, params: Params):
            return middleware(request, params, next_handler)

        return wrapped

    def _register(self, method: str, path: str, middlewares: tuple[Callable, ...]):
        def decorator(handler: Callable):
            all_mw = self.global_middlewares + list(middlewares)

            wrapped_handler = handler

            for mw in reversed(all_mw):
                wrapped_handler = self._wrap(mw, wrapped_handler)

            self.routes.append(Route(method, path, wrapped_handler))
            return handler
        return decorator

    def resolve(self, method: str, path: str) -> tuple[Route | None, dict, bool]:
        allowed = False

        for route in self.routes:
            match = route.regex.match(path)
            if match is None:
                continue

            allowed = True
            if route.method == method:
                return route, match.groupdict(), True

        return None, {}, allowed

    def get(self, path: str, middlewares: tuple = ()):
        return self._register("GET", path, middlewares)

    def post(self, path: str, middlewares: tuple = ()):
        return self._register("POST", path, middlewares)

    def put(self, path: str, middlewares: tuple = ()):
        return self._register("PUT", path, middlewares)

    def delete(self, path: str, middlewares: tuple = ()):
        return self._register("DELETE", path, middlewares)