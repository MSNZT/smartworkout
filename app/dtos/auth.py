import re
from dataclasses import dataclass

from app.dtos.base import BaseDTO

EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

@dataclass
class RegisterDTO(BaseDTO):
    email: str
    password: str

    def _validate_email(self, value: str) -> str | None:
        self.email = value.lower()
        if not EMAIL_RE.match(self.email):
            return "invalid email address"
        return None

    def _validate_password(self, value: str) -> str | None:
        if len(value) < 6:
            return "password must be at least 6 characters long"

        if len(value) > 32:
            return "password must be at most 30 characters long"
        return None

@dataclass
class LoginDTO(BaseDTO):
    email: str
    password: str

    def _validate_email(self, value: str) -> str | None:
        if not value or not value.strip():
            return "email is required"

        self.email = value.strip().lower()
        return None

    def _validate_password(self, value: str) -> str | None:
        if not value:
            return "password is required"
        return None