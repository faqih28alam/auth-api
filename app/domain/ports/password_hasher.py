from typing import Protocol


class PasswordHasher(Protocol):
    dummy_hash: str

    def hash(self, password: str) -> str: ...

    def verify(self, password: str, password_hash: str) -> bool: ...
