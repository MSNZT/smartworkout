from app.repositories import UserRepository
from app.services import UserService, AuthService
from app.database import get_db

from pymongo.database import Database

db: Database = get_db()

user_repo = UserRepository(db)
user_service = UserService(user_repo)
auth_service = AuthService(
    user_service=user_service,
)