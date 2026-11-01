from datetime import datetime, timezone

from pymongo.asynchronous.database import AsyncDatabase

from app.domain.entities.refresh_token import RefreshToken
from app.domain.time import utcnow


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class MongoRefreshTokenRepository:
    def __init__(self, database: AsyncDatabase) -> None:
        self._collection = database["refresh_tokens"]

    async def ensure_indexes(self) -> None:
        await self._collection.create_index("token_hash", unique=True, name="token_hash_unique")
        await self._collection.create_index("expires_at", expireAfterSeconds=0, name="expires_at_ttl")
        await self._collection.create_index("user_id", name="user_id")

    async def store(self, *, token_hash: str, user_id: str, expires_at: datetime) -> None:
        await self._collection.insert_one(
            {
                "token_hash": token_hash,
                "user_id": user_id,
                "expires_at": expires_at,
                "revoked": False,
                "created_at": utcnow(),
            }
        )

    async def get(self, token_hash: str) -> RefreshToken | None:
        document = await self._collection.find_one({"token_hash": token_hash})
        if document is None:
            return None
        return RefreshToken(
            token_hash=document["token_hash"],
            user_id=document["user_id"],
            expires_at=_aware(document["expires_at"]),
            revoked=bool(document["revoked"]),
        )

    async def revoke(self, token_hash: str) -> None:
        await self._collection.update_one({"token_hash": token_hash}, {"$set": {"revoked": True}})

    async def revoke_all_for_user(self, user_id: str) -> None:
        await self._collection.update_many({"user_id": user_id}, {"$set": {"revoked": True}})
