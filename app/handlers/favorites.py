from http import HTTPStatus
from bson import ObjectId
from app.routing import router
from app.httpresponse import json_response, error_response
from app.database.client import get_db


@router.get("/favorites")
def get_favorites(request, params):
    db = get_db()
    user = request.get("user") or {}
    favorite_ids = user.get("favorite_program_ids", [])

    if not favorite_ids:
        return json_response([], HTTPStatus.OK)

    programs = list(db.programs.find({"_id": {"$in": favorite_ids}}))
    for p in programs:
        p["_id"] = str(p["_id"])

    return json_response(programs, HTTPStatus.OK)


@router.post("/favorites")
def add_to_favorites(request, params):
    db = get_db()
    user = request.get("user") or {}
    body = request.get("body") or {}
    program_id = body.get("program_id")

    if not program_id or not ObjectId.is_valid(program_id):
        return error_response(
            {"code": "BAD_REQUEST", "message": "Invalid program ID"},
            HTTPStatus.BAD_REQUEST
        )

    program = db.programs.find_one({"_id": ObjectId(program_id)})
    if not program:
        return error_response(
            {"code": "NOT_FOUND", "message": "Program not found"},
            HTTPStatus.NOT_FOUND
        )

    db.users.update_one(
        {"_id": user["_id"]},
        {"$addToSet": {"favorite_program_ids": ObjectId(program_id)}}
    )
    return json_response({"status": "success"}, HTTPStatus.CREATED)


@router.delete("/favorites/{program_id}")
def remove_from_favorites(request, params):
    db = get_db()
    user = request.get("user") or {}
    program_id = params.get("program_id")

    if not program_id or not ObjectId.is_valid(program_id):
        return error_response(
            {"code": "BAD_REQUEST", "message": "Invalid program ID"},
            HTTPStatus.BAD_REQUEST
        )

    db.users.update_one(
        {"_id": user["_id"]},
        {"$pull": {"favorite_program_ids": ObjectId(program_id)}}
    )
    return json_response({"status": "success"}, HTTPStatus.OK)