from http.cookies import SimpleCookie


def parse_cookies(header: str | None) -> dict[str, str]:
    if not header:
        return {}
    cookie = SimpleCookie()
    try:
        cookie.load(header)
    except Exception:
        return {}
    return {k: m.value for k, m in cookie.items()}


def build_set_cookie(
    name: str,
    value: str,
    *,
    max_age: int,
    path: str = "/",
    http_only: bool = True,
    secure: bool = True,
    same_site: str = "Strict",
) -> str:
    parts = [f"{name}={value}", f"Max-Age={max_age}", f"Path={path}"]
    if http_only:
        parts.append("HttpOnly")
    if secure:
        parts.append("Secure")
    if same_site:
        parts.append(f"SameSite={same_site}")
    return "; ".join(parts)


def clear_cookie(name: str, path: str = "/") -> str:
    return f"{name}=; Max-Age=0; Path={path}; HttpOnly; Secure; SameSite=Strict"