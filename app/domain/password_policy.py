import re

from app.domain.exceptions import WeakPassword

PASSWORD_RULES = (
    "Password must be 8-128 characters and include an uppercase letter, "
    "a lowercase letter, and a digit."
)


def validate_password(password: str) -> None:
    if (
        not 8 <= len(password) <= 128
        or re.search(r"[A-Z]", password) is None
        or re.search(r"[a-z]", password) is None
        or re.search(r"\d", password) is None
    ):
        raise WeakPassword(PASSWORD_RULES)
