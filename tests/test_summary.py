import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.infrastructure.database import engine, Base
from app.features.runs.models import Run, Brand, Prompt, run_brands, run_prompts
from app.infrastructure.database import AsyncSessionLocal
from sqlalchemy import insert


@pytest.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_get_run_summary():
    # 1. Setup Data
    async with AsyncSessionLocal() as session:
        run = Run(status="completed")
        session.add(run)
        await session.flush()

        brand = Brand(name="Acme")
        session.add(brand)
        await session.flush()

        prompt = Prompt(text="Test Prompt")
        session.add(prompt)
        await session.flush()

        await session.execute(
            insert(run_brands).values(run_id=run.id, brand_id=brand.id)
        )
        await session.execute(
            insert(run_prompts).values(run_id=run.id, prompt_id=prompt.id)
        )

        await session.commit()
        run_id = run.id

    # 2. Call Summary Endpoint
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get(f"/api/runs/{run_id}/summary")

    assert response.status_code == 200
    data = response.json()

    assert data["run_id"] == str(run_id)
    assert data["total_prompts"] == 1
    assert len(data["metrics"]) == 1
    assert data["metrics"][0]["brand_name"] == "Acme"
