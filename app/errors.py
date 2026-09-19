from http import HTTPStatus


def bad_request(errors: list[dict]):
    """400 с полями."""
    return {
        "code": "BAD_REQUEST",
        "message": "Validation failed",
        "errors": errors,
    }, HTTPStatus.BAD_REQUEST


def unauthorized():
    """401 без полей."""
    return {
        "code": "UNAUTHORIZED",
        "message": "Authorization required",
    }, HTTPStatus.UNAUTHORIZED


def forbidden(message="Access denied"):
    """403."""
    return {
        "code": "FORBIDDEN",
        "message": message,
    }, HTTPStatus.FORBIDDEN


def not_found(message="Resource not found"):
    """404."""
    return {
        "code": "NOT_FOUND",
        "message": message,
    }, HTTPStatus.NOT_FOUND


def conflict(errors: list[dict]):
    """409 с полями."""
    return {
        "code": "CONFLICT",
        "message": "Conflict",
        "errors": errors,
    }, HTTPStatus.CONFLICT