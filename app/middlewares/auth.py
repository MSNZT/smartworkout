from app.core.config import settings
from app.errors.auth import (
    AuthorizationRequiredError,
    TokenExpiredError,
    TokenInvalidError,
)
from app.errors.user import AccessDeniedError
from app.security.token import verify


def require_auth(request, next_handler):
    header = next(
        (
            value
            for name, value in request["headers"].items()
            if name.lower() == "authorization"
        ),
        "",
    )

    parts = header.split()

    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise AuthorizationRequiredError()

    try:
        payload = verify(parts[1], settings.token_secret)
    except (TokenExpiredError, TokenInvalidError):
        raise AuthorizationRequiredError() from None

    request["user"] = {
        "id": payload["sub"],
        "email": payload.get("email"),
        "role": payload.get("role"),
    }

    return next_handler(request)


def require_admin(request, next_handler):
    user = request.get("user")

    if not user:
        raise AuthorizationRequiredError()

    if user.get("role") != "ADMIN":
        raise AccessDeniedError()

    return next_handler(request)