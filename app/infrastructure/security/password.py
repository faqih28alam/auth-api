from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher


class Argon2PasswordHasher:
    def __init__(self, *, testing: bool = False) -> None:
        if testing:
            self._hasher = PasswordHash(
                (Argon2Hasher(time_cost=1, memory_cost=8192, parallelism=1),)
            )
        else:
            self._hasher = PasswordHash.recommended()
        self.dummy_hash = self._hasher.hash("not-a-real-password")

    def hash(self, password: str) -> str:
        return self._hasher.hash(password)

    def verify(self, password: str, password_hash: str) -> bool:
        try:
            return self._hasher.verify(password, password_hash)
        except Exception:
            return False
