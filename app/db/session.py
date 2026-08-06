"""Async database engine, session factory, and FastAPI dependency."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import Settings, get_settings


def build_engine(settings: Settings) -> AsyncEngine:
    connect_args = {}
    # SQLite needs this to allow the connection to be used across the
    # async event loop's task boundaries in a single-process dev/test setup.
    if settings.database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    return create_async_engine(
        settings.database_url,
        echo=settings.database_echo,
        connect_args=connect_args,
        pool_pre_ping=True,
    )


_settings = get_settings()
engine: AsyncEngine = build_engine(_settings)
async_session_factory = async_sessionmaker(
    bind=engine, expire_on_commit=False, class_=AsyncSession
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: yields a request-scoped session, committing on
    success and rolling back on any unhandled exception."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
