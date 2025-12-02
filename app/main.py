from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from app.features.runs.router import router as runs_router
from app.features.settings.router import router as settings_router
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
    {
        "name": "Settings",
        "description": "Configuration and API key management.",
    },
]

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="A minimal engine to track brand visibility across LLM responses.",
    version="0.1.0",
    openapi_tags=tags_metadata,
    lifespan=lifespan,
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "error": str(exc)},
    )


app.include_router(runs_router, prefix="/api")
app.include_router(settings_router, prefix="/api")


@app.get("/")
async def root():
    return {"message": "Welcome to the AI Visibility Platform API"}
