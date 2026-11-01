import os
import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.infrastructure.config import Settings
from app.main import create_app


@pytest.fixture
async def app():
    settings = Settings(
        environment="test",
        mongodb_uri=os.environ.get(
            "TEST_MONGODB_URI",
            "mongodb://auth:authpass@localhost:27017/?authSource=admin",
        ),
        mongodb_db=f"auth_test_{uuid.uuid4().hex}",
        jwt_secret="test-secret-key-with-32-characters-min",
        access_token_expire_minutes=15,
        refresh_token_expire_days=7,
        cors_origins="http://localhost:3000",
        trusted_hosts="localhost,127.0.0.1",
        admin_username="Admin",
        admin_password="Admin123",
        admin_email="admin@example.com",
    )
    application = create_app(settings)
    async with application.router.lifespan_context(application):
        yield application
        await application.state.container.mongo_client.drop_database(settings.mongodb_db)


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client
