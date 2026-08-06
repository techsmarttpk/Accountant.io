import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    telegram_user_id: int | None
    display_name: str | None
    created_at: datetime
