from bson import ObjectId

from app.dtos.exercises import ExerciseListDTO
from app.errors.exercises import ExerciseInUseError, ExerciseNotFoundError
from app.repositories.exercises import ExerciseRepository


class ExerciseService:
    def __init__(self, exercise_repo: ExerciseRepository):
        self.exercise_repo = exercise_repo

    def create(self, values: dict) -> dict:
        return self.exercise_repo.create(values)

    def get(self, exercise_id: ObjectId) -> dict:
        document = self.exercise_repo.find_by_id(exercise_id)
        if document is None:
            raise ExerciseNotFoundError()
        return document

    def update(self, exercise_id: ObjectId, changes: dict) -> dict:
        document = self.exercise_repo.update(exercise_id, changes)
        if document is None:
            raise ExerciseNotFoundError()
        return document

    def delete(self, exercise_id: ObjectId) -> None:
        self.get(exercise_id)
        if self.exercise_repo.is_used_in_programs(exercise_id):
            raise ExerciseInUseError()
        if not self.exercise_repo.delete(exercise_id):
            raise ExerciseNotFoundError()

    def list(self, filters: ExerciseListDTO) -> dict:
        documents = self.exercise_repo.find_page(filters)
        has_more = len(documents) > filters.limit
        data = documents[:filters.limit]
        return {
            'data': data,
            'next': str(data[-1].get('_id')) if has_more else None,
            'limit': filters.limit,
            'has_more': has_more,
        }
