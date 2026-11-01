from pymongo import AsyncMongoClient


def create_mongo_client(uri: str) -> AsyncMongoClient:
    return AsyncMongoClient(uri, tz_aware=True, serverSelectionTimeoutMS=5000)
