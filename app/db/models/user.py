from __future__ import annotations

import uuid

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    # Telegram is the only identity provider today. Nullable + unique so a
    # future web/OAuth signup path can create a User row with no Telegram
    # id and link one later.
    telegram_user_id: Mapped[int | None] = mapped_column(
        BigInteger, unique=True, index=True, nullable=True
    )
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    documents: Mapped[list["Document"]] = relationship(back_populates="user")
    calculations: Mapped[list["Calculation"]] = relationship(back_populates="user")

    def __repr__(self) -> str:  # pragma: no cover - debugging aid only
        return f"User(id={self.id}, telegram_user_id={self.telegram_user_id})"
