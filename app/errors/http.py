from http import HTTPStatus

def bad_request(errors: list[dict]):
    return {
        "code": "BAD_REQUEST",
        "message": "Validation failed",
        "errors": errors,
    }, HTTPStatus.BAD_REQUEST

# def bad_request(errors: list[dict]):
#     return {
#         "code": "BAD_REQUEST",
#         "message": "Validation failed",
#         "errors": errors,
#     }, HTTPStatus.BAD_REQUEST
#
#
# def unauthorized(message: str = "Authorization required"):
#     return {
#         "code": "UNAUTHORIZED",
#         "message": message,
#     }, HTTPStatus.UNAUTHORIZED
#
#
# def forbidden(message: str = "Access denied"):
#     return {
#         "code": "FORBIDDEN",
#         "message": message,
#     }, HTTPStatus.FORBIDDEN
#
#
# def not_found(message: str = "Resource not found"):
#     return {
#         "code": "NOT_FOUND",
#         "message": message,
#     }, HTTPStatus.NOT_FOUND
#
#
# def conflict(message: str = "Conflict"):
#     return {"code": "CONFLICT", "message": message}, HTTPStatus.CONFLICT
#
# def internal_error(message: str = "Internal server error"):
#     return {
#         "code": "INTERNAL_ERROR",
#         "message": message,
#     }, HTTPStatus.INTERNAL_SERVER_ERROR