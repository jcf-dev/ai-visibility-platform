import pytest
from app.features.runs.service import Orchestrator
from app.features.runs.models import Run, Brand, Prompt
from app.infrastructure.database import AsyncSessionLocal, init_db, engine, Base
from sqlalchemy import select
from sqlalchemy.orm import selectinload

@pytest.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.mark.asyncio
async def test_orchestrator_flow():
    # 1. Setup Data
    async with AsyncSessionLocal() as session:
        run = Run(status="pending")
        session.add(run)
        await session.flush()
        
        session.add(Brand(run_id=run.id, name="Acme"))
        session.add(Prompt(run_id=run.id, text="Test Prompt"))
        await session.commit()
        run_id = run.id

    # 2. Run Orchestrator
    orchestrator = Orchestrator(AsyncSessionLocal)
    await orchestrator.process_run(run_id, ["mock-model"])

    # 3. Verify
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Run)
            .options(selectinload(Run.responses))
            .where(Run.id == run_id)
        )
        run = result.scalars().first()
        
        assert run.status == "completed"
        assert len(run.responses) == 1
        assert run.responses[0].model == "mock-model"

@pytest.mark.asyncio
async def test_orchestrator_multi_model():
    # 1. Setup Data
    async with AsyncSessionLocal() as session:
        run = Run(status="pending")
        session.add(run)
        await session.flush()
        
        session.add(Brand(run_id=run.id, name="Acme"))
        session.add(Prompt(run_id=run.id, text="Test Prompt"))
        await session.commit()
        run_id = run.id

    # 2. Run Orchestrator with multiple models
    orchestrator = Orchestrator(AsyncSessionLocal)
    await orchestrator.process_run(run_id, ["mock-1", "mock-2"])

    # 3. Verify
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Run)
            .options(selectinload(Run.responses))
            .where(Run.id == run_id)
        )
        run = result.scalars().first()
        
        assert run.status == "completed"
        assert len(run.responses) == 2
        models = {r.model for r in run.responses}
        assert "mock-1" in models
        assert "mock-2" in models
