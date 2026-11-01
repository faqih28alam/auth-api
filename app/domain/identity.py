import re

from app.domain.exceptions import InvalidEmail, InvalidUsername

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,32}$")


def normalize_email(email: str) -> str:
    cleaned = email.strip().lower()
    if _EMAIL_RE.fullmatch(cleaned) is None:
        raise InvalidEmail("Email is invalid.")
    return cleaned


def normalize_username(username: str) -> str:
    cleaned = username.strip()
    if _USERNAME_RE.fullmatch(cleaned) is None:
        raise InvalidUsername(
            "Username must be 3-32 characters and contain only letters, digits, and underscores."
        )
    return cleaned
