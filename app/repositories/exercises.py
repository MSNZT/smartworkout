import re
from datetime import UTC, datetime

from bson import ObjectId
from pymongo import ASCENDING, ReturnDocument
from pymongo.database import Database

from app.database.collections import EXERCISES, PROGRAMS
from app.dtos.exercises import ExerciseListDTO


class ExerciseRepository:
    def __init__(self, db: Database):
        self.collection = db[EXERCISES]
        self.programs = db[PROGRAMS]

    def create(self, values: dict) -> dict:
        document = {**values, 'created_at': datetime.now(UTC)}
        result = self.collection.insert_one(document)
        document['_id'] = result.inserted_id
        return document

    def find_by_id(self, exercise_id: ObjectId) -> dict | None:
        return self.collection.find_one({'_id': exercise_id})

    def find_page(self, filters: ExerciseListDTO) -> list[dict]:
        query = {}
        if filters.muscle_group is not None:
            query['muscle_groups'] = {'$in': filters.muscle_group}
        if filters.equipment is not None:
            query['equipment'] = {'$in': filters.equipment}
        if filters.search is not None:
            pattern = {'$regex': re.escape(filters.search), '$options': 'i'}
            query['$or'] = [{'name': pattern}, {'description': pattern}]
        if filters.cursor is not None:
            query['_id'] = {'$gt': filters.cursor}
        return list(self.collection.find(query).sort('_id', ASCENDING).limit(filters.limit + 1))

    def update(self, exercise_id: ObjectId, changes: dict) -> dict | None:
        if not changes:
            return self.find_by_id(exercise_id)
        return self.collection.find_one_and_update(
            {'_id': exercise_id}, {'$set': changes}, return_document=ReturnDocument.AFTER,
        )

    def is_used_in_programs(self, exercise_id: ObjectId) -> bool:
        return self.programs.find_one(
            {'exercises.exercise_id': {'$in': [exercise_id, str(exercise_id)]}}, {'_id': 1},
        ) is not None

    def delete(self, exercise_id: ObjectId) -> bool:
        return self.collection.delete_one({'_id': exercise_id}).deleted_count == 1
