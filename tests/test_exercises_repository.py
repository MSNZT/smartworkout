import importlib
import unittest
from datetime import UTC, datetime
from unittest.mock import patch

from bson import ObjectId
from pymongo.errors import WriteError

from app.database import indexes, validators
from app.dtos.exercises import ExerciseListDTO
from tests.exercises_support import TemporaryDatabase


class ExerciseRepositoryTests(unittest.TestCase):
    def setUp(self):
        try:
            module = importlib.import_module('app.repositories.exercises')
        except ModuleNotFoundError as exc:
            if exc.name != 'app.repositories.exercises':
                raise
            self.fail('Exercise persistence is not implemented')
        self.fixture = TemporaryDatabase()
        self.addCleanup(self.fixture.close)
        self.db = self.fixture.db
        with patch.object(validators, 'get_db', return_value=self.db), patch.object(indexes, 'get_db', return_value=self.db):
            validators.ensure_schema()
            indexes.ensure_indexes()
        self.repo = module.ExerciseRepository(self.db)

    def create(self, name='Bench press', muscle_groups=None, equipment=None, **extra):
        return self.repo.create({'name': name, 'muscle_groups': muscle_groups or ['CHEST'], 'equipment': equipment or ['DUMBBELL'], **extra})

    def test_create_stores_object_id_and_utc_date(self):
        doc = self.create()
        self.assertIsInstance(doc.get('_id'), ObjectId)
        self.assertIsInstance(doc.get('created_at'), datetime)
        self.assertEqual(doc.get('created_at').utcoffset(), UTC.utcoffset(None))
        stored = self.repo.find_by_id(doc.get('_id'))
        self.assertEqual(stored.get('name'), 'Bench press')
        self.assertNotIn('description', stored)

    def test_update_preserves_other_fields(self):
        doc = self.create(description='Technique')
        updated = self.repo.update(doc.get('_id'), {'name': 'New name'})
        self.assertEqual(updated.get('name'), 'New name')
        self.assertEqual(updated.get('description'), 'Technique')
        self.assertEqual(updated.get('equipment'), ['DUMBBELL'])
        self.assertEqual(self.repo.update(doc.get('_id'), {}).get('name'), 'New name')
        self.assertIsNone(self.repo.update(ObjectId(), {'name': 'Missing'}))

    def test_filters_use_or_inside_and_across_fields(self):
        self.create(name='Bench')
        self.create(name='Curl', muscle_groups=['ARMS'])
        self.create(name='Push-up', equipment=['BODYWEIGHT'])
        self.create(name='Row', muscle_groups=['BACK'])
        matches = self.repo.find_page(ExerciseListDTO(muscle_group='CHEST,ARMS', equipment='DUMBBELL'))
        self.assertEqual({item.get('name') for item in matches}, {'Bench', 'Curl'})

    def test_literal_search_and_case_insensitive_cyrillic(self):
        self.create(name='Literal .* exercise')
        self.create(name='Other', description='Жим лёжа')
        self.create(name='Plain')
        self.assertEqual([item.get('name') for item in self.repo.find_page(ExerciseListDTO(search='.*'))], ['Literal .* exercise'])
        self.assertEqual([item.get('name') for item in self.repo.find_page(ExerciseListDTO(search='жим'))], ['Other'])
        self.assertEqual(self.repo.find_page(ExerciseListDTO(search='[')), [])

    def test_cursor_keeps_filtered_pages_disjoint(self):
        expected = []
        for number in range(5):
            expected.append(self.create(name=f'Exercise {number}', muscle_groups=['CHEST' if number % 2 == 0 else 'ARMS']).get('_id'))
        self.create(name='Excluded', equipment=['BODYWEIGHT'])
        first = self.repo.find_page(ExerciseListDTO(muscle_group='CHEST,ARMS', equipment='DUMBBELL', limit=2))
        self.assertEqual([item.get('_id') for item in first], expected[:3])
        second = self.repo.find_page(ExerciseListDTO(muscle_group='CHEST,ARMS', equipment='DUMBBELL', limit=2, cursor=str(first[1].get('_id'))))
        self.assertEqual([item.get('_id') for item in second], expected[2:5])
        last = self.repo.find_page(ExerciseListDTO(muscle_group='CHEST,ARMS', equipment='DUMBBELL', limit=2, cursor=str(second[1].get('_id'))))
        self.assertEqual([item.get('_id') for item in last], expected[4:])

    def test_usage_checks_object_id_and_string_references(self):
        doc = self.create()
        exercise_id = doc.get('_id')
        self.assertFalse(self.repo.is_used_in_programs(exercise_id))
        self.db.programs.insert_one({'exercises': [{'exercise_id': ObjectId()}]})
        self.assertFalse(self.repo.is_used_in_programs(exercise_id))
        for reference in (exercise_id, str(exercise_id)):
            with self.subTest(reference=reference):
                program_id = self.db.programs.insert_one({'exercises': [{'exercise_id': reference}]}).inserted_id
                self.assertTrue(self.repo.is_used_in_programs(exercise_id))
                self.db.programs.delete_one({'_id': program_id})

    def test_delete_removes_document(self):
        exercise_id = self.create().get('_id')
        self.assertTrue(self.repo.delete(exercise_id))
        self.assertIsNone(self.repo.find_by_id(exercise_id))
        self.assertFalse(self.repo.delete(exercise_id))

    def test_schema_rejects_extra_fields_empty_arrays_and_invalid_enum(self):
        valid = {'name': 'Exercise', 'muscle_groups': ['CHEST'], 'equipment': ['BODYWEIGHT'], 'created_at': datetime.now(UTC)}
        for invalid in ({'extra': 'value'}, {'muscle_groups': []}, {'equipment': ['UNKNOWN']}, {'description': None}, {'name': 'x' * 101}):
            with self.subTest(values=invalid), self.assertRaises(WriteError):
                self.db.exercises.insert_one({**valid, **invalid})
        self.db.exercises.insert_one({**valid, 'muscle_groups': ['CHEST', 'CHEST']})
        self.assertEqual(self.db.exercises.count_documents({}), 1)


if __name__ == '__main__':
    unittest.main()
