import importlib
import unittest
from datetime import UTC, datetime

from bson import ObjectId

from app.dtos.exercises import ExerciseListDTO
from app.errors.exercises import ExerciseInUseError, ExerciseNotFoundError


class RepositoryDouble:
    def __init__(self):
        self.documents = {}
        self.used = set()
        self.page = []
        self.disappear_before_delete = False

    def create(self, values):
        doc = {'_id': ObjectId(), 'created_at': datetime.now(UTC), **values}
        self.documents[doc.get('_id')] = doc
        return doc

    def find_by_id(self, exercise_id):
        return self.documents.get(exercise_id)

    def update(self, exercise_id, changes):
        doc = self.documents.get(exercise_id)
        if doc is not None:
            doc.update(changes)
        return doc

    def find_page(self, filters):
        return self.page

    def is_used_in_programs(self, exercise_id):
        return exercise_id in self.used

    def delete(self, exercise_id):
        previous = self.documents.pop(exercise_id, None)
        return previous is not None and not self.disappear_before_delete


class ExerciseServiceTests(unittest.TestCase):
    def setUp(self):
        try:
            module = importlib.import_module('app.services.exercises.service')
        except ModuleNotFoundError as exc:
            if exc.name not in ('app.services.exercises', 'app.services.exercises.service'):
                raise
            self.fail('Exercise service rules are not implemented')
        self.repo = RepositoryDouble()
        self.service = module.ExerciseService(self.repo)

    def create(self):
        return self.service.create({'name': 'Push-up', 'muscle_groups': ['CHEST'], 'equipment': ['BODYWEIGHT']})

    def test_missing_exercise_raises_not_found(self):
        missing = ObjectId()
        for operation in (lambda: self.service.get(missing), lambda: self.service.update(missing, {'name': 'New'}), lambda: self.service.delete(missing)):
            with self.subTest(operation=operation), self.assertRaises(ExerciseNotFoundError) as caught:
                operation()
            self.assertEqual(caught.exception.status, 404)
            self.assertEqual(caught.exception.code, 'NOT_FOUND')

    def test_used_exercise_is_not_deleted(self):
        doc = self.create()
        self.repo.used.add(doc.get('_id'))
        with self.assertRaises(ExerciseInUseError) as caught:
            self.service.delete(doc.get('_id'))
        self.assertEqual(caught.exception.status, 409)
        self.assertEqual(caught.exception.message, 'Exercise is used in one or more programs')
        self.assertEqual(self.service.get(doc.get('_id')).get('name'), 'Push-up')

    def test_free_exercise_is_deleted(self):
        doc = self.create()
        self.service.delete(doc.get('_id'))
        with self.assertRaises(ExerciseNotFoundError):
            self.service.get(doc.get('_id'))

    def test_disappearance_during_delete_returns_not_found(self):
        doc = self.create()
        self.repo.disappear_before_delete = True
        with self.assertRaises(ExerciseNotFoundError):
            self.service.delete(doc.get('_id'))

    def test_update_returns_changed_document(self):
        doc = self.create()
        result = self.service.update(doc.get('_id'), {'name': 'Bench press'})
        self.assertEqual(result.get('name'), 'Bench press')
        self.assertEqual(result.get('equipment'), ['BODYWEIGHT'])

    def test_extra_page_result_is_not_returned(self):
        self.repo.page = [self.create() for _ in range(3)]
        result = self.service.list(ExerciseListDTO(limit=2))
        self.assertEqual(len(result.get('data')), 2)
        self.assertTrue(result.get('has_more'))
        self.assertEqual(result.get('limit'), 2)
        self.assertEqual(result.get('next'), str(self.repo.page[1].get('_id')))

    def test_last_and_empty_pages_have_no_next_cursor(self):
        for size in (0, 1, 2):
            self.repo.page = [self.create() for _ in range(size)]
            with self.subTest(size=size):
                result = self.service.list(ExerciseListDTO(limit=2))
                self.assertFalse(result.get('has_more'))
                self.assertIsNone(result.get('next'))
                self.assertEqual(len(result.get('data')), size)


if __name__ == '__main__':
    unittest.main()
