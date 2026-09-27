import logging

from pymongo import ASCENDING, IndexModel

from .client import get_db
from .collections import USERS

logger = logging.getLogger(__name__)

INDEXES = {
    USERS: [
        IndexModel(
            [("email", ASCENDING)],
            unique=True,
            name="uniq_email",
        ),
        IndexModel(
            [("favorite_program_ids", ASCENDING)],
            name="idx_favorite_program_ids",
        ),
    ],
}

def ensure_indexes() -> None:
    db = get_db()

    for name, index_models in INDEXES.items():
        result = db[name].create_indexes(index_models)
        logger.info({
            "event": "indexes_ensured",
            "collection": name,
            "created": result,
        })