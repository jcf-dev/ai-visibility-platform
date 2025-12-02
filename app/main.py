from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.features.runs.router import router
from app.infrastructure.database import init_db
from app.infrastructure.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


tags_metadata = [
    {
        "name": "Runs",
        "description": "Operations to manage and analyze visibility runs.",
    },
]

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="A minimal engine to track brand visibility across LLM responses.",
    version="0.1.0",
    openapi_tags=tags_metadata,
    lifespan=lifespan,
)

app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    return {"message": "Welcome to the AI Visibility Platform API"}
