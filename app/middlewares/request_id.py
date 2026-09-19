from app.context import new_request_id, get_request_id

def request_id_middleware(request, params, next_handler):
    new_request_id()
    response = next_handler(request, params)
    response.headers["X-Request-Id"] = get_request_id()
    return response