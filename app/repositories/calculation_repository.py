from sqlalchemy import select

from app.db.models.calculation import Calculation
from app.repositories.base import BaseRepository


class CalculationRepository(BaseRepository[Calculation]):
    model = Calculation

    async def list_for_user(self, user_id, *, limit: int = 20) -> list[Calculation]:
        result = await self.session.execute(
            select(Calculation)
            .where(Calculation.user_id == user_id)
            .order_by(Calculation.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
