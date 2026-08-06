from sqlalchemy import select

from app.db.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    async def get_by_telegram_id(self, telegram_user_id: int) -> User | None:
        result = await self.session.execute(
            select(User).where(User.telegram_user_id == telegram_user_id)
        )
        return result.scalar_one_or_none()

    async def get_or_create_by_telegram_id(
        self, telegram_user_id: int, display_name: str | None = None
    ) -> User:
        user = await self.get_by_telegram_id(telegram_user_id)
        if user is not None:
            return user
        return await self.add(User(telegram_user_id=telegram_user_id, display_name=display_name))
