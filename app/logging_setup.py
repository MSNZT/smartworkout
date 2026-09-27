import json
import logging
import sys
from datetime import datetime, timezone

from app.context import get_request_id

_RESERVED = {
    "name", "msg", "args", "levelname", "levelno", "pathname",
    "filename", "module", "exc_info", "exc_text", "stack_info",
    "lineno", "funcName", "created", "msecs", "relativeCreated",
    "thread", "threadName", "processName", "process", "message",
    "asctime", "taskName",
}

class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        now = datetime.now(timezone.utc).astimezone()

        payload = {
            "time": now.isoformat(timespec="microseconds"),
            "level": record.levelname,
        }

        if isinstance(record.msg, dict):
            payload.update(record.msg)
        else:
            payload["msg"] = record.getMessage()

        for key, value in record.__dict__.items():
            if key in _RESERVED or key.startswith("_"):
                continue
            payload[key] = value

        if record.exc_info:
            payload["traceback"] = self.formatException(record.exc_info)

        try:
            req_id = get_request_id()
            if req_id and req_id != "-":
                payload["request_id"] = req_id
        except Exception:
            pass

        return json.dumps(payload, ensure_ascii=False, default=str)


log = logging.getLogger(__name__)


def setup_logger(level=logging.INFO):
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)