"""Generic repository base class.

Keeps raw SQLAlchemy query construction out of the service layer. Services
depend on repositories, never on `AsyncSession` directly — this is what
makes the service layer trivially unit-testable with an in-memory fake.
"""

import uuid
from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    model: type[ModelType]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, id_: uuid.UUID) -> ModelType | None:
        return await self.session.get(self.model, id_)

    async def add(self, instance: ModelType) -> ModelType:
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[ModelType]:
        result = await self.session.execute(
            select(self.model).limit(limit).offset(offset)
        )
        return list(result.scalars().all())
