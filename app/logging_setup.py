import json
import logging
import sys
from datetime import datetime, timezone
from app.context import get_request_id


class JsonFormatter(logging.Formatter):
    def format(self, record):
        now = datetime.now(timezone.utc).astimezone()
        
        log_record = {
            "time": now.isoformat(timespec='microseconds'),
            "level": record.levelname,
            "msg": "http request completed"
        }
        
        if isinstance(record.msg, dict):
            log_record.update(record.msg)
        else:
            log_record["msg"] = record.getMessage()

        try:
            req_id = get_request_id()
            if req_id and req_id != "-":
                log_record["request_id"] = req_id
        except Exception:
            pass
            
        return json.dumps(log_record, ensure_ascii=False)


log = logging.getLogger(__name__)

def setup_logger(level=logging.INFO):
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)