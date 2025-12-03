from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, insert
from sqlalchemy.orm import selectinload
from uuid import UUID, uuid4
import hashlib
import json

from app.infrastructure.database import get_db, AsyncSessionLocal
from app.features.runs.models import Run, Brand, Prompt, Response, ResponseBrandMention, run_brands, run_prompts
from app.features.runs.service import get_or_create_brand, get_or_create_prompt
from app.features.runs.schemas import (
    RunCreate,
    RunRead,
    RunDetail,
    RunSummary,
    BrandVisibilityMetric,
)
from app.features.runs.service import Orchestrator
from app.infrastructure.llm.client import get_llm_provider

router = APIRouter(tags=["Runs"])


@router.get(
    "/models",
    summary="List available models",
    description="Fetch available models from all configured providers.",
)
async def list_models():
    provider = get_llm_provider()
    # The MultiProviderRouter has a list_models method
    if hasattr(provider, "list_models"):
        return await provider.list_models()
    return {}


def _calculate_input_hash(brands: list[str], prompts: list[str], models: list[str]) -> str:
    data = {
        "brands": sorted(brands),
        "prompts": sorted(prompts),
        "models": sorted(models),
    }
    serialized = json.dumps(data, sort_keys=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


@router.post(
    "/runs",
    response_model=RunRead,
    status_code=201,
    summary="Create a new run",
    description=(
        "Start a new visibility analysis run with a list of brands and prompts."
    ),
)
async def create_run(
    run_in: RunCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    # Calculate hash to avoid duplicate runs
    input_hash = _calculate_input_hash(run_in.brands, run_in.prompts, run_in.models)

    # Check for existing run (excluding failed ones, which we might want to retry)
    stmt = (
        select(Run)
        .options(selectinload(Run.brands), selectinload(Run.prompts))
        .where(
            Run.input_hash == input_hash,
            Run.status.in_(["pending", "running", "completed"]),
        )
    )
    result = await db.execute(stmt)
    existing_run = result.scalars().first()

    if existing_run:
        return existing_run

    # 1. Create Run Record
    new_run = Run(
        id=uuid4(),
        notes=run_in.notes,
        status="pending",
        input_hash=input_hash,
    )
    db.add(new_run)
    await db.flush()  # Get ID

    # 2. Get or Create Brands and Prompts (case-insensitive upsert)
    for brand_name in run_in.brands:
        brand = await get_or_create_brand(db, brand_name)
        # Insert into association table
        await db.execute(
            insert(run_brands).values(run_id=new_run.id, brand_id=brand.id)
        )
    
    for prompt_text in run_in.prompts:
        prompt = await get_or_create_prompt(db, prompt_text)
        # Insert into association table
        await db.execute(
            insert(run_prompts).values(run_id=new_run.id, prompt_id=prompt.id)
        )

    await db.commit()

    # Reload to get relationships for response
    query = (
        select(Run)
        .options(selectinload(Run.brands), selectinload(Run.prompts))
        .where(Run.id == new_run.id)
    )
    result = await db.execute(query)
    run_loaded = result.scalars().first()

    # 3. Trigger Background Processing
    orchestrator = Orchestrator(AsyncSessionLocal)
    background_tasks.add_task(orchestrator.process_run, new_run.id, run_in.models)

    return run_loaded


@router.get(
    "/runs",
    response_model=list[RunRead],
    summary="List all runs",
    description="Retrieve a list of all runs, ordered by creation date descending.",
)
async def list_runs(
    skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)
):
    query = (
        select(Run)
        .options(selectinload(Run.brands), selectinload(Run.prompts))
        .order_by(Run.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().all()


@router.get(
    "/runs/{run_id}",
    response_model=RunDetail,
    summary="Get run details",
    description=(
        "Retrieve full details of a run, including all responses and brand mentions."
    ),
)
async def get_run(run_id: UUID, db: AsyncSession = Depends(get_db)):
    query = (
        select(Run)
        .options(
            selectinload(Run.brands),
            selectinload(Run.prompts),
            selectinload(Run.responses)
            .selectinload(Response.mentions)
            .selectinload(ResponseBrandMention.brand),
            selectinload(Run.responses).selectinload(Response.prompt),
        )
        .where(Run.id == run_id)
    )

    result = await db.execute(query)
    run = result.scalars().first()

    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    # Helper to format mentions for the schema
    responses_data = []
    for r in run.responses:
        mentions_data = []
        for m in r.mentions:
            mentions_data.append(
                {
                    "brand_name": m.brand.name if m.brand else "Unknown",
                    "mentioned": m.mentioned,
                    "count": m.count,
                    "position_index": m.position_index,
                }
            )

        responses_data.append(
            {
                "id": r.id,
                "prompt_text": r.prompt.text if r.prompt else "Unknown",
                "model": r.model,
                "latency_ms": r.latency_ms or 0.0,
                "raw_text": r.raw_text or "",
                "mentions": mentions_data,
                "error": r.error,
            }
        )

    return {
        "id": run.id,
        "created_at": run.created_at,
        "status": run.status,
        "notes": run.notes,
        "brands": run.brands,
        "prompts": run.prompts,
        "responses": responses_data,
    }


@router.get(
    "/runs/{run_id}/summary",
    response_model=RunSummary,
    summary="Get run summary",
    description="Get aggregated visibility metrics for a specific run.",
)
async def get_run_summary(run_id: UUID, db: AsyncSession = Depends(get_db)):
    # Check if run exists
    run = await db.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    # Calculate metrics
    # Total prompts
    # Total responses
    # For each brand: % of responses where mentioned=True

    # We can do this with SQL aggregation or in python.
    # SQL is better for scale.

    # Total Prompts
    # Actually, total prompts configured vs total responses received.
    # run.prompts might be loaded, but let's count.

    # We need to join tables.

    # 1. Get Brands
    brands_result = await db.execute(select(Brand).join(Brand.runs).where(Run.id == run_id))
    brands = brands_result.scalars().all()

    # 2. Get Counts
    # This is a bit manual but clear.

    metrics = []

    # Total responses for this run
    total_responses_query = select(func.count(Response.id)).where(
        Response.run_id == run_id
    )
    total_responses = (await db.execute(total_responses_query)).scalar() or 0

    # Total prompts configured
    total_prompts_query = select(func.count(Prompt.id)).join(Prompt.runs).where(Run.id == run_id)
    total_prompts = (await db.execute(total_prompts_query)).scalar() or 0

    if total_responses == 0:
        for brand in brands:
            metrics.append(
                BrandVisibilityMetric(
                    brand_name=brand.name,
                    total_prompts=total_prompts,
                    mentions=0,
                    total_mentions_count=0,
                    visibility_score=0.0,
                )
            )
    else:
        for brand in brands:
            # Count mentions (responses where brand is mentioned)
            mentions_count_query = (
                select(func.count(ResponseBrandMention.id))
                .join(Response)
                .where(
                    Response.run_id == run_id,
                    ResponseBrandMention.brand_id == brand.id,
                    ResponseBrandMention.mentioned.is_(True),
                )
            )
            mentions_count = (await db.execute(mentions_count_query)).scalar() or 0

            # Total count of mentions (sum of counts in all responses)
            total_mentions_count_query = (
                select(func.sum(ResponseBrandMention.count))
                .join(Response)
                .where(
                    Response.run_id == run_id,
                    ResponseBrandMention.brand_id == brand.id,
                )
            )
            total_mentions_count = (await db.execute(total_mentions_count_query)).scalar() or 0

            metrics.append(
                BrandVisibilityMetric(
                    brand_name=brand.name,
                    total_prompts=total_prompts,
                    mentions=mentions_count,
                    total_mentions_count=total_mentions_count,
                    visibility_score=(mentions_count / total_responses) * 100.0,
                )
            )

    return RunSummary(
        run_id=run_id,
        status=run.status,
        total_prompts=total_prompts,
        total_responses=total_responses,
        metrics=metrics,
    )
