import pytest
from unittest.mock import AsyncMock
from app.features.runs.service import Orchestrator
from app.features.runs.models import Run, Brand, Prompt, Response
from app.infrastructure.database import AsyncSessionLocal, engine, Base
from sqlalchemy import select
from app.infrastructure.llm.client import LLMResponse

@pytest.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.mark.asyncio
async def test_idempotency():
    # 1. Setup Data
    async with AsyncSessionLocal() as session:
        run = Run(status="pending")
        session.add(run)
        await session.flush()
        session.add(Brand(run_id=run.id, name="Acme"))
        session.add(Prompt(run_id=run.id, text="Test Prompt"))
        await session.commit()
        run_id = run.id

    # 2. Mock LLM Provider
    mock_provider = AsyncMock()
    mock_provider.generate.return_value = LLMResponse(text="Response with Acme", latency_ms=100)

    orchestrator = Orchestrator(AsyncSessionLocal)
    orchestrator.llm_provider = mock_provider

    # 3. Run Orchestrator First Time
    await orchestrator.process_run(run_id, ["mock-model"])
    assert mock_provider.generate.call_count == 1

    # 4. Run Orchestrator Second Time
    await orchestrator.process_run(run_id, ["mock-model"])
    
    # 5. Verify LLM was NOT called again
    assert mock_provider.generate.call_count == 1

@pytest.mark.asyncio
async def test_error_handling():
    # 1. Setup Data
    async with AsyncSessionLocal() as session:
        run = Run(status="pending")
        session.add(run)
        await session.flush()
        session.add(Brand(run_id=run.id, name="Acme"))
        session.add(Prompt(run_id=run.id, text="Test Prompt"))
        await session.commit()
        run_id = run.id

    # 2. Mock LLM Provider to Fail
    mock_provider = AsyncMock()
    mock_provider.generate.side_effect = Exception("LLM Failed")

    orchestrator = Orchestrator(AsyncSessionLocal)
    orchestrator.llm_provider = mock_provider

    # 3. Run Orchestrator
    await orchestrator.process_run(run_id, ["mock-model"])

    # 4. Verify Run Status is Failed (since all tasks failed)
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Run).where(Run.id == run_id))
        run = result.scalars().first()
        assert run.status == "failed"

        # Verify Error Response was saved
        result = await session.execute(select(Response).where(Response.run_id == run_id))
        response = result.scalars().first()
        assert response is not None
        assert response.error == "LLM Failed"
        assert response.latency_ms == 0
