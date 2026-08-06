"""FastAPI application factory.

The Telegram bot (app/bot) is a thin client of this API — it holds no
business logic of its own. This is the single source of truth for
document ingestion, tax calculation, and RAG question-answering.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.logging import configure_logging, get_logger
from app.services.rag.embedding_provider import TfidfEmbeddingProvider
from app.services.rag.generation_provider import ExtractiveGenerationProvider
from app.services.rag.rag_service import RAGService
from app.services.rag.retriever import Retriever
from app.services.rag.vector_store import InMemoryVectorStore

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    retriever = Retriever.from_directory(
        settings.knowledge_base_dir, TfidfEmbeddingProvider(), InMemoryVectorStore()
    )
    app.state.rag_service = RAGService(
        retriever,
        ExtractiveGenerationProvider(),
        top_k=settings.rag_top_k,
        min_score=settings.rag_min_score,
    )
    logger.info("rag_knowledge_base_loaded", directory=str(settings.knowledge_base_dir))

    yield


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings)

    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
    )

    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        logger.warning(
            "app_error",
            error_code=exc.error_code,
            path=request.url.path,
            message=exc.message,
        )
        return JSONResponse(
            status_code=exc.http_status,
            content={"error_code": exc.error_code, "message": exc.message, "details": exc.details},
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        # Never leak raw exception text to the caller (the legacy bot did
        # exactly this) — log full detail server-side, return a safe generic
        # message with a code an operator can grep for.
        logger.error("unhandled_exception", path=request.url.path, exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error_code": "internal_error", "message": "An unexpected error occurred."},
        )

    app.include_router(api_router, prefix=settings.api_v1_prefix)

    return app


app = create_app()
