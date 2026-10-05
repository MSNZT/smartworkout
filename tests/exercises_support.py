from uuid import uuid4

from pymongo import MongoClient

from app.core.config import settings


class TemporaryDatabase:
    prefix = 'smartworkout_exercises_test_'

    def __init__(self):
        self.name = self.prefix + uuid4().hex
        self.client = MongoClient(settings.mongo_uri, serverSelectionTimeoutMS=3000, tz_aware=True)
        try:
            self.client.admin.command('ping')
        except Exception:
            self.client.close()
            raise
        self.db = self.client[self.name]

    def close(self):
        if not self.name.startswith(self.prefix) or self.name == settings.mongo_db:
            raise RuntimeError('Refusing to drop a non-test database')
        try:
            self.client.drop_database(self.name)
        finally:
            self.client.close()
