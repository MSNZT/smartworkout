from http import HTTPStatus


class AppError(Exception):
    status = HTTPStatus.BAD_REQUEST
    code = "APP_ERROR"

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)