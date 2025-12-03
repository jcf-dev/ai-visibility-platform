import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.infrastructure.database import engine, Base


@pytest.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_duplicate_run_deduplication():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {
            "brands": ["BrandA", "BrandB"],
            "prompts": ["Prompt 1"],
            "models": ["mock-model"],
        }

        # First request
        response1 = await ac.post("/api/runs", json=payload)
        assert response1.status_code == 201
        data1 = response1.json()
        run_id1 = data1["id"]

        # Second request (same payload)
        response2 = await ac.post("/api/runs", json=payload)
        assert response2.status_code == 201
        data2 = response2.json()
        run_id2 = data2["id"]

        assert run_id1 == run_id2

        # Third request (different payload)
        payload_diff = {
            "brands": ["BrandA", "BrandB"],
            "prompts": ["Prompt 2"],  # Different prompt
            "models": ["mock-model"],
        }
        response3 = await ac.post("/api/runs", json=payload_diff)
        assert response3.status_code == 201
        data3 = response3.json()
        run_id3 = data3["id"]

        assert run_id1 != run_id3


@pytest.mark.asyncio
async def test_case_insensitive_brand_and_prompt_upsert():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # First run with "BrandA" and "Prompt 1"
        response1 = await ac.post(
            "/api/runs",
            json={
                "brands": ["BrandA"],
                "prompts": ["Prompt 1"],
                "models": ["mock-model"],
            },
        )
        assert response1.status_code == 201
        data1 = response1.json()
        brand_id1 = data1["brands"][0]["id"]
        prompt_id1 = data1["prompts"][0]["id"]

        # Second run with "branda" (lowercase) and "prompt 1" (lowercase)
        response2 = await ac.post(
            "/api/runs",
            json={
                "brands": ["branda"],
                "prompts": ["prompt 1"],
                "models": ["mock-model"],
            },
        )
        assert response2.status_code == 201
        data2 = response2.json()
        brand_id2 = data2["brands"][0]["id"]
        prompt_id2 = data2["prompts"][0]["id"]

        # Should reuse the same brand and prompt (case-insensitive)
        assert brand_id1 == brand_id2
        assert prompt_id1 == prompt_id2

        # Third run with "BRANDA" (uppercase)
        response3 = await ac.post(
            "/api/runs",
            json={
                "brands": ["BRANDA"],
                "prompts": ["PROMPT 1"],
                "models": ["mock-model"],
            },
        )
        assert response3.status_code == 201
        data3 = response3.json()
        brand_id3 = data3["brands"][0]["id"]
        prompt_id3 = data3["prompts"][0]["id"]

        # Should still reuse the same brand and prompt
        assert brand_id1 == brand_id3
        assert prompt_id1 == prompt_id3
