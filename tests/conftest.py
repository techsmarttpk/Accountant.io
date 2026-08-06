"""Shared pytest fixtures.

Tests run against an in-memory SQLite database (via `StaticPool` so every
connection in the pool shares the same in-memory DB) rather than the
configured production database — this is what makes the suite fast,
hermetic, and runnable with zero external services.
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.db.base import Base
from app.db.models import *  # noqa: F401,F403 -- populate metadata
from app.db.session import get_db
from app.main import create_app

TEST_INTERNAL_API_KEY = get_settings().internal_api_key.get_secret_value()


@pytest.fixture
async def db_engine():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def db_session(db_engine) -> AsyncSession:
    session_factory = async_sessionmaker(bind=db_engine, expire_on_commit=False, class_=AsyncSession)
    async with session_factory() as session:
        yield session


@pytest.fixture
async def app(db_session):
    application = create_app()

    async def override_get_db():
        yield db_session

    application.dependency_overrides[get_db] = override_get_db

    async with application.router.lifespan_context(application):
        yield application


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def auth_headers():
    def _make(telegram_user_id: int = 1001) -> dict:
        return {
            "X-Internal-Api-Key": TEST_INTERNAL_API_KEY,
            "X-Telegram-User-Id": str(telegram_user_id),
        }

    return _make
