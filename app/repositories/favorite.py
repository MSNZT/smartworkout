from pymongo.database import Database
from pymongo.collection import Collection

from app.database.collections import USERS, PROGRAMS


class FavoriteRepository:
    def __init__(self, db: Database):
        self.users: Collection = db[USERS]
        self.programs: Collection = db[PROGRAMS]

    def get_favorite_ids(self, user_id) -> list:
        user = self.users.find_one(
            {"_id": user_id},
            {"favorite_program_ids": 1},
        )
        return user.get("favorite_program_ids", []) if user else []

    def get_programs_by_ids(self, program_ids: list) -> list[dict]:
        return list(self.programs.find({"_id": {"$in": program_ids}}))

    def get_program(self, program_id) -> dict | None:
        return self.programs.find_one({"_id": program_id})

    def add_to_favorites(self, user_id, program_id) -> bool:
        result = self.users.update_one(
            {"_id": user_id, "favorite_program_ids": {"$ne": program_id}},
            {"$push": {"favorite_program_ids": program_id}}
        )
        return result.modified_count > 0

    def remove_from_favorites(self, user_id, program_id) -> bool:
        result = self.users.update_one(
            {"_id": user_id, "favorite_program_ids": program_id},
            {"$pull": {"favorite_program_ids": program_id}},
        )
        return result.modified_count > 0