from dataclasses import dataclass
from bson import ObjectId

from app.dtos.base import BaseDTO


@dataclass
class FavoriteDTO(BaseDTO):
    program_id: str

    def _validate_program_id(self, value: str) -> str | None:
        if not ObjectId.is_valid(value):
            return "invalid program id format"
        return None