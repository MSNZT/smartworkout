from http import HTTPStatus

from app.dtos.favorite import FavoriteDTO
from app.dtos.base import DTOValidationError
from app.httpresponse import error_response, json_response
from app.routing import router
from app.middlewares.auth import require_auth
from app.dependencies import favorite_service


@router.get("/me/favorites", middlewares=[require_auth])
def get_favorites(request):
    user = request["user"]
    programs = favorite_service.get_favorites(user["id"])
    return json_response(programs, HTTPStatus.OK)


@router.post("/me/favorites", middlewares=[require_auth])
def add_to_favorites(request):
    user = request["user"]

    try:
        dto = FavoriteDTO.from_dict(request.get("body"))
    except DTOValidationError as exc:
        return error_response(
            {
                "code": "BAD_REQUEST",
                "message": "Validation failed",
                "errors": exc.errors,
            },
            HTTPStatus.BAD_REQUEST,
        )

    favorite_service.add_to_favorites(user["id"], dto.program_id)
    return json_response({"status": "success"}, HTTPStatus.CREATED)


@router.delete("/me/favorites/{program_id}", middlewares=[require_auth])
def remove_from_favorites(request):
    user = request["user"]
    program_id = request["params"]["program_id"]

    favorite_service.remove_from_favorites(user["id"], program_id)
    return json_response({"status": "success"}, HTTPStatus.OK)