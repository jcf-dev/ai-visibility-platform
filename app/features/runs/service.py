import asyncio
import logging
import httpx
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from uuid import UUID
from app.features.runs.models import Run, Prompt, Brand, Response, ResponseBrandMention
from app.infrastructure.llm.client import get_llm_provider
from app.infrastructure.config import settings

logger = logging.getLogger(__name__)


class Orchestrator:
    def __init__(self, db_session_factory):
        self.db_session_factory = db_session_factory
        self.llm_provider = get_llm_provider()
        self.semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_REQUESTS)

    async def process_run(self, run_id: UUID, models: list[str]):
        """
        Main entry point to process a run in the background.
        """
        async with self.db_session_factory() as session:
            # 1. Fetch Run Details
            result = await session.execute(
                select(Run)
                .options(selectinload(Run.prompts), selectinload(Run.brands))
                .where(Run.id == run_id)
            )
            run = result.scalars().first()

            if not run:
                logger.error(f"Run {run_id} not found")
                return

            run.status = "running"
            await session.commit()

            prompts = run.prompts
            brands = run.brands

            # 2. Create Tasks
            tasks = []
            for prompt in prompts:
                for model in models:
                    tasks.append(
                        self._process_single_prompt(run_id, prompt, model, brands)
                    )

            # 3. Execute with concurrency control
            # We don't want to gather all at once if there are thousands.
            # But with a semaphore inside the task function, we can just gather them.
            # For truly massive scale, we'd use a queue, but for "hundreds/thousands",
            # asyncio.gather with a semaphore is sufficient.

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 4. Update Run Status
            # Check if any critical failures occurred (exceptions in tasks)
            failed_count = sum(1 for r in results if isinstance(r, Exception))

            if failed_count == len(tasks) and len(tasks) > 0:
                run.status = "failed"
            else:
                run.status = "completed"

            await session.commit()
            logger.info(f"Run {run_id} completed. Failed tasks: {failed_count}")

    async def _process_single_prompt(
        self, run_id: UUID, prompt: Prompt, model: str, brands: list[Brand]
    ):
        async with self.semaphore:
            # We create a NEW session for each task or small batch to avoid
            # long-lived session issues and to allow partial commits.
            async with self.db_session_factory() as session:
                try:
                    # Call LLM
                    llm_response = await self.llm_provider.generate(prompt.text, model)

                    # Analyze Response
                    mentions_data = self._analyze_mentions(llm_response.text, brands)

                    # Save Response
                    response_entry = Response(
                        run_id=run_id,
                        prompt_id=prompt.id,
                        model=model,
                        latency_ms=llm_response.latency_ms,
                        raw_text=llm_response.text,
                    )
                    session.add(response_entry)
                    await session.flush()  # Get ID

                    # Save Mentions
                    for m in mentions_data:
                        mention_entry = ResponseBrandMention(
                            response_id=response_entry.id,
                            brand_id=m["brand_id"],
                            mentioned=m["mentioned"],
                            position_index=m["position_index"],
                        )
                        session.add(mention_entry)

                    await session.commit()

                except Exception as e:
                    error_msg = str(e)
                    if isinstance(e, httpx.HTTPStatusError):
                        error_msg = f"HTTP {e.response.status_code}: {e.response.text}"

                    logger.error(f"Error processing prompt {prompt.id}: {error_msg}")

                    # Log failure in DB
                    async with self.db_session_factory() as err_session:
                        # Re-fetch prompt/run context if needed,
                        # or just insert a failed response
                        # For simplicity, we insert a failed response record
                        failed_response = Response(
                            run_id=run_id,
                            prompt_id=prompt.id,
                            model=model,
                            latency_ms=0.0,
                            raw_text="",
                            error=error_msg,
                        )
                        err_session.add(failed_response)
                        await err_session.commit()
                    # We don't re-raise here to allow other tasks to continue,
                    # but we return the exception so gather can see it.
                    # Actually, gather with return_exceptions=True will catch it
                    # if we raise.
                    raise e

    def _analyze_mentions(self, text: str, brands: list[Brand]) -> list[dict]:
        results = []
        text_lower = text.lower()
        for brand in brands:
            brand_lower = brand.name.lower()
            index = text_lower.find(brand_lower)
            results.append(
                {
                    "brand_id": brand.id,
                    "mentioned": index != -1,
                    "position_index": index if index != -1 else None,
                }
            )
        return results
