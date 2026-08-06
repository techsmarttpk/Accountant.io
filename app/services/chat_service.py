"""Orchestrates a RAG question/answer turn: run retrieval+generation,
persist the exchange (with its cited sources) for history/audit, and log it."""

from __future__ import annotations

import uuid

from app.db.models.chat import ChatMessage
from app.repositories.chat_repository import ChatRepository
from app.services.audit_service import AuditService
from app.services.rag.rag_service import RagAnswer, RAGService


class ChatService:
    def __init__(
        self,
        chat_repository: ChatRepository,
        rag_service: RAGService,
        audit_service: AuditService,
    ) -> None:
        self._repo = chat_repository
        self._rag = rag_service
        self._audit = audit_service

    async def ask(self, *, user_id: uuid.UUID, question: str) -> RagAnswer:
        answer = self._rag.answer(question)

        await self._repo.add(
            ChatMessage(
                user_id=user_id,
                question=question,
                answer=answer.answer,
                retrieved_sources=[
                    {"source": s.source, "title": s.title, "score": s.score, "excerpt": s.excerpt}
                    for s in answer.sources
                ],
                confidence=answer.confidence,
            )
        )

        await self._audit.record(
            action="chat.answered" if answer.grounded else "chat.unanswered_ungrounded",
            entity_type="chat_message",
            user_id=user_id,
            context={"question": question[:280], "confidence": answer.confidence},
            success=answer.grounded,
        )

        return answer
