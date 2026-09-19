import contextvars
import uuid

request_id_var = contextvars.ContextVar("request_id", default="-")

def new_request_id() -> str:
    rid = uuid.uuid4().hex[:12]
    request_id_var.set(rid)
    return rid


def get_request_id() -> str:
    return request_id_var.get()