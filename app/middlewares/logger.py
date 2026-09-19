import logging
import time
from http import HTTPStatus

log = logging.getLogger(__name__)

def logging_middleware(request, params, next_handler):
    start = time.perf_counter()
    try:
        response = next_handler(request, params)
    except Exception as e:
        duration_ms = int((time.perf_counter() - start) * 1000)
        log.error(
            "Unhandled exception during request",
            extra={
                "method": request["method"],
                "path": request["path"],
                "status": int(HTTPStatus.INTERNAL_SERVER_ERROR),
                "duration_ms": duration_ms,
                "error": str(e),
            },
            exc_info=True,
        )
        raise

    duration_ms = int((time.perf_counter() - start) * 1000)
    data = {
        "method": request["method"],
        "path": request["path"],
        "status": int(response.status),
        "duration_ms": duration_ms,
    }

    if response.status == HTTPStatus.NOT_FOUND:
        log.warning(data)
    elif response.status >= 500:
        log.error(data)
    else:
        log.info(data)

    return response