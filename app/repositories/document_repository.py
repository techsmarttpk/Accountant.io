from app.db.models.document import Document
from app.repositories.base import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    model = Document
