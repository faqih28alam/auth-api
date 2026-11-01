import re
from datetime import datetime, timezone

from bson import ObjectId
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.errors import DuplicateKeyError

from app.domain.entities.user import Role, User, UserStats
from app.domain.exceptions import UserAlreadyExists, UserNotFound


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class MongoUserRepository:
    def __init__(self, database: AsyncDatabase) -> None:
        self._collection = database["users"]

    async def ensure_indexes(self) -> None:
        await self._collection.create_index("email", unique=True, name="email_unique")
        await self._collection.create_index(
            "username_normalized",
            unique=True,
            name="username_normalized_unique",
        )

    async def add(self, user: User) -> User:
        document = {
            "email": user.email.strip().lower(),
            "username": user.username,
            "username_normalized": user.username_normalized.strip().lower(),
            "password_hash": user.password_hash,
            "role": user.role.value,
            "is_active": user.is_active,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
        }
        try:
            result = await self._collection.insert_one(document)
        except DuplicateKeyError as exc:
            raise UserAlreadyExists() from exc
        user.id = str(result.inserted_id)
        return user

    async def get_by_id(self, user_id: str) -> User | None:
        oid = self._object_id(user_id)
        if oid is None:
            return None
        document = await self._collection.find_one({"_id": oid})
        return self._to_user(document) if document else None

    async def get_by_email(self, email: str) -> User | None:
        document = await self._collection.find_one({"email": email.strip().lower()})
        return self._to_user(document) if document else None

    async def get_by_username(self, username_normalized: str) -> User | None:
        document = await self._collection.find_one(
            {"username_normalized": username_normalized.strip().lower()}
        )
        return self._to_user(document) if document else None

    async def update(self, user: User) -> User:
        if user.id is None:
            raise RuntimeError("Cannot update a user without an id.")
        oid = self._object_id(user.id)
        if oid is None:
            raise UserNotFound()
        await self._collection.update_one(
            {"_id": oid},
            {
                "$set": {
                    "email": user.email.strip().lower(),
                    "username": user.username,
                    "username_normalized": user.username_normalized.strip().lower(),
                    "password_hash": user.password_hash,
                    "role": user.role.value,
                    "is_active": user.is_active,
                    "updated_at": user.updated_at,
                }
            },
        )
        return user

    async def delete(self, user_id: str) -> None:
        oid = self._object_id(user_id)
        if oid is None:
            return
        await self._collection.delete_one({"_id": oid})

    async def list_users(
        self,
        *,
        page: int,
        limit: int,
        role: Role | None,
        search: str | None,
    ) -> tuple[list[User], int]:
        query = self._filter(role, search)
        total = await self._collection.count_documents(query)
        cursor = (
            self._collection.find(query)
            .sort("created_at", -1)
            .skip((page - 1) * limit)
            .limit(limit)
        )
        documents = await cursor.to_list(length=limit)
        return [self._to_user(document) for document in documents], total

    async def stats(self) -> UserStats:
        total = await self._collection.count_documents({})
        active = await self._collection.count_documents({"is_active": True})
        by_role = {
            role.value: await self._collection.count_documents({"role": role.value})
            for role in Role
        }
        return UserStats(total=total, active=active, by_role=by_role)

    async def count_active_admins(self) -> int:
        return await self._collection.count_documents(
            {"role": Role.ADMIN.value, "is_active": True}
        )

    async def has_admin(self) -> bool:
        document = await self._collection.find_one(
            {"role": Role.ADMIN.value},
            projection={"_id": 1},
        )
        return document is not None

    def _filter(self, role: Role | None, search: str | None) -> dict:
        query: dict = {}
        if role is not None:
            query["role"] = role.value
        if search:
            escaped = re.escape(search)
            query["$or"] = [
                {"email": {"$regex": escaped, "$options": "i"}},
                {"username": {"$regex": escaped, "$options": "i"}},
            ]
        return query

    def _to_user(self, document: dict) -> User:
        return User(
            id=str(document["_id"]),
            email=document["email"],
            username=document["username"],
            username_normalized=document["username_normalized"],
            password_hash=document["password_hash"],
            role=Role(document["role"]),
            is_active=bool(document["is_active"]),
            created_at=_aware(document["created_at"]),
            updated_at=_aware(document["updated_at"]),
        )

    def _object_id(self, user_id: str) -> ObjectId | None:
        if not ObjectId.is_valid(user_id):
            return None
        return ObjectId(user_id)
