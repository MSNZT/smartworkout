from app.routing import router
from app.httpresponse import json_response

@router.get("/login")
def login(request, params):
    return json_response({"message": "hello"})