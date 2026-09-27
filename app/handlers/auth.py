from http import HTTPStatus

from app.core.config import settings
from app.core.cookies import build_set_cookie
from app.dependencies import auth_service
from app.dtos.auth import LoginDTO, RegisterDTO
from app.dtos.base import DTOValidationError
from app.httpresponse import error_response, json_response
from app.routing import router

@router.post("/auth/register")
def register(request, params):
    body = request.get("body") or {}

    print(request)

    try:
        dto = RegisterDTO(email=body.get("email"), password=body.get("password"))
    except DTOValidationError as exc:
        return error_response(
            {
                "code": "BAD_REQUEST",
                "message": "Validation failed",
                "errors": exc.errors,
            },
            HTTPStatus.BAD_REQUEST,
        )

    user = auth_service.register(
        dto.email,
        dto.password,
    )

    return json_response(
        {
            "id": str(user["_id"]),
            "email": user["email"],
            "created_at": user["created_at"].isoformat(),
        },
        HTTPStatus.CREATED,
    )

@router.post("/auth/login")
def login(request, params):
    body = request.get("body") or {}

    try:
        dto = LoginDTO(email=body.get("email"), password=body.get("password"))
    except DTOValidationError as exc:
        return error_response(
            {
                "code": "BAD_REQUEST",
                "message": "Validation failed",
                "errors": exc.errors,
            },
            HTTPStatus.BAD_REQUEST,
        )

    result = auth_service.login(
        dto.email,
        dto.password,
    )

    set_cookie = build_set_cookie(
        "refresh_token",
        result["refresh_token"],
        max_age=result["refresh_ttl"],
        path="/auth",
        secure=settings.is_production(),
    )

    return json_response(
        {
            "access_token": result["access_token"],
            "user": {
                "id": str(result["user"]["_id"]),
                "email": result["user"]["email"],
            },
        },
        HTTPStatus.OK,
        headers=[
            ("Set-Cookie", set_cookie),
        ],
    )