import re
from dataclasses import dataclass

EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

@dataclass
class RegisterDTO:
    email: str
    password: str
    confirm_password: str

    def __post_init__(self):
        if not isinstance(self.email, str):
            raise ValueError("email must be a string")
        if not isinstance(self.password, str):
            raise ValueError("password must be a string")

        self.email = self.email.strip().lower()
        self.password = self.password.strip()
        
        if not EMAIL_RE.match(self.email):
            raise ValueError("invalid email")
        if len(self.password) < 8:
            raise ValueError("password too short, min length 8")
        if len(self.confirm_password) < 8:
            raise ValueError("confirm_password too short, min length 8")
        if self.password != self.confirm_password:
            raise ValueError("passwords don't match")