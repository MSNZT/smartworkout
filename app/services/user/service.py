from app.repositories import UserRepository

class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def create(self, email: str, password_hash: str) -> dict:
        return self.user_repo.create(email, password_hash)

    def find_by_email(self, email: str) -> dict | None:
        return self.user_repo.find_by_email(email)