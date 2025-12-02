import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.infrastructure.database import engine, Base
from app.features.settings.models import ApiKey
from sqlalchemy import select
from app.infrastructure.database import AsyncSessionLocal
from app.infrastructure.security import decrypt_value


@pytest.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_set_and_get_api_key():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Set Key
        response = await ac.put(
            "/api/settings/keys",
            json={"provider": "openai", "api_key": "sk-test-key"},
        )
        assert response.status_code == 200

        # 2. Verify in DB (Encrypted)
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(ApiKey).where(ApiKey.provider == "openai")
            )
            key = result.scalars().first()
            assert key is not None
            assert key.api_key != "sk-test-key"  # Should be encrypted
            assert decrypt_value(key.api_key) == "sk-test-key"

        # 3. List Keys (should only show provider name)
        response = await ac.get("/api/settings/keys")
        assert response.status_code == 200
        data = response.json()
        assert "openai" in data["providers"]


@pytest.mark.asyncio
async def test_update_existing_key():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Set Initial Key
        await ac.put(
            "/api/settings/keys",
            json={"provider": "openai", "api_key": "sk-initial"},
        )

        # 2. Update Key
        await ac.put(
            "/api/settings/keys",
            json={"provider": "openai", "api_key": "sk-updated"},
        )

        # 3. Verify Update
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(ApiKey).where(ApiKey.provider == "openai")
            )
            key = result.scalars().first()
            assert decrypt_value(key.api_key) == "sk-updated"
