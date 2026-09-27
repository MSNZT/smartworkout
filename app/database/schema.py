from .indexes import ensure_indexes
from .validators import ensure_schema


def ensure_all() -> None:
    ensure_schema()
    ensure_indexes()