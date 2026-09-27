from http import HTTPStatus
from app.errors.base import AppError

class InvalidCredentialsError(AppError):
    status = HTTPStatus.UNAUTHORIZED
    code = "INVALID_CREDENTIALS"

    def __init__(self, message: str = "invalid email or password"):
        super().__init__(message)


class AuthorizationRequiredError(AppError):
    status = HTTPStatus.UNAUTHORIZED
    code = "UNAUTHORIZED"

    def __init__(self, message: str = "authorization required"):
        super().__init__(message)


class TokenExpiredError(AppError):
    status = HTTPStatus.UNAUTHORIZED
    code = "TOKEN_EXPIRED"

    def __init__(self, message: str = "token expired"):
        super().__init__(message)


class TokenInvalidError(AppError):
    status = HTTPStatus.UNAUTHORIZED
    code = "TOKEN_INVALID"

    def __init__(self, message: str = "invalid token"):
        super().__init__(message)