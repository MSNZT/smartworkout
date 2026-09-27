from app.services.user.service import UserService
from app.core.config import settings
from app.errors.auth import InvalidCredentialsError
from app.security.password import hash_password, verify_password
from app.security.token import issue, verify

_DUMMY_HASH = hash_password("dummy")

class AuthService:
    def __init__(self, user_service: UserService):
        self.user_service = user_service

    def register(self, email: str, password: str) -> dict:
        password_hash = hash_password(password)
        return self.user_service.create(email, password_hash)

    def login(self, email: str, password: str) -> dict:
        user = self.user_service.find_by_email(email)

        password_hash = user["password_hash"] if user else _DUMMY_HASH
        password_ok = verify_password(password, password_hash)

        if not user or not password_ok:
            raise InvalidCredentialsError()

        payload = {
            "sub": str(user["_id"]),
            "email": user["email"],
            "role": user["role"],
        }
        return {
            "access_token": issue(payload, settings.token_secret, settings.access_ttl_seconds),
            "refresh_token": issue(payload, settings.token_secret, settings.refresh_ttl_seconds),
            "refresh_ttl": settings.refresh_ttl_seconds,
            "user": user,
        }

    def refresh(self, refresh_token: str) -> dict:
        data = verify(refresh_token, "refresh")

        # TODO: проверка токена на чёрный список

        payload = {"sub": data["sub"], "email": data["email"], "role": data["role"]}

        new_access = issue(payload, "access", settings.access_ttl_seconds)
        new_refresh = issue(payload, "refresh", settings.refresh_ttl_seconds)

        # TODO: добавить в чёрный список refresh токен

        return {
            "access_token": new_access,
            "refresh_token": new_refresh,
        }