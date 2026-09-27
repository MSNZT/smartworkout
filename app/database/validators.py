import logging

from .client import get_db
from .collections import USERS

logger = logging.getLogger(__name__)

VALIDATORS = {
    USERS: {
        "schema": {
            "bsonType": "object",
            "required": ["email", "password_hash", "role", "created_at"],
            "properties": {
                "_id": {"bsonType": "objectId"},
                "email": {
                    "bsonType": "string",
                    "pattern": "^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$",
                },
                "role": {
                    "bsonType": "string",
                    "enum": ["USER", "ADMIN"],
                    "description": "User role",
                },
                "password_hash": {
                    "bsonType": "string",
                    "minLength": 1,
                    "description": "Password hash must not be empty",
                },
                "created_at": {"bsonType": "date"},
                "favorite_program_ids": {
                    "bsonType": "array",
                    "items": {"bsonType": "objectId"},
                    "uniqueItems": True,
                    "description": "IDs of programs added to favorites",
                },
            },
            "additionalProperties": False,
        },
        "validationLevel": "strict",
        "validationAction": "error",
    },
}


def ensure_schema() -> None:
    db = get_db()
    existing = set(db.list_collection_names())

    for name, spec in VALIDATORS.items():
        validator = {"$jsonSchema": spec["schema"]}
        level = spec.get("validationLevel", "strict")
        action = spec.get("validationAction", "error")

        if name not in existing:
            db.create_collection(
                name,
                validator=validator,
                validationLevel=level,
                validationAction=action,
            )
            logger.info({"event": "collection_created", "collection": name})
        else:
            db.command({
                "collMod": name,
                "validator": validator,
                "validationLevel": level,
                "validationAction": action,
            })
            logger.info({"event": "collection_validator_updated", "collection": name})