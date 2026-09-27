from http import HTTPStatus
from app.errors.base import AppError

class UserNotFoundError(AppError):
    status = HTTPStatus.NOT_FOUND
    code = "USER_NOT_FOUND"

    def __init__(self, message: str = "user not found"):
        super().__init__(message)


class DuplicateEmailError(AppError):
    status = HTTPStatus.CONFLICT
    code = "DUPLICATE_EMAIL"

    def __init__(self, message: str = "email already exists"):
        super().__init__(message)


class AccessDeniedError(AppError):
    status = HTTPStatus.FORBIDDEN
    code = "FORBIDDEN"

    def __init__(self, message: str = "access denied"):
        super().__init__(message)