from app.db.models.chat import ChatMessage
from app.repositories.base import BaseRepository


class ChatRepository(BaseRepository[ChatMessage]):
    model = ChatMessage
