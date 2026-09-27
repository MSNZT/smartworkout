from datetime import datetime, UTC

from pymongo.database import Database
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError
from app.errors import DuplicateEmailError

from app.database.collections import USERS

class UserRepository:
    def __init__(self, db: Database):
        self.collection: Collection = db[USERS]

    def create(self, email: str, password_hash: str):
        doc = {
            "email": email,
            "password_hash": password_hash,
            "role": "USER",
            "created_at": datetime.now(UTC),
            "favorite_program_ids": []
        }

        try:
            res = self.collection.insert_one(doc)
        except DuplicateKeyError:
            raise DuplicateEmailError() from None
        doc["_id"] = res.inserted_id
        return doc

    def find_by_email(self, email: str) -> dict | None:
        return self.collection.find_one({"email": email})
