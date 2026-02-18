"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging import setup_logging, get_logger
from app.api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    setup_logging()
    logger = get_logger("main")

    settings = get_settings()
    logger.info(f"Starting {settings.APP_NAME}")
    logger.info(f"LLM: {settings.LLM_MODEL} | Embedding: {settings.EMBEDDING_MODEL}")
    logger.info(f"Pinecone index: {settings.PINECONE_INDEX_NAME}")

    # Pre-initialize services (validates connections at startup)
    try:
        from app.services.vector_store import get_vector_store
        from app.services.llm import get_llm_provider
        from app.services.embeddings import get_embedding_provider

        get_embedding_provider()
        get_llm_provider()
        store = get_vector_store()
        conn = store.check_connection()
        logger.info(f"Pinecone connection: {conn.get('connected', False)}")
    except Exception as e:
        logger.warning(f"Service pre-initialization warning: {e}")

    yield

    logger.info("Shutting down...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        description="Formula 1 RAG Assistant with hybrid retrieval and tool-augmented live data",
        version="2.0.0",
        lifespan=lifespan,
    )

    # CORS
    origins = [o.strip() for o in settings.CORS_ORIGINS.split(",")]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount API router
    app.include_router(router)

    # Health check at root
    @app.get("/")
    async def root():
        return {"status": "ok", "service": settings.APP_NAME, "version": "2.0.0"}

    return app


app = create_app()
