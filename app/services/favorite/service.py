from bson import ObjectId

from app.errors.favorite import InvalidProgramIdError, ProgramNotFoundError
from app.repositories.favorite import FavoriteRepository


class FavoriteService:
    def __init__(self, favorite_repo: FavoriteRepository):
        self.favorite_repo = favorite_repo

    def get_favorites(self, user_id: str) -> list[dict]:
        user_obj_id = ObjectId(user_id)
        favorite_ids = self.favorite_repo.get_favorite_ids(user_obj_id)

        if not favorite_ids:
            return []

        programs = self.favorite_repo.get_programs_by_ids(favorite_ids)
        for program in programs:
            program["_id"] = str(program["_id"])
        return programs

    def add_to_favorites(self, user_id: str, program_id: str) -> None:
        program_obj_id = ObjectId(program_id)

        if not self.favorite_repo.program_exists(program_obj_id):
            raise ProgramNotFoundError()

        self.favorite_repo.add_to_favorites(ObjectId(user_id), program_obj_id)

    def remove_from_favorites(self, user_id: str, program_id: str) -> None:
        if not ObjectId.is_valid(program_id):
            raise InvalidProgramIdError()

        self.favorite_repo.remove_from_favorites(ObjectId(user_id), ObjectId(program_id))